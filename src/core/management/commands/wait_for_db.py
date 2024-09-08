from django.db.utils import OperationalError
from psycopg import OperationalError as PsycopgError
from django.core.management import BaseCommand

import time


class Command(BaseCommand):
    def handle(self, *args, **options) -> str | None:
        """
        Checks if DB is initialized. Run before booting up server.
        """

        self.stdout.write("Waiting for database ready...")

        db_up = False
        while db_up is False:
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
                "Database ready."
            )
        )