import contextlib
import importlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock, patch

from google import genai
from google.genai.errors import APIError

import index_documents
from app.core import tracer as tracing


class IndexingTracingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="indexing_trace_test_")
        self.addCleanup(self.temp.cleanup)
        self.log = Path(self.temp.name) / "traces.jsonl"
        self.input_file = Path(self.temp.name) / "sample.pdf"
        self.input_file.touch()
        self.start_patch(patch.object(tracing, "TRACE_FILE", self.log))
        self.output = io.StringIO()
        self.start_patch(contextlib.redirect_stdout(self.output))
        self.errors = io.StringIO()
        self.start_patch(contextlib.redirect_stderr(self.errors))

        # Importing the embedding module must never construct a real API client.
        with patch.object(genai, "Client", return_value=Mock()):
            self.embedder = importlib.import_module("app.ingestion.embedder")

        self.chunks = [
            {"chunk_id": f"chunk-{i}", "document_name": "sample.pdf", "text": "private text"}
            for i in range(2)
        ]

    def start_patch(self, context):
        value = context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)
        return value

    def events(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def prepare_cli(self):
        self.start_patch(patch("sys.argv", [
            "index_documents.py", "--file", str(self.input_file), "--strategy", "sentence"
        ]))
        self.start_patch(patch.object(
            index_documents.DOCUMENT_TYPES["pdf"], "parse", return_value=[{"text": "private text"}]
        ))
        self.start_patch(patch.object(
            index_documents, "create_chunker",
            return_value=SimpleNamespace(chunk=lambda pages: self.chunks),
        ))
        self.start_patch(patch.object(index_documents, "init_db"))
        return self.start_patch(patch.object(index_documents, "insert_chunks"))

    def test_full_run_correlates_stage_counts_and_timings(self):
        insert = self.prepare_cli()
        with patch.object(self.embedder, "embed_document", return_value=[0.1] * 768):
            index_documents.main()
        events = self.events()
        self.assertEqual(len({event["trace_id"] for event in events}), 1)
        completed = {
            event["stage"]: event["data"]
            for event in events if event["data"]["status"] == "completed"
        }
        for stage in ["parse", "clean", "chunk", "database_init", "embedding_setup",
                      "embedding", "database_save", "total"]:
            self.assertIn(f"indexing.{stage}", completed)
        self.assertEqual(completed["indexing.total"]["chunk_count"], 2)
        self.assertTrue(all(event["data"]["latency_ms"] >= 0 for event in events))
        self.assertEqual(completed["indexing.embedding_chunk"]["completed_chunks"], 2)
        self.assertEqual(len(insert.call_args.args[0]), 2)
        self.assertIn("embedding chunk 2/2", self.output.getvalue())
        self.assertIn("Indexed sample.pdf: 2 chunks", self.output.getvalue())
        self.assertNotIn("private text", self.log.read_text())
        for event in events:
            self.assertTrue({"text", "embedding", "api_key"}.isdisjoint(event["data"]))

    def test_late_429_records_failed_chunk_without_logging_exception_body(self):
        insert = self.prepare_cli()
        error = APIError(429, {"error": {
            "code": 429, "status": "RESOURCE_EXHAUSTED", "message": "private-api-secret"
        }})
        with patch.object(self.embedder, "embed_document", side_effect=[[0.1] * 768, error]):
            with self.assertRaises(SystemExit) as raised:
                index_documents.main()
        self.assertEqual(raised.exception.code, 1)
        failed = [event for event in self.events()
                  if event["stage"] == "indexing.embedding_chunk"
                  and event["data"]["status"] == "failed"]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["data"]["chunk_number"], 2)
        self.assertEqual(failed[0]["data"]["completed_chunks"], 1)
        self.assertEqual(failed[0]["data"]["error_code"], 429)
        self.assertNotIn("private-api-secret", self.log.read_text() + self.output.getvalue())
        insert.assert_not_called()

    def test_heartbeat_runs_while_work_is_waiting_and_stops_before_completion(self):
        monitor = tracing.IndexingTracer(heartbeat_seconds=0.01)
        seen_waiting = Event()
        real_trace = tracing.trace

        def capture(trace_id, stage, data):
            real_trace(trace_id, stage, data)
            if data["status"] == "waiting":
                seen_waiting.set()

        with patch.object(tracing, "trace", side_effect=capture):
            with monitor.stage("embedding_chunk", heartbeat=True, chunk_number=1, chunk_count=2):
                self.assertTrue(seen_waiting.wait(2), "No heartbeat during a blocked request")
        statuses = [event["data"]["status"] for event in self.events()]
        self.assertEqual(statuses[0], "started")
        self.assertIn("waiting", statuses)
        self.assertEqual(statuses[-1], "completed")

    def test_trace_file_failure_does_not_abort_work(self):
        monitor = tracing.IndexingTracer()
        with patch.object(tracing, "trace", side_effect=PermissionError("private path")):
            with monitor.stage("parse"):
                pass
            with monitor.stage("clean"):
                pass
        self.assertEqual(self.errors.getvalue().count("cannot write the trace log"), 1)
        self.assertNotIn("private path", self.errors.getvalue())
        self.assertIn("[clean] completed", self.output.getvalue())

    def test_ctrl_c_records_cancelled_status_and_exits_130(self):
        insert = self.prepare_cli()
        with patch.object(self.embedder, "embed_document", side_effect=KeyboardInterrupt):
            with self.assertRaises(SystemExit) as raised:
                index_documents.main()
        self.assertEqual(raised.exception.code, 130)
        self.assertEqual(self.events()[-1]["data"]["status"], "cancelled")
        insert.assert_not_called()

    def test_untraced_embedding_remains_supported(self):
        with patch.object(self.embedder, "embed_document", return_value=[0.1] * 768):
            results = self.embedder.embed_chunks(self.chunks)
        self.assertEqual(len(results), 2)
        self.assertEqual(self.output.getvalue(), "")
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
