from django.test import TestCase
from django.contrib.auth.models import User
from taskManager.models import Project
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
    
    def test_update_profile(self):
        print("Test Update Profile")
        self.client.login(username="chris", password="test123")
        data = {'first_name':'Chris', 'last_name':'TestUpdate', 'email':'chris@tm.com', 'dob': '03/03/83'}
        self.client.post('/taskManager/profile/3', data)
        res = self.client.get("/taskManager/profile/3").content
        self.assertEqual(True, (b"TestUpdate" in res))

class ProjectTestCase(TestCase):
    def setUp(self):
        Project.objects.create(
            title="Test Project",
            text="Test Description",
            start_date = timezone.now(),
            due_date = timezone.now() + datetime.timedelta(weeks=1)
        )
        self.client = Client()

    def test_project_create(self):
        print("Test Project Exists")
        self.assertEqual(Project.objects.filter(title="Test Project").exists(),True)
    
    def test_search_project(self):
        print("Test Search Project")
        res = self.client.get("/taskManager/projects/?search=Test").content
        self.assertEqual(True, (b"Test Project" in res))
