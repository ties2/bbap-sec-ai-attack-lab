"""
BBAP-Sec AI Attack Lab — MITRE ATLAS Client
=============================================
Loads and queries the MITRE ATLAS knowledge base (ATLAS.yaml).
Provides lookup, search, and mapping functions for tactics, techniques,
mitigations, and case studies.

Inspired by the ATT-CKGenius integration pattern:
  https://github.com/ties2/ATT-CKGenius

Data source: https://github.com/mitre-atlas/atlas-data
"""

import os
import yaml
from pathlib import Path
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger("atlas")

# ── Path to bundled ATLAS data ──
_ATLAS_YAML = os.path.join(os.path.dirname(__file__), "ATLAS.yaml")


class ATLASClient:
    """
    Client for querying MITRE ATLAS adversarial ML knowledge base.

    Usage:
        atlas = ATLASClient()
        atlas.load()

        # Lookup by ID
        tech = atlas.get_technique("AML.T0043")
        tactic = atlas.get_tactic("AML.TA0001")

        # Search by keyword
        results = atlas.search_techniques("poisoning")

        # Get mitigations for a technique
        mits = atlas.get_mitigations_for_technique("AML.T0020")

        # Get case studies for a technique
        cases = atlas.get_case_studies_for_technique("AML.T0015")
    """

    def __init__(self, yaml_path: str = None):
        self._yaml_path = yaml_path or _ATLAS_YAML
        self._data = None
        self._matrix = None
        self._tactics = {}
        self._techniques = {}
        self._mitigations = {}
        self._case_studies = {}
        self._loaded = False

    def load(self):
        """Load and index the ATLAS YAML data."""
        if self._loaded:
            return self

        logger.info(f"Loading ATLAS data from {self._yaml_path}")
        with open(self._yaml_path, "r") as f:
            self._data = yaml.safe_load(f)

        self._matrix = self._data["matrices"][0]

        # Index by ID for O(1) lookup
        for t in self._matrix.get("tactics", []):
            self._tactics[t["id"]] = t

        for t in self._matrix.get("techniques", []):
            self._techniques[t["id"]] = t

        for m in self._matrix.get("mitigations", []):
            self._mitigations[m["id"]] = m

        for cs in self._data.get("case-studies", []):
            self._case_studies[cs["id"]] = cs

        self._loaded = True
        logger.info(
            f"ATLAS v{self._data.get('version', '?')} loaded: "
            f"{len(self._tactics)} tactics, {len(self._techniques)} techniques, "
            f"{len(self._mitigations)} mitigations, {len(self._case_studies)} case studies"
        )
        return self

    def _ensure_loaded(self):
        if not self._loaded:
            self.load()

    # ── Lookups ──

    @property
    def version(self) -> str:
        self._ensure_loaded()
        return self._data.get("version", "unknown")

    def get_tactic(self, tactic_id: str) -> Optional[dict]:
        """Get a tactic by ID (e.g., 'AML.TA0001')."""
        self._ensure_loaded()
        return self._tactics.get(tactic_id)

    def get_technique(self, technique_id: str) -> Optional[dict]:
        """Get a technique by ID (e.g., 'AML.T0043')."""
        self._ensure_loaded()
        return self._techniques.get(technique_id)

    def get_mitigation(self, mitigation_id: str) -> Optional[dict]:
        """Get a mitigation by ID (e.g., 'AML.M0000')."""
        self._ensure_loaded()
        return self._mitigations.get(mitigation_id)

    def get_case_study(self, case_study_id: str) -> Optional[dict]:
        """Get a case study by ID (e.g., 'AML.CS0000')."""
        self._ensure_loaded()
        return self._case_studies.get(case_study_id)

    # ── Lists ──

    def list_tactics(self) -> list:
        """Return all tactics as list of dicts."""
        self._ensure_loaded()
        return list(self._tactics.values())

    def list_techniques(self, tactic_id: str = None) -> list:
        """Return techniques, optionally filtered by tactic ID."""
        self._ensure_loaded()
        techs = list(self._techniques.values())
        if tactic_id:
            techs = [t for t in techs if tactic_id in t.get("tactics", [])]
        return techs

    def list_subtechniques(self, parent_id: str) -> list:
        """Return sub-techniques for a parent technique (e.g., AML.T0043.xxx)."""
        self._ensure_loaded()
        return [t for t in self._techniques.values()
                if t["id"].startswith(parent_id + ".") and t["id"] != parent_id]

    def list_mitigations(self) -> list:
        self._ensure_loaded()
        return list(self._mitigations.values())

    def list_case_studies(self) -> list:
        self._ensure_loaded()
        return list(self._case_studies.values())

    # ── Search ──

    def search_techniques(self, keyword: str) -> list:
        """Search techniques by keyword in name or description."""
        self._ensure_loaded()
        kw = keyword.lower()
        return [t for t in self._techniques.values()
                if kw in t.get("name", "").lower() or kw in t.get("description", "").lower()]

    def search_case_studies(self, keyword: str) -> list:
        """Search case studies by keyword in name, summary, or target."""
        self._ensure_loaded()
        kw = keyword.lower()
        return [cs for cs in self._case_studies.values()
                if kw in cs.get("name", "").lower()
                or kw in cs.get("summary", "").lower()
                or kw in cs.get("target", "").lower()]

    def search_mitigations(self, keyword: str) -> list:
        """Search mitigations by keyword."""
        self._ensure_loaded()
        kw = keyword.lower()
        return [m for m in self._mitigations.values()
                if kw in m.get("name", "").lower() or kw in m.get("description", "").lower()]

    # ── Relationships ──

    def get_mitigations_for_technique(self, technique_id: str) -> list:
        """Get all mitigations that apply to a technique."""
        self._ensure_loaded()
        results = []
        for m in self._mitigations.values():
            for t in m.get("techniques", []):
                if t.get("id") == technique_id:
                    results.append({**m, "_use": t.get("use", "")})
                    break
        return results

    def get_case_studies_for_technique(self, technique_id: str) -> list:
        """Get case studies that reference a technique in their procedure."""
        self._ensure_loaded()
        results = []
        for cs in self._case_studies.values():
            for step in cs.get("procedure", []):
                if step.get("technique", "") == technique_id:
                    results.append(cs)
                    break
        return results

    def get_techniques_for_tactic(self, tactic_id: str) -> list:
        """Get all techniques under a tactic."""
        return self.list_techniques(tactic_id=tactic_id)

    def get_tactic_for_technique(self, technique_id: str) -> list:
        """Get the tactic(s) a technique belongs to."""
        self._ensure_loaded()
        tech = self._techniques.get(technique_id)
        if not tech:
            return []
        return [self._tactics[tid] for tid in tech.get("tactics", []) if tid in self._tactics]

    # ── ATT&CK Cross-Reference ──

    def get_attck_reference(self, atlas_id: str) -> Optional[dict]:
        """Get the ATT&CK cross-reference for an ATLAS tactic/technique."""
        self._ensure_loaded()
        item = self._tactics.get(atlas_id) or self._techniques.get(atlas_id)
        if item:
            return item.get("ATT&CK-reference")
        return None

    # ── Formatting ──

    def format_technique(self, technique_id: str) -> str:
        """Format a technique for display."""
        t = self.get_technique(technique_id)
        if not t:
            return f"[Unknown: {technique_id}]"
        tactics = ", ".join(self._tactics.get(tid, {}).get("name", tid) for tid in t.get("tactics", []))
        desc = t.get("description", "")[:200]
        attck = t.get("ATT&CK-reference", {})
        attck_str = f" (ATT&CK: {attck['id']})" if attck else ""
        return f"{t['id']} — {t['name']}{attck_str}\n  Tactic(s): {tactics}\n  {desc}..."

    def format_mitigation(self, mitigation_id: str) -> str:
        m = self.get_mitigation(mitigation_id)
        if not m:
            return f"[Unknown: {mitigation_id}]"
        return f"{m['id']} — {m['name']}\n  {m.get('description', '')[:200]}..."

    def format_case_study(self, case_study_id: str) -> str:
        cs = self.get_case_study(case_study_id)
        if not cs:
            return f"[Unknown: {case_study_id}]"
        return (f"{cs['id']} — {cs['name']}\n"
                f"  Target: {cs.get('target', 'N/A')}\n"
                f"  Date: {cs.get('incident-date', 'N/A')}\n"
                f"  {cs.get('summary', '')[:200]}...")

    # ── Stats ──

    def stats(self) -> dict:
        """Return summary statistics."""
        self._ensure_loaded()
        return {
            "version": self.version,
            "tactics": len(self._tactics),
            "techniques": len(self._techniques),
            "mitigations": len(self._mitigations),
            "case_studies": len(self._case_studies),
        }


# ── Singleton instance ──
_client = None

def get_atlas() -> ATLASClient:
    """Get the singleton ATLASClient instance (auto-loads on first call)."""
    global _client
    if _client is None:
        _client = ATLASClient()
        _client.load()
    return _client
