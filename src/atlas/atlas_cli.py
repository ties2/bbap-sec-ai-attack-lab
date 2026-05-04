"""
BBAP-Sec AI Attack Lab — ATLAS CLI
====================================
Command-line interface for querying MITRE ATLAS data
and viewing attack module mappings.

Usage:
    python -m src.atlas.atlas_cli stats
    python -m src.atlas.atlas_cli lookup AML.T0043
    python -m src.atlas.atlas_cli search "adversarial evasion"
    python -m src.atlas.atlas_cli mapping adversarial
    python -m src.atlas.atlas_cli mapping all
    python -m src.atlas.atlas_cli chain AML.CS0000
    python -m src.atlas.atlas_cli mitigations AML.T0043
    python -m src.atlas.atlas_cli tactics
    python -m src.atlas.atlas_cli coverage
    python -m src.atlas.atlas_cli report --output results/atlas_report.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.utils.logger import setup_logger, get_logger, get_project_root
from src.atlas.atlas_data import ATLASDatabase
from src.atlas.atlas_mapper import ATLASMapper, ATTACK_MODULE_MAPPINGS

logger = get_logger("atlas_cli")


def cmd_stats(db: ATLASDatabase, args):
    """Show ATLAS database statistics."""
    stats = db.get_stats()
    logger.info("ATLAS Database Statistics")
    for k, v in stats.items():
        logger.info(f"  {k}: {v}")


def cmd_tactics(db: ATLASDatabase, args):
    """List all ATLAS tactics."""
    logger.info(f"ATLAS Tactics ({len(db.tactics)})")
    for tid, t in sorted(db.tactics.items()):
        logger.info(f"  {tid:<16} {t['name']}")


def cmd_lookup(db: ATLASDatabase, args):
    """Lookup an ATLAS object by ID."""
    obj_id = args.id
    logger.info(f"Looking up: {obj_id}")

    # Try each collection
    if obj_id.startswith("AML.TA"):
        obj = db.get_tactic(obj_id)
        obj_type = "Tactic"
    elif obj_id.startswith("AML.T"):
        obj = db.get_technique(obj_id)
        obj_type = "Technique"
    elif obj_id.startswith("AML.M"):
        obj = db.get_mitigation(obj_id)
        obj_type = "Mitigation"
    elif obj_id.startswith("AML.CS"):
        obj = db.get_case_study(obj_id)
        obj_type = "Case Study"
    else:
        logger.error(f"Unknown ID format: {obj_id}")
        return

    if not obj:
        logger.error(f"Not found: {obj_id}")
        return

    logger.info(f"  Type: {obj_type}")
    logger.info(f"  ID: {obj['id']}")
    logger.info(f"  Name: {obj['name']}")
    if "description" in obj:
        desc = obj["description"]
        if len(desc) > 300:
            desc = desc[:300] + "..."
        logger.info(f"  Description: {desc}")
    if "tactics" in obj:
        tactic_names = [db.get_tactic(tid).get("name", tid) if db.get_tactic(tid) else tid for tid in obj["tactics"]]
        logger.info(f"  Tactics: {', '.join(tactic_names)}")
    if "maturity" in obj:
        logger.info(f"  Maturity: {obj['maturity']}")
    if obj_type == "Technique":
        subs = db.get_subtechniques(obj_id)
        if subs:
            logger.info(f"  Sub-techniques ({len(subs)}):")
            for s in subs:
                logger.info(f"    {s['id']}: {s['name']}")
        mits = db.get_mitigations_for_technique(obj_id)
        if mits:
            logger.info(f"  Mitigations ({len(mits)}):")
            for m in mits:
                logger.info(f"    {m['id']}: {m['name']}")
    logger.info(f"  URL: https://atlas.mitre.org/techniques/{obj_id}")


def cmd_search(db: ATLASDatabase, args):
    """Search techniques by keyword."""
    results = db.search_techniques(args.query, max_results=args.max_results)
    logger.info(f"Search results for '{args.query}' ({len(results)} found)")
    for t in results:
        tactics = ", ".join(t.get("tactics", []))
        logger.info(f"  {t['id']:<16} {t['name']}")
        if tactics:
            logger.info(f"  {'':16} Tactics: [{tactics}]")


def cmd_mapping(db: ATLASDatabase, args):
    """Show ATLAS mapping for a BBAP-Sec module."""
    mapper = ATLASMapper(db)
    if args.module == "all":
        for name in ATTACK_MODULE_MAPPINGS:
            mapper.print_mapping(name)
    else:
        mapper.print_mapping(args.module)


def cmd_chain(db: ATLASDatabase, args):
    """Show the attack procedure chain of a case study."""
    cs = db.get_case_study(args.id)
    if not cs:
        logger.error(f"Case study not found: {args.id}")
        return

    logger.info(f"Case Study: {cs['name']}")
    logger.info(f"  ID: {cs['id']}")
    logger.info(f"  Date: {cs.get('incident-date', 'Unknown')}")
    logger.info(f"  Summary: {cs.get('summary', '')[:200]}")

    chain = db.get_case_study_chain(args.id)
    if chain:
        logger.info(f"\n  Attack Chain ({len(chain)} steps):")
        for i, step in enumerate(chain, 1):
            logger.info(f"  [{i}/{len(chain)}] {step['tactic_name']} → {step['technique_name']}")
            logger.info(f"         {step['technique_id']}: {step['description'][:120]}...")


def cmd_mitigations(db: ATLASDatabase, args):
    """Show mitigations for a technique."""
    mits = db.get_mitigations_for_technique(args.id)
    tech = db.get_technique(args.id)
    name = tech.get("name", args.id) if tech else args.id

    logger.info(f"Mitigations for {args.id} ({name}): {len(mits)} found")
    for m in mits:
        logger.info(f"  {m['id']:<16} {m['name']}")
        if m.get("_use"):
            logger.info(f"  {'':16} Usage: {m['_use'][:150]}")


def cmd_coverage(db: ATLASDatabase, args):
    """Show BBAP-Sec's coverage of ATLAS tactics."""
    mapper = ATLASMapper(db)
    coverage = mapper.get_coverage_matrix()
    logger.info("BBAP-Sec ATLAS Tactic Coverage")
    logger.info(f"  {'Tactic':<35} {'Covered By'}")
    logger.info(f"  {'─'*35} {'─'*35}")

    all_tactic_names = [t.get("name", "") for t in db.tactics.values()]
    for tactic_name in sorted(all_tactic_names):
        modules = coverage.get(tactic_name, [])
        marker = ", ".join(modules) if modules else "(not covered)"
        logger.info(f"  {tactic_name:<35} {marker}")

    covered = sum(1 for t in all_tactic_names if t in coverage)
    logger.info(f"\n  Coverage: {covered}/{len(all_tactic_names)} tactics ({100*covered/len(all_tactic_names):.0f}%)")


