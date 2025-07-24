# pylint: disable=import-error,protected-access,relative-beyond-top-level
"""Test cases for the rabbitmq.log model in Odoo."""

from datetime import datetime, timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase
from ..models.rabbitmq_log import convert_to_odoo_datetime


class TestRabibitLog(TransactionCase):
    """Tests for rabbitmq.log model."""

    @classmethod
    def setUpClass(cls):  # pylint: disable=invalid-name
        """Set up the test environment."""
        super().setUpClass()
        cls.log_model = cls.env["rabbitmq.log"]

    def test_prepare_log_vals(self):
        """Test preparing log values."""
        msg = {"record_id": 42, "other": "value"}
        vals = self.log_model.prepare_log_vals(msg)
        self.assertIn("record_id", vals)
        self.assertEqual(vals["record_id"], 42)

    def test_convert_to_odoo_datetime(self):
        """Test converting various datetime formats to Odoo datetime."""

        # Test ISO string input
        iso_str = "2025-07-23T08:00:00+00:00"
        dt = convert_to_odoo_datetime(iso_str)
        self.assertIsInstance(dt, datetime)
        self.assertIsNone(dt.tzinfo)

        # Test datetime input
        now = datetime.utcnow()
        dt2 = convert_to_odoo_datetime(now)
        self.assertEqual(dt2.replace(tzinfo=None), now.replace(tzinfo=None))

        # Test bad input raises ValueError
        with self.assertRaises(ValueError):
            convert_to_odoo_datetime(12345)

    def test_prepare_vals_datetime_conversion(self):
        """Test preparing values with datetime conversion."""
        log = self.log_model.new({})
        vals = {
            "check_in": "2025-07-23T08:00:00+00:00",
            "check_out": "2025-07-23T10:00:00+00:00",
            "name": "Test",
        }
        converted = log._prepare_vals(vals)
        self.assertIsInstance(converted["check_in"], datetime)
        self.assertIsInstance(converted["check_out"], datetime)
        self.assertEqual(converted["name"], "Test")

    def test_execute_operation_create_and_write(self):
        """Test executing create and write operations."""
        log = self.log_model.create(
            {
                "model_name": "res.partner",
                "operation": "create",
                "data": {"name": "Test Partner"},
            }
        )
        # Create operation should create a new partner
        partner = log._execute_operation("create", log.data)
        self.assertTrue(partner.exists())
        self.assertEqual(partner.name, "Test Partner")
        self.assertEqual(log.state, "success")
        self.assertFalse(log.error)

        # Now test write operation updates record
        log.operation = "write"
        log.data = {"record_id": partner.id, "name": "Updated Partner"}
        result = log._execute_operation("write", log.data)
        self.assertTrue(result)
        updated_partner = self.env["res.partner"].browse(partner.id)
        self.assertEqual(updated_partner.name, "Updated Partner")
        self.assertEqual(log.state, "success")

        # Write with invalid record_id sets fail state
        log.data = {"record_id": 9999999, "name": "No One"}
        result = log._execute_operation("write", log.data)
        self.assertFalse(result)
        self.assertEqual(log.state, "fail")
        self.assertIn("Record not found", log.error)

    def test_execute_operation_exception_handling(self):
        """Test handling exceptions during operation execution."""
        log = self.log_model.new(
            {
                "model_name": "res.partner",
                "operation": "create",
                "data": {"invalid_field": "value"},
            }
        )

        # Patch the actual model class method, not the recordset
        with patch(
            "odoo.addons.base.models.res_partner.Partner.create",
            side_effect=Exception("Boom"),
        ):
            result = log._execute_operation("create", log.data)
            self.assertFalse(result)
            self.assertEqual(log.state, "fail")
            self.assertIn("Sync Error", log.error)

    def test_process_odoo_operation(self):
        """Test processing Odoo operations."""
        log = self.log_model.create(
            {
                "model_name": "res.partner",
                "operation": "create",
                "data": {"name": "Proc Partner"},
            }
        )
        result = log.process_odoo_operation()
        self.assertTrue(result)
        self.assertEqual(log.state, "success")

        # Use new() instead of write to bypass validation
        invalid_log = self.log_model.new(
            {
                "model_name": "res.partner",
                "operation": "invalid_op",
                "data": {},
            }
        )
        result = invalid_log.process_odoo_operation()
        self.assertFalse(result)
        self.assertEqual(invalid_log.state, "fail")

    def test_cron_clean_successful_logs(self):
        """Create some logs with 'success' state older than 2 days and recent logs"""
        old_log = self.log_model.create(
            {
                "state": "success",
                "data": {"name": "Old"},
                "create_date": (
                    fields.Datetime.to_string(datetime.utcnow() - timedelta(days=3))
                ),
            }
        )
        recent_log = self.log_model.create(
            {
                "state": "success",
                "data": {"name": "Recent"},
                "create_date": fields.Datetime.to_string(datetime.utcnow()),
            }
        )

        # Call cron method
        self.log_model.cron_clean_successful_logs()

        # Old log should be deleted
        self.assertFalse(old_log.exists())
        # Recent log should still exist
        self.assertTrue(recent_log.exists())
