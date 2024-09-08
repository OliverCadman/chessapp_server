from django.test import TestCase
from unittest.mock import patch

from django.core.management import call_command
from django.db.utils import OperationalError

from psycopg import OperationalError as PsycopgError




@patch("core.management.commands.wait_for_db.Command.check")
class CommandTests(TestCase):
    """
    Management command tests

    1. Wait for Postgres DB ready
    2. Retry DB connection in case of failure
    """

    def test_wait_for_db_ready(self, patched_check):
        """Wait for Postgres DB ready"""

        patched_check.return_value = True

        call_command("wait_for_db")
        patched_check.assert_called_once_with(databases=["default"])

    @patch("time.sleep")
    def test_db_connection_retry(self, _, patched_check):
         
         patched_check.side_effect = [OperationalError] * 2 + \
            [PsycopgError] * 3 + [True]
         
         call_command("wait_for_db")

         patched_check.assert_called_with(databases=["default"])
