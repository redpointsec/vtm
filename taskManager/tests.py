from django.test import TestCase
from django.contrib.auth.models import User
from taskManager.models import Project, Task, Notes, UserProfile
from django.db import models
from django.contrib.auth import authenticate
from django.utils import timezone
from django.test import Client
import datetime


class UserTestCase(TestCase):
    fixtures = ['users', 'usersProfiles', 'groups', 'auth_group_permissions', 'taskManagerProjects', 'taskManagerNotes', 'taskManagerTasks' ]

    def setUp(self):
        self.client = Client()

    def test_user_create(self):
        print("Test User Exists")
        self.assertEqual(User.objects.filter(username="chris").exists(),True)

    def test_user_login(self):
        print("Test User Login")
        self.client.login(username="chris", password="test123")
        res = self.client.get("/taskManager/profile/3").content
        self.assertEqual(True, (b"Edit Profile" in res))
    
    def test_user_change_password(self):
        print("Test User Change Password")
        self.client.login(username="chris", password="test123")
        data = {'new_password':'test1234', 'confirm_password':'test1234'}
        self.client.post('/taskManager/change_password/', data)
        self.client.logout()
        self.client.login(username="chris", password="test1234")
        res = self.client.get("/taskManager/profile/3").content
        self.assertEqual(True, (b"Edit Profile" in res))
    
    def test_update_profile(self):
        print("Test Update Profile")
        self.client.login(username="chris", password="test123")
        data = {'first_name':'Chris', 'last_name':'TestUpdate', 'email':'chris@tm.com', 'dob': '03/03/83', 'ssn': '123-45-6789'}
        self.client.post('/taskManager/profile/3', data)
        res = self.client.get("/taskManager/profile/3").content
        self.assertEqual(True, (b"TestUpdate" in res))

class ProjectTestCase(TestCase):
    fixtures = ['users', 'usersProfiles', 'groups', 'auth_group_permissions', 'taskManagerProjects', 'taskManagerNotes', 'taskManagerTasks' ]

    def setUp(self):
        User.objects.create_user(username="testuser", password="testpassword")
        Project.objects.create(
            title="Test Project",
            text="Test Description",
            start_date = timezone.now(),
            due_date = timezone.now() + datetime.timedelta(weeks=1)
        )
        Task.objects.create(
            title="Test Task",
            text="Test Description",
            start_date = timezone.now(),
            due_date = timezone.now() + datetime.timedelta(weeks=1),
            project = Project.objects.get(title="Test Project")
        )
        Notes.objects.create(
            title="Test Note",
            text="Test Description",
            task = Task.objects.get(title="Test Task"),
            user = User.objects.get(username="testuser")
        )
        self.client = Client()

    def test_project_create(self):
        print("Test Project Exists")
        self.assertEqual(Project.objects.filter(title="Test Project").exists(),True)
    
    def test_task_exists(self):
        print("Test Task Exists")
        self.assertEqual(Task.objects.filter(title="Test Task").exists(),True)
    
    def test_note_exists(self):
        print("Test Note Exists")
        self.assertEqual(Notes.objects.filter(title="Test Note").exists(),True)
    
    def test_search_project(self):
        print("Test Search Project")
        self.client.login(username="testuser", password="testpassword")
        res = self.client.get("/taskManager/search/?q=Marketing").content
        self.assertEqual(True, (b"Marketing" in res))
