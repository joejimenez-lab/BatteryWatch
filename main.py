from __future__ import annotations

import argparse
from pathlib import Path

from analyzer import compare_sessions
from collector import record_session
from monitor import run_monitor
from reporter import format_comparison
from utils import load_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batterywatch",
        description="BatteryWatch: compare macOS Normal Mode vs Low Power Mode.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    record_parser = subparsers.add_parser("record", help="Record a session")
    record_parser.add_argument("mode", choices=["normal", "lowpower"])
    record_parser.add_argument("--duration", type=int, default=300, help="Recording duration in seconds")
    record_parser.add_argument("--interval", type=int, default=10, help="Sampling interval in seconds")
    record_parser.add_argument("--top-n", type=int, default=10, help="Number of processes to keep")
    record_parser.add_argument(
        "--with-power",
        action="store_true",
        help="Also sample CPU/GPU temperature and package power via powermetrics (requires passwordless sudo)",
    )

    compare_parser = subparsers.add_parser("compare", help="Compare two session files")
    compare_parser.add_argument("normal_session", type=Path)
    compare_parser.add_argument("lowpower_session", type=Path)
    compare_parser.add_argument("--top-n", type=int, default=5, help="Number of process changes to print")

    monitor_parser = subparsers.add_parser("monitor", help="Live terminal monitor")
    monitor_parser.add_argument("--interval", type=int, default=5, help="Sampling interval in seconds")
    monitor_parser.add_argument("--top-n", type=int, default=8, help="Number of processes to display")
    monitor_parser.add_argument(
        "--with-power",
        action="store_true",
        help="Include CPU/GPU temperature and package power (requires passwordless sudo)",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "record":
        output_path = record_session(
            mode=args.mode,
            duration_seconds=args.duration,
            interval_seconds=args.interval,
            top_n=args.top_n,
            with_power=args.with_power,
        )
        print(f"Saved {args.mode} session to {output_path}")
        return

    if args.command == "monitor":
        run_monitor(
            interval_seconds=args.interval,
            top_n=args.top_n,
            with_power=args.with_power,
        )
        return

    if args.command == "compare":
        normal_session = load_json(args.normal_session)
        lowpower_session = load_json(args.lowpower_session)
        comparison = compare_sessions(normal_session, lowpower_session)
        print(format_comparison(comparison, top_n=args.top_n))
        return

    parser.error(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
