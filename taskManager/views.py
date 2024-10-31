# Vulnerable Task Manager

import datetime
import mimetypes
import os
import re
import codecs
import subprocess
import requests
import io
import uuid
import logging

from django.http import (
    HttpResponse,  HttpResponseRedirect,
)
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from django.template import RequestContext
from django.db import connection

from django.views.decorators.csrf import csrf_exempt

from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import Group, User
from django.contrib.auth import logout
from django.contrib.auth.decorators import user_passes_test, login_required

from taskManager.models import Task, Project, Notes, File, UserProfile
from taskManager.misc import store_uploaded_file, store_url_data
from taskManager.forms import UserForm, ProjectFileForm, ProfileForm

from rest_framework.authtoken.models import Token

# Setup logging
logger = logging.getLogger('django')

@login_required
def manage_tasks(request, project_id):

    user = request.user
    proj = Project.objects.get(pk=project_id)
    logger.info('User %s managing tasks for project %s' % (user.username,proj.title))

    if user.is_authenticated:

        if user.has_perm('can_change_task'):

            if request.method == 'POST':

                userid = request.POST.get("userid")
                taskid = request.POST.get("taskid")

                user = User.objects.get(pk=userid)
                task = Task.objects.get(pk=taskid)

                task.users_assigned.add(user)

                return redirect('/taskManager/')
            else:
                return render(
                    request,
                    'taskManager/manage_tasks.html',
                    {
                        'tasks': Task.objects.filter(
                            project=proj).order_by('title'),
                        'users': User.objects.order_by('date_joined')})

        else:
            return redirect('/taskManager/', {'permission': False})

    return redirect('/taskManager/', {'logged_in': False})

@login_required
def manage_projects(request):

    user = request.user
    logger.info('User %s manage_projects' % (user.username))

    if user.is_authenticated:
        logged_in = True

        if user.has_perm('auth.change_group'):
            if request.method == 'POST':

                userid = request.POST.get("userid")
                projectid = request.POST.get("projectid")

                user = User.objects.get(pk=userid)
                project = Project.objects.get(pk=projectid)

                project.users_assigned.add(user)

                return redirect('/taskManager/')
            else:

                return render(
                    request,
                    'taskManager/manage_projects.html',
                    {
                        'projects': Project.objects.order_by('title'),
                        'users': User.objects.order_by('date_joined'),
                        'logged_in': logged_in})

        else:
            return redirect('/taskManager/', {'permission': False})

    return redirect('/taskManager/', {'logged_in': False})

# Group management

@login_required
def manage_groups(request):

    user = request.user
    logger.info('User %s manage_groups' % (user.username))

    if user.is_authenticated:

        user_list = User.objects.order_by('date_joined')

        if request.method == 'POST':

            post_data = request.POST.dict()

            accesslevel = post_data["accesslevel"].strip()

            if accesslevel in ['admin_g', 'project_managers', 'team_member']:

                # Create the group if it doesn't already exist
                try:
                    grp = Group.objects.get(name=accesslevel)
                except Group.DoesNotExist:
                    grp = Group.objects.create(name=accesslevel)
                specified_user = User.objects.get(pk=post_data["userid"])
                # Check if the user even exists
                if specified_user is None:
                    return redirect('/taskManager/', {'permission': False})
                specified_user.groups.add(grp)
                specified_user.save()
                return render(
                    request,
                    'taskManager/manage_groups.html',
                    {
                        'users': user_list,
                        'groups_changed': True,
                        'logged_in': True})
            else:
                return render(
                    request,
                    'taskManager/manage_groups.html',
                    {
                        'users': user_list,
                        'logged_in': True})

        else:
            if user.has_perm('auth.change_group'):
                return render(
                    request,
                    'taskManager/manage_groups.html',
                    {
                        'users': user_list,
                        'logged_in': True})
            else:
                return redirect('/taskManager/', {'permission': False})

    return redirect('/taskManager/', {'logged_in': False})

