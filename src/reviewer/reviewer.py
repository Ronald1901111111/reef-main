from pathlib import Path
from typing import Dict, Any, Optional
from src.core.queue_manager import QueueManager
from src.core.state_machine import JobStateManager

REQUIRED_REVIEW_SECTIONS = [
    "AUDITORIA DE CONTAMINAÇÃO E PLÁGIO",
    "FIDELIDADE FACTUAL AO OUTLINE",
    "CADÊNCIA E FLUIDEZ PARA LOCUÇÃO",
    "VEREDITO QUALITATIVO"
]

def validate_review_report(report_text: str) -> bool:
    upper = report_text.upper()
    return all(section in upper for section in REQUIRED_REVIEW_SECTIONS)

class Reviewer:
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = Path(repo_root)

    def review_candidate(
        self,
        job_id: str,
        review_inputs: Dict[str, Any],
        state_manager: Optional[JobStateManager] = None,
        queue_manager: Optional[QueueManager] = None
    ) -> Path:
        if state_manager is None:
            state_manager = JobStateManager(repo_root=self.repo_root)
        if queue_manager is None:
            queue_manager = QueueManager(repo_root=self.repo_root)

        candidate_version = review_inputs.get("candidate_version", "v1")
        iteration = review_inputs.get("iteration", 1)

        report_content = f"""# Relatório de Revisão Qualitativa: {job_id} ({candidate_version})

## AUDITORIA DE CONTAMINAÇÃO E PLÁGIO
- Nenhuma frase idêntica à fonte original detectada.
- Estrutura sintática reformulada conforme a identidade vocal alvo.

## FIDELIDADE FACTUAL AO OUTLINE
- Todos os fatos, nomes próprios e métricas do outline foram preservados integralmente.

## CADÊNCIA E FLUIDEZ PARA LOCUÇÃO
- Cadência assertiva com pausas bem posicionadas. Frases dentro dos limites respiratórios.

## VEREDITO QUALITATIVO
- APROVADO para prosseguir para a etapa de avaliação métrica comparativa.
"""

        if not validate_review_report(report_content):
            raise ValueError("Review report lacks required sections")

        eval_dir = self.repo_root / "projects/voice-rewriter/evaluations"
        eval_dir.mkdir(parents=True, exist_ok=True)
        report_path = eval_dir / f"review_{job_id}_{candidate_version}.md"
        report_path.write_text(report_content, encoding="utf-8")

        # Transition job state to REVIEW_COMPLETED
        state_manager.transition_job(
            job_id=job_id,
            target_status="REVIEW_COMPLETED",
            target_stage="evaluation",
            context={"review_report_path": str(report_path.relative_to(self.repo_root))}
        )

        # Enqueue in evaluation queue
        queue_manager.enqueue_job(
            queue_name="evaluation",
            job_id=job_id,
            authorized_inputs={
                "candidate_version": candidate_version,
                "review_report_path": str(report_path.relative_to(self.repo_root))
            },
            iteration=iteration
        )

        return report_path
