"""Модуль логирования для ВПТК."""

import json
import csv
import io
from datetime import datetime
from dataclasses import dataclass, asdict, field


@dataclass
class LogEntry:
    timestamp: str
    level: str
    event: str
    message: str
    data: dict = field(default_factory=dict)


class Logger:
    def __init__(self):
        self._entries: list[LogEntry] = []
        self._max_entries = 1000

    def log(self, level, event, message, **data):
        entry = LogEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            level=level, event=event, message=message, data=data,
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)
        return entry

    def info(self, event, message, **data):  return self.log("INFO", event, message, **data)
    def warn(self, event, message, **data):  return self.log("WARN", event, message, **data)
    def error(self, event, message, **data): return self.log("ERROR", event, message, **data)

    def get_entries(self): return list(self._entries)

    def get_text(self) -> str:
        lines = []
        for e in self._entries:
            data_str = ""
            if e.data:
                data_str = " | " + ", ".join(f"{k}={v}" for k, v in e.data.items())
            lines.append(f"[{e.timestamp}] [{e.level}] {e.event}: {e.message}{data_str}")
        return "\n".join(lines) if lines else "(лог пуст)"

    def clear(self): self._entries.clear()
    def export_txt(self): return self.get_text()
    def export_json(self):
        return json.dumps([asdict(e) for e in self._entries],
                          ensure_ascii=False, indent=2)
    def export_csv(self):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "level", "event", "message", "data"])
        for e in self._entries:
            writer.writerow([e.timestamp, e.level, e.event, e.message,
                             json.dumps(e.data, ensure_ascii=False)])
        return output.getvalue()


logger = Logger()

def log_info(event, message, **data):  return logger.info(event, message, **data)
def log_warn(event, message, **data):  return logger.warn(event, message, **data)
def log_error(event, message, **data): return logger.error(event, message, **data)
def get_log() -> str:                  return logger.get_text()
def clear_log():                       logger.clear()

def export_log(fmt: str = "txt") -> str:
    if fmt == "txt":  return logger.export_txt()
    if fmt == "json": return logger.export_json()
    if fmt == "csv":  return logger.export_csv()
    raise ValueError(f"Неизвестный формат: {fmt}")