# Upload file
@login_required
def upload(request, project_id):

    logger.info('User %s upload %s' % (request.user.username,project_id))

    if request.method == 'POST':
        print(request.POST)
        print(project_id)
        proj = Project.objects.get(pk=project_id)
        form = ProjectFileForm(request.POST, request.FILES)
        ## kind of janky, you have to subimt a file and file by url, I wasn't sure how to get the form to validate
        if (form.is_valid()) and (proj.users_assigned.filter(id=request.user.id).exists()):
            if request.POST.get('url', False) != '':
                name = request.POST.get('name', False)
                url = request.POST.get('url', False)
                response = requests.get(url, timeout=15) #making request for image
                _file = response.content # taking response content and storing it in _file var
                content_type = response.headers["Content-Type"]
                if "image" in content_type:
                    upload_path = store_url_data(url, _file)
                else:
                    messages.warning(request, "Error in URL Upload")
                    # I don't know how to return the data _file.decode("utf-8")
                    return render(request, 'taskManager/upload.html', {'data': (_file.decode("utf-8"),"Good effort but we can't give you everything!")["security-credentials" in url] , 'name': name, 'url': url })

            else:
                name = request.POST.get('name', False)
                upload_path = store_uploaded_file(name, request.FILES['file'])

            #Insert file details into the database
            curs = connection.cursor()
            curs.execute(
                "insert into taskManager_file (name,path,project_id,uuid) values (%s, %s, %s, %s)",
                (name, upload_path, project_id, str(uuid.uuid4())))

            # file = File(
            #name = name,
            #path = upload_path,
            # project = proj)

            # file.save()

            return redirect('/taskManager/' + project_id +
                            '/project_details/', {'new_file_added': True})
        else:
            form = ProjectFileForm()
    else:
        form = ProjectFileForm()
    return render(
        request, 'taskManager/upload.html', {'form': form})

# File functions
@login_required
def download(request, file_id):

    logger.info('User %s download file %s' % (request.user.username,file_id))

    file = File.objects.get(pk=file_id)
    response = HttpResponse("yo", 200)
    if file.project.users_assigned.filter(id=request.user.id).exists():
        abspath = open(
            os.path.dirname(
                os.path.realpath(__file__)) +
            file.path,
            'rb')
        response = HttpResponse(content=abspath.read())
        response['Content-Type'] = mimetypes.guess_type(file.path)[0]
        response['Content-Disposition'] = 'attachment; filename=%s' % file.name
    else:
        response = HttpResponse('Unauthorized', status=401)

    return response

@login_required
def download_profile_pic(request, user_id):

    logger.info('User %s download profile pic for user %s' % (request.user.username,user_id))

    user = User.objects.get(pk=user_id)
    filepath = user.userprofile.image
    return redirect(filepath)

def belongs_to_project(user, project_id):
    project = Project.objects.get(pk=project_id)
    return project.users_assigned.filter(id=user.id).exists()

# Task functions
@login_required
def task_create(request, project_id):

    logger.info('User %s create task for project %s' % (request.user.username,project_id))
    if request.method == 'POST' and belongs_to_project(request.user, project_id):
        proj = Project.objects.get(pk=project_id)

        text = request.POST.get('text', False)
        task_title = request.POST.get('task_title', False)
        now = timezone.now()
        task_duedate = timezone.now() + datetime.timedelta(weeks=1)
        if request.POST.get('task_duedate') != '':
            task_duedate = datetime.datetime.strptime(
                request.POST.get('task_duedate', False),'%Y-%m-%d')

        task = Task(
            text=text,
            title=task_title,
            start_date=now,
            due_date=task_duedate,
            project=proj)

        task.save()
        task.users_assigned.add(request.user)

        return redirect('/taskManager/' + project_id +
                        '/project_details/', {'new_task_added': True})
    else:
        return render(
            request, 'taskManager/task_create.html', {'proj_id': project_id})

# end ID
@login_required
def task_edit(request, project_id, task_id):

    proj = Project.objects.get(pk=project_id)
    task = Task.objects.get(pk=task_id)

    logger.info('User %s editing task %s for project %s' % (request.user.username,project_id,task_id))

    if request.method == 'POST' and belongs_to_project(request.user, project_id):

        if task.project == proj:

            text = request.POST.get('text', False)
            task_title = request.POST.get('task_title', False)
            task_completed = request.POST.get('task_completed', False)
            if request.POST.get('task_duedate') != '':
                task_duedate = datetime.datetime.strptime(
                    request.POST.get('task_duedate', False),'%Y-%m-%d')

            task.title = task_title
            task.text = text
            task.completed = True if task_completed == "1" else False
            task.due_date = task_duedate
            task.save()

        return redirect('/taskManager/' + project_id + '/' + task_id)
    else:
        due_date = task.due_date.strftime('%Y-%m-%d')
        return render(
            request, 'taskManager/task_edit.html', {'task': task, 'due_date': due_date})

