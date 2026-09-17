from enum import Enum
from typing import Dict, Set, List, Optional, Any
from src.core.exceptions import IllegalStateTransitionError

class JobState(str, Enum):
    WAITING_FOR_TRANSCRIPT = "WAITING_FOR_TRANSCRIPT"
    SEMANTIC_EXTRACTION_PENDING = "SEMANTIC_EXTRACTION_PENDING"
    SEMANTIC_EXTRACTION_COMPLETED = "SEMANTIC_EXTRACTION_COMPLETED"
    WRITING_PENDING = "WRITING_PENDING"
    CANDIDATE_GENERATED = "CANDIDATE_GENERATED"
    CI_PENDING = "CI_PENDING"
    CI_PASSED = "CI_PASSED"
    CI_FAILED = "CI_FAILED"
    REVIEW_PENDING = "REVIEW_PENDING"
    REVIEW_COMPLETED = "REVIEW_COMPLETED"
    EVALUATION_PENDING = "EVALUATION_PENDING"
    EVALUATED = "EVALUATED"
    ITERATING = "ITERATING"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    READY_FOR_HUMAN_APPROVAL = "READY_FOR_HUMAN_APPROVAL"
    APPROVED_BY_HUMAN = "APPROVED_BY_HUMAN"
    PROMOTED = "PROMOTED"
    FAILED = "FAILED"

class QueueState(str, Enum):
    QUEUED = "QUEUED"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

JOB_TRANSITIONS: Dict[JobState, Set[JobState]] = {
    JobState.WAITING_FOR_TRANSCRIPT: {
        JobState.SEMANTIC_EXTRACTION_PENDING,
        JobState.FAILED,
    },
    JobState.SEMANTIC_EXTRACTION_PENDING: {
        JobState.SEMANTIC_EXTRACTION_COMPLETED,
        JobState.FAILED,
    },
    JobState.SEMANTIC_EXTRACTION_COMPLETED: {
        JobState.WRITING_PENDING,
        JobState.FAILED,
    },
    JobState.WRITING_PENDING: {
        JobState.CANDIDATE_GENERATED,
        JobState.FAILED,
    },
    JobState.CANDIDATE_GENERATED: {
        JobState.CI_PENDING,
        JobState.FAILED,
    },
    JobState.CI_PENDING: {
        JobState.CI_PASSED,
        JobState.CI_FAILED,
        JobState.FAILED,
    },
    JobState.CI_PASSED: {
        JobState.REVIEW_PENDING,
        JobState.FAILED,
    },
    JobState.CI_FAILED: {
        JobState.ITERATING,
        JobState.NEEDS_HUMAN_REVIEW,
        JobState.FAILED,
    },
    JobState.REVIEW_PENDING: {
        JobState.REVIEW_COMPLETED,
        JobState.FAILED,
    },
    JobState.REVIEW_COMPLETED: {
        JobState.EVALUATION_PENDING,
        JobState.FAILED,
    },
    JobState.EVALUATION_PENDING: {
        JobState.EVALUATED,
        JobState.FAILED,
    },
    JobState.EVALUATED: {
        JobState.ITERATING,
        JobState.READY_FOR_HUMAN_APPROVAL,
        JobState.NEEDS_HUMAN_REVIEW,
        JobState.FAILED,
    },
    JobState.ITERATING: {
        JobState.WRITING_PENDING,
        JobState.NEEDS_HUMAN_REVIEW,
        JobState.FAILED,
    },
    JobState.NEEDS_HUMAN_REVIEW: {
        JobState.WRITING_PENDING,
        JobState.READY_FOR_HUMAN_APPROVAL,
        JobState.FAILED,
    },
    JobState.READY_FOR_HUMAN_APPROVAL: {
        JobState.APPROVED_BY_HUMAN,
        JobState.NEEDS_HUMAN_REVIEW,
        JobState.FAILED,
    },
    JobState.APPROVED_BY_HUMAN: {
        JobState.PROMOTED,
        JobState.FAILED,
    },
    JobState.PROMOTED: set(),
    JobState.FAILED: set(),
}

QUEUE_TRANSITIONS: Dict[QueueState, Set[QueueState]] = {
    QueueState.QUEUED: {QueueState.CLAIMED, QueueState.FAILED},
    QueueState.CLAIMED: {QueueState.RUNNING, QueueState.QUEUED, QueueState.FAILED},
    QueueState.RUNNING: {QueueState.COMPLETED, QueueState.FAILED, QueueState.QUEUED},
    QueueState.COMPLETED: set(),
    QueueState.FAILED: {QueueState.QUEUED},
}

def can_transition_job(current: str, target: str) -> bool:
    try:
        cur_enum = JobState(current)
        tgt_enum = JobState(target)
    except ValueError:
        return False
    return tgt_enum in JOB_TRANSITIONS.get(cur_enum, set())

