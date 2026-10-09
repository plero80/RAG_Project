import json
import sys
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, Lock, Thread
from typing import Any


TRACE_FILE = Path("logs/traces.jsonl")
_TRACE_LOCK = Lock()


def create_trace_id() -> str:
    return str(uuid.uuid4())


def trace(
    trace_id: str,
    stage: str,
    data: dict
) -> None:
    
    
    TRACE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )
    
    
    event = {
        "trace_id" : trace_id,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "stage" : stage,
        "data" : data
    }
    
    
    with _TRACE_LOCK, TRACE_FILE.open(
        "a", encoding="utf-8"
    ) as file:
        
        file.write(
            json.dumps(
                event,
                ensure_ascii=False
            )
            + "\n"
        )


class IndexingTracer:
    """Show live indexing progress and record timings under one trace ID."""

    def __init__(self, heartbeat_seconds: float = 10.0):
        if heartbeat_seconds <= 0:
            raise ValueError("heartbeat_seconds must be positive")
        self.trace_id = create_trace_id()
        self.heartbeat_seconds = heartbeat_seconds
        self._log_unavailable = False

    def _record(self, stage: str, data: dict[str, Any]) -> None:
        # A logging problem must not discard embeddings or hide an API error.
        if self._log_unavailable:
            return
        try:
            trace(self.trace_id, f"indexing.{stage}", data)
        except OSError:
            self._log_unavailable = True
            print(
                "Warning: cannot write the trace log; console timings will continue.",
                file=sys.stderr,
                flush=True,
            )

    @contextmanager
    def stage(
        self, stage: str, *, heartbeat: bool = False, **metadata: Any
    ) -> Iterator[dict[str, Any]]:
        """Time a stage, including SDK retries; yield metadata for final counts."""
        started = time.perf_counter()
        stopped = Event()
        label = stage.replace("_", " ")
        if "chunk_number" in metadata:
            label += f" {metadata['chunk_number']}/{metadata['chunk_count']}"

        def report(status: str, **extra: Any) -> None:
            elapsed = time.perf_counter() - started
            self._record(stage, {
                **metadata,
                **extra,
                "status": status,
                "latency_ms": round(elapsed * 1000, 3),
            })
            print(f"[{label}] {status} | {elapsed:.2f}s", flush=True)

        def report_waiting() -> None:
            while not stopped.wait(self.heartbeat_seconds):
                report("waiting")

        report("started")
        worker = None
        if heartbeat:
            worker = Thread(target=report_waiting, daemon=True)
            worker.start()

        status = "completed"
        error: dict[str, Any] = {}
        try:
            yield metadata
        except BaseException as exc:
            status = "cancelled" if isinstance(exc, KeyboardInterrupt) else "failed"
            # Exception messages may contain credentials or request content.
            error["error_type"] = type(exc).__name__
            code = getattr(exc, "code", None)
            if isinstance(code, int):
                error["error_code"] = code
            raise
        finally:
            stopped.set()
            if worker is not None:
                worker.join()
            report(status, **error)
