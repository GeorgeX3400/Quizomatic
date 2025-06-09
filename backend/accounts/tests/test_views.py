import uuid
import json
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser  

class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('v2_register')

    def test_register_user(self):
        # Generate random username and email
        random_string = str(uuid.uuid4())[:8]  # Short random string
        username = f"user_{random_string}"
        email = f"{random_string}@example.com"
        password = "securepassword123"

        # Prepare POST data
        post_data = {
            'username': username,
            'email': email,
            'password': password,
        }

        # Make POST request to register view with JSON data
        response = self.client.post(
            self.register_url,
            data=json.dumps(post_data),
            content_type='application/json'
        )

        # Check response status
        self.assertEqual(response.status_code, 201)

        # Validate user was added to the database
        self.assertTrue(CustomUser.objects.filter(username=username).exists())
        user = CustomUser.objects.get(username=username)
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))  # Verify password