# TODO: Check authorization
@login_required
def task_delete(request, project_id, task_id):
    proj = Project.objects.get(pk=project_id)
    task = Task.objects.get(pk=task_id)
    logger.info('User %s deleting task %s from project %s' % (request.user.username,project_id,task_id))
    if proj is not None and belongs_to_project(request.user, project_id):
        if task is not None and task.project == proj:
            task.delete()

    return redirect('/taskManager/' + project_id + '/project_details/')

# TODO: additional task completion checks
@login_required
def task_complete(request, project_id, task_id):
    proj = Project.objects.get(pk=project_id)
    task = Task.objects.get(pk=task_id)
    logger.info('User %s completed task %s for project %s' % (request.user.username,project_id,task_id))
    if proj is not None and belongs_to_project(request.user, project_id):
        if task is not None and task.project == proj:
            task.completed = not task.completed
            task.save()

    return redirect('/taskManager/' + project_id + '/project_details/')


def can_create_project(user):
    return user.has_perm('taskManager.add_project')

def can_edit_project(user):
    return user.has_perm('taskManager.change_project')

def can_delete_project(user):
    return user.has_perm('taskManager.delete_project')

@login_required
@user_passes_test(can_create_project)
def project_create(request):

    if request.method == 'POST':

        title = request.POST.get('title', False)
        text = request.POST.get('text', False)
        project_priority = int(request.POST.get('project_priority', False))
        now = timezone.now()
        project_duedate = timezone.make_aware(datetime.datetime.strptime(
            request.POST.get('project_duedate', False),'%Y-%m-%d'))

        project = Project(title=title,
                          text=text,
                          priority=project_priority,
                          due_date=project_duedate,
                          start_date=now)
        project.save()
        project.users_assigned.add(request.user)

        return redirect('/taskManager/', {'new_project_added': True})
    else:
        return render(
            request,
            'taskManager/project_create.html',
            {})


# Project editing must allow both GET and POST
@login_required
@user_passes_test(can_edit_project)
def project_edit(request, project_id):

    proj = Project.objects.get(pk=project_id)

    if request.method == 'POST':

        title = request.POST.get('title', False)
        text = request.POST.get('text', False)
        project_priority = int(request.POST.get('project_priority', False))
        project_duedate = timezone.make_aware(datetime.datetime.strptime(
            request.POST.get('project_duedate', False),'%Y-%m-%d'))

        proj.title = title
        proj.text = text
        proj.priority = project_priority
        proj.due_date = project_duedate
        proj.save()

        return redirect('/taskManager/' + project_id + '/project_details/')
    else:
        due_date = proj.due_date.strftime('%Y-%m-%d')
        return render(
            request, 'taskManager/project_edit.html', {'proj': proj, 'due_date': due_date})

# Project deletion
@login_required
@user_passes_test(can_delete_project)
def project_delete(request, project_id):
    # Delete a project here
    project = Project.objects.get(pk=project_id)
    if belongs_to_project(user, project_id):
        project.delete()
    return redirect('/taskManager/dashboard')

# Authentification functions
def logout_view(request):
    logger.info('User %s logout' % (request.user.username))
    logout(request)
    return redirect(request.GET.get('redirect', '/taskManager/'))


def login(request):
    if request.method == 'POST':
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)

        if User.objects.filter(username=username).exists():
            user = authenticate(username=username, password=password)
            if user is not None:
                logger.info(user)
                if user.is_active:
                    logger.info('Succesful Login (%s)' % (username))
                    auth_login(request, user)
                    # Redirect to a success page.
                    return HttpResponseRedirect(request.GET.get('next','/taskManager/'))
                else:
                    logger.info('Disabled Account (%s:%s)' % (username,password))
                    # Return a 'disabled account' error message
                    return redirect('/taskManager/', {'disabled_user': True})
            else:
                # Return an 'invalid login' error message.
                logger.info('Failed login (%s:%s)' % (username,password))
                return render(request,
                              'taskManager/login.html',
                              {'failed_login': False, 'username': username})
        else:
            logger.info('Invalid User (%s:%s)' % (username,password))
            return render(request,
                          'taskManager/login.html',
                          {'invalid_username': False, 'username': username})
    else:
        return render(request,'taskManager/login.html', {})


