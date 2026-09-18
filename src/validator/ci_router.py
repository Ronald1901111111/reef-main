from pathlib import Path
from typing import Dict, Any, Optional
from src.core.queue_manager import QueueManager
from src.core.state_machine import JobStateManager

class CIRouter:
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = Path(repo_root)

    def route_lint_result(
        self,
        job_id: str,
        lint_report: Dict[str, Any],
        state_manager: Optional[JobStateManager] = None,
        queue_manager: Optional[QueueManager] = None
    ) -> Dict[str, Any]:
        if state_manager is None:
            state_manager = JobStateManager(repo_root=self.repo_root)
        if queue_manager is None:
            queue_manager = QueueManager(repo_root=self.repo_root)

        status = lint_report["status"]
        cand_version = lint_report.get("candidate_version", "v1")

        if status == "PASSED":
            # CI_PASSED -> Enqueue in review
            state_manager.transition_job(
                job_id=job_id,
                target_status="CI_PASSED",
                target_stage="review",
                context={"lint_status": "PASSED"}
            )
            envelope = queue_manager.enqueue_job(
                queue_name="review",
                job_id=job_id,
                authorized_inputs={
                    "candidate_version": cand_version,
                    "lint_report": lint_report
                },
                iteration=1
            )
            return {"routed_to": "review", "envelope": envelope}
        else:
            # CI_FAILED -> Enqueue in controller
            state_manager.transition_job(
                job_id=job_id,
                target_status="CI_FAILED",
                target_stage="controller",
                context={"violations": lint_report.get("violations", [])}
            )
            envelope = queue_manager.enqueue_job(
                queue_name="controller",
                job_id=job_id,
                authorized_inputs={
                    "origin_stage": "ci_linter",
                    "reason": "lint_failure",
                    "lint_report": lint_report
                },
                iteration=1
            )
            return {"routed_to": "controller", "envelope": envelope}
