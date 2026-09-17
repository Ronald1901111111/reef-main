import hashlib
import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import jsonschema

from src.core.exceptions import (
    OptimisticLockError,
    LeaseActiveError,
    InvalidQueueEnvelopeError,
    SecurityViolationError,
)

FORBIDDEN_WRITING_KEYS = {
    "source_path",
    "raw_source",
    "source_material",
    "source_material_path",
    "raw_transcript",
    "transcript",
    "url",
    "source_url",
    "youtube_url",
}

class QueueManager:
    def __init__(self, repo_root: Optional[Path] = None, queue_dir_rel: str = "spark-github/queues"):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = Path(repo_root)
        self.queue_dir = self.repo_root / queue_dir_rel
        self.schemas_dir = self.repo_root / "schemas"
        self._envelope_schema = None

    @property
    def envelope_schema(self) -> Dict[str, Any]:
        if self._envelope_schema is None:
            schema_path = self.schemas_dir / "queue_envelope.schema.json"
            with open(schema_path, "r", encoding="utf-8") as f:
                self._envelope_schema = json.load(f)
        return self._envelope_schema

    def validate_envelope(self, envelope: Dict[str, Any]) -> None:
        try:
            jsonschema.validate(instance=envelope, schema=self.envelope_schema)
        except jsonschema.ValidationError as e:
            raise InvalidQueueEnvelopeError(f"Invalid queue envelope: {e.message}") from e

    def _compute_revision(self, data: Dict[str, Any]) -> str:
        state_repr = f"{data['job_id']}:{data['claim_status']}:{data.get('claim_owner')}:{data.get('attempt')}:{data.get('iteration')}:{data['updated_at']}"
        return hashlib.sha256(state_repr.encode("utf-8")).hexdigest()[:16]

    def _compute_idempotency_key(self, queue_name: str, job_id: str, iteration: int) -> str:
        raw = f"{queue_name}:{job_id}:{iteration}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

    def sanitize_authorized_inputs(self, queue_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = dict(inputs)
        if queue_name == "writing":
            for k in list(sanitized.keys()):
                if k in FORBIDDEN_WRITING_KEYS:
                    del sanitized[k]
        return sanitized

    def get_queue_path(self, queue_name: str) -> Path:
        p = self.queue_dir / queue_name
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_envelope_path(self, queue_name: str, job_id: str) -> Path:
        return self.get_queue_path(queue_name) / f"{job_id}.json"

    def enqueue_job(
        self,
        queue_name: str,
        job_id: str,
        authorized_inputs: Dict[str, Any],
        iteration: int = 1,
        expected_output_path: Optional[str] = None,
        run_id: Optional[str] = None,
        attempt: int = 1
    ) -> Dict[str, Any]:
        sanitized_inputs = self.sanitize_authorized_inputs(queue_name, authorized_inputs)
        now_iso = datetime.now(timezone.utc).isoformat()
        if run_id is None:
            run_id = f"run_{uuid.uuid4().hex[:12]}"
        
        idempotency_key = self._compute_idempotency_key(queue_name, job_id, iteration)
        envelope_path = self.get_envelope_path(queue_name, job_id)

        if envelope_path.exists():
            try:
                with open(envelope_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if existing.get("idempotency_key") == idempotency_key and existing.get("claim_status") == "COMPLETED":
                    return existing
            except Exception:
                pass

        envelope = {
            "job_id": job_id,
            "run_id": run_id,
            "queue_name": queue_name,
            "attempt": attempt,
            "queue_revision": "initial_rev",
            "claim_status": "QUEUED",
            "claim_owner": None,
            "claimed_at": None,
            "lease_expires_at": None,
            "idempotency_key": idempotency_key,
            "iteration": iteration,
            "authorized_inputs": sanitized_inputs,
            "expected_output_path": expected_output_path,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        envelope["queue_revision"] = self._compute_revision(envelope)
        self.validate_envelope(envelope)

        with open(envelope_path, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False)

        return envelope

    def poll_queue(self, queue_name: str, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        if now is None:
            now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        queue_path = self.get_queue_path(queue_name)
        eligible = []

        for item_path in sorted(queue_path.glob("*.json")):
            try:
                with open(item_path, "r", encoding="utf-8") as f:
                    envelope = json.load(f)
                status = envelope.get("claim_status")
                if status == "QUEUED":
                    eligible.append(envelope)
                elif status in ("CLAIMED", "RUNNING"):
                    lease_exp = envelope.get("lease_expires_at")
                    if lease_exp and now_iso > lease_exp:
                        eligible.append(envelope)
            except Exception:
                continue

        return eligible

    def claim_job(
        self,
        queue_name: str,
        job_id: str,
        worker_id: str,
        expected_revision: str,
        lease_duration_seconds: int = 300,
        now: Optional[datetime] = None
    ) -> Dict[str, Any]:
        if now is None:
            now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        envelope_path = self.get_envelope_path(queue_name, job_id)
        if not envelope_path.exists():
            raise FileNotFoundError(f"Job envelope not found at {envelope_path}")

        with open(envelope_path, "r", encoding="utf-8") as f:
            envelope = json.load(f)

        current_rev = envelope.get("queue_revision")
        if current_rev != expected_revision:
            raise OptimisticLockError(
                f"OCC conflict on {job_id} in {queue_name}: expected {expected_revision}, got {current_rev}"
            )

        status = envelope.get("claim_status")
        if status in ("CLAIMED", "RUNNING"):
            lease_exp = envelope.get("lease_expires_at")
            if lease_exp and now_iso <= lease_exp and envelope.get("claim_owner") != worker_id:
                raise LeaseActiveError(
                    f"Job {job_id} in {queue_name} has active lease held by {envelope.get('claim_owner')} until {lease_exp}"
                )

        lease_expires = (now + timedelta(seconds=lease_duration_seconds)).isoformat()
        envelope["claim_status"] = "CLAIMED"
        envelope["claim_owner"] = worker_id
        envelope["claimed_at"] = now_iso
        envelope["lease_expires_at"] = lease_expires
        if status in ("CLAIMED", "RUNNING"):
            envelope["attempt"] = envelope.get("attempt", 1) + 1
        envelope["updated_at"] = now_iso
        envelope["queue_revision"] = self._compute_revision(envelope)

        self.validate_envelope(envelope)
        with open(envelope_path, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False)

        return envelope

    def mark_running(self, queue_name: str, job_id: str, worker_id: str, expected_revision: str) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        envelope_path = self.get_envelope_path(queue_name, job_id)
        with open(envelope_path, "r", encoding="utf-8") as f:
            envelope = json.load(f)

        if envelope.get("queue_revision") != expected_revision:
            raise OptimisticLockError("OCC conflict marking running")
        if envelope.get("claim_owner") != worker_id:
            raise LeaseActiveError("Not lease owner")

        envelope["claim_status"] = "RUNNING"
        envelope["updated_at"] = now_iso
        envelope["queue_revision"] = self._compute_revision(envelope)
        self.validate_envelope(envelope)

        with open(envelope_path, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False)
        return envelope

    def complete_queue_item(
        self,
        queue_name: str,
        job_id: str,
        worker_id: str,
        expected_revision: str,
        archive: bool = True
    ) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        envelope_path = self.get_envelope_path(queue_name, job_id)
        with open(envelope_path, "r", encoding="utf-8") as f:
            envelope = json.load(f)

        if envelope.get("queue_revision") != expected_revision:
            raise OptimisticLockError("OCC conflict completing queue item")
        if envelope.get("claim_owner") != worker_id:
            raise LeaseActiveError("Not lease owner")

        envelope["claim_status"] = "COMPLETED"
        envelope["updated_at"] = now_iso
        envelope["queue_revision"] = self._compute_revision(envelope)
        self.validate_envelope(envelope)

        if archive:
            envelope_path.unlink(missing_ok=True)
        else:
            with open(envelope_path, "w", encoding="utf-8") as f:
                json.dump(envelope, f, indent=2, ensure_ascii=False)
        return envelope

    def fail_queue_item(
        self,
        queue_name: str,
        job_id: str,
        worker_id: str,
        expected_revision: str,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        envelope_path = self.get_envelope_path(queue_name, job_id)
        with open(envelope_path, "r", encoding="utf-8") as f:
            envelope = json.load(f)

        if envelope.get("queue_revision") != expected_revision:
            raise OptimisticLockError("OCC conflict failing queue item")

        envelope["claim_status"] = "FAILED"
        if error_message:
            envelope["error_message"] = error_message
        envelope["updated_at"] = now_iso
        envelope["queue_revision"] = self._compute_revision(envelope)
        self.validate_envelope(envelope)

        with open(envelope_path, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, ensure_ascii=False)
        return envelope
