"""
BBAP-Sec AI Attack Lab — ATLAS Attack Mapper
=============================================
Maps each BBAP-Sec attack module to its corresponding MITRE ATLAS
techniques, mitigations, and real-world case studies.

This is the bridge between our educational pipeline and the
ATLAS threat intelligence framework.

Usage:
    from src.atlas.atlas_mapper import ATLASMapper
    mapper = ATLASMapper()
    mapping = mapper.get_mapping("adversarial")
    mapper.print_mapping("adversarial")
    full = mapper.get_full_report()
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.atlas.atlas_data import ATLASDatabase
from src.utils.logger import get_logger

logger = get_logger("atlas_mapper")


# ──────────────────────────────────────────────
# Static Mapping: BBAP-Sec Modules → ATLAS IDs
# ──────────────────────────────────────────────
# Each entry maps a BBAP-Sec attack module to the specific ATLAS
# techniques it implements/tests, plus relevant mitigations and case studies.

ATTACK_MODULE_MAPPINGS = {
    "adversarial": {
        "module": "src/attacks/adversarial.py",
        "name": "Adversarial Attacks (FGSM / PGD)",
        "description": "Gradient-based input perturbations to cause misclassification",
        "atlas_techniques": [
            {
                "id": "AML.T0043",
                "relevance": "Craft Adversarial Data — core technique; FGSM and PGD directly implement this",
                "bbap_functions": ["fgsm_attack()", "pgd_attack()"],
            },
            {
                "id": "AML.T0043.000",
                "relevance": "Insert Backdoor Trigger — related; adversarial patches can serve as backdoors",
                "bbap_functions": [],
            },
            {
                "id": "AML.T0043.001",
                "relevance": "Craft Adversarial Data: Perturbation — direct match; both FGSM and PGD generate Lp-bounded perturbations",
                "bbap_functions": ["fgsm_attack()", "pgd_attack()"],
            },
            {
                "id": "AML.T0047",
                "relevance": "Evade ML Model — the goal of adversarial examples; tested by evaluate_robustness()",
                "bbap_functions": ["evaluate_robustness()"],
            },
        ],
        "atlas_mitigations": ["AML.M0004", "AML.M0003", "AML.M0014"],
        "atlas_case_studies": ["AML.CS0000", "AML.CS0003", "AML.CS0004"],
    },

    "data_poisoning": {
        "module": "src/attacks/data_poisoning.py",
        "name": "Data Poisoning (Label-flip / Backdoor)",
        "description": "Training-time attacks that corrupt model behavior via malicious data",
        "atlas_techniques": [
            {
                "id": "AML.T0020",
                "relevance": "Poison Training Data — core technique; both label-flip and backdoor are direct implementations",
                "bbap_functions": ["label_flip_poison()", "backdoor_poison()"],
            },
            {
                "id": "AML.T0020.000",
                "relevance": "Poison ML Training Data: Label Corruption — direct match for label_flip_poison()",
                "bbap_functions": ["label_flip_poison()"],
            },
            {
                "id": "AML.T0020.001",
                "relevance": "Poison ML Training Data: Data Injection — matches backdoor_poison() trigger insertion",
                "bbap_functions": ["backdoor_poison()"],
            },
            {
                "id": "AML.T0043.000",
                "relevance": "Insert Backdoor Trigger — directly tested by backdoor_poison()",
                "bbap_functions": ["backdoor_poison()"],
            },
        ],
        "atlas_mitigations": ["AML.M0004", "AML.M0001", "AML.M0002"],
        "atlas_case_studies": ["AML.CS0002", "AML.CS0009"],
    },

    "evasion": {
        "module": "src/attacks/evasion.py",
        "name": "Evasion Attacks (Pixel / Noise / Spatial)",
        "description": "Inference-time input manipulation to bypass model detection",
        "atlas_techniques": [
            {
                "id": "AML.T0047",
                "relevance": "Evade ML Model — core technique; all three evasion methods target this",
                "bbap_functions": ["pixel_perturbation_evasion()", "feature_noise_evasion()", "spatial_transform_evasion()"],
            },
            {
                "id": "AML.T0047.000",
                "relevance": "Evade ML Model: Adversarial Inputs — pixel perturbation and noise injection create adversarial inputs",
                "bbap_functions": ["pixel_perturbation_evasion()", "feature_noise_evasion()"],
            },
            {
                "id": "AML.T0047.003",
                "relevance": "Evade ML Model: Physical Environment Manipulation — spatial transforms simulate physical-world evasion",
                "bbap_functions": ["spatial_transform_evasion()"],
            },
        ],
        "atlas_mitigations": ["AML.M0004", "AML.M0014", "AML.M0003"],
        "atlas_case_studies": ["AML.CS0000", "AML.CS0001", "AML.CS0003"],
    },

    "model_extraction": {
        "module": "src/attacks/model_extraction.py",
        "name": "Model Extraction (Random / Active Learning)",
        "description": "Stealing model functionality by querying its API",
        "atlas_techniques": [
            {
                "id": "AML.T0005",
                "relevance": "ML Model Inference API Access — prerequisite; VictimAPI class simulates this access",
                "bbap_functions": ["VictimAPI.predict()", "VictimAPI.predict_proba()"],
            },
            {
                "id": "AML.T0005.000",
                "relevance": "Closed-Set Classification Model — label-only extraction via predict()",
                "bbap_functions": ["VictimAPI.predict()"],
            },
            {
                "id": "AML.T0005.002",
                "relevance": "Model API with Full Output — confidence extraction via predict_proba()",
                "bbap_functions": ["VictimAPI.predict_proba()"],
            },
            {
                "id": "AML.T0044",
                "relevance": "Full ML Model Access — the goal of extraction attacks",
                "bbap_functions": ["random_query_extraction()", "active_learning_extraction()"],
            },
            {
                "id": "AML.T0024",
                "relevance": "Exfiltration via ML Inference API — core technique; both random and active strategies extract model knowledge through API queries",
                "bbap_functions": ["random_query_extraction()", "active_learning_extraction()"],
            },
        ],
        "atlas_mitigations": ["AML.M0000", "AML.M0005", "AML.M0003"],
        "atlas_case_studies": ["AML.CS0005", "AML.CS0006"],
    },

    "prompt_injection": {
        "module": "src/attacks/prompt_injection.py",
        "name": "Prompt Injection (Direct / Indirect / Exfiltration)",
        "description": "Testing LLM systems against prompt-based attacks",
        "atlas_techniques": [
            {
                "id": "AML.T0051",
                "relevance": "LLM Prompt Injection — core technique; direct injection tests (DI-001 to DI-004)",
                "bbap_functions": ["DIRECT_INJECTION_TESTS"],
            },
            {
                "id": "AML.T0051.000",
                "relevance": "LLM Prompt Injection: Direct — system prompt override, role reassignment, encoding bypass",
                "bbap_functions": ["DIRECT_INJECTION_TESTS"],
            },
            {
                "id": "AML.T0051.001",
                "relevance": "LLM Prompt Injection: Indirect — document-embedded and RAG context poisoning tests",
                "bbap_functions": ["INDIRECT_INJECTION_TESTS"],
            },
            {
                "id": "AML.T0053",
                "relevance": "Extract ML Artifacts — data exfiltration tests probe for system prompt and context leakage",
                "bbap_functions": ["DATA_EXFILTRATION_TESTS"],
            },
            {
                "id": "AML.T0054",
                "relevance": "LLM Jailbreak — instruction hierarchy tests attempt to bypass safety constraints",
                "bbap_functions": ["INSTRUCTION_HIERARCHY_TESTS"],
            },
        ],
        "atlas_mitigations": ["AML.M0004", "AML.M0016", "AML.M0015"],
        "atlas_case_studies": ["AML.CS0016", "AML.CS0012"],
    },
}


class ATLASMapper:
    """
    Maps BBAP-Sec attack modules to MITRE ATLAS threat intelligence.
    Enriches static mappings with live data from the ATLAS database.
    """

    def __init__(self, db: ATLASDatabase = None):
        self.db = db or ATLASDatabase()
        self.db._ensure_loaded()
        logger.info("ATLASMapper initialized with ATLAS v" + str(self.db.version))

    def get_mapping(self, module_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the full enriched mapping for a BBAP-Sec attack module.
        Resolves ATLAS IDs to full objects with names and descriptions.
        """
        static = ATTACK_MODULE_MAPPINGS.get(module_name)
        if not static:
            logger.warning(f"No ATLAS mapping defined for module: {module_name}")
            return None

        # Enrich techniques with full ATLAS data
        enriched_techniques = []
        for tech_ref in static["atlas_techniques"]:
            tech = self.db.get_technique(tech_ref["id"])
            enriched_techniques.append({
                "id": tech_ref["id"],
                "name": tech.get("name", "Unknown") if tech else "Not found in ATLAS",
                "description": (tech.get("description", "")[:200] + "...") if tech and len(tech.get("description", "")) > 200 else (tech.get("description", "") if tech else ""),
                "tactics": tech.get("tactics", []) if tech else [],
                "relevance": tech_ref["relevance"],
                "bbap_functions": tech_ref["bbap_functions"],
                "atlas_url": f"https://atlas.mitre.org/techniques/{tech_ref['id']}" if tech else None,
            })

        # Enrich mitigations
        enriched_mitigations = []
        for mid in static.get("atlas_mitigations", []):
            mit = self.db.get_mitigation(mid)
            if mit:
                enriched_mitigations.append({
                    "id": mid,
                    "name": mit.get("name", ""),
                    "description": mit.get("description", "")[:200],
                    "atlas_url": f"https://atlas.mitre.org/mitigations/{mid}",
                })

        # Enrich case studies
        enriched_cases = []
        for csid in static.get("atlas_case_studies", []):
            cs = self.db.get_case_study(csid)
            if cs:
                enriched_cases.append({
                    "id": csid,
                    "name": cs.get("name", ""),
                    "summary": cs.get("summary", "")[:200],
                    "incident_date": cs.get("incident-date", ""),
                    "atlas_url": f"https://atlas.mitre.org/studies/{csid}",
                })

        return {
            "module": static["module"],
            "name": static["name"],
            "description": static["description"],
            "techniques": enriched_techniques,
            "mitigations": enriched_mitigations,
            "case_studies": enriched_cases,
        }

    def get_all_mappings(self) -> Dict[str, Any]:
        """Get enriched mappings for all BBAP-Sec modules."""
        return {name: self.get_mapping(name) for name in ATTACK_MODULE_MAPPINGS}

    def get_coverage_matrix(self) -> Dict[str, List[str]]:
        """
        Returns which ATLAS tactics are covered by BBAP-Sec modules.
        Useful for gap analysis.
        """
        coverage = {}
        for module_name, static in ATTACK_MODULE_MAPPINGS.items():
            for tech_ref in static["atlas_techniques"]:
                tech = self.db.get_technique(tech_ref["id"])
                if tech:
                    for tactic_id in tech.get("tactics", []):
                        tactic = self.db.get_tactic(tactic_id)
                        tactic_name = tactic.get("name", tactic_id) if tactic else tactic_id
                        if tactic_name not in coverage:
                            coverage[tactic_name] = []
                        if module_name not in coverage[tactic_name]:
                            coverage[tactic_name].append(module_name)
        return coverage

    def print_mapping(self, module_name: str):
        """Print a formatted mapping for a module."""
        mapping = self.get_mapping(module_name)
        if not mapping:
            print(f"No mapping found for: {module_name}")
            return

        print(f"\n{'='*70}")
        print(f"  ATLAS Mapping: {mapping['name']}")
        print(f"  {mapping['description']}")
        print(f"{'='*70}")

        print(f"\n  TECHNIQUES ({len(mapping['techniques'])})")
        print(f"  {'─'*66}")
        for t in mapping["techniques"]:
            print(f"  {t['id']:<16} {t['name']}")
            print(f"  {'':16} Relevance: {t['relevance']}")
            if t["bbap_functions"]:
                print(f"  {'':16} Functions: {', '.join(t['bbap_functions'])}")
            print()

        print(f"  MITIGATIONS ({len(mapping['mitigations'])})")
        print(f"  {'─'*66}")
        for m in mapping["mitigations"]:
            print(f"  {m['id']:<16} {m['name']}")

        print(f"\n  CASE STUDIES ({len(mapping['case_studies'])})")
        print(f"  {'─'*66}")
        for cs in mapping["case_studies"]:
            print(f"  {cs['id']:<16} {cs['name']}")

        print(f"\n{'='*70}\n")

    def get_full_report(self) -> Dict[str, Any]:
        """Generate a comprehensive ATLAS coverage report."""
        all_mappings = self.get_all_mappings()
        coverage = self.get_coverage_matrix()
        stats = self.db.get_stats()

        # Count unique techniques covered
        all_tech_ids = set()
        for mapping in all_mappings.values():
            if mapping:
                for t in mapping["techniques"]:
                    all_tech_ids.add(t["id"])

        return {
            "atlas_version": stats["version"],
            "atlas_stats": stats,
            "bbap_modules": len(all_mappings),
            "unique_techniques_covered": len(all_tech_ids),
            "technique_ids_covered": sorted(all_tech_ids),
            "tactic_coverage": coverage,
            "mappings": all_mappings,
        }
