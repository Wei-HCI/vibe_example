from __future__ import annotations

import argparse
import json

from rcode.super_analyze import build_method_recommendations, build_scan_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Super Analyze helper CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Detect questionnaire and design.")
    scan_parser.add_argument("path", help="Path to a CSV or Excel file.")

    recommend_parser = subparsers.add_parser(
        "recommend",
        help="Run assumption checks and suggest analysis methods.",
    )
    recommend_parser.add_argument("path", help="Path to a CSV or Excel file.")
    recommend_parser.add_argument("--questionnaire", help="Override detected questionnaire type.")
    recommend_parser.add_argument("--subject-col", help="Override subject ID column.")
    recommend_parser.add_argument("--condition-col", help="Override condition column.")
    recommend_parser.add_argument(
        "--dvs",
        nargs="*",
        help="Override dependent variable columns.",
    )

    args = parser.parse_args()

    if args.command == "scan":
        payload = build_scan_report(args.path)
    else:
        payload = build_method_recommendations(
            args.path,
            questionnaire=args.questionnaire,
            subject_col=args.subject_col,
            condition_col=args.condition_col,
            dvs=args.dvs,
        )

    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
