#!/usr/bin/env bash
# Host-side only: wait for a phone to appear in adb, install a Magisk APK, launch it, then retry `su -c id`
# until uid=0 (or give up). Leaves nothing extra on the phone. The user still enables USB debugging and
# taps Allow; the Magisk app may show "Requires additional setup": tap OK (see recipes.md, screenshot + tap).
# Usage: watch_and_verify.sh SERIAL MAGISK.apk [LOGFILE]   (runs up to 12 h; run it in the background)
set -u
S=${1:?serial}; APK=${2:?apk}; L=${3:-verify.log}
log(){ echo "$(date +%T) $*" >> "$L"; }
end=$((SECONDS+43200)); log "watching for adb device $S"
while [ $SECONDS -lt $end ]; do
  if [ "$(adb -s "$S" get-state 2>/dev/null)" = device ]; then
    log "adb up; installing Magisk"; adb -s "$S" install -r "$APK" >> "$L" 2>&1
    adb -s "$S" shell monkey -p com.topjohnwu.magisk -c android.intent.category.LAUNCHER 1 >> "$L" 2>&1
    for i in $(seq 1 60); do
      out=$(timeout 40 adb -s "$S" shell su -c id 2>&1); log "su attempt $i: $out"
      case "$out" in *uid=0*) log "ROOT VERIFIED"; exit 0;; esac
      sleep 15
    done
    log "su not granted after 60 attempts"; exit 1
  fi
  sleep 20
done
log "gave up after 12 h"
