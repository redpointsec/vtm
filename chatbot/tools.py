from taskManager.models import Project, Task


def _format_datetime(value):
    return value.strftime('%Y-%m-%d') if value else 'No due date'


def get_projects(user):
    """Return all projects owned by the user."""
    projects = Project.objects.filter(users_assigned=user).order_by('due_date', 'title')
    lines = []
    for i, p in enumerate(projects, 1):
        task_count = p.task_set.count()
        complete_count = p.task_set.filter(completed=True).count()
        lines.append(
            f'{i}. "{p.title}" - {p.text} '
            f'(Priority: {p.priority}, Due: {_format_datetime(p.due_date)}, '
            f'Tasks: {complete_count}/{task_count} complete)'
        )
    return '\n'.join(lines) if lines else 'No projects found.'


def get_tasks(user, status=None):
    """Return tasks assigned to the user."""
    tasks = Task.objects.filter(users_assigned=user).select_related('project')
    if status == 'completed':
        tasks = tasks.filter(completed=True)
    elif status == 'active':
        tasks = tasks.filter(completed=False)
    tasks = tasks.order_by('completed', 'due_date', 'title')
    lines = []
    for i, t in enumerate(tasks, 1):
        state = 'Done' if t.completed else 'Open'
        lines.append(
            f'{i}. [{state}] "{t.title}" in project '
            f'"{t.project.title}" (Due: {_format_datetime(t.due_date)})'
            f'{": " + t.text if t.text else ""}'
        )
    return '\n'.join(lines) if lines else 'No tasks found.'


def get_users():
    """Return list of all users."""
    from django.contrib.auth.models import User
    users = User.objects.all().order_by('username')
    lines = [f'{i}. {u.username} ({u.email})' for i, u in enumerate(users, 1)]
    return '\n'.join(lines) if lines else 'No users found.'


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
    }
