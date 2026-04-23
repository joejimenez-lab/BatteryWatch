# BatteryWatch

BatteryWatch is a macOS tool for comparing battery behavior in Normal Mode versus Low Power Mode.

It records short sessions, stores structured JSON samples, and compares two recordings to answer:

- How fast the battery drained in each mode
- Which processes changed the most
- Whether the improvement looks app-specific or system-wide

## Features

- Record a `normal` or `lowpower` session
- Capture battery state and top processes every few seconds
- Save session files as JSON
- Compare two session files and print a readable summary

## Requirements

- macOS (Apple Silicon or Intel MacBook)
- Python 3.10+
- Access to `pmset` and `top` (built in)

## Usage

Record a normal-mode session:

```bash
python main.py record normal
```

Record a low-power session:

```bash
python main.py record lowpower
```

Compare two sessions:

```bash
python main.py compare sessions/normal_001.json sessions/lowpower_001.json
```

Optional recording flags:

```bash
python main.py record normal --duration 300 --interval 10 --top-n 10
```

Live terminal monitor:

```bash
python main.py monitor --interval 5
```

Include CPU/GPU temperature and package power (requires passwordless `sudo` for `powermetrics`):

```bash
python main.py record normal --with-power
python main.py monitor --with-power
```

To enable, add an entry like this to `/etc/sudoers.d/batterywatch` via `sudo visudo -f /etc/sudoers.d/batterywatch`:

```text
yourusername ALL=(root) NOPASSWD: /usr/bin/powermetrics
```

## Project Layout

```text
BatteryWatch/
├── main.py
├── collector.py
├── parser.py
├── analyzer.py
├── reporter.py
├── utils.py
└── sessions/
```

## Roadmap

- Phase 1 (current): CLI recording + comparison
- Phase 2: richer metrics (powermetrics, temperature, background task breakdown)
- Phase 3: native UI dashboard with live monitor + compare views
