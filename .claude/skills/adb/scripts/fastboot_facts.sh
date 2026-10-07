#!/usr/bin/env bash
# Read-only: dump selected fastboot variables as JSON. Device must be in bootloader mode or fastbootd.
# Usage: fastboot_facts.sh [serial]
set -u
S=()
[ "${1:-}" ] && S=(-s "$1")
[ -n "$(timeout 10 fastboot devices 2>/dev/null)" ] || { echo '{"error": "no device in fastboot/fastbootd (fastboot devices is empty)"}'; exit 1; }
tmp=$(mktemp); trap 'rm -f "$tmp"' EXIT
timeout 60 fastboot "${S[@]}" getvar all > "$tmp" 2>&1 || true
python3 -I - "$tmp" <<'EOF2'
import json, sys, re
raw = open(sys.argv[1], errors="replace").read()
want = ("product", "variant", "current-slot", "slot-count", "unlocked", "secure", "is-userspace",
        "max-download-size", "version-bootloader", "version-baseband", "serialno",
        "snapshot-update-status", "ro.carrier", "securestate")
facts = {}
for line in raw.splitlines():
    line = re.sub(r"^\(bootloader\)\s*", "", line.strip())
    if ":" not in line or line.startswith("Finished") or line.startswith("all:"):
        continue
    k, _, v = line.partition(":")
    k, v = k.strip(), v.strip()
    if any(k == w or k.startswith(w + "[") for w in want):
        facts[k] = v
names = sorted({m.group(1) for m in re.finditer(r"partition-type:([\w\-]+):", raw)})
print(json.dumps({"vars": facts, "partitions": names,
                  "has_init_boot": any(n.startswith("init_boot") for n in names),
                  "has_vbmeta": any(n.startswith("vbmeta") for n in names),
                  "raw_lines": len(raw.splitlines())}, indent=2))
EOF2