def register(request):

    context = RequestContext(request)

    registered = False

    if request.method == 'POST':

        user_form = UserForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            user.set_password(user.password)

            # add user to lowest permission group

            grp = Group.objects.get(name='team_member')
            user.groups.add(grp)

            user.userProfile = UserProfile.objects.create(user=user)
            user.userProfile.dob = request.POST.get('dob', "99/99/99")
            user.userProfile.ssn = request.POST.get('ssn', "999-99-9999")
            Token.objects.create(user=user)
            user.userProfile.save()
            user.is_active=True
            user.save()

            # Update our variable to tell the template registration was
            # successful.
            registered = True

        else:
            print(user_form.errors)

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()

    # Render the template depending on the context.
    return render(
        request,
        'taskManager/register.html',
        {'user_form': user_form, 'registered': registered})

@login_required
def index(request):
    sorted_projects = Project.objects.order_by('-start_date')

    admin_level = False

    if request.user.groups.filter(name='admin_g').exists():
        admin_level = True

    list_to_show = []
    for project in sorted_projects:
        if(project.users_assigned.filter(username=request.user.username)).exists():
            list_to_show.append(project)

    if request.user.is_authenticated:
        return redirect("/taskManager/dashboard")
    else:
        return render(
            request,
            'taskManager/index.html',
            {'project_list': sorted_projects,
             'user': request.user,
             'admin_level': admin_level}
        )

# View all user information
@login_required
@user_passes_test(lambda u: u.is_superuser)
def view_all_users(request):
    return render(request, 'taskManager/view_all_users.html', {'users' : User.objects.all()})

