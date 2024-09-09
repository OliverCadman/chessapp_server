from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import User

class UserModelTests(TestCase):
    """
    Test Auth User models

    1. Test create user successful
    2. Test create superuser successful
    3. Test create user no email raises ValidationError
    4. Test create user no password raises ValidationError
    5. Test create user weak password raises ValidationError
    """

    @staticmethod
    def create_user(email: str = "test@example.com", password: str = "testpass123!") -> User:
        return get_user_model().objects.create_user(
            email=email, password=password
        )
    
    def test_create_user_successful(self):
        """
        Test creating a user is successful
        """

        test_email = "test@example.com"
        test_pass = "testpass123!"

        test_user = self.create_user(test_email, test_pass)
        self.assertEqual(test_user.email, test_email)
        self.assertTrue(test_user.check_password(test_pass))

    def test_create_superuser_successful(self):
        """
        Test creating a superuser is successful
        """

        test_email = "super@example.com"
        test_pass = "testpass123!"

        test_superuser = get_user_model().objects.create_superuser(
            test_email,
            test_pass
        )

        self.assertTrue(test_superuser.is_superuser)
        self.assertTrue(test_superuser.is_staff)
