import time
from typing import Dict, Any, Optional

class TelemetryTracker:
    def __init__(self):
        self.metrics: Dict[str, float] = {}
        self._start_times: Dict[str, float] = {}

    def start(self, metric_name: str):
        self._start_times[metric_name] = time.time()

    def end(self, metric_name: str):
        if metric_name in self._start_times:
            duration = time.time() - self._start_times[metric_name]
            self.metrics[metric_name] = round(duration, 3)
            del self._start_times[metric_name]

    def record(self, metric_name: str, value: float):
        self.metrics[metric_name] = value

    def get_metrics(self) -> Dict[str, float]:
        return self.metrics.copy()

    def clear(self):
        self.metrics.clear()
        self._start_times.clear()
