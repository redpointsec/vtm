import json

from django.contrib.auth.models import User
from django.test import TestCase

from chatbot.tools import (
    add_note,
    add_project,
    add_task,
    search_database,
    update_note,
    update_project,
    update_task,
)
from chatbot.views import _execute_tool
from taskManager.models import Notes, Project, Task


class ChatbotToolTests(TestCase):
    fixtures = [
        'users',
        'usersProfiles',
        'groups',
        'auth_group_permissions',
        'taskManagerProjects',
        'taskManagerNotes',
        'taskManagerTasks',
    ]

    def setUp(self):
        self.user = User.objects.get(username='chris')

    def test_search_database_can_find_records_across_models(self):
        result = search_database(self.user, 'seth', models=['users', 'profiles'])

        self.assertIn('Users:', result)
        self.assertIn('seth@tm.com', result)
        self.assertIn('Profiles:', result)

    def test_add_and_update_project(self):
        created = add_project(
            self.user,
            title='Chatbot Created Project',
            text='Created from chatbot',
            due_date='2026-06-01',
            priority=3,
            assigned_usernames=['ken'],
        )

        project = Project.objects.get(title='Chatbot Created Project')
        self.assertIn(f'Project #{project.pk}', created)
        self.assertTrue(project.users_assigned.filter(username='chris').exists())
        self.assertTrue(project.users_assigned.filter(username='ken').exists())

        updated = update_project(
            self.user,
            str(project.pk),
            title='Chatbot Updated Project',
            priority=4,
        )
        project.refresh_from_db()

        self.assertIn('Updated Project', updated)
        self.assertEqual(project.title, 'Chatbot Updated Project')
        self.assertEqual(project.priority, 4)

    def test_add_and_update_task(self):
        project = Project.objects.get(pk=6)

        created = add_task(
            self.user,
            str(project.pk),
            title='Chatbot Created Task',
            text='Task from chatbot',
            due_date='2026-06-02',
        )
        task = Task.objects.get(title='Chatbot Created Task')

        self.assertIn(f'Task #{task.pk}', created)
        self.assertTrue(task.users_assigned.filter(username='chris').exists())

        updated = update_task(
            self.user,
            str(task.pk),
            title='Chatbot Updated Task',
            completed=True,
        )
        task.refresh_from_db()

        self.assertIn('Updated Task', updated)
        self.assertEqual(task.title, 'Chatbot Updated Task')
        self.assertTrue(task.completed)

    def test_add_and_update_note(self):
        project = Project.objects.get(pk=6)
        task = Task.objects.create(
            project=project,
            title='Note Parent',
            text='Parent task',
            start_date=project.start_date,
            due_date=project.due_date,
        )
        task.users_assigned.add(self.user)

        created = add_note(
            self.user,
            str(task.pk),
            title='Chatbot Created Note',
            text='Note from chatbot',
        )
        note = Notes.objects.get(title='Chatbot Created Note')

        self.assertIn(f'Note #{note.pk}', created)
        self.assertEqual(note.user, 'chris')

        updated = update_note(
            self.user,
            str(note.pk),
            title='Chatbot Updated Note',
            text='Updated note text',
        )
        note.refresh_from_db()

        self.assertIn('Updated Note', updated)
        self.assertEqual(note.title, 'Chatbot Updated Note')
        self.assertEqual(note.text, 'Updated note text')

    def test_execute_tool_dispatches_new_tool_functions(self):
        payload = json.loads(_execute_tool(
            'add_project',
            {'title': 'Executor Project', 'text': 'Created through dispatcher'},
            self.user,
        ))

        self.assertIn('result', payload)
        self.assertTrue(Project.objects.filter(title='Executor Project').exists())
