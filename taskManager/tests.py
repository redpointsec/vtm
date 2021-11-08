from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


class UserTestCase(TestCase):
	def setUp(self):
		User.objects.create(username="testuser", password="testpassword")

	def test_user_create(self):
		self.assertEqual(User.objects.filter(username="testuser").exists(),True)
		
