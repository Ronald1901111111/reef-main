import json
import os
import unittest
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError

REPO_ROOT = Path(__file__).parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"

def load_schema(schema_name):
    schema_path = SCHEMAS_DIR / schema_name
    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError(f"Canonical schema {schema_name} not found at {schema_path}")


class TestJobStateSchema(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema("job_state.schema.json")
        self.valid_job_states = [
            "WAITING_FOR_TRANSCRIPT",
            "SEMANTIC_EXTRACTION_PENDING",
            "SEMANTIC_EXTRACTION_COMPLETED",
            "WRITING_PENDING",
            "CANDIDATE_GENERATED",
            "CI_PENDING",
            "CI_PASSED",
            "CI_FAILED",
            "REVIEW_PENDING",
            "REVIEW_COMPLETED",
            "EVALUATION_PENDING",
            "EVALUATED",
            "ITERATING",
            "NEEDS_HUMAN_REVIEW",
            "READY_FOR_HUMAN_APPROVAL",
            "APPROVED_BY_HUMAN",
            "PROMOTED",
            "FAILED",
        ]
        self.valid_base_job = {
            "job_id": "job_test_001",
            "current_stage": "writing",
            "status": "WRITING_PENDING",
            "iteration": 1,
            "max_iterations": 5,
            "failure_count": 0,
            "max_failures": 3,
            "created_at": "2026-09-17T17:00:00Z",
            "updated_at": "2026-09-17T17:05:00Z",
            "voice_model_bundle_path": "projects/voice-rewriter/profiles/ronald_ferrari/versions/v2.0.0/",
            "calibration_manifest_path": "projects/voice-rewriter/voice_corpus/calibration_manifests/calibration_v1.json",
            "global_artifacts": {
                "source_type": "youtube_url",
                "source_path": "projects/voice-rewriter/source_material/job_test_001/raw_source.txt"
            }
        }

    def test_all_18_valid_job_states_pass(self):
        for state in self.valid_job_states:
            job = dict(self.valid_base_job)
            job["status"] = state
            validate(instance=job, schema=self.schema)

    def test_invalid_job_state_fails(self):
        invalid_states = [
            "UNKNOWN_STATE",
            "PROCESSING",
            "IN_PROGRESS",
            "DONE",
            "SUCCESS",
            "COMPLETED"
        ]
        for state in invalid_states:
            job = dict(self.valid_base_job)
            job["status"] = state
            with self.assertRaises(ValidationError, msg=f"State {state} should have been rejected as JobState"):
                validate(instance=job, schema=self.schema)

    def test_cannot_mix_queue_state_into_job_state(self):
        queue_states = ["QUEUED", "CLAIMED", "RUNNING", "COMPLETED"]
        for qs in queue_states:
            job = dict(self.valid_base_job)
            job["status"] = qs
            with self.assertRaises(ValidationError, msg=f"Queue state {qs} must not be accepted in job_state"):
                validate(instance=job, schema=self.schema)

    def test_promoted_is_recognized_terminal_success_state(self):
        job = dict(self.valid_base_job)
        job["status"] = "PROMOTED"
        validate(instance=job, schema=self.schema)
        status_enum = self.schema.get("properties", {}).get("status", {}).get("enum", [])
        self.assertIn("PROMOTED", status_enum)
        self.assertNotIn("COMPLETED", status_enum, "COMPLETED must not be in JobState enum")

    def test_missing_required_fields_fails(self):
        required_fields = [
            "job_id",
            "status",
            "current_stage",
            "iteration",
            "max_iterations",
            "failure_count",
            "max_failures",
            "created_at",
            "updated_at",
            "voice_model_bundle_path",
            "calibration_manifest_path",
        ]
        for field in required_fields:
            job = dict(self.valid_base_job)
            del job[field]
            with self.assertRaises(ValidationError, msg=f"Missing {field} should fail"):
                validate(instance=job, schema=self.schema)

    def test_frozen_paths_must_be_non_empty_strings(self):
        job = dict(self.valid_base_job)
        job["voice_model_bundle_path"] = ""
        with self.assertRaises(ValidationError):
            validate(instance=job, schema=self.schema)

        job = dict(self.valid_base_job)
        job["calibration_manifest_path"] = ""
        with self.assertRaises(ValidationError):
            validate(instance=job, schema=self.schema)

    def test_invalid_types_fail(self):
        job = dict(self.valid_base_job)
        job["iteration"] = "one"
        with self.assertRaises(ValidationError):
            validate(instance=job, schema=self.schema)

        job = dict(self.valid_base_job)
        job["failure_count"] = -1
        with self.assertRaises(ValidationError):
            validate(instance=job, schema=self.schema)

        job = dict(self.valid_base_job)
        job["max_iterations"] = 0
        with self.assertRaises(ValidationError):
            validate(instance=job, schema=self.schema)


class TestQueueEnvelopeSchema(unittest.TestCase):
    def setUp(self):
        self.schema = load_schema("queue_envelope.schema.json")
        self.valid_queue_states = [
            "QUEUED",
            "CLAIMED",
            "RUNNING",
            "COMPLETED",
            "FAILED",
        ]
        self.valid_base_envelope = {
            "job_id": "job_test_001",
            "run_id": "run_wri_88921",
            "queue_name": "writing",
            "attempt": 1,
            "queue_revision": "rev_001_abc",
            "claim_status": "QUEUED",
            "claim_owner": None,
            "claimed_at": None,
            "lease_expires_at": None,
            "idempotency_key": "job_test_001_iter_1_writing",
            "iteration": 1,
            "authorized_inputs": {
                "outline_path": "projects/voice-rewriter/outlines/outline_job_test_001.json",
                "voice_model_bundle_path": "projects/voice-rewriter/profiles/ronald_ferrari/versions/v2.0.0/"
            },
            "expected_output_path": "projects/voice-rewriter/candidates/candidate_job_test_001_v1.md",
            "created_at": "2026-09-17T17:00:00Z",
            "updated_at": "2026-09-17T17:00:00Z"
        }

    def test_all_5_valid_queue_states_pass(self):
        for state in self.valid_queue_states:
            env = dict(self.valid_base_envelope)
            env["claim_status"] = state
            if state in ["CLAIMED", "RUNNING", "COMPLETED"]:
                env["claim_owner"] = "worker_writer_spark"
                env["claimed_at"] = "2026-09-17T17:01:00Z"
                env["lease_expires_at"] = "2026-09-17T17:16:00Z"
            validate(instance=env, schema=self.schema)

    def test_invalid_queue_state_fails(self):
        invalid_states = [
            "WAITING",
            "PENDING",
            "IN_PROGRESS",
            "SUCCESS",
            "PROMOTED",
            "WAITING_FOR_TRANSCRIPT"
        ]
        for state in invalid_states:
            env = dict(self.valid_base_envelope)
            env["claim_status"] = state
            with self.assertRaises(ValidationError, msg=f"State {state} should be rejected as QueueState"):
                validate(instance=env, schema=self.schema)

    def test_cannot_mix_job_state_into_queue_state(self):
        job_states = [
            "PROMOTED",
            "WAITING_FOR_TRANSCRIPT",
            "CI_PENDING",
            "CI_PASSED",
            "ITERATING",
            "READY_FOR_HUMAN_APPROVAL"
        ]
        for js in job_states:
            env = dict(self.valid_base_envelope)
            env["claim_status"] = js
            with self.assertRaises(ValidationError, msg=f"Job state {js} must not be accepted as claim_status"):
                validate(instance=env, schema=self.schema)

    def test_missing_queue_revision_fails(self):
        env = dict(self.valid_base_envelope)
        del env["queue_revision"]
        with self.assertRaises(ValidationError):
            validate(instance=env, schema=self.schema)

    def test_missing_idempotency_key_fails(self):
        env = dict(self.valid_base_envelope)
        del env["idempotency_key"]
        with self.assertRaises(ValidationError):
            validate(instance=env, schema=self.schema)

    def test_missing_run_id_fails(self):
        env = dict(self.valid_base_envelope)
        del env["run_id"]
        with self.assertRaises(ValidationError):
            validate(instance=env, schema=self.schema)

    def test_missing_lease_fields_fail(self):
        lease_fields = ["claim_owner", "claimed_at", "lease_expires_at"]
        for field in lease_fields:
            env = dict(self.valid_base_envelope)
            del env[field]
            with self.assertRaises(ValidationError, msg=f"Missing {field} must be rejected"):
                validate(instance=env, schema=self.schema)

    def test_missing_queue_identification_fails(self):
        env = dict(self.valid_base_envelope)
        del env["queue_name"]
        with self.assertRaises(ValidationError):
            validate(instance=env, schema=self.schema)

    def test_invalid_types_fail(self):
        env = dict(self.valid_base_envelope)
        env["attempt"] = "first"
        with self.assertRaises(ValidationError):
            validate(instance=env, schema=self.schema)

        env = dict(self.valid_base_envelope)
        env["attempt"] = 0
        with self.assertRaises(ValidationError):
            validate(instance=env, schema=self.schema)

        env = dict(self.valid_base_envelope)
        env["queue_revision"] = 123
        with self.assertRaises(ValidationError):
            validate(instance=env, schema=self.schema)

        env = dict(self.valid_base_envelope)
        env["idempotency_key"] = ""
        with self.assertRaises(ValidationError):
            validate(instance=env, schema=self.schema)


if __name__ == "__main__":
    unittest.main()
