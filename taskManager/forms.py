# Vulnerable Task Manager

""" forms.py contains various Django forms for the application """

from taskManager.models import Project, Task
from django import forms
from django.contrib.auth.models import User


def get_my_choices_users():
    """ Retrieves a list of all users in the system
        for the user management page
    """

    user_list = User.objects.order_by('date_joined')
    user_tuple = []
    counter = 1
    for user in user_list:
        user_tuple.append((counter, user))
        counter = counter + 1
    return user_tuple


def get_my_choices_tasks(current_proj):
    """ Retrieves all tasks in the system
        for the task management page
    """

    task_list = []
    tasks = Task.objects.all()
    for task in tasks:
        if task.project == current_proj:
            task_list.append(task)

    task_tuple = []
    counter = 1
    for task in task_list:
        task_tuple.append((counter, task))
        counter = counter + 1
    return task_tuple


def get_my_choices_projects():
    """ Retrieves all projects in the system
        for the project management page
    """

    proj_list = Project.objects.all()
    proj_tuple = []
    counter = 1
    for proj in proj_list:
        proj_tuple.append((counter, proj))
        counter = counter + 1
    return proj_tuple

# A2: Broken Authentication and Session Management


class UserForm(forms.ModelForm):
    """ User registration form """
    class Meta:
        model = User
        exclude = ['groups', 'user_permissions', 'last_login', 'date_joined']


class ProjectFileForm(forms.Form):
    """ Used for uploading files attached to projects """
    name = forms.CharField(max_length=300)
    file = forms.FileField(required=False)
    url = forms.CharField(max_length=2048, required=False)

    def clean(self):
        check = [self.cleaned_data['file'], self.cleaned_data['url']]
        if any(check) and not all(check):
            return self.cleaned_data
        raise forms.ValidationError("Select either File or URL")


class ProfileForm(forms.Form):
    """ Provides a form for editing your own profile """
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.CharField(max_length=300, required=False)
    ssn = forms.CharField(max_length=11, required=False)
    dob = forms.DateField(required=False)
    picture = forms.FileField(required=False)
