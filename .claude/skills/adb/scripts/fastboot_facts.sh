#!/usr/bin/env bash
# Read-only: dump selected fastboot variables as JSON. Device must be in bootloader mode.
# Usage: fastboot_facts.sh [serial]
set -u
S=()
[ "${1:-}" ] && S=(-s "$1")
raw=$(fastboot "${S[@]}" getvar all 2>&1) || true
python3 -I - "$raw" <<'EOF'
import json, sys, re
raw = sys.argv[1]
want = ("product", "variant", "current-slot", "slot-count", "unlocked", "secure", "is-userspace",
        "max-download-size", "version-bootloader", "version-baseband", "serialno", "has-slot",
        "partition-type", "partition-size", "snapshot-update-status", "ro.carrier", "securestate")
facts, parts = {}, {}
for line in raw.splitlines():
    line = re.sub(r"^\(bootloader\)\s*", "", line.strip())
    if ":" not in line or line.startswith("Finished") or line.startswith("all:"):
        continue
    k, _, v = line.partition(":")
    k, v = k.strip(), v.strip()
    if k.startswith("partition-type") or k.startswith("partition-size"):
        parts.setdefault(k.split(":")[-1] if ":" in k else k, v)
        name = line.split(":")[1] if line.count(":") >= 2 else None
        if name:
            parts.setdefault(name, {})
        continue
    if any(k.startswith(w) or w in k for w in want):
        facts[k] = v
names = sorted({m.group(1) for m in re.finditer(r"partition-type:([\w\-]+):", raw)})
print(json.dumps({"vars": facts, "partitions": names,
                  "has_init_boot": any(n.startswith("init_boot") for n in names),
                  "has_vbmeta": any(n.startswith("vbmeta") for n in names),
                  "raw_lines": len(raw.splitlines())}, indent=2))
EOF
