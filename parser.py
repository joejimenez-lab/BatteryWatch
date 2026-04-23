from __future__ import annotations

import re


BATTERY_LINE_RE = re.compile(r"(\d+)%")
PROCESS_LINE_RE = re.compile(
    r"^\s*(?P<pid>\d+)\s+(?P<command>.+?)\s+(?P<cpu>-?\d+(?:\.\d+)?)\s+(?P<mem>\S+)\s*$"
)


def parse_pmset_batt(output: str) -> dict[str, object]:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    battery_line = next((line for line in lines if "%" in line), "")
    percent_match = BATTERY_LINE_RE.search(battery_line)
    percent = int(percent_match.group(1)) if percent_match else None

    lower_line = battery_line.lower()
    is_charging = "charging" in lower_line
    is_discharging = "discharging" in lower_line or "battery power" in lower_line

    return {
        "battery_percent": percent,
        "is_charging": is_charging,
        "is_discharging": is_discharging,
        "raw_battery_line": battery_line,
    }


def parse_pmset_settings(output: str) -> dict[str, object]:
    low_power_mode = None
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("lowpowermode"):
            parts = stripped.split()
            if parts:
                try:
                    low_power_mode = bool(int(parts[-1]))
                except ValueError:
                    low_power_mode = None
            break

    return {"low_power_mode": low_power_mode}


def parse_top_output(output: str, top_n: int) -> list[dict[str, object]]:
    processes: list[dict[str, object]] = []

    # When `top -l 2` is used, only the second frame has valid CPU deltas.
    # Split on the column header and keep the last frame.
    frames = re.split(r"^\s*PID\s+COMMAND.*$", output, flags=re.MULTILINE)
    body = frames[-1] if frames else output

    for line in body.splitlines():
        match = PROCESS_LINE_RE.match(line)
        if not match:
            continue

        command = match.group("command").strip()
        if command.lower() == "command":
            continue

        processes.append(
            {
                "pid": int(match.group("pid")),
                "command": command,
                "cpu": float(match.group("cpu")),
                "mem": match.group("mem"),
            }
        )

        if len(processes) >= top_n:
            break

    return processes