def profile_view(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return redirect("/taskManager/dashboard")

    if request.user.groups.filter(name='admin_g').exists():
        role = "Admin"
    elif request.user.groups.filter(name='project_managers').exists():
        role = "Project Manager"
    else:
        role = "Team Member"

    sorted_projects = Project.objects.filter(
        users_assigned=request.user.id).order_by('title')

    return render(request, 'taskManager/profile_view.html',
                  {'user': user, 'role': role, 'project_list': sorted_projects})

@login_required
def project_details(request, project_id):
    proj = Project.objects.extra(select={'total_completed_tasks': "100 * (select count(*) from taskManager_task where completed=1 and project_id = %s)/(select count(*) from taskManager_task where project_id = %s)" % (project_id, project_id)}).get(pk=project_id.split()[0])
    user_can_edit = request.user.has_perm('project_edit')

    return render(request, 'taskManager/project_details.html',
                  {'proj': proj, 'user_can_edit': user_can_edit})

# Note creation
@login_required
def note_create(request, project_id, task_id):
    parent_task = Task.objects.get(pk=task_id)
    if request.method == 'POST' and belongs_to_project(request.user, parent_task.project.id):

        note_title = request.POST.get('note_title', False)
        text = request.POST.get('text', False)

        note = Notes(
            title=note_title,
            text=text,
            user=request.user,
            task=parent_task)

        note.save()
        return redirect('/taskManager/' + project_id + '/' +
                        task_id, {'new_note_added': True})
    else:
        return render(
            request, 'taskManager/note_create.html', {'task_id': task_id} )

# Notes associated with tasks
@login_required
def note_edit(request, project_id, task_id, note_id):

    proj = Project.objects.get(pk=project_id)
    task = Task.objects.get(pk=task_id)
    note = Notes.objects.get(pk=note_id)

    if not belongs_to_project(request.user, task.project.id):
        return HttpResponse('Unauthorized', status=401)

    if request.method == 'POST':

        if task.project == proj:

            if note.task == task:

                text = request.POST.get('text', False)
                note_title = request.POST.get('note_title', False)

                note.title = note_title
                note.text = text
                note.save()

        return redirect('/taskManager/' + project_id + '/' + task_id)
    else:
        return render(
            request, 'taskManager/note_edit.html', {'note': note})

# Allows the user to delete notes
@login_required
def note_delete(request, project_id, task_id, note_id):
    proj = Project.objects.get(pk=project_id)
    task = Task.objects.get(pk=task_id)
    note = Notes.objects.get(pk=note_id)

    if proj is not None:
        if task is not None and task.project == proj and belongs_to_project(request.user, task.project.id):
            if note is not None and note.task == task:
                note.delete()

    return redirect('/taskManager/' + project_id + '/' + task_id)

@login_required
def task_details(request, project_id, task_id):

    task = Task.objects.get(pk=task_id)
    if not belongs_to_project(request.user, task.project.id):
        return HttpResponse('Unauthorized', status=401)

    logged_in = True

    if not request.user.is_authenticated:
        logged_in = False

    admin_level = False
    if request.user.groups.filter(name='admin_g').exists():
        admin_level = True

    pmanager_level = False
    if request.user.groups.filter(name='project_managers').exists():
        pmanager_level = True

    assigned_to = False
    if task.users_assigned.filter(username=request.user.username).exists():
        assigned_to = True
    elif admin_level:
        assigned_to = True
    elif pmanager_level:
        project_users = task.project.users_assigned
        if project_users.filter(username=request.user.username).exists():
            assigned_to = True

    return render(request,
                  'taskManager/task_details.html',
                  {'task': task,
                   'assigned_to': assigned_to,
                   'logged_in': logged_in,
                   'completed_task': "Yes" if task.completed else "No"})

def dashboard(request):
    sorted_projects = Project.objects.filter(
        users_assigned=request.user.id).order_by('title')
    sorted_tasks = Task.objects.filter(
        users_assigned=request.user.id).order_by('title')
    return render(request,
                  'taskManager/dashboard.html',
                  {'project_list': sorted_projects,
                   'user': request.user,
                   'task_list': sorted_tasks})

@login_required
def project_list(request):
    sorted_projects = Project.objects.filter(
        users_assigned=request.user.id).order_by('title')
    user_can_edit = request.user.has_perm('project_edit')
    user_can_delete = request.user.has_perm('project_delete')
    user_can_add = request.user.has_perm('project_add')
    return render(request,
                  'taskManager/project_list.html',
                  {'project_list': sorted_projects,
                   'user': request.user,
                   'user_can_edit': user_can_edit,
                   'user_can_delete': user_can_delete,
                   'user_can_add': user_can_add})

@login_required
def task_list(request):
    my_task_list = Task.objects.filter(users_assigned=request.user.id)
    return render(request, 'taskManager/task_list.html',
                  {'task_list': my_task_list, 'user': request.user})

@login_required
def search(request):
    query = request.GET.get('q', '')

    my_project_list = Project.objects.filter(
        users_assigned=request.user.id).filter(
            title__icontains=query).order_by('title')

    # TODO Task list query is complicated, switch to using ORM sometime soon.
    task_query = "%%" + query + "%%"
    sql = "select * from taskManager_task as t INNER JOIN taskManager_task_users_assigned as a ON t.id = a.task_id WHERE t.text LIKE '%s' OR t.title LIKE '%s' AND a.user_id = %d" % (task_query,task_query,request.user.id)
    my_task_list = Task.objects.raw(sql)

    #my_task_list = Task.objects.filter(
    #    users_assigned=request.user.id).filter(
    #        title__icontains=query).order_by('title')
    return render(request,
                  'taskManager/search.html',
                  {'q': query,
                   'task_list': my_task_list,
                   'project_list': my_project_list,
                   'user': request.user})

@login_required
def profile(request):
    return render(request, 'taskManager/profile.html', {'user': request.user})

# Look up profiles by ID

@login_required
@csrf_exempt
def profile_by_id(request, user_id):
    user = User.objects.get(pk=user_id)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES)
        if len(request.POST.get('dob')) > 8:
          raise Exception("Birthday does not match format")
        # Need to figure out how to handle socials, compliance wants us to mask these
        # if len(request.POST.get('ssn')) > 11:
        #  raise Exception("SSN does not match format")
        if form.is_valid():
            if request.POST.get('first_name') != user.first_name:
                user.first_name = request.POST.get('first_name')
            if request.POST.get('last_name') != user.last_name:
                user.last_name = request.POST.get('last_name')
            if request.POST.get('email') != user.email:
                user.email = request.POST.get('email')
            if request.POST.get('dob') != user.userprofile.dob:
                user.userprofile.dob = request.POST.get('dob')
                user.userprofile.save()
            if request.POST.get('ssn') != user.userprofile.ssn:
                user.userprofile.ssn = request.POST.get('ssn')
                user.userprofile.save()
            if request.POST.get('password'):
                user.set_password(request.POST.get('password'))
            if request.FILES:
                user.userprofile.image = store_uploaded_file(user.get_full_name(
                ) + "." + request.FILES['picture'].name.split(".")[-1], request.FILES['picture'])
                user.userprofile.save()
            user.save()
            messages.info(request, "User Updated")
    else:
        form = ProfileForm()

    return render(request, 'taskManager/profile.html', {'user': user, 'form': form.as_table})

