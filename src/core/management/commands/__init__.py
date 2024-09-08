from typing import Any
from django.db.utils import OperationalError
from psycopg import OperationalError as PsycopgError
from django.core.management import BaseCommand, call_command

import time


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> str | None:
        """
        Boot command to wait for db. Should be ran before server starts.
        """

        db_up = False
        while db_up is False:
            self.stdout.write("Waiting for database...")
            try:
                self.check(databases=["default"])
                db_up = True
            except (OperationalError, PsycopgError):
                self.stdout.write(
                    self.style.ERROR(
                        "Database initialization failed. Retrying..."
                    )
                )
                time.sleep(1)
                
        self.stdout.write(
            self.style.SUCCESS(
                "Database is ready."
            )
        )

