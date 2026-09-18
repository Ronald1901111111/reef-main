import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import jsonschema
from src.core.state_machine import JobStateManager

class ApprovalMissingError(Exception):
    pass

class ApprovalMismatchError(Exception):
    pass

class ScriptPromoter:
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = Path(repo_root)
        self.schemas_dir = self.repo_root / "schemas"
        self._schema = None

    @property
    def schema(self) -> Dict[str, Any]:
        if self._schema is None:
            schema_path = self.schemas_dir / "approval.schema.json"
            with open(schema_path, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
        return self._schema

    def validate_approval(self, approval_data: Dict[str, Any]) -> None:
        jsonschema.validate(instance=approval_data, schema=self.schema)

    def promote_candidate(
        self,
        job_id: str,
        candidate_version: str,
        candidate_file_path: Path,
        approval_file_path: Path,
        state_manager: Optional[JobStateManager] = None
    ) -> Path:
        if not approval_file_path.exists():
            raise ApprovalMissingError(f"Formal approval file not found at {approval_file_path}")

        with open(approval_file_path, "r", encoding="utf-8") as f:
            approval_data = json.load(f)

        self.validate_approval(approval_data)

        if approval_data["job_id"] != job_id:
            raise ApprovalMismatchError(
                f"Approval job_id mismatch: expected '{job_id}', found '{approval_data['job_id']}'"
            )
        if approval_data["candidate_version"] != candidate_version:
            raise ApprovalMismatchError(
                f"Approval version mismatch: expected '{candidate_version}', found '{approval_data['candidate_version']}'"
            )
        if approval_data["decision"] != "APPROVED":
            raise ApprovalMismatchError("Approval artifact decision is not APPROVED")

        slug = approval_data["slug"]
        outputs_dir = self.repo_root / "projects/voice-rewriter/outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)
        dest_path = outputs_dir / f"{slug}.md"

        # Copy candidate to promoted output
        shutil.copyfile(candidate_file_path, dest_path)

        if state_manager is None:
            state_manager = JobStateManager(repo_root=self.repo_root)

        # Transition job state strictly: READY_FOR_HUMAN_APPROVAL -> APPROVED_BY_HUMAN -> PROMOTED
        current_st = state_manager.get_job(job_id).get("status")
        if current_st == "READY_FOR_HUMAN_APPROVAL":
            state_manager.transition_job(
                job_id=job_id,
                target_status="APPROVED_BY_HUMAN",
                target_stage="human_approval",
                context={"approval_file": str(approval_file_path)}
            )
        state_manager.transition_job(
            job_id=job_id,
            target_status="PROMOTED",
            target_stage="completed",
            context={
                "promoted_file": str(dest_path.relative_to(self.repo_root)),
                "approved_by": approval_data["approved_by"]
            }
        )

        return dest_path
