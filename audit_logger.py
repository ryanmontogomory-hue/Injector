import json
import os
from datetime import datetime
from threading import Lock

class AuditLogger:
    def __init__(self, log_path="logs/audit.log"):
        self.log_path = log_path
        self.lock = Lock()
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def log(self, action, user=None, details=None, status="success", error=None):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user": user or "anonymous",
            "details": details or {},
            "status": status,
            "error": error,
        }
        with self.lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

    def get_recent(self, n=20):
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-n:]
            return [json.loads(line) for line in lines]
        except Exception:
            return []

audit_logger = AuditLogger()
