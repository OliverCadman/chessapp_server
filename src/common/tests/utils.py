from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

import pytest
from datetime import timezone as tz


@database_sync_to_async
def acreate_user_with_token(email="test@example.com", password="Testpass123!"):
    user = get_user_model().objects.create_user(
        email=email, password=password
    )

    access = AccessToken.for_user(user)
    return user, access


def create_user_with_token(email="test@example.com", password="Testpass123!"):
    user = get_user_model().objects.create_user(
        email=email, password=password
    )

    access = AccessToken.for_user(user)
    return user, access


def create_user(email="test@example.com", password="Testpass123!"):
    return get_user_model().objects.create_user(email=email, password=password)