# Password reset needed
@csrf_exempt
def reset_password(request):

    if request.method == 'POST':

        reset_token = request.POST.get('reset_token')

        try:
            userprofile = UserProfile.objects.get(reset_token = reset_token)
            if timezone.now() > userprofile.reset_token_expiration:
                # Reset the token and move on
                userprofile.reset_token_expiration = timezone.now()
                userprofile.reset_token = ''
                userprofile.save()
                return redirect('/taskManager/')

        except UserProfile.DoesNotExist:
            messages.warning(request, 'Invalid password reset token')
            return render(request, 'taskManager/reset_password.html')

        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password != confirm_password:
            messages.warning(request, 'Passwords do not match')
            return render(request, 'taskManager/reset_password.html')

        # Reset the user's password + remove the tokens
        userprofile.user.set_password(new_password)
        userprofile.reset_token = ''
        userprofile.reset_token_expiration = timezone.now()
        userprofile.user.save()
        userprofile.save()

        messages.success(request, 'Password has been successfully reset')
        return redirect('/taskManager/login')

    return render(request, 'taskManager/reset_password.html')


@csrf_exempt
def forgot_password(request):

    if request.method == 'POST':
        t_email = request.POST.get('email')

        try:
            result = User.objects.raw("SELECT * FROM auth_user where email = '%s'" % t_email)

            if len(list(result)) > 0:
                reset_user = result[0]
                # Generate secure random 6 digit number
                res = ""
                nums = [x for x in os.urandom(6)]
                for x in nums:
                    res = res + str(x)

                reset_token = res[:6]
                reset_user.userprofile.reset_token = reset_token
                reset_user.userprofile.reset_token_expiration = timezone.now() + datetime.timedelta(minutes=10)
                reset_user.userprofile.save()
                reset_user.save()

                #reset_user.email_user(
                	#"Reset your password",
                	#"You can reset your password at /taskManager/reset_password/. Use \"{}\" as your token. This link will only work for 10 minutes.".format(reset_token))

                messages.success(request, 'Check your email for a reset token')
                return redirect('/taskManager/reset_password')
            else:
                messages.warning(request, 'Check your email for a reset token')
        except User.DoesNotExist:
            messages.warning(request, 'Check your email for a reset token')

    return render(request, 'taskManager/forgot_password.html')

@login_required
@csrf_exempt
def change_password(request):

    if request.method == 'POST':
        user = request.user
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password == confirm_password:
            user.set_password(new_password)
            user.save()
            messages.success(request, 'Password Updated')
        else:
            messages.warning(request, 'Passwords do not match')

    return render(request,
                  'taskManager/change_password.html',
                  {'user': request.user})

def tm_settings(request):
    settings_list = request.META
    return render(request, 'taskManager/settings.html', {'settings': settings_list})

def view_img(request):
    img_url = request.GET.get('u')
    return render(request, 'taskManager/view_img.html', {'img_url': img_url})

@csrf_exempt
def ping(request):

    data = ""
    if request.method == 'POST':
        ip = request.POST.get('ip')
        if re.match('.*(rm|sudo|wget|curl|su|shred) .*',ip,re.I):
            data = "Nice try on the dangerous commands, but no"
        else:
            cmd = "ping -c 5 %s" % ip
            data = subprocess.getoutput(cmd)

    return render(request, 'taskManager/ping.html', {'data': data})
