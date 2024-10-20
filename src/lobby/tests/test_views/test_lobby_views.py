from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from common.tests.utils import create_user_with_token
from django.urls import reverse
from rest_framework import status

# LIST_USER_URL = reverse("lobby:lobby-list")

class LobbyViewTests(TestCase):

    def setUp(self):
        self.client = Client()

        self.test_user_1, token = create_user_with_token()
        self.test_user_2, token = create_user_with_token(
            email="another@example.com"
        )
    
        test_user_1_logged_in = self.client.force_login(self.test_user_1)
        test_user_2_logged_in = self.client.force_login(self.test_user_2)

    def test_user_list_view(self):
        """
        Test that all logged-in users are returned.
        Users who aren't logged in should be hidden.
        """

        # hidden_user = create_user_with_token(
        #     email="hidden@example.com"
        # )

        # res = self.client.get(LIST_USER_URL)

        # self.assertEqual(res.status_code)
        pass
        

