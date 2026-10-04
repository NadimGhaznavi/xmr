"""Tests for the deployment DNS report."""

import subprocess
import unittest
from unittest.mock import patch

from constants.DHost import DNSRecord
from scripts.dns_report import NOT_FOUND, cname_target, main, render_report


class DNSReportTest(unittest.TestCase):
    @staticmethod
    def dig_result(stdout: str, returncode: int = 0):
        return subprocess.CompletedProcess([], returncode, stdout, "")

    def test_cname_target_removes_trailing_dot(self):
        runner = lambda *args, **kwargs: self.dig_result("target.example.com.\n")
        self.assertEqual(cname_target("alias.example.com", runner), "target.example.com")

    def test_cname_target_reports_missing_and_failed_queries(self):
        empty_runner = lambda *args, **kwargs: self.dig_result("")
        failed_runner = lambda *args, **kwargs: self.dig_result("", 9)
        self.assertEqual(cname_target("missing.example.com", empty_runner), NOT_FOUND)
        self.assertEqual(cname_target("failed.example.com", failed_runner), NOT_FOUND)

    def test_render_report_includes_record_and_target(self):
        report = render_report(
            [(DNSRecord("DEV", "Web", "web.example.com"), "host.example.com")]
        )
        self.assertIn("Environment", report)
        self.assertIn("web.example.com", report)
        self.assertIn("host.example.com", report)

    @patch("scripts.dns_report.shutil.which", return_value=None)
    @patch("scripts.dns_report.print")
    def test_main_requires_dig(self, unused_print, unused_which):
        self.assertEqual(main(), 2)

    @patch("scripts.dns_report.DNS_RECORDS", (DNSRecord("DEV", "Web", "web"),))
    @patch("scripts.dns_report.shutil.which", return_value="/usr/bin/dig")
    @patch("scripts.dns_report.cname_target", return_value=NOT_FOUND)
    @patch("scripts.dns_report.print")
    def test_main_returns_one_for_a_missing_record(
        self, unused_print, unused_target, unused_which
    ):
        self.assertEqual(main(), 1)


if __name__ == "__main__":
    unittest.main()
