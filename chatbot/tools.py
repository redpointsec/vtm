import datetime

from django.contrib.auth.models import User
from django.apps import apps
from django.db.models import Q
from django.db import models as django_models
from django.utils import timezone

from taskManager.models import File, Notes, Project, Task, UserProfile


def _format_datetime(value):
    return value.strftime('%Y-%m-%d') if value else 'No due date'


def _parse_date(value, default=None):
    if not value:
        return default
    parsed = datetime.datetime.strptime(value, '%Y-%m-%d')
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed)
    return parsed


def _find_project(identifier):
    if not identifier:
        raise ValueError('project_id or project_uuid is required')
    lookup = {'uuid': identifier} if '-' in str(identifier) else {'pk': identifier}
    return Project.objects.get(**lookup)


def _find_task(identifier):
    if not identifier:
        raise ValueError('task_id or task_uuid is required')
    lookup = {'uuid': identifier} if '-' in str(identifier) else {'pk': identifier}
    return Task.objects.select_related('project').get(**lookup)


def _find_note(identifier):
    if not identifier:
        raise ValueError('note_id or note_uuid is required')
    lookup = {'uuid': identifier} if '-' in str(identifier) else {'pk': identifier}
    return Notes.objects.select_related('task', 'task__project').get(**lookup)


def _resolve_users(usernames):
    if not usernames:
        return []
    users = []
    for username in usernames:
        if not username:
            continue
        users.append(User.objects.get(username=username))
    return users


def _project_accessible(user, project):
    return user.is_staff or project.users_assigned.filter(pk=user.pk).exists()


def _task_accessible(user, task):
    return user.is_staff or task.users_assigned.filter(pk=user.pk).exists() or _project_accessible(user, task.project)


def _note_accessible(user, note):
    return user.is_staff or _task_accessible(user, note.task)


def _format_project(project):
    task_count = project.task_set.count()
    complete_count = project.task_set.filter(completed=True).count()
    assigned = ', '.join(project.users_assigned.values_list('username', flat=True)) or 'none'
    return (
        f'Project #{project.pk} ({project.uuid}): "{project.title}" - {project.text} '
        f'(Priority: {project.priority}, Due: {_format_datetime(project.due_date)}, '
        f'Tasks: {complete_count}/{task_count} complete, Users: {assigned})'
    )


def _format_task(task):
    assigned = ', '.join(task.users_assigned.values_list('username', flat=True)) or 'none'
    state = 'Done' if task.completed else 'Open'
    return (
        f'Task #{task.pk} ({task.uuid}): [{state}] "{task.title}" in project '
        f'#{task.project_id} "{task.project.title}" '
        f'(Due: {_format_datetime(task.due_date)}, Users: {assigned})'
        f'{": " + task.text if task.text else ""}'
    )


def _format_note(note):
    return (
        f'Note #{note.pk} ({note.uuid}): "{note.title}" on task '
        f'#{note.task_id} "{note.task.title}" by {note.user}: {note.text}'
    )


def get_projects(user):
    """Return all projects owned by the user."""
    projects = Project.objects.filter(users_assigned=user).order_by('due_date', 'title')
    lines = [f'{i}. {_format_project(p)}' for i, p in enumerate(projects, 1)]
    return '\n'.join(lines) if lines else 'No projects found.'


def get_tasks(user, status=None):
    """Return tasks assigned to the user."""
    tasks = Task.objects.filter(users_assigned=user).select_related('project')
    if status == 'completed':
        tasks = tasks.filter(completed=True)
    elif status == 'active':
        tasks = tasks.filter(completed=False)
    tasks = tasks.order_by('completed', 'due_date', 'title')
    lines = [f'{i}. {_format_task(t)}' for i, t in enumerate(tasks, 1)]
    return '\n'.join(lines) if lines else 'No tasks found.'


def get_users():
    """Return list of all users."""
    users = User.objects.all().order_by('username')
    lines = [f'{i}. {u.username} ({u.email})' for i, u in enumerate(users, 1)]
    return '\n'.join(lines) if lines else 'No users found.'


