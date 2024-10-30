from celery import shared_task
from core.models import Room


@shared_task(name="core.tasks.prune_players")
def prune_players():
    return Room.objects.prune_players()
