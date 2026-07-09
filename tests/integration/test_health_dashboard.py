"""
Integration test: Health Dashboard.
Verifies that the health system correctly aggregates subsystem statuses.
"""

import pytest
from edith.core.health_dashboard import HealthDashboard
from edith.ai.models import HealthStatus


class MockHealthySubsystem:
    def health_check(self):
        return HealthStatus(status="healthy", provider="mock", model="mock")


class MockUnhealthySubsystem:
    def health_check(self):
        return HealthStatus(status="unhealthy", provider="mock", model="mock", error="Test failure")


class MockNoHealthCheck:
    pass


def test_all_healthy():
    dashboard = HealthDashboard()
    dashboard.register_subsystem(MockHealthySubsystem())
    dashboard.register_subsystem(MockHealthySubsystem())

    report = dashboard.get_report()
    assert report.overall_status == "healthy"
    assert len(report.subsystems) == 2


def test_degraded_on_failure():
    dashboard = HealthDashboard()
    dashboard.register_subsystem(MockHealthySubsystem())
    dashboard.register_subsystem(MockUnhealthySubsystem())

    report = dashboard.get_report()
    assert report.overall_status == "degraded"


def test_no_health_check():
    dashboard = HealthDashboard()
    dashboard.register_subsystem(MockNoHealthCheck())

    report = dashboard.get_report()
    assert report.subsystems[0].status == "no_health_check"


def test_dict_serialization():
    dashboard = HealthDashboard()
    dashboard.register_subsystem(MockHealthySubsystem())

    result = dashboard.get_report_dict()
    assert "overall_status" in result
    assert "subsystems" in result
    assert "capabilities" in result
