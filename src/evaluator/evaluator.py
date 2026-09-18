import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import jsonschema
from src.core.queue_manager import QueueManager
from src.core.state_machine import JobStateManager

class Evaluator:
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = Path(repo_root)
        self.schemas_dir = self.repo_root / "schemas"
        self._schema = None

    @property
    def schema(self) -> Dict[str, Any]:
        if self._schema is None:
            schema_path = self.schemas_dir / "evaluation.schema.json"
            with open(schema_path, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
        return self._schema

    def evaluate_candidate(
        self,
        job_id: str,
        candidate_version: str,
        scores_input: Dict[str, float],
        state_manager: Optional[JobStateManager] = None,
        queue_manager: Optional[QueueManager] = None
    ) -> Dict[str, Any]:
        if state_manager is None:
            state_manager = JobStateManager(repo_root=self.repo_root)
        if queue_manager is None:
            queue_manager = QueueManager(repo_root=self.repo_root)

        job = state_manager.get_job(job_id)
        frozen_calib = job["calibration_manifest_path"]
        frozen_bundle = job["voice_model_bundle_path"]

        factual_fidelity = scores_input.get("factual_fidelity", 10.0)
        contamination = scores_input.get("source_style_contamination", 0.0)
        func_vocab = scores_input.get("functional_vocabulary_score", 9.0)
        syntax_cadence = scores_input.get("syntactic_cadence_score", 9.0)
        rhetorical = scores_input.get("rhetorical_alignment_score", 9.0)

        # Compute weighted composite score (heavy weight on functional vocabulary and cadence)
        # Functional vocab: 40%, cadence: 30%, rhetorical: 30%
        composite = round(0.4 * func_vocab + 0.3 * syntax_cadence + 0.3 * rhetorical, 2)

        # Veto gates
        factual_passed = factual_fidelity >= 9.5
        contamination_passed = contamination <= 2.0

        if not factual_passed or not contamination_passed:
            recommendation = "NEEDS_ITERATION"
        elif composite >= 8.5:
            recommendation = "PROCEED_TO_HUMAN_APPROVAL"
        else:
            recommendation = "NEEDS_ITERATION"

        report = {
            "job_id": job_id,
            "candidate_version": candidate_version,
            "calibration_manifest_path": frozen_calib,
            "voice_model_bundle_path": frozen_bundle,
            "scores": {
                "functional_vocabulary_score": round(func_vocab, 2),
                "syntactic_cadence_score": round(syntax_cadence, 2),
                "rhetorical_alignment_score": round(rhetorical, 2),
                "factual_fidelity": round(factual_fidelity, 2),
                "source_style_contamination": round(contamination, 2),
                "composite_similarity_score": composite
            },
            "veto_gates": {
                "factual_fidelity_passed": factual_passed,
                "contamination_passed": contamination_passed
            },
            "recommendation": recommendation,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        # Validate against schema
        jsonschema.validate(instance=report, schema=self.schema)

        eval_dir = self.repo_root / "projects/voice-rewriter/evaluations"
        eval_dir.mkdir(parents=True, exist_ok=True)
        eval_path = eval_dir / f"eval_{job_id}_{candidate_version}.json"
        eval_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        # Transition job state to EVALUATION_PENDING then EVALUATED
        current_st = job.get("status")
        if current_st == "REVIEW_COMPLETED":
            state_manager.transition_job(
                job_id=job_id,
                target_status="EVALUATION_PENDING",
                target_stage="evaluation",
                context={"evaluation_path": str(eval_path.relative_to(self.repo_root))}
            )
        state_manager.transition_job(
            job_id=job_id,
            target_status="EVALUATED",
            target_stage="controller",
            context={"evaluation_path": str(eval_path.relative_to(self.repo_root))}
        )

        # Enqueue in controller queue
        queue_manager.enqueue_job(
            queue_name="controller",
            job_id=job_id,
            authorized_inputs={
                "candidate_version": candidate_version,
                "evaluation_path": str(eval_path.relative_to(self.repo_root)),
                "recommendation": recommendation
            },
            iteration=1
        )

        return report
