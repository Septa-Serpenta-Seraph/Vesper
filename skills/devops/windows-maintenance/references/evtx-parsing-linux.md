# Parsing Windows .evtx event logs on Linux

Tyler can export Event Viewer logs (System, Application, etc.) as `.evtx` files
and drop them in `cache/documents/`. They're a binary format — parse them on
the VM with `python-evtx`. Verified 2026-08-16 while diagnosing the recurring
GPU Code 43 (event log exonerated the card: no nvlddmkm, no WHEA).

## Setup (uv, no pip needed)

```bash
uv venv /tmp/evtxenv -q
uv pip install --python /tmp/evtxenv/bin/python -q python-evtx
```

## Core gotcha — attributes vs text in the XML

EVTX records are XML. **`Provider` Name and `TimeCreated` SystemTime are
ATTRIBUTES, not element text.** A naive extractor that reads `.text` returns
empty strings and you'll "scan 9000 records, find nothing interesting."
`EventID` and `Level` are element text (but `EventID` may carry a
`Qualifiers` attribute). Extract both:

```python
import xml.etree.ElementTree as ET
from Evtx.Evtx import Evtx

NS = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}

def _t(sys_el, tag):
    el = sys_el.find(f"e:{tag}", NS)
    if el is None:
        return ""
    if el.attrib:                      # Provider Name, TimeCreated SystemTime live here
        return " ".join(el.attrib.values())
    return el.text or ""               # EventID, Level are text
```

## Filtering recipe

Provider-filter on the System section; pull EventData values for context.
A working dump script: `/tmp/evtx_dump.py` pattern from the 8/16 session —
filter providers (nvlddmkm, Display, Kernel-Power, WHEA, Kernel-Boot,
EventLog), print `[TimeCreated] Level Provider (ID): data`, grep the result.
Records in an export are NOT always chronological — sort by timestamp.

## Event semantics worth knowing (System log)

| Event | Meaning |
|---|---|
| `nvlddmkm` (any) | NVIDIA driver crash/TDR — presence = driver-crash story |
| `WHEA` (any) | PCIe/hardware fault — presence = hardware story |
| `Display` 4125 | Screen-blip / display-link event — clusters around monitor sleep/resume |
| `Kernel-Power` 41 + `BugcheckCode=0` | Unexpected power loss, NO blue screen — hard power cut (often the user's own PSU drain) |
| `Kernel-Boot` `LastShutdownGood=False` | Previous shutdown was dirty (boot after a hard cut) |
| `EventLog` 32768 with a date-time string | Event 6008 — "previous shutdown at <time> was not clean" |

## Verify

- `wc -l` the filtered output; expect lines, not just the scan header.
- Cross-check point-in-time claims against `TZ=America/Denver date` — log
  timestamps are UTC; convert to Mountain Time before narrating the user's day.
