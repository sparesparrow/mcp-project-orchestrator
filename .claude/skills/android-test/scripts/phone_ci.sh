#!/usr/bin/env bash
# Phone-as-test-device loop: fetch CI-built APKs from GitHub Actions, install them
# on a USB/wireless phone, run instrumented tests, collect evidence.
#
#   phone_ci.sh --repo OWNER/REPO --pkg APP_ID [--workflow device-apks.yml]
#               [--ref BRANCH] [--artifact device-apks] [--serial S]
#               [--runner androidx.test.runner.AndroidJUnitRunner]
#               [--out DIR] [--run-id N] [--release TAG|latest] [--timeout SEC] [--dispatch] [--dry-run]
#
# Needs: gh (authenticated), adb, unzip. Does not build anything locally.
# --pkg is the installed app id (for debug builds with applicationIdSuffix ".debug",
# pass the suffixed id). The test package is "<pkg>.test".
# Without --run-id it uses the newest successful run of the workflow on --ref;
# --release TAG|latest takes the APKs from a GitHub release (newest incl. pre-releases) instead of a run.
# --dispatch triggers a new run first (outward-facing: runs the repo's CI) and waits.
set -euo pipefail

repo="" pkg="" wf="device-apks.yml" ref="" artifact="device-apks" serial=""
runner="androidx.test.runner.AndroidJUnitRunner" out="" run_id="" dispatch=0 dry=0 tmo=600 release=""
usage() { sed -n '2,15p' "$0"; exit "${1:-2}"; }
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) repo=$2; shift 2;; --pkg) pkg=$2; shift 2;; --workflow) wf=$2; shift 2;;
    --ref) ref=$2; shift 2;; --artifact) artifact=$2; shift 2;; --serial) serial=$2; shift 2;;
    --runner) runner=$2; shift 2;; --out) out=$2; shift 2;; --run-id) run_id=$2; shift 2;; --timeout) tmo=$2; shift 2;; --release) release=$2; shift 2;;
    --dispatch) dispatch=1; shift;; --dry-run) dry=1; shift;; -h|--help) usage 0;;
    *) echo "unknown arg: $1" >&2; usage;;
  esac
done
[ -n "$repo" ] && [ -n "$pkg" ] || usage
for t in gh adb unzip; do command -v "$t" >/dev/null || { echo "missing tool: $t" >&2; exit 1; }; done

if [ -z "$serial" ]; then
  mapfile -t devs < <(adb devices | awk 'NR>1 && $2=="device"{print $1}')
  [ "${#devs[@]}" -eq 1 ] || { echo "need exactly one adb device (found ${#devs[@]}); pass --serial" >&2; exit 1; }
  serial=${devs[0]}
fi
A=(adb -s "$serial")
[ -n "$out" ] || out="phone-ci-$(date +%Y%m%d-%H%M%S)"
out=$(realpath -m "$out")

refargs=(); [ -z "$ref" ] || refargs=(--branch "$ref")
if [ -n "$release" ]; then
  [ "$release" != latest ] || release=$(gh release list -R "$repo" --limit 1 --json tagName --jq '.[0].tagName')
  echo "release: $release  device: $serial  out: $out"
elif [ "$dispatch" = 1 ]; then
  [ "$dry" = 0 ] || { echo "dry-run: would dispatch $wf on ${ref:-default branch} in $repo"; }
  if [ "$dry" = 0 ]; then
    gh workflow run "$wf" -R "$repo" ${ref:+--ref "$ref"}
    sleep 8
    run_id=$(gh run list -R "$repo" --workflow "$wf" "${refargs[@]}" --limit 1 --json databaseId --jq '.[0].databaseId')
    gh run watch "$run_id" -R "$repo" --exit-status
  fi
fi
if [ -z "$release" ] && [ -z "$run_id" ]; then
  run_id=$(gh run list -R "$repo" --workflow "$wf" "${refargs[@]}" --status success --limit 1 \
           --json databaseId --jq '.[0].databaseId // empty')
  [ -n "$run_id" ] || { echo "no successful run of $wf on ${ref:-any branch}; use --dispatch" >&2; exit 1; }
fi
[ -n "$release" ] || echo "run: $run_id  device: $serial  out: $out"

if [ "$dry" = 1 ]; then
  if [ -n "$release" ]; then src="release $release assets"; else src="'$artifact' from run $run_id"; fi
  echo "dry-run: would download $src, install app + test APK, run $pkg.test/$runner"
  exit 0
fi

mkdir -p "$out"
if [ -n "$release" ]; then
  gh release download "$release" -R "$repo" -p '*.apk' -D "$out/apks"
else
  gh run download "$run_id" -R "$repo" -n "$artifact" -D "$out/apks"
fi
app_apk=$(find "$out/apks" -name '*.apk' ! -name '*androidTest*' | head -1)
test_apk=$(find "$out/apks" -name '*androidTest*.apk' | head -1)
[ -n "$app_apk" ] && [ -n "$test_apk" ] || { echo "artifact lacks app or androidTest APK" >&2; exit 1; }

"${A[@]}" logcat -c || true
# -g grants every runtime permission: foreground services with camera/location types crash on
# Android 14+ without them (seen on mia, DrivingService).
"${A[@]}" install -r -g -t "$app_apk"
"${A[@]}" install -r -g -t "$test_apk"
set +e
timeout "$tmo" adb -s "$serial" shell am instrument -w -r "$pkg.test/$runner" | tee "$out/instrument.txt"
rc=${PIPESTATUS[0]}
set -e
[ "$rc" != 124 ] || echo "instrumentation timed out after ${tmo}s" >&2
"${A[@]}" logcat -d -v threadtime >"$out/logcat.txt" || true
"${A[@]}" exec-out screencap -p >"$out/final-screen.png" || true

# am instrument exits 0 even when tests fail; read the summary.
if grep -q '^OK (' "$out/instrument.txt"; then verdict=PASS
elif grep -qE 'FAILURES!!!|INSTRUMENTATION_FAILED|shortMsg=' "$out/instrument.txt"; then verdict=FAIL
else verdict=UNKNOWN; fi
total=$(grep -m1 -oE 'numtests=[0-9]+' "$out/instrument.txt" | cut -d= -f2 || true)
failed=$(grep -c 'INSTRUMENTATION_STATUS_CODE: -[0-9]' "$out/instrument.txt" || true)
echo "verdict: $verdict (tests=${total:-?} failed=${failed:-0} adb rc=$rc); evidence in $out"
[ "$verdict" = PASS ]
