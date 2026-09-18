import json
import re
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import jsonschema

class VoiceLinter:
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = Path(repo_root)
        self.schemas_dir = self.repo_root / "schemas"
        self._schema = None

    @property
    def schema(self) -> Dict[str, Any]:
        if self._schema is None:
            schema_path = self.schemas_dir / "lint_report.schema.json"
            with open(schema_path, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
        return self._schema

    def tokenize_words(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\b[a-zA-Z0-9áéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ\-]+\b", text)]

    def split_sentences(self, text: str) -> List[str]:
        raw = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in raw if len(s.strip()) > 1 and any(c.isalnum() for c in s)]

    def lint(
        self,
        job_id: str,
        candidate_text: str,
        candidate_version: str,
        voice_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        strat = voice_profile.get("vocabulary_stratification", {})
        forbidden = set(strat.get("explicitly_forbidden_terms", []))
        unobserved = set(strat.get("statistically_unobserved_terms", []))
        voice_model_version = voice_profile.get("version", "unknown")

        tokens = self.tokenize_words(candidate_text)
        sentences = self.split_sentences(candidate_text)

        violations = []
        warnings = []

        # 1. Check forbidden terms -> VIOLATION
        for term in forbidden:
            if term.lower() in tokens:
                violations.append(f"Forbidden term detected: '{term}'")

        # 2. Check sentence length > 24 words -> VIOLATION
        max_len = 0
        long_count = 0
        for s in sentences:
            s_tokens = self.tokenize_words(s)
            length = len(s_tokens)
            if length > max_len:
                max_len = length
            if length > 24:
                long_count += 1
                violations.append(f"Sentence exceeds 24 words ({length} words): '{s[:60]}...'")

        # 3. Check statistically unobserved terms -> WARNING only
        for term in unobserved:
            if term.lower() in tokens:
                warnings.append(f"Statistically unobserved term used: '{term}' (allowed, flagged for review)")

        status = "FAILED" if violations else "PASSED"

        report = {
            "job_id": job_id,
            "candidate_version": candidate_version,
            "voice_model_version": voice_model_version,
            "status": status,
            "violations": violations,
            "warnings": warnings,
            "metrics": {
                "max_sentence_length": max_len,
                "long_sentences_count": long_count
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        jsonschema.validate(instance=report, schema=self.schema)
        return report
