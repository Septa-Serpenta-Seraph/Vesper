#!/usr/bin/env python3
"""
evtx-dump.py — Filter a Windows .evtx System log for GPU/driver/power/hardware
events from Linux. Created 8/16/26 while diagnosing recurring GPU Code 43.

Setup (uv doesn't ship pip into venvs by default — use `uv pip install`):
    uv venv /tmp/evtxenv
    uv pip install --python /tmp/evtxenv/bin/python python-evtx

Usage:
    /tmp/evtxenv/bin/python evtx-dump.py /path/to/Events.evtx > out.txt

PITFALL: In EVTX XML, Provider Name and TimeCreated SystemTime are ATTRIBUTES,
not element text — a naive `.text` read silently returns nothing. The parser
below reads attributes first (see _t()).

Then inspect the output: grep for nvlddmkm, " Display ", Kernel-Power, WHEA,
EventLog (6008), and correlate timestamps with the failure windows.
"""
import sys
import xml.etree.ElementTree as ET
from Evtx.Evtx import Evtx

NS = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}

# Providers of interest — GPU/driver/power/hardware
INTEREST = ("nvlddmkm", "Display", "Kernel-Power", "WHEA", "NvContainer",
            "EventLog", "Kernel-Boot", "BugCheck", "LiveKernelEvent",
            "Microsoft-Windows-DriverFrameworks-UserMode", "volmgr")

out = []
count = 0
try:
    with Evtx(sys.argv[1]) as log:
        for record in log.records():
            count += 1
            try:
                root = ET.fromstring(record.xml())
            except Exception:
                continue
            sys_el = root.find("e:System", NS)
            if sys_el is None:
                continue

            def _t(tag):
                el = sys_el.find(f"e:{tag}", NS)
                if el is None:
                    return ""
                if el.attrib:  # Provider Name / TimeCreated SystemTime live here
                    return " ".join(el.attrib.values())
                return el.text or ""

            provider = _t("Provider")
            if not any(p.lower() in provider.lower() for p in INTEREST):
                continue
            eid = _t("EventID")
            ts = _t("TimeCreated")
            level = _t("Level")
            data_el = root.find("e:EventData", NS)
            data_parts = []
            if data_el is not None:
                for d in data_el:
                    name = d.get("Name", "")
                    txt = (d.text or "").strip()
                    if txt:
                        data_parts.append(f"{name}={txt}" if name else txt)
            evdata = " | ".join(data_parts)[:400]
            out.append(f"[{ts}] L{level} {provider} (ID {eid}): {evdata}")
except Exception as e:
    out.append(f"PARSE ERROR: {e}")

print(f"# scanned {count} records")
print("\n".join(out))
