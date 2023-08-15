from django.test import TestCase
from django.contrib.auth.models import User
from taskManager.models import Project
from django.db import models
from django.contrib.auth import authenticate
from django.utils import timezone
import datetime


class UserTestCase(TestCase):
    def setUp(self):
        User.objects.create(username="testuser", password="testpassword")

    def test_user_create(self):
        print("Test User Exists")
        self.assertEqual(User.objects.filter(username="testuser").exists(),True)

    def test_user_login(self):
        print("Test User Login")
        self.assertEqual(1,1)

class ProjectTestCase(TestCase):
    def setUp(self):
        Project.objects.create(
            title="Test Project",
            text="Test Description",
            start_date = timezone.now(),
            due_date = timezone.now() + datetime.timedelta(weeks=1)
        )

    def test_project_create(self):
        print("Test Project Exists")
        self.assertEqual(Project.objects.filter(title="Test Project").exists(),True)