def cmd_report(db: ATLASDatabase, args):
    """Generate a full ATLAS coverage report as JSON."""
    mapper = ATLASMapper(db)
    report = mapper.get_full_report()
    output = args.output or "results/atlas_report.json"
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(report, f, indent=2, default=str)
    logger.info(f"ATLAS report saved → {output}")
    logger.info(f"  Techniques covered: {report['unique_techniques_covered']}")
    logger.info(f"  Modules mapped: {report['bbap_modules']}")


def main():
    parser = argparse.ArgumentParser(
        description="BBAP-Sec — MITRE ATLAS CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.atlas.atlas_cli stats
  python -m src.atlas.atlas_cli lookup AML.T0043
  python -m src.atlas.atlas_cli search "adversarial evasion"
  python -m src.atlas.atlas_cli mapping adversarial
  python -m src.atlas.atlas_cli chain AML.CS0000
  python -m src.atlas.atlas_cli coverage
  python -m src.atlas.atlas_cli report --output results/atlas_report.json
        """,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("stats", help="Show ATLAS database statistics")
    sub.add_parser("tactics", help="List all ATLAS tactics")

    p_lookup = sub.add_parser("lookup", help="Lookup an ATLAS object by ID")
    p_lookup.add_argument("id", help="ATLAS ID (e.g., AML.T0043, AML.CS0000, AML.M0004)")

    p_search = sub.add_parser("search", help="Search techniques by keyword")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--max-results", type=int, default=10)

    p_mapping = sub.add_parser("mapping", help="Show ATLAS mapping for a BBAP-Sec module")
    p_mapping.add_argument("module", choices=list(ATTACK_MODULE_MAPPINGS.keys()) + ["all"])

    p_chain = sub.add_parser("chain", help="Show attack chain of a case study")
    p_chain.add_argument("id", help="Case study ID (e.g., AML.CS0000)")

    p_mit = sub.add_parser("mitigations", help="Show mitigations for a technique")
    p_mit.add_argument("id", help="Technique ID (e.g., AML.T0043)")

    sub.add_parser("coverage", help="Show BBAP-Sec coverage of ATLAS tactics")

    p_report = sub.add_parser("report", help="Generate full ATLAS coverage report")
    p_report.add_argument("--output", type=str, default=None)

    args = parser.parse_args()
    setup_logger(get_project_root())

    logger.info("=" * 60)
    logger.info("BBAP-Sec — MITRE ATLAS CLI")
    logger.info("=" * 60)

    db = ATLASDatabase()
    db.load()

    commands = {
        "stats": cmd_stats, "tactics": cmd_tactics, "lookup": cmd_lookup,
        "search": cmd_search, "mapping": cmd_mapping, "chain": cmd_chain,
        "mitigations": cmd_mitigations, "coverage": cmd_coverage, "report": cmd_report,
    }
    commands[args.command](db, args)

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