def assert_transition_job(current: str, target: str, context: Optional[Dict[str, Any]] = None) -> None:
    if not can_transition_job(current, target):
        ctx_str = f" Context: {context}" if context else ""
        raise IllegalStateTransitionError(
            f"Illegal JobState transition: '{current}' -> '{target}'.{ctx_str}"
        )

def get_valid_next_job_states(current: str) -> List[str]:
    try:
        cur_enum = JobState(current)
        return [s.value for s in JOB_TRANSITIONS.get(cur_enum, set())]
    except ValueError:
        return []

def can_transition_queue(current: str, target: str) -> bool:
    try:
        cur_enum = QueueState(current)
        tgt_enum = QueueState(target)
    except ValueError:
        return False
    return tgt_enum in QUEUE_TRANSITIONS.get(cur_enum, set())

def assert_transition_queue(current: str, target: str, context: Optional[Dict[str, Any]] = None) -> None:
    if not can_transition_queue(current, target):
        ctx_str = f" Context: {context}" if context else ""
        raise IllegalStateTransitionError(
            f"Illegal QueueState transition: '{current}' -> '{target}'.{ctx_str}"
        )

def get_valid_next_queue_states(current: str) -> List[str]:
    try:
        cur_enum = QueueState(current)
        return [s.value for s in QUEUE_TRANSITIONS.get(cur_enum, set())]
    except ValueError:
        return []

import json
from datetime import datetime, timezone
from pathlib import Path
import jsonschema

class JobStateManager:
    def __init__(self, repo_root: Optional[Path] = None, state_dir_rel: str = "spark-github/state/jobs"):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = Path(repo_root)
        self.state_dir = self.repo_root / state_dir_rel
        self.schemas_dir = self.repo_root / "schemas"
        self._job_schema = None

    @property
    def job_schema(self) -> Dict[str, Any]:
        if self._job_schema is None:
            schema_path = self.schemas_dir / "job_state.schema.json"
            with open(schema_path, "r", encoding="utf-8") as f:
                self._job_schema = json.load(f)
        return self._job_schema

    def validate_job(self, job_data: Dict[str, Any]) -> None:
        jsonschema.validate(instance=job_data, schema=self.job_schema)

    def get_job_path(self, job_id: str) -> Path:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        return self.state_dir / f"{job_id}.json"

    def create_job(
        self,
        job_id: str,
        voice_model_bundle_path: str,
        calibration_manifest_path: str,
        initial_status: str = "WAITING_FOR_TRANSCRIPT",
        initial_stage: str = "ingestion",
        iteration: int = 1,
        max_iterations: int = 5,
        max_failures: int = 3,
        global_artifacts: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        job_data = {
            "job_id": job_id,
            "status": initial_status,
            "current_stage": initial_stage,
            "iteration": iteration,
            "max_iterations": max_iterations,
            "failure_count": 0,
            "max_failures": max_failures,
            "voice_model_bundle_path": voice_model_bundle_path,
            "calibration_manifest_path": calibration_manifest_path,
            "global_artifacts": global_artifacts or {},
            "created_at": now_iso,
            "updated_at": now_iso
        }
        self.validate_job(job_data)
        job_path = self.get_job_path(job_id)
        with open(job_path, "w", encoding="utf-8") as f:
            json.dump(job_data, f, indent=2, ensure_ascii=False)
        return job_data

    def get_job(self, job_id: str) -> Dict[str, Any]:
        job_path = self.get_job_path(job_id)
        if not job_path.exists():
            raise FileNotFoundError(f"Job state file not found at {job_path}")
        with open(job_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def transition_job(
        self,
        job_id: str,
        target_status: str,
        target_stage: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        global_artifacts_update: Optional[Dict[str, Any]] = None,
        iteration_increment: int = 0,
        failure_increment: int = 0
    ) -> Dict[str, Any]:
        job_data = self.get_job(job_id)
        current_status = job_data["status"]
        assert_transition_job(current_status, target_status, context=context)

        now_iso = datetime.now(timezone.utc).isoformat()
        job_data["status"] = target_status
        if target_stage:
            job_data["current_stage"] = target_stage
        if iteration_increment:
            job_data["iteration"] += iteration_increment
        if failure_increment:
            job_data["failure_count"] += failure_increment

        if global_artifacts_update:
            if "global_artifacts" not in job_data or not isinstance(job_data["global_artifacts"], dict):
                job_data["global_artifacts"] = {}
            job_data["global_artifacts"].update(global_artifacts_update)

        job_data["updated_at"] = now_iso
        self.validate_job(job_data)

        job_path = self.get_job_path(job_id)
        with open(job_path, "w", encoding="utf-8") as f:
            json.dump(job_data, f, indent=2, ensure_ascii=False)
        return job_data
