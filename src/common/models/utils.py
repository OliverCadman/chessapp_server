from django.utils import timezone


def current_datetime() -> timezone.datetime:
    return timezone.now()
