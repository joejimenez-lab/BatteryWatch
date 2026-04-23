from __future__ import annotations

from typing import Any


def format_comparison(comparison: dict[str, Any], top_n: int = 5) -> str:
    normal = comparison["normal"]
    lowpower = comparison["lowpower"]
    process_changes = comparison["process_changes"][:top_n]

    interpretation = _build_interpretation(comparison)

    lines = [
        "Session comparison",
        "",
        "Battery drain:",
        f"Normal mode: {normal['battery_drain_per_hour']:.1f}%/hr",
        f"Low power mode: {lowpower['battery_drain_per_hour']:.1f}%/hr",
        f"Difference: {comparison['drain_improvement_pct']:.1f}%",
        "",
        "Average CPU:",
        f"Normal mode: {normal['average_total_cpu']:.1f}%",
        f"Low power mode: {lowpower['average_total_cpu']:.1f}%",
        "",
        "Top CPU process changes:",
    ]

    if process_changes:
        for item in process_changes:
            lines.append(
                f"{item['command']}: {item['normal_cpu']:.1f}% -> {item['lowpower_cpu']:.1f}%"
            )
    else:
        lines.append("No process differences were found.")

    similarity = comparison.get("workload_similarity")
    if similarity is not None:
        pct = similarity * 100
        if similarity < 0.5:
            warn = " — workloads look quite different; comparison may be unfair"
        elif similarity < 0.75:
            warn = " — workloads partially overlap; treat with some caution"
        else:
            warn = " — workloads match well"
        lines.extend(["", f"Workload similarity: {pct:.0f}%{warn}"])

    power_lines = _format_power(comparison)
    if power_lines:
        lines.extend(["", "Power / thermal:"] + power_lines)

    lines.extend(["", "Interpretation:", interpretation])
    return "\n".join(lines)


def _format_power(comparison: dict[str, Any]) -> list[str]:
    normal_power = comparison["normal"].get("power_averages") or {}
    lowpower_power = comparison["lowpower"].get("power_averages") or {}
    labels = {
        "cpu_die_temp_c": ("CPU die temp", "C"),
        "gpu_die_temp_c": ("GPU die temp", "C"),
        "cpu_power_mw": ("CPU power", "mW"),
        "gpu_power_mw": ("GPU power", "mW"),
        "package_power_mw": ("Package power", "mW"),
    }
    out: list[str] = []
    for field, (label, unit) in labels.items():
        normal_value = normal_power.get(field)
        lowpower_value = lowpower_power.get(field)
        if normal_value is None and lowpower_value is None:
            continue
        normal_str = f"{normal_value:.1f}" if normal_value is not None else "—"
        lowpower_str = f"{lowpower_value:.1f}" if lowpower_value is not None else "—"
        out.append(f"{label}: {normal_str} -> {lowpower_str} {unit}")
    return out


def _build_interpretation(comparison: dict[str, Any]) -> str:
    normal = comparison["normal"]
    lowpower = comparison["lowpower"]
    biggest_changes = comparison["process_changes"][:3]

    if lowpower["battery_drain_per_hour"] < normal["battery_drain_per_hour"]:
        lead = "Low Power Mode reduced battery drain."
    elif lowpower["battery_drain_per_hour"] > normal["battery_drain_per_hour"]:
        lead = "Low Power Mode increased battery drain in this run."
    else:
        lead = "Battery drain was effectively unchanged between runs."

    changed_processes = [item for item in biggest_changes if item["abs_delta_cpu"] > 1.0]
    if len(changed_processes) >= 2:
        detail = "The change appears to be broad across multiple processes."
    elif len(changed_processes) == 1:
        detail = f"The biggest change came from {changed_processes[0]['command']}."
    else:
        detail = "The improvement looks more like overall system behavior than one standout app."

    return f"{lead} {detail}"
