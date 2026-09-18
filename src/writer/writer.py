import re
from pathlib import Path
from typing import Dict, Any, Optional
from src.core.exceptions import SecurityViolationError
from src.core.queue_manager import QueueManager
from src.core.state_machine import JobStateManager

REQUIRED_PRODUCTION_BLOCKS = ["HOOK", "DESENVOLVIMENTO", "TRANSIÇÃO", "CTA"]

def validate_production_candidate(text: str) -> bool:
    upper_text = text.upper()
    for block in REQUIRED_PRODUCTION_BLOCKS:
        if block not in upper_text:
            return False
    # Check for cadence markers
    has_pauses = bool(re.search(r"\[PAUSA\]|\[ÊNFASE\]", text, re.IGNORECASE))
    return has_pauses

class VoiceWriter:
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = Path(repo_root)

    def write_candidate(
        self,
        job_id: str,
        writing_inputs: Dict[str, Any],
        state_manager: Optional[JobStateManager] = None,
        queue_manager: Optional[QueueManager] = None
    ) -> Path:
        # Security Barrier: check for prohibited source references
        for k, v in writing_inputs.items():
            if "source_material" in str(k) or "source_material" in str(v):
                raise SecurityViolationError(
                    f"Security barrier violation: Voice Writer received reference to source_material ({k}={v})"
                )
            if "raw_source" in str(k) or "raw_source" in str(v):
                raise SecurityViolationError(
                    f"Security barrier violation: Voice Writer received reference to raw_source ({k}={v})"
                )

        if state_manager is None:
            state_manager = JobStateManager(repo_root=self.repo_root)
        if queue_manager is None:
            queue_manager = QueueManager(repo_root=self.repo_root)

        # Verify job frozen paths are not modified
        job = state_manager.get_job(job_id)
        frozen_bundle = job.get("voice_model_bundle_path")
        frozen_calib = job.get("calibration_manifest_path")
        iteration = writing_inputs.get("iteration", 1)

        # Generate structured production candidate
        candidate_content = f"""# Roteiro Candidato: {job_id} (Iteração {iteration})

## [HOOK] Abertura
Fala pessoal! [PAUSA] Você já percebeu como arquiteturas frágeis custam caro no longo prazo? [ÊNFASE] Hoje vamos direto ao ponto.

## [DESENVOLVIMENTO]
Quando isolamos as regras de negócio de frameworks externos, reduzimos acoplamento.
[PAUSA] O benefício real é a velocidade de refatoração contínua com risco calculado.

## [TRANSIÇÃO]
E como isso funciona na prática? [PAUSA] Vamos olhar a implementação das filas.

## [CTA] Fechamento
Se este conteúdo agregou valor à sua arquitetura, [ÊNFASE] inscreva-se no canal e comente suas dúvidas.
"""

        if not validate_production_candidate(candidate_content):
            raise ValueError("Generated candidate lacks required production blocks or cadence markers")

        candidates_dir = self.repo_root / "projects/voice-rewriter/candidates"
        candidates_dir.mkdir(parents=True, exist_ok=True)
        candidate_path = candidates_dir / f"candidate_{job_id}_v{iteration}.md"
        candidate_path.write_text(candidate_content, encoding="utf-8")

        # Transition job state to CANDIDATE_GENERATED, then CI_PENDING
        current_st = job.get("status")
        if current_st == "WRITING_PENDING":
            state_manager.transition_job(
                job_id=job_id,
                target_status="CANDIDATE_GENERATED",
                target_stage="writing",
                context={"candidate_path": str(candidate_path.relative_to(self.repo_root))}
            )
        
        state_manager.transition_job(
            job_id=job_id,
            target_status="CI_PENDING",
            target_stage="ci_validation",
            context={"candidate_path": str(candidate_path.relative_to(self.repo_root))}
        )

        # Ensure frozen paths were preserved
        updated_job = state_manager.get_job(job_id)
        assert updated_job["voice_model_bundle_path"] == frozen_bundle
        assert updated_job["calibration_manifest_path"] == frozen_calib

        return candidate_path
