"""
BBAP-Sec AI Attack Lab — MITRE ATLAS Integration
==================================================
Loads ATLAS v5.6.0 data (tactics, techniques, mitigations, case studies)
and provides search, lookup, and mapping APIs.

Data source: https://github.com/mitre-atlas/atlas-data (dist/ATLAS.yaml)

Usage:
    from src.atlas.atlas_data import ATLASDatabase
    db = ATLASDatabase()
    db.load()

    # Lookup by ID
    tech = db.get_technique("AML.T0043")

    # Search by keyword
    results = db.search_techniques("adversarial evasion")

    # Get mitigations for a technique
    mits = db.get_mitigations_for_technique("AML.T0043")

    # Get full attack chain from a case study
    chain = db.get_case_study_chain("AML.CS0000")
"""

import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Any

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.logger import get_logger

logger = get_logger("atlas")

# Path to bundled ATLAS.yaml
ATLAS_YAML_PATH = os.path.join(os.path.dirname(__file__), "ATLAS.yaml")

# GitHub source for updates
ATLAS_GITHUB_RAW = "https://raw.githubusercontent.com/mitre-atlas/atlas-data/main/dist/ATLAS.yaml"


class ATLASDatabase:
    """
    In-memory ATLAS knowledge base with search, lookup, and mapping APIs.
    Mirrors the approach of ATT-CKGenius but for ML/AI-specific threats.
    """

    def __init__(self, yaml_path: str = None):
        self.yaml_path = yaml_path or ATLAS_YAML_PATH
        self.version = None
        self.tactics: Dict[str, Dict] = {}
        self.techniques: Dict[str, Dict] = {}
        self.mitigations: Dict[str, Dict] = {}
        self.case_studies: Dict[str, Dict] = {}
        self._loaded = False

    def load(self):
        """Load and index ATLAS data from YAML file."""
        logger.info(f"Loading ATLAS data from {self.yaml_path}")

        with open(self.yaml_path, "r") as f:
            data = yaml.safe_load(f)

        self.version = data.get("version", "unknown")
        matrix = data["matrices"][0]

        # Index tactics
        for t in matrix.get("tactics", []):
            self.tactics[t["id"]] = t
        logger.info(f"  Tactics loaded: {len(self.tactics)}")

        # Index techniques (including sub-techniques)
        for t in matrix.get("techniques", []):
            self.techniques[t["id"]] = t
        logger.info(f"  Techniques loaded: {len(self.techniques)}")

        # Index mitigations and build reverse lookup
        for m in matrix.get("mitigations", []):
            self.mitigations[m["id"]] = m
        logger.info(f"  Mitigations loaded: {len(self.mitigations)}")

        # Index case studies
        for cs in data.get("case-studies", []):
            self.case_studies[cs["id"]] = cs
        logger.info(f"  Case studies loaded: {len(self.case_studies)}")

        logger.info(f"ATLAS v{self.version} loaded — {len(self.tactics)} tactics, "
                     f"{len(self.techniques)} techniques, {len(self.mitigations)} mitigations, "
                     f"{len(self.case_studies)} case studies")
        self._loaded = True
        return self

    def _ensure_loaded(self):
        if not self._loaded:
            self.load()

    # ── Lookup by ID ──

    def get_tactic(self, tactic_id: str) -> Optional[Dict]:
        """Get a tactic by its ATLAS ID (e.g., AML.TA0000)."""
        self._ensure_loaded()
        return self.tactics.get(tactic_id)

    def get_technique(self, tech_id: str) -> Optional[Dict]:
        """Get a technique by its ATLAS ID (e.g., AML.T0043)."""
        self._ensure_loaded()
        return self.techniques.get(tech_id)

    def get_mitigation(self, mit_id: str) -> Optional[Dict]:
        """Get a mitigation by its ATLAS ID (e.g., AML.M0000)."""
        self._ensure_loaded()
        return self.mitigations.get(mit_id)

    def get_case_study(self, cs_id: str) -> Optional[Dict]:
        """Get a case study by its ATLAS ID (e.g., AML.CS0000)."""
        self._ensure_loaded()
        return self.case_studies.get(cs_id)

    # ── Search ──

    def search_techniques(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search techniques by keyword in name and description."""
        self._ensure_loaded()
        query_lower = query.lower()
        scored = []
        for tech in self.techniques.values():
            name = tech.get("name", "").lower()
            desc = tech.get("description", "").lower()
            score = 0
            for term in query_lower.split():
                if term in name:
                    score += 3  # name matches weighted higher
                if term in desc:
                    score += 1
            if score > 0:
                scored.append((score, tech))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [t for _, t in scored[:max_results]]
        logger.debug(f"Search '{query}' returned {len(results)} techniques")
        return results

    def search_case_studies(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search case studies by keyword in name and summary."""
        self._ensure_loaded()
        query_lower = query.lower()
        scored = []
        for cs in self.case_studies.values():
            name = cs.get("name", "").lower()
            summary = cs.get("summary", "").lower()
            score = 0
            for term in query_lower.split():
                if term in name:
                    score += 3
                if term in summary:
                    score += 1
            if score > 0:
                scored.append((score, cs))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [cs for _, cs in scored[:max_results]]

    def search_mitigations(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search mitigations by keyword."""
        self._ensure_loaded()
        query_lower = query.lower()
        scored = []
        for m in self.mitigations.values():
            name = m.get("name", "").lower()
            desc = m.get("description", "").lower()
            score = sum(3 if t in name else (1 if t in desc else 0) for t in query_lower.split())
            if score > 0:
                scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:max_results]]

    # ── Relationship Queries ──

    def get_techniques_for_tactic(self, tactic_id: str) -> List[Dict]:
        """Get all techniques under a specific tactic."""
        self._ensure_loaded()
        return [t for t in self.techniques.values()
                if tactic_id in (t.get("tactics") or [])]

    def get_mitigations_for_technique(self, tech_id: str) -> List[Dict]:
        """Get all mitigations that address a specific technique."""
        self._ensure_loaded()
        results = []
        for m in self.mitigations.values():
            tech_refs = m.get("techniques", [])
            for ref in tech_refs:
                if ref.get("id") == tech_id:
                    results.append({**m, "_use": ref.get("use", "")})
                    break
        return results

    def get_case_study_chain(self, cs_id: str) -> Optional[List[Dict]]:
        """
        Get the full attack procedure chain from a case study.
        Returns a list of steps with tactic, technique, and description.
        """
        self._ensure_loaded()
        cs = self.case_studies.get(cs_id)
        if not cs:
            return None
        procedure = cs.get("procedure", [])
        chain = []
        for step in procedure:
            tactic = self.tactics.get(step.get("tactic", ""), {})
            technique = self.techniques.get(step.get("technique", ""), {})
            chain.append({
                "tactic_id": step.get("tactic", ""),
                "tactic_name": tactic.get("name", "Unknown"),
                "technique_id": step.get("technique", ""),
                "technique_name": technique.get("name", "Unknown"),
                "description": step.get("description", ""),
            })
        return chain

    def get_subtechniques(self, parent_id: str) -> List[Dict]:
        """Get all sub-techniques of a parent technique."""
        self._ensure_loaded()
        prefix = parent_id + "."
        return [t for tid, t in self.techniques.items() if tid.startswith(prefix)]

    # ── Statistics ──

    def get_stats(self) -> Dict[str, int]:
        """Return counts of all ATLAS object types."""
        self._ensure_loaded()
        parent_techs = sum(1 for t in self.techniques if "." not in t.split("T")[-1])
        sub_techs = len(self.techniques) - parent_techs
        return {
            "version": self.version,
            "tactics": len(self.tactics),
            "techniques_total": len(self.techniques),
            "techniques_parent": parent_techs,
            "techniques_sub": sub_techs,
            "mitigations": len(self.mitigations),
            "case_studies": len(self.case_studies),
        }

    # ── Export ──

    def to_dict(self) -> Dict[str, Any]:
        """Export the full database as a dictionary."""
        self._ensure_loaded()
        return {
            "version": self.version,
            "tactics": list(self.tactics.values()),
            "techniques": list(self.techniques.values()),
            "mitigations": list(self.mitigations.values()),
            "case_studies": list(self.case_studies.values()),
        }
