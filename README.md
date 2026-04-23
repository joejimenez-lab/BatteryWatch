# PowerDiff

PowerDiff is a CLI tool for comparing macOS battery behavior in Normal Mode versus Low Power Mode.

The MVP records short sessions, stores structured JSON samples, and compares two recordings to answer:

- How fast the battery drained in each mode
- Which processes changed the most
- Whether the improvement looks app-specific or system-wide

## Features

- Record a `normal` or `lowpower` session
- Capture battery state and top processes every few seconds
- Save session files as JSON
- Compare two session files and print a readable summary

## Requirements

- macOS
- Python 3.10+
- Access to `pmset` and `top`

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

## Project Layout

```text
powerdiff/
├── main.py
├── collector.py
├── parser.py
├── analyzer.py
├── reporter.py
├── utils.py
└── sessions/
```

## Notes

- The collector is intentionally simple for the first milestone.
- Session files are ignored by Git except for `sessions/.gitkeep`.
- Future versions can add workload validation, graphs, and richer system metrics.
