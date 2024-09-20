from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from django.contrib.auth import get_user_model

import json

CREATE_USER_URL = reverse("authenticate:sign-up")

class AuthenticationTests(APITestCase):
    """
    Tests for Authentication Views
    """

    def test_user_signup_successful(self):
        """
        Test a user can sign up successfully.
        """

        payload = {
            "email": "test@example.com",
            "password1": "Testpass123!",
            "password2": "Testpass123!"
        }

        res = self.client.post(CREATE_USER_URL, data=payload)
        
        user = get_user_model().objects.last()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["id"], user.id)
        self.assertEqual(res.data["email"], user.email)
        self.assertNotIn("password", res.data)
    
    def test_user_signup_invalid_password_returns_401(self):
        """
        Test bad password returns five BAD REQUEST responses, followed by one CREATED
        after submitting valid data.
        """

        payloads = [
            {
                "email": "test@example.com",
                "password1": "password",
                "password2": "password"
            },
            {
                "email": "test@example.com",
                "password1": "pass",
                "password2": "pass"
            },
            {
                "email": "test@example.com",
                "password1": "Password",
                "password2": "Password"
            },
            {
                "email": "test@example.com",
                "password1": "Password123",
                "password2": "Password123"
            },
            {
                "email": "test@example.com",
                "password1": "Password!",
                "password2": "Password!"
            }
        ]

        error_msg = (
            "Passwords must contain at least 8 characters, one uppercase letter, one number and one special character."
            )

        # password
        res = self.client.post(CREATE_USER_URL, data=payloads[0])
        res_data = res.data
        res_error_msg = res_data["non_field_errors"][0]

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", res_data)
        self.assertEqual(res_error_msg, error_msg)

        # pass
        res = self.client.post(CREATE_USER_URL, data=payloads[1])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", res_data)
        self.assertEqual(res_error_msg, error_msg)

        # Password
        res = self.client.post(CREATE_USER_URL, data=payloads[2])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", res_data)
        self.assertEqual(res_error_msg, error_msg)
        
        # Password123
        res = self.client.post(CREATE_USER_URL, data=payloads[3])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", res_data)
        self.assertEqual(res_error_msg, error_msg)

        # Password!
        res = self.client.post(CREATE_USER_URL, data=payloads[4])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", res_data)
        self.assertEqual(res_error_msg, error_msg)


        # Valid (should return 201)
        valid_payload = {
            "email": "test@example.com",
            "password1": "Testpass123!",
            "password2": "Testpass123!"
        }

        res = self.client.post(CREATE_USER_URL, data=valid_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
