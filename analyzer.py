from __future__ import annotations

from collections import defaultdict
from typing import Any


def _hours_between(first_timestamp: str, last_timestamp: str) -> float:
    from datetime import datetime

    start = datetime.fromisoformat(first_timestamp)
    end = datetime.fromisoformat(last_timestamp)
    elapsed_seconds = max((end - start).total_seconds(), 0.0)
    return elapsed_seconds / 3600 if elapsed_seconds else 0.0


def session_summary(session: dict[str, Any]) -> dict[str, Any]:
    samples = session.get("samples", [])
    if len(samples) < 2:
        raise ValueError("session requires at least two samples to analyze")

    first = samples[0]
    last = samples[-1]
    first_battery = first.get("battery_percent")
    last_battery = last.get("battery_percent")

    if first_battery is None or last_battery is None:
        raise ValueError("session is missing battery percentage data")

    hours = _hours_between(first["timestamp"], last["timestamp"])
    drain_amount = float(first_battery) - float(last_battery)
    drain_per_hour = (drain_amount / hours) if hours > 0 else 0.0

    per_process: dict[str, list[float]] = defaultdict(list)
    total_cpu_samples: list[float] = []
    command_set: set[str] = set()

    power_fields = ("cpu_die_temp_c", "gpu_die_temp_c", "cpu_power_mw", "gpu_power_mw", "package_power_mw")
    power_values: dict[str, list[float]] = {field: [] for field in power_fields}

    for sample in samples:
        sample_total_cpu = 0.0
        for process in sample.get("processes", []):
            command = str(process.get("command", "unknown"))
            cpu = float(process.get("cpu", 0.0))
            per_process[command].append(cpu)
            command_set.add(command)
            sample_total_cpu += cpu
        total_cpu_samples.append(sample_total_cpu)

        power = sample.get("power") or {}
        for field in power_fields:
            value = power.get(field)
            if value is not None:
                power_values[field].append(float(value))

    power_averages: dict[str, float | None] = {
        field: (sum(values) / len(values) if values else None)
        for field, values in power_values.items()
    }

    average_cpu_by_process = {
        command: sum(values) / len(values) for command, values in per_process.items() if values
    }
    average_total_cpu = (
        sum(total_cpu_samples) / len(total_cpu_samples) if total_cpu_samples else 0.0
    )

    return {
        "session_type": session.get("session_type", "unknown"),
        "duration_hours": hours,
        "battery_start": first_battery,
        "battery_end": last_battery,
        "battery_drain": drain_amount,
        "battery_drain_per_hour": drain_per_hour,
        "average_total_cpu": average_total_cpu,
        "average_cpu_by_process": average_cpu_by_process,
        "process_set": command_set,
        "power_averages": power_averages,
        "sample_count": len(samples),
        "low_power_mode": last.get("low_power_mode"),
    }


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def compare_sessions(normal_session: dict[str, Any], lowpower_session: dict[str, Any]) -> dict[str, Any]:
    normal = session_summary(normal_session)
    lowpower = session_summary(lowpower_session)

    all_commands = set(normal["average_cpu_by_process"]) | set(lowpower["average_cpu_by_process"])
    process_changes = []
    for command in all_commands:
        normal_cpu = normal["average_cpu_by_process"].get(command, 0.0)
        lowpower_cpu = lowpower["average_cpu_by_process"].get(command, 0.0)
        process_changes.append(
            {
                "command": command,
                "normal_cpu": normal_cpu,
                "lowpower_cpu": lowpower_cpu,
                "delta_cpu": lowpower_cpu - normal_cpu,
                "abs_delta_cpu": abs(lowpower_cpu - normal_cpu),
            }
        )

    process_changes.sort(key=lambda item: item["abs_delta_cpu"], reverse=True)

    normal_drain = normal["battery_drain_per_hour"]
    lowpower_drain = lowpower["battery_drain_per_hour"]
    improvement_pct = (
        ((lowpower_drain - normal_drain) / normal_drain) * 100 if normal_drain else 0.0
    )

    workload_similarity = _jaccard(normal["process_set"], lowpower["process_set"])

    power_deltas: dict[str, float | None] = {}
    for field, normal_value in normal["power_averages"].items():
        lowpower_value = lowpower["power_averages"].get(field)
        if normal_value is None or lowpower_value is None:
            power_deltas[field] = None
        else:
            power_deltas[field] = lowpower_value - normal_value

    return {
        "normal": normal,
        "lowpower": lowpower,
        "drain_difference_per_hour": lowpower_drain - normal_drain,
        "drain_improvement_pct": improvement_pct,
        "process_changes": process_changes,
        "workload_similarity": workload_similarity,
        "power_deltas": power_deltas,
    }
