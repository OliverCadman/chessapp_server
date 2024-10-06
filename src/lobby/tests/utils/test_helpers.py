from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

from datetime import timezone as tz


def create_test_datetime() -> timezone.datetime:
    return timezone.datetime(2024, 9, 15, tzinfo=tz.utc)


def create_test_user(
        email: str = "test@example.com",
        password: str = "testpass123!"
        ) -> User:
    
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )