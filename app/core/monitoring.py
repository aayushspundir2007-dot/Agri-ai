"""Prediction logging, analytics, and model drift monitoring."""
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings


class Monitor:
    def __init__(self):
        self._start_time = time.time()
        self._log_path   = settings.LOG_FILE
        self._counters: Dict[str, int]   = defaultdict(int)
        self._latencies: Dict[str, list] = defaultdict(list)
        self._confidences: Dict[str, list] = defaultdict(list)
        self._crop_hist: list = []

    def _write(self, entry: dict):
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass  # never crash the app due to logging

    def log_startup(self, load_times: dict):
        self._write({"event": "startup", "ts": self._ts(), "load_times": load_times})

    def log_prediction(self, module: str, inputs: dict,
                       output: Any, latency_ms: float, confidence: float = None):
        self._counters[module] += 1
        self._latencies[module].append(latency_ms)
        if confidence is not None:
            self._confidences[module].append(confidence)
        if module == "crop" and isinstance(output, str):
            self._crop_hist.append(output)
        entry = {
            "event":      "prediction",
            "ts":         self._ts(),
            "module":     module,
            "inputs":     inputs,
            "output":     output,
            "latency_ms": round(latency_ms, 2),
        }
        if confidence is not None:
            entry["confidence"] = confidence
        self._write(entry)

    def analytics(self) -> dict:
        from collections import Counter
        crop_counts = dict(Counter(self._crop_hist).most_common(5))
        avg_lat = {k: round(sum(v)/len(v), 2) if v else 0
                   for k, v in self._latencies.items()}
        avg_conf = {k: round(sum(v)/len(v), 4) if v else None
                    for k, v in self._confidences.items()}
        return {
            "total_predictions": dict(self._counters),
            "average_latency_ms": avg_lat,
            "average_confidence": avg_conf,
            "top5_crops": crop_counts,
            "uptime_seconds": round(time.time() - self._start_time, 1),
        }

    @staticmethod
    def _ts() -> str:
        return datetime.now(timezone.utc).isoformat()

    def load_history(self) -> list:
        """Read prediction log and return list of entries."""
        if not Path(self._log_path).exists():
            return []
        entries = []
        with open(self._log_path, encoding="utf-8") as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
        return entries

monitor = Monitor()
