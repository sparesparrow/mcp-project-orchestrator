#!/usr/bin/env bash
# Shared adb UI helpers for the android-test skill. Source it, do not run it.
# Ported from mia's android-adb-test.sh (uiautomator text lookup), made package-agnostic.
#
# Required before use:  SERIAL=<adb serial>  PKG=<application id>
# Optional:             MAIN_ACTIVITY=.MainActivity  OUT=<dir for screenshots/logs>  DELAY_MS=800
# Needs: adb, python3. Taps by on-screen text/content-desc (uiautomator bounds), so no
# screenshot scale factor is involved.

: "${DELAY_MS:=800}" "${MAIN_ACTIVITY:=.MainActivity}" "${OUT:=.}"

_a() { adb -s "$SERIAL" "$@"; }
_err() { echo "ERROR: $*" >&2; }
_sleep_ms() { local ms=${1:-$DELAY_MS} s; printf -v s '%d.%03d' $((ms / 1000)) $((ms % 1000)); sleep "$s"; }

ui_require() {
  [ -n "${SERIAL:-}" ] && [ -n "${PKG:-}" ] || { _err "set SERIAL and PKG"; return 1; }
  command -v python3 >/dev/null || { _err "python3 needed to parse uiautomator XML"; return 1; }
}

ui_wake() {
  _a shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1 || true
  _a shell wm dismiss-keyguard >/dev/null 2>&1 || true   # no effect with a PIN: unlock by hand
}

# Grant every runtime ("dangerous") permission the package declares. Without this, apps that start
# foreground services with a camera/location type crash on Android 14+ (SecurityException).
ui_grant_permissions() {
  local p
  while read -r p; do
    [ -n "$p" ] && _a shell pm grant "$PKG" "$p" >/dev/null 2>&1 || true
  done < <(_a shell dumpsys package "$PKG" | tr -d '\r' \
            | sed -n '/requested permissions:/,/install permissions:/p' \
            | grep -oE '[A-Za-z0-9_.]+\.permission\.[A-Z_]+' | sort -u)
}

ui_launch() {
  ui_wake
  _a shell am start -W -n "$PKG/$MAIN_ACTIVITY" >/dev/null 2>&1 || { _err "could not start $PKG/$MAIN_ACTIVITY"; return 1; }
  _sleep_ms 1200
  _a shell cmd statusbar collapse >/dev/null 2>&1 || true
}

ui_dump() {
  _a shell uiautomator dump /sdcard/ui_dump.xml >/dev/null 2>&1 || return 1
  _a shell cat /sdcard/ui_dump.xml | tr -d '\r'
}

# ui_find TEXT [contains|exact] [first|bottom-most]  -> prints "x y" (real pixels) or exits 1
ui_find() {
  ui_dump | python3 -c '
import re, sys
import xml.etree.ElementTree as ET
needle, mode, place = sys.argv[1].strip().lower(), sys.argv[2], sys.argv[3]
xml = sys.stdin.read().strip()
if not xml: sys.exit(1)
c = []
for n in ET.fromstring(xml).iter("node"):
    hay = " ".join(p for p in ((n.get("text") or "").strip(), (n.get("content-desc") or "").strip()) if p).lower()
    if not hay or (hay != needle if mode == "exact" else needle not in hay): continue
    b = [int(v) for v in re.findall(r"\d+", n.get("bounds", ""))]
    if len(b) == 4: c.append(((b[1] + b[3]) // 2, (b[0] + b[2]) // 2))
if not c: sys.exit(1)
c.sort(); y, x = c[-1] if place == "bottom-most" else c[0]
print(x, y)' "$1" "${2:-contains}" "${3:-first}"
}

ui_has() { ui_find "$@" >/dev/null 2>&1; }

ui_tap_text() {
  local xy x y
  xy=$(ui_find "$@") || { _err "UI text not found: $1"; return 1; }
  read -r x y <<<"$xy"
  _a shell input tap "$x" "$y"
  _sleep_ms
}

# ui_wait TEXT [attempts=10] [mode] [placement]
ui_wait() {
  local needle=$1 n=${2:-10} i
  for ((i = 0; i < n; i++)); do
    ui_has "$needle" "${3:-contains}" "${4:-first}" && return 0
    _sleep_ms 500
  done
  return 1
}

# ui_open_tab LABEL [MARKER_TEXT]: tap a bottom-navigation label, optionally wait for a marker.
ui_open_tab() {
  ui_wait "$1" 12 exact bottom-most || { _err "tab '$1' not visible"; return 1; }
  ui_tap_text "$1" exact bottom-most || return 1
  [ -z "${2:-}" ] || ui_wait "$2" 12 || { _err "did not reach '$2' after tapping '$1'"; return 1; }
}

ui_shot() {   # ui_shot NAME -> $OUT/screenshots/NAME.png
  mkdir -p "$OUT/screenshots"
  _a exec-out screencap -p >"$OUT/screenshots/$1.png"
}

ui_app_alive() { [ -n "$(_a shell pidof "$PKG" | tr -d '\r')" ]; }

# Crash/ANR evidence for the package since the last `logcat -c`.
ui_diagnostics() {
  mkdir -p "$OUT/logs"
  _a logcat -d -v threadtime >"$OUT/logs/logcat.txt" 2>&1 || true
  _a logcat -d -b crash -v threadtime >"$OUT/logs/crash.txt" 2>&1 || true
  _a shell dumpsys activity processes 2>/dev/null | grep -i -A2 "$PKG" >"$OUT/logs/procs.txt" || true
  ui_shot failure || true
  local n
  n=$(grep -c "FATAL EXCEPTION" "$OUT/logs/crash.txt" 2>/dev/null || true)
  echo "${n:-0}"
}
