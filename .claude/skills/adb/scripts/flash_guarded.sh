#!/usr/bin/env bash
# Guarded fastboot flash. Prints the command; only runs it with --yes-i-confirmed.
# Usage: flash_guarded.sh <partition> <image> --serial S --product CODENAME [--yes-i-confirmed]
#   --serial and --product are mandatory with --yes-i-confirmed (optional for a dry run).
# Checks: partition allowlist, image size > 1 MB, image header magic (ANDROID! / VNDRBOOT / AVB0),
# and, against the device in fastboot (read-only getvar): exactly this serial, product == CODENAME,
# unlocked == yes, explicit slot suffix == current-slot (catches stale slots after an OTA),
# image fits partition-size.
set -euo pipefail
usage="usage: $0 <partition> <image> --serial S --product CODENAME [--yes-i-confirmed]"
[ $# -ge 2 ] || { echo "$usage" >&2; exit 2; }
part=$1; img=$2; shift 2
serial=""; product=""; confirmed=0
while [ $# -gt 0 ]; do
  case "$1" in
    --serial) [ $# -ge 2 ] || { echo "$usage" >&2; exit 2; }; serial=$2; shift 2;;
    --product) [ $# -ge 2 ] || { echo "$usage" >&2; exit 2; }; product=$2; shift 2;;
    --yes-i-confirmed) confirmed=1; shift;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done
base=${part%_[ab]}
suffix=""; [ "$base" != "$part" ] && suffix=${part#"$base"}
# Allowlist: only boot-chain images needed for Magisk rooting / rollback.
case "$base" in
  boot|init_boot|recovery) magic='ANDROID!';;
  vendor_boot) magic='VNDRBOOT';;
  vbmeta|vbmeta_system|vbmeta_vendor) magic='AVB0';;
  *) echo "REFUSED: '$part' is not in the allowlist (boot, init_boot, vendor_boot, recovery, vbmeta*)." >&2
     echo "Protected examples: bootloader, preloader, lk, tee, modem, radio, persist, nvdata, nvram, efs, gpt." >&2
     exit 3;;
esac
[ -f "$img" ] || { echo "image not found: $img" >&2; exit 4; }
size=$(stat -c %s "$img")
case "$base" in vbmeta*) min=1024;; *) min=1048576;; esac
[ "$size" -gt "$min" ] || { echo "REFUSED: image suspiciously small ($size bytes)" >&2; exit 4; }
head_magic=$(head -c ${#magic} "$img" | tr -d '\0')
[ "$head_magic" = "$magic" ] || { echo "REFUSED: image header is not '$magic' (wrong/sparse/compressed image for $base?)" >&2; exit 4; }

if [ "$confirmed" -eq 1 ]; then
  [ -n "$serial" ] || { echo "REFUSED: --serial is required with --yes-i-confirmed" >&2; exit 5; }
  [ -n "$product" ] || { echo "REFUSED: --product <codename> is required with --yes-i-confirmed" >&2; exit 5; }
fi

gv() { fastboot -s "$serial" getvar "$1" 2>&1 | sed -n "s/^\(([a-z]*) \)\{0,1\}$1: *//p" | head -1 | tr -d '\r'; }
devs=$(fastboot devices 2>/dev/null | awk 'NF{print $1}' || true)
ndev=$(printf '%s\n' "$devs" | grep -c . || true)
checked=0
if [ -n "$serial" ] && printf '%s\n' "$devs" | grep -qxF -- "$serial"; then
  checked=1
  dprod=$(gv product); dslot=$(gv current-slot); dunl=$(gv unlocked)
  # the bootloader prints "unlocked: not found" on some Motorola units; fastbootd says yes. Fall back to securestate.
  case "$dunl" in yes|no) ;; *) case "$(gv securestate)" in *flashing_unlocked*|*unlocked*) dunl=yes;; *) dunl=${dunl:-unknown};; esac;; esac
  echo "device:    serial=$serial product=$dprod current-slot=$dslot unlocked=$dunl"
  [ -z "$product" ] || [ "$dprod" = "$product" ] || { echo "REFUSED: fastboot product '$dprod' != expected '$product'" >&2; exit 6; }
  [ "$dunl" = "yes" ] || { echo "REFUSED: bootloader not unlocked (unlocked=$dunl)" >&2; exit 6; }
  if [ -n "$dslot" ]; then
    [ -n "$suffix" ] || { echo "REFUSED: A/B device: use an explicit slot suffix (current-slot is '$dslot', e.g. ${base}_$dslot)" >&2; exit 6; }
    [ "$suffix" = "_${dslot#_}" ] || { echo "REFUSED: requested $part but current-slot is '$dslot' (stale slot after an OTA/slot switch? re-triage)" >&2; exit 6; }
  fi
  psz=$(gv "partition-size:$part")
  if [[ "$psz" =~ ^(0x[0-9a-fA-F]+|[0-9]+)$ ]] && [ $((psz)) -gt 0 ]; then
    [ "$size" -le $((psz)) ] || { echo "REFUSED: image ($size) larger than partition $part ($((psz)))" >&2; exit 6; }
  fi
elif [ "$confirmed" -eq 1 ]; then
  echo "REFUSED: serial '$serial' is not in 'fastboot devices' (found $ndev: ${devs//$'\n'/ })" >&2; exit 5
else
  echo "device:    not checked (dry run; pass --serial/--product with the phone in fastboot to check)"
fi

cmd=(fastboot)
[ -n "$serial" ] && cmd+=(-s "$serial")
cmd+=(flash "$part" "$img")
echo "partition: $part"; echo "image:     $img ($size bytes, header $magic ok)"; sha256sum "$img"
printf 'command:   '; printf '%q ' "${cmd[@]}"; echo
if [ "$confirmed" -ne 1 ]; then
  echo "DRY RUN: add --yes-i-confirmed only after the user approved this exact command."
  exit 0
fi
[ "$checked" -eq 1 ] || { echo "REFUSED: device checks did not run" >&2; exit 5; }
exec "${cmd[@]}"
