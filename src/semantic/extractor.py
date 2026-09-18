import json
from pathlib import Path
from typing import Dict, Any, Optional
import jsonschema

class SemanticOutlineValidationError(Exception):
    pass

class SemanticExtractor:
    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is None:
            repo_root = Path(__file__).parent.parent.parent
        self.repo_root = Path(repo_root)
        self.schemas_dir = self.repo_root / "schemas"
        self._schema = None

    @property
    def schema(self) -> Dict[str, Any]:
        if self._schema is None:
            schema_path = self.schemas_dir / "outline.schema.json"
            with open(schema_path, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
        return self._schema

    def validate_outline(self, outline_data: Dict[str, Any]) -> None:
        try:
            jsonschema.validate(instance=outline_data, schema=self.schema)
        except jsonschema.ValidationError as e:
            raise SemanticOutlineValidationError(f"Invalid semantic outline: {e.message}") from e

    def build_writing_payload(
        self,
        job_id: str,
        outline_rel_path: str,
        voice_model_bundle_path: str,
        iteration: int = 1
    ) -> Dict[str, Any]:
        """Constructs sanitized writing payload enforcing least privilege (zero source_material leakage)."""
        payload = {
            "job_id": job_id,
            "outline_path": outline_rel_path,
            "voice_model_bundle_path": voice_model_bundle_path,
            "iteration": iteration
        }
        # Double check no source_material reference exists
        for key in payload:
            if "source_material" in key or "raw_source" in key:
                raise ValueError(f"Prohibited source reference in writing payload: {key}")
        return payload