def search_database(user, query, models=None, limit=10):
    """Search installed database models for text."""
    query = (query or '').strip()
    if not query:
        return 'Search query is required.'

    limit = max(1, min(int(limit or 10), 50))
    requested = set(m.lower() for m in models) if models else None
    sections = []

    aliases = {
        'users': 'auth.user',
        'user': 'auth.user',
        'profiles': 'taskmanager.userprofile',
        'userprofiles': 'taskmanager.userprofile',
        'projects': 'taskmanager.project',
        'project': 'taskmanager.project',
        'tasks': 'taskmanager.task',
        'task': 'taskmanager.task',
        'notes': 'taskmanager.notes',
        'note': 'taskmanager.notes',
        'files': 'taskmanager.file',
        'file': 'taskmanager.file',
        'chatsessions': 'chatbot.chatsession',
        'chatmessages': 'chatbot.chatmessage',
    }

    for model in apps.get_models():
        model_key = f'{model._meta.app_label}.{model._meta.model_name}'.lower()
        object_name = model._meta.object_name.lower()
        if requested and model_key not in requested and object_name not in requested:
            aliased = {aliases.get(name, name) for name in requested}
            if model_key not in aliased:
                continue

        searchable_fields = [
            field.name
            for field in model._meta.fields
            if isinstance(field, (django_models.CharField, django_models.TextField, django_models.EmailField))
        ]
        if not searchable_fields and not query.isdigit():
            continue

        predicate = Q()
        for field_name in searchable_fields:
            predicate |= Q(**{f'{field_name}__icontains': query})
        if query.isdigit():
            predicate |= Q(pk=int(query))

        try:
            matches = list(model.objects.filter(predicate).distinct()[:limit])
        except Exception as exc:
            sections.append(f'{model._meta.label}: search error: {exc}')
            continue

        if not matches:
            continue

        formatted = []
        for obj in matches:
            if isinstance(obj, Project):
                formatted.append(f'- {_format_project(obj)}')
            elif isinstance(obj, Task):
                formatted.append(f'- {_format_task(obj)}')
            elif isinstance(obj, Notes):
                formatted.append(f'- {_format_note(obj)}')
            elif isinstance(obj, File):
                formatted.append(
                    f'- File #{obj.pk} ({obj.uuid}) "{obj.name}" in project #{obj.project_id}: {obj.path}'
                )
            elif isinstance(obj, UserProfile):
                formatted.append(
                    f'- Profile #{obj.pk} ({obj.uuid}) for {obj.user.username}: '
                    f'DOB={obj.dob}, SSN={obj.ssn}, image={obj.image}'
                )
            elif isinstance(obj, User):
                formatted.append(
                    f'- User #{obj.pk}: {obj.username} ({obj.email}) {obj.first_name} {obj.last_name}'.strip()
                )
            else:
                values = []
                for field_name in searchable_fields[:6]:
                    value = getattr(obj, field_name, '')
                    if value:
                        values.append(f'{field_name}={value}')
                formatted.append(f'- {model._meta.label} #{obj.pk}: ' + ', '.join(values))

        sections.append(f'{model._meta.verbose_name_plural.title()}:\n' + '\n'.join(formatted))

    return '\n\n'.join(sections) if sections else 'No database results found.'


def add_project(user, title, text='', due_date=None, priority=1, assigned_usernames=None):
    """Create a project and assign it to the current user plus optional users."""
    if not title:
        return 'Project title is required.'

    project = Project.objects.create(
        title=title,
        text=text or '',
        priority=int(priority or 1),
        start_date=timezone.now(),
        due_date=_parse_date(due_date, timezone.now() + datetime.timedelta(weeks=1)),
    )
    users = [user] + _resolve_users(assigned_usernames or [])
    project.users_assigned.add(*users)
    return f'Created {_format_project(project)}'


