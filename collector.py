from __future__ import annotations

import subprocess
import time
from typing import Any

from parser import parse_pmset_batt, parse_pmset_settings, parse_top_output
from utils import next_session_path, save_json, utc_timestamp


def run_command(args: list[str]) -> str:
    completed = subprocess.run(args, capture_output=True, text=True, check=True)
    return completed.stdout


def collect_sample(top_n: int) -> dict[str, Any]:
    battery_output = run_command(["pmset", "-g", "batt"])
    settings_output = run_command(["pmset", "-g"])
    top_output = run_command(
        ["top", "-l", "2", "-o", "cpu", "-n", str(top_n), "-stats", "pid,command,cpu,mem"]
    )

    battery_data = parse_pmset_batt(battery_output)
    settings_data = parse_pmset_settings(settings_output)
    processes = parse_top_output(top_output, top_n=top_n)

    return {
        "timestamp": utc_timestamp(),
        **battery_data,
        **settings_data,
        "processes": processes,
    }


def record_session(mode: str, duration_seconds: int, interval_seconds: int, top_n: int) -> str:
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")
    if top_n <= 0:
        raise ValueError("top_n must be positive")

    samples: list[dict[str, Any]] = []
    started_at = utc_timestamp()
    deadline = time.monotonic() + duration_seconds

    while True:
        samples.append(collect_sample(top_n=top_n))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(interval_seconds, remaining))

    session = {
        "session_type": mode,
        "started_at": started_at,
        "ended_at": utc_timestamp(),
        "duration_seconds": duration_seconds,
        "interval_seconds": interval_seconds,
        "top_n": top_n,
        "sample_count": len(samples),
        "samples": samples,
    }

    output_path = next_session_path(mode)
    save_json(output_path, session)
    return str(output_path)
