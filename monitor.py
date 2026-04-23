from __future__ import annotations

import time
from datetime import datetime

from collector import collect_sample


CLEAR = "\x1b[2J\x1b[H"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RESET = "\x1b[0m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
RED = "\x1b[31m"
CYAN = "\x1b[36m"


def _drain_rate(history: list[dict]) -> float | None:
    """Percent per hour using the oldest-to-newest battery delta."""
    usable = [s for s in history if s.get("battery_percent") is not None]
    if len(usable) < 2:
        return None
    first, last = usable[0], usable[-1]
    delta_pct = float(first["battery_percent"]) - float(last["battery_percent"])
    start = datetime.fromisoformat(first["timestamp"])
    end = datetime.fromisoformat(last["timestamp"])
    hours = (end - start).total_seconds() / 3600
    if hours <= 0:
        return None
    return delta_pct / hours


def _color_for_drain(rate: float | None) -> str:
    if rate is None or rate <= 0:
        return GREEN
    if rate < 8:
        return GREEN
    if rate < 15:
        return YELLOW
    return RED


def _render(sample: dict, history: list[dict], interval: int) -> str:
    lines: list[str] = []
    lines.append(f"{CLEAR}{BOLD}BatteryWatch — live monitor{RESET}")
    lines.append(f"{DIM}sampling every {interval}s · ctrl-c to stop{RESET}")
    lines.append("")

    battery = sample.get("battery_percent")
    charging = sample.get("is_charging")
    lpm = sample.get("low_power_mode")
    state = "charging" if charging else ("on battery" if sample.get("is_discharging") else "idle")
    lpm_str = (
        f"{CYAN}ON{RESET}" if lpm else f"{DIM}off{RESET}" if lpm is False else f"{DIM}unknown{RESET}"
    )

    drain = _drain_rate(history)
    drain_color = _color_for_drain(drain)
    drain_str = f"{drain_color}{drain:+.1f}%/hr{RESET}" if drain is not None else f"{DIM}—{RESET}"

    lines.append(f"{BOLD}Battery:{RESET}       {battery}%   ({state})")
    lines.append(f"{BOLD}Low Power Mode:{RESET} {lpm_str}")
    lines.append(f"{BOLD}Drain rate:{RESET}    {drain_str}   {DIM}(since monitor start, n={len(history)}){RESET}")

    power = sample.get("power")
    if power:
        cpu_temp = power.get("cpu_die_temp_c")
        gpu_temp = power.get("gpu_die_temp_c")
        pkg_power = power.get("package_power_mw")
        cpu_power = power.get("cpu_power_mw")
        if any(v is not None for v in (cpu_temp, gpu_temp, pkg_power, cpu_power)):
            lines.append("")
            lines.append(f"{BOLD}Power / thermal:{RESET}")
            if cpu_temp is not None:
                lines.append(f"  CPU die temp:   {cpu_temp:.1f} C")
            if gpu_temp is not None:
                lines.append(f"  GPU die temp:   {gpu_temp:.1f} C")
            if cpu_power is not None:
                lines.append(f"  CPU power:      {cpu_power:.0f} mW")
            if pkg_power is not None:
                lines.append(f"  Package power:  {pkg_power:.0f} mW")

    lines.append("")
    lines.append(f"{BOLD}Top processes by CPU:{RESET}")
    procs = sample.get("processes", [])
    if not procs:
        lines.append(f"  {DIM}no process data{RESET}")
    else:
        for proc in procs:
            cpu = float(proc.get("cpu", 0.0))
            bar_width = min(int(cpu / 2), 30)
            bar = "█" * bar_width
            command = str(proc.get("command", "?"))[:20]
            lines.append(f"  {command:<20} {cpu:5.1f}%  {DIM}{bar}{RESET}")

    lines.append("")
    lines.append(f"{DIM}last updated: {sample.get('timestamp', '')}{RESET}")
    return "\n".join(lines)


def run_monitor(interval_seconds: int, top_n: int, with_power: bool) -> None:
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")
    if top_n <= 0:
        raise ValueError("top_n must be positive")

    history: list[dict] = []
    try:
        while True:
            sample = collect_sample(top_n=top_n, with_power=with_power)
            history.append(sample)
            # Keep history bounded so drain rate reflects recent behavior.
            if len(history) > 240:
                history = history[-240:]
            print(_render(sample, history, interval_seconds), flush=True)
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print(f"\n{DIM}monitor stopped.{RESET}")
