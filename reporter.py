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

    lines.extend(["", "Interpretation:", interpretation])
    return "\n".join(lines)


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
