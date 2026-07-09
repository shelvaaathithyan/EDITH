"""
Health Dashboard.
Aggregates health status from all registered subsystems into a single report.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from edith.utils.logger import get_logger
from edith.core.events import event_bus, AppEvent
from edith.sdk.capability import capability_registry
from edith.sdk.capability.capability_health import CapabilityHealth

logger = get_logger("edith.core.health")


@dataclass
class SubsystemHealth:
    name: str
    status: str = "unknown"
    latency_ms: float = 0.0
    version: str = "1.0.0"
    details: str = ""
    dependencies: List[str] = field(default_factory=list)


@dataclass
class SystemHealth:
    overall_status: str = "unknown"
    subsystems: List[SubsystemHealth] = field(default_factory=list)
    capabilities: Dict[str, str] = field(default_factory=dict)
    timestamp: str = ""


class HealthDashboard:
    """
    Queries every registered subsystem and capability for health status.
    Exposes the aggregated report to the Developer UI.
    """

    def __init__(self):
        self._subsystems: List[Any] = []

    def register_subsystem(self, subsystem) -> None:
        """Register a subsystem for health monitoring."""
        self._subsystems.append(subsystem)

    def get_report(self) -> SystemHealth:
        """Generates a full health report by querying all subsystems and capabilities."""
        import time

        report = SystemHealth(timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        all_healthy = True

        # Query subsystems
        for sub in self._subsystems:
            name = sub.__class__.__name__
            health = SubsystemHealth(name=name)

            if hasattr(sub, "health_check"):
                try:
                    start = time.time()
                    result = sub.health_check()
                    health.latency_ms = round((time.time() - start) * 1000, 2)

                    if hasattr(result, "status"):
                        health.status = result.status
                    elif isinstance(result, CapabilityHealth):
                        health.status = result.value
                    else:
                        health.status = str(result) if result else "healthy"

                    if health.status != "healthy" and health.status != CapabilityHealth.HEALTHY.value:
                        all_healthy = False
                        health.details = getattr(result, "error", "")

                except Exception as e:
                    health.status = "error"
                    health.details = str(e)
                    all_healthy = False
            else:
                health.status = "no_health_check"

            report.subsystems.append(health)

        # Query capabilities
        for cap_id, cap in capability_registry._capabilities.items():
            try:
                cap_health = cap.health_check()
                report.capabilities[cap_id] = cap_health.value if isinstance(cap_health, CapabilityHealth) else str(cap_health)
            except Exception:
                report.capabilities[cap_id] = "error"
                all_healthy = False

        report.overall_status = "healthy" if all_healthy else "degraded"
        return report

    def get_report_dict(self) -> Dict[str, Any]:
        """Returns the report as a plain dict for JSON serialization."""
        report = self.get_report()
        return {
            "overall_status": report.overall_status,
            "timestamp": report.timestamp,
            "subsystems": [
                {
                    "name": s.name,
                    "status": s.status,
                    "latency_ms": s.latency_ms,
                    "details": s.details
                }
                for s in report.subsystems
            ],
            "capabilities": report.capabilities
        }


# Global instance
health_dashboard = HealthDashboard()
