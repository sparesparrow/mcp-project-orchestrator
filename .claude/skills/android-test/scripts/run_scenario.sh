#!/usr/bin/env bash
# Run a named UI scenario from a project profile on the phone.
#
#   run_scenario.sh --profile profiles/mia.env --scenario nav-all [--serial S] [--out DIR]
#   run_scenario.sh --profile profiles/mia.env --list
#
# A profile (profiles/*.env) sets PKG, MAIN_ACTIVITY, TABS="Label1 Label2 ..." and may define
# scenario_<name>() functions using ui_* helpers from ui_lib.sh. Built-in scenarios:
#   launch  start the app, grant permissions, check it stays alive 5 s
#   nav-all open each bottom-nav label in $TABS, screenshot each, check the app is alive
# Scenario functions must `return 1` explicitly on any failed step. Exit 0 only if the scenario passed and logcat shows no FATAL EXCEPTION for the run.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
profile="" scenario="" SERIAL="" OUT="" list=0
while [ $# -gt 0 ]; do
  case "$1" in
    --profile) profile=$2; shift 2;; --scenario) scenario=$2; shift 2;; --serial) SERIAL=$2; shift 2;;
    --out) OUT=$2; shift 2;; --list) list=1; shift;; -h|--help) sed -n '2,11p' "$0"; exit 0;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done
[ -f "$profile" ] || { echo "need --profile FILE" >&2; exit 2; }
profile=$(realpath "$profile")
# shellcheck disable=SC1090
. "$profile"
# shellcheck source=ui_lib.sh
. "$here/ui_lib.sh"

scenario_launch() { ui_launch || return 1; sleep 5; ui_app_alive; }
scenario_nav-all() {
  # explicit `|| return 1`: set -e is ignored inside a function called from `||`
  ui_launch || return 1
  local t
  for t in ${TABS:?profile must set TABS}; do
    ui_open_tab "$t" || return 1
    ui_shot "tab-$t" || true
    ui_app_alive || { _err "app died on tab $t"; return 1; }
  done
}

if [ "$list" = 1 ]; then declare -F | awk '{print $3}' | sed -n 's/^scenario_//p'; exit 0; fi
[ -n "$scenario" ] || { echo "need --scenario (or --list)" >&2; exit 2; }
declare -F "scenario_$scenario" >/dev/null || { echo "no scenario '$scenario' in $profile" >&2; exit 2; }

if [ -z "$SERIAL" ]; then
  mapfile -t devs < <(adb devices | awk 'NR>1 && $2=="device"{print $1}')
  [ "${#devs[@]}" -eq 1 ] || { echo "need exactly one adb device; pass --serial" >&2; exit 1; }
  SERIAL=${devs[0]}
fi
OUT=${OUT:-scenario-$scenario-$(date +%Y%m%d-%H%M%S)}; mkdir -p "$OUT"; OUT=$(realpath "$OUT")
export SERIAL PKG OUT MAIN_ACTIVITY
ui_require
_a shell pm path "$PKG" >/dev/null 2>&1 || { _err "$PKG is not installed on $SERIAL"; exit 1; }
ui_grant_permissions
_a logcat -c
rc=0; "scenario_$scenario" || rc=$?
crashes=$(ui_diagnostics)
ui_cleanup
if [ "$rc" = 0 ] && [ "${crashes:-0}" = 0 ]; then echo "verdict: PASS ($scenario) evidence: $OUT"; exit 0; fi
echo "verdict: FAIL ($scenario) scenario rc=$rc, FATAL EXCEPTION count=$crashes, evidence: $OUT"; exit 1