def update_project(user, project_id, title=None, text=None, due_date=None, priority=None, assigned_usernames=None):
    """Update a project visible to the current user."""
    project = _find_project(project_id)
    if not _project_accessible(user, project):
        return 'Project not found or not accessible.'

    if title is not None:
        project.title = title
    if text is not None:
        project.text = text
    if due_date is not None:
        project.due_date = _parse_date(due_date, project.due_date)
    if priority is not None:
        project.priority = int(priority)
    project.save()

    if assigned_usernames is not None:
        users = [user] + _resolve_users(assigned_usernames)
        project.users_assigned.set(users)

    return f'Updated {_format_project(project)}'


def add_task(user, project_id, title, text='', due_date=None, completed=False, assigned_usernames=None):
    """Create a task in a project visible to the current user."""
    if not title:
        return 'Task title is required.'
    project = _find_project(project_id)
    if not _project_accessible(user, project):
        return 'Project not found or not accessible.'

    task = Task.objects.create(
        project=project,
        title=title,
        text=text or '',
        start_date=timezone.now(),
        due_date=_parse_date(due_date, timezone.now() + datetime.timedelta(weeks=1)),
        completed=bool(completed),
    )
    users = [user] + _resolve_users(assigned_usernames or [])
    task.users_assigned.add(*users)
    return f'Created {_format_task(task)}'


def update_task(user, task_id, title=None, text=None, due_date=None, completed=None, assigned_usernames=None):
    """Update a task visible to the current user."""
    task = _find_task(task_id)
    if not _task_accessible(user, task):
        return 'Task not found or not accessible.'

    if title is not None:
        task.title = title
    if text is not None:
        task.text = text
    if due_date is not None:
        task.due_date = _parse_date(due_date, task.due_date)
    if completed is not None:
        task.completed = bool(completed)
    task.save()

    if assigned_usernames is not None:
        users = [user] + _resolve_users(assigned_usernames)
        task.users_assigned.set(users)

    return f'Updated {_format_task(task)}'


def add_note(user, task_id, title, text, image=''):
    """Create a note on a task visible to the current user."""
    if not title:
        return 'Note title is required.'
    if text is None:
        return 'Note text is required.'
    task = _find_task(task_id)
    if not _task_accessible(user, task):
        return 'Task not found or not accessible.'

    note = Notes.objects.create(
        task=task,
        title=title,
        text=text,
        image=image or '',
        user=user.username,
    )
    return f'Created {_format_note(note)}'


def update_note(user, note_id, title=None, text=None, image=None):
    """Update a note visible to the current user."""
    note = _find_note(note_id)
    if not _note_accessible(user, note):
        return 'Note not found or not accessible.'

    if title is not None:
        note.title = title
    if text is not None:
        note.text = text
    if image is not None:
        note.image = image
    note.save()
    return f'Updated {_format_note(note)}'


def get_overview(user):
    """Return a compact snapshot of the current user's task-manager data."""
    return (
        'Projects:\n'
        f'{get_projects(user)}\n\n'
        'Open tasks:\n'
        f'{get_tasks(user, status="active")}'
    )


def _object_schema(properties=None, required=None):
    return {
        'type': 'object',
        'properties': properties or {},
        'required': required or [],
        'additionalProperties': False,
    }


