import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Set

def stratify_vocabulary(
    corpus_tokens: List[str],
    forbidden_overrides: List[str],
    vocab_dictionary: Set[str]
) -> Dict[str, List[str]]:
    token_counts = {}
    for t in corpus_tokens:
        token_counts[t] = token_counts.get(t, 0) + 1

    char_terms = []
    obs_terms = []
    rare_terms = []
    unobserved = []

    for t, count in token_counts.items():
        if count >= 3:
            char_terms.append(t)
        elif count == 2:
            obs_terms.append(t)
        else:
            rare_terms.append(t)

    for word in sorted(vocab_dictionary):
        if word not in token_counts:
            unobserved.append(word)

    return {
        "characteristic_terms": sorted(char_terms),
        "observed_terms": sorted(obs_terms),
        "rare_terms": sorted(rare_terms),
        "statistically_unobserved_terms": sorted(unobserved),
        "explicitly_forbidden_terms": sorted(list(set(forbidden_overrides)))
    }

def validate_voice_profile(profile_data: Dict[str, Any], schema_path: Path) -> None:
    import jsonschema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(instance=profile_data, schema=schema)

def validate_voice_analysis(analysis_data: Dict[str, Any], schema_path: Path) -> None:
    import jsonschema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(instance=analysis_data, schema=schema)

def validate_curated_samples_manifest(manifest_data: Dict[str, Any], schema_path: Path) -> None:
    import jsonschema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(instance=manifest_data, schema=schema)
    for s in manifest_data.get("samples", []):
        if s.get("provenance", {}).get("split") != "training":
            raise ValueError("Curated samples must strictly originate from the training split")
