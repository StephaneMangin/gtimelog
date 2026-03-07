from dataclasses import dataclass


@dataclass
class SyncPayload:
    """Payload produced by a sync backend and persisted by the sync service."""

    tasks: list
    filename: str
    customer_name: str
    task_format: str