def get_tools():
    """Return the dict of available tools for the ReAct agent."""
    return {
        'get_overview': {
            'function': {
                'name': 'get_overview',
                'description': 'Get a compact overview of the current user projects and open tasks.',
                'parameters': _object_schema(),
            },
            'code': get_overview,
        },
        'get_projects': {
            'function': {
                'name': 'get_projects',
                'description': 'List all projects for the current user',
                'parameters': _object_schema(),
            },
            'code': get_projects,
        },
        'get_tasks': {
            'function': {
                'name': 'get_tasks',
                'description': 'List tasks assigned to the current user. Optional status filter: "active" or "completed".',
                'parameters': _object_schema({
                    'status': {
                        'type': 'string',
                        'enum': ['active', 'completed'],
                        'description': 'Filter by status.',
                    },
                }),
            },
            'code': get_tasks,
        },
        'get_users': {
            'function': {
                'name': 'get_users',
                'description': 'List all users in the system',
                'parameters': _object_schema(),
            },
            'code': get_users,
        },
        'search_database': {
            'function': {
                'name': 'search_database',
                'description': 'Search users, profiles, projects, tasks, notes, and files for text. This is broad database search.',
                'parameters': _object_schema({
                    'query': {
                        'type': 'string',
                        'description': 'Text to search for.',
                    },
                    'models': {
                        'type': 'array',
                        'items': {
                            'type': 'string',
                        },
                        'description': 'Optional list of model names or aliases, such as users, projects, tasks, notes, files, auth.User, or chatbot.ChatMessage.',
                    },
                    'limit': {
                        'type': 'integer',
                        'description': 'Maximum results per model group, from 1 to 50.',
                    },
                }, ['query']),
            },
            'code': search_database,
        },
        'add_project': {
            'function': {
                'name': 'add_project',
                'description': 'Create a new project and assign it to the current user.',
                'parameters': _object_schema({
                    'title': {'type': 'string'},
                    'text': {'type': 'string'},
                    'due_date': {'type': 'string', 'description': 'Optional YYYY-MM-DD due date.'},
                    'priority': {'type': 'integer'},
                    'assigned_usernames': {
                        'type': 'array',
                        'items': {'type': 'string'},
                        'description': 'Optional additional usernames to assign.',
                    },
                }, ['title']),
            },
            'code': add_project,
        },
        'update_project': {
            'function': {
                'name': 'update_project',
                'description': 'Update an existing project visible to the current user.',
                'parameters': _object_schema({
                    'project_id': {'type': 'string', 'description': 'Project numeric id or UUID.'},
                    'title': {'type': 'string'},
                    'text': {'type': 'string'},
                    'due_date': {'type': 'string', 'description': 'Optional YYYY-MM-DD due date.'},
                    'priority': {'type': 'integer'},
                    'assigned_usernames': {
                        'type': 'array',
                        'items': {'type': 'string'},
                    },
                }, ['project_id']),
            },
            'code': update_project,
        },
        'add_task': {
            'function': {
                'name': 'add_task',
                'description': 'Create a task in a project visible to the current user.',
                'parameters': _object_schema({
                    'project_id': {'type': 'string', 'description': 'Project numeric id or UUID.'},
                    'title': {'type': 'string'},
                    'text': {'type': 'string'},
                    'due_date': {'type': 'string', 'description': 'Optional YYYY-MM-DD due date.'},
                    'completed': {'type': 'boolean'},
                    'assigned_usernames': {
                        'type': 'array',
                        'items': {'type': 'string'},
                    },
                }, ['project_id', 'title']),
            },
            'code': add_task,
        },
        'update_task': {
            'function': {
                'name': 'update_task',
                'description': 'Update a task visible to the current user.',
                'parameters': _object_schema({
                    'task_id': {'type': 'string', 'description': 'Task numeric id or UUID.'},
                    'title': {'type': 'string'},
                    'text': {'type': 'string'},
                    'due_date': {'type': 'string', 'description': 'Optional YYYY-MM-DD due date.'},
                    'completed': {'type': 'boolean'},
                    'assigned_usernames': {
                        'type': 'array',
                        'items': {'type': 'string'},
                    },
                }, ['task_id']),
            },
            'code': update_task,
        },
        'add_note': {
            'function': {
                'name': 'add_note',
                'description': 'Create a note on a task visible to the current user.',
                'parameters': _object_schema({
                    'task_id': {'type': 'string', 'description': 'Task numeric id or UUID.'},
                    'title': {'type': 'string'},
                    'text': {'type': 'string'},
                    'image': {'type': 'string'},
                }, ['task_id', 'title', 'text']),
            },
            'code': add_note,
        },
        'update_note': {
            'function': {
                'name': 'update_note',
                'description': 'Update a note visible to the current user.',
                'parameters': _object_schema({
                    'note_id': {'type': 'string', 'description': 'Note numeric id or UUID.'},
                    'title': {'type': 'string'},
                    'text': {'type': 'string'},
                    'image': {'type': 'string'},
                }, ['note_id']),
            },
            'code': update_note,
        },
    }
