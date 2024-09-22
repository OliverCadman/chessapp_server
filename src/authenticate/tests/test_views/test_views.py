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
        res_error_msg = res_data["weak_password"][0]

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("weak_password", res_data)
        self.assertNotIn("password_mismatch", res_data)
        self.assertEqual(res_error_msg, error_msg)

        # pass
        res = self.client.post(CREATE_USER_URL, data=payloads[1])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("weak_password", res_data)
        self.assertNotIn("password_mismatch", res_data)
        self.assertEqual(res_error_msg, error_msg)

        # Password
        res = self.client.post(CREATE_USER_URL, data=payloads[2])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("weak_password", res_data)
        self.assertNotIn("password_mismatch", res_data)
        self.assertEqual(res_error_msg, error_msg)
        
        # Password123
        res = self.client.post(CREATE_USER_URL, data=payloads[3])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("weak_password", res_data)
        self.assertNotIn("password_mismatch", res_data)
        self.assertEqual(res_error_msg, error_msg)

        # Password!
        res = self.client.post(CREATE_USER_URL, data=payloads[4])
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("weak_password", res_data)
        self.assertNotIn("password_mismatch", res_data)
        self.assertEqual(res_error_msg, error_msg)


        # Valid (should return 201)
        valid_payload = {
            "email": "test@example.com",
            "password1": "Testpass123!",
            "password2": "Testpass123!"
        }

        res = self.client.post(CREATE_USER_URL, data=valid_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_user_signup_differing_passwords_returns_400(self):
        """
        If user supplies two passwords that don't match, return 400.
        """
        
        invalid_payload = {
            "email": "test@example.com",
            "password1": "Testpass123!",
            "password2": "testPass123!"
        }

        res = self.client.post(CREATE_USER_URL, data=invalid_payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        
        res_data = res.data
        self.assertIn("password_mismatch", res_data)

        res_error_msg = res_data["password_mismatch"][0]
        error_msg = "Passwords must match."
        self.assertEqual(res_error_msg, error_msg)

    def test_user_signup_invalid_password_no_match_returns_both_errors(self):
        """
        If user supplies invalid password AND they don't match,
        return both error messages in response.
        """

        invalid_payload = {
            "email": "test@example.com",
            "password1": "Testpass123!",
            "password2": "testPass"
        }

        res = self.client.post(CREATE_USER_URL, data=invalid_payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        password_mismatch_error_msg = "Passwords must match."
        weak_password_error_msg = ("Passwords must contain at least 8 characters, "
                                   "one uppercase letter, one number and one "
                                   "special character.")
        
        res_data = res.data
        self.assertIn("weak_password", res_data)
        self.assertIn("password_mismatch", res_data)

        password_mismatch_error = res_data["password_mismatch"][0]
        weak_password_error = res_data["weak_password"][0]

        self.assertEqual(password_mismatch_error, password_mismatch_error_msg)
        self.assertEqual(weak_password_error, weak_password_error_msg)
