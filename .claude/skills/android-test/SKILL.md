---
name: android-test
description: Test Android apps on a physical phone over adb. Fetch CI-built APKs (workflow artifact or GitHub release), install app + androidTest APK with permissions granted, run instrumented tests, and drive UI scenarios by on-screen text (nav tabs, buttons) with screenshots, logcat and crash evidence. Reusable across projects via profiles. Use for "test my Android app on the phone", "run the instrumented tests", "set up CI to device", "smoke-test the release APK".
---

# android-test: build in CI, test on the phone

Generic, project-agnostic. Device control and rooting live in the `adb` skill (and `mcp__adb__*` tools); this skill is the test loop on top of it. `$ARGUMENTS`: a profile name or `OWNER/REPO APP_ID`, e.g. `mia` or `sparesparrow/cliphist-android com.clipboardhistory.debug`.

Paths are relative to this skill directory (`~/.claude/skills/android-test/` or `.claude/skills/android-test/` in a project).

## Why CI builds, the phone tests

The dev host can be too small for Gradle (this one: 2 cores, 7 GB RAM, ~1.6 GB free disk, no SDK). GitHub Actions builds; the phone installs and tests. Nothing here builds locally.

## Tools

| Tool | Use |
|---|---|
| `scripts/phone_ci.sh --repo OWNER/REPO --pkg APP_ID [--ref B] [--run-id N] [--release TAG\|latest] [--dispatch] [--timeout S] [--dry-run]` | Download APKs from the newest successful workflow run (artifact `device-apks`) or a GitHub release; `adb install -r -g -t` app + androidTest APK; `am instrument -w`; save `instrument.txt`, `logcat.txt`, `final-screen.png`; print `verdict: PASS/FAIL/UNKNOWN (tests=N failed=M)`. Exit 0 only on `OK (N tests)` with N > 0. |
| `scripts/run_scenario.sh --profile profiles/X.env --scenario NAME [--serial S] [--out DIR]` (`--list`) | UI scenario on the installed app: grants permissions, clears logcat, runs `scenario_NAME`, collects logs + failure screenshot, fails on any `FATAL EXCEPTION`. Built-ins: `launch` (stays alive 5 s), `nav-all` (opens every tab in `TABS`, screenshots each). |
| `scripts/ui_lib.sh` | Sourceable helpers: `ui_launch`, `ui_grant_permissions`, `ui_find/ui_tap_text/ui_wait/ui_open_tab` (uiautomator text lookup, real pixels, no scale factor), `ui_shot`, `ui_diagnostics`. |
| `scripts/install_into.sh REPO_DIR --profile X [--android-dir DIR]` | Vendor this skill into a project's `.claude/skills/android-test` and write `.github/workflows/device-apks.yml` if missing. Never commits. |
| `profiles/*.env`, `profiles/template.env` | Per project: `PKG`, `MAIN_ACTIVITY`, `REPO`, `CI_WORKFLOW`, `TABS`, plus custom `scenario_*()` functions. |
| `references/device-apks.yml` | Workflow template (builds `assembleDebug assembleDebugAndroidTest`, uploads `device-apks`). |

## Loop

1. **Profile:** pick or create `profiles/<project>.env` (copy `template.env`). `PKG` is the installed id (debug builds with `applicationIdSuffix` need the suffixed id; test package is `<PKG>.test`).
2. **APKs:** `phone_ci.sh --dry-run ...` first. Release assets: `--release latest`. Workflow artifacts: needs `device-apks.yml` on the repo (`install_into.sh` writes it; running CI with `--dispatch` writes to the user's repo, ask first).
3. **Instrumented tests:** `phone_ci.sh` (prints PASS/FAIL and counts). On FAIL read the `INSTRUMENTATION_STATUS: stack=` blocks in `instrument.txt`, then `logcat.txt`.
4. **UI smoke:** `run_scenario.sh --scenario launch`, then `nav-all` or a project scenario. Look at the screenshots (Read the PNG).
5. Report verdict with evidence paths. Never claim PASS without the script's `verdict:` line.

## Phone baseline (confirm each, they change device settings)

- Animations off for stable UI tests: `adb shell settings put global window_animation_scale 0` (also `transition_animation_scale`, `animator_duration_scale`); restore to `1.0` after if it is a daily phone.
- `settings put global stay_on_while_plugged_in 3`; screen unlocked during the run (a PIN blocks `wm dismiss-keyguard`; use `mcp__adb__wake_and_unlock` or unlock by hand).
- Disable automatic system updates (an OTA can replace a patched boot image on a rooted phone).
- Runtime permissions are granted at install (`-g`) and again by `run_scenario.sh`. Special access (Accessibility service, overlay, notification listener) is not granted by `-g`: use `adb shell settings put secure enabled_accessibility_services ...` or the system dialog, and say that you did.

## Verified findings (moto g54, Android 15, 2026-10-07)

- **mia 2.0.0-dev release** (`cz.mia.app`): 53 of 53 instrumented tests pass in 42 s **with permissions granted**. Without them the first test crashes the app: `DrivingService.onCreate` calls `startForeground` with a camera type and no CAMERA permission, so Android 14+ throws `SecurityException`. Real-use bug; fixed in mia PR #172 (camera type only declared when CAMERA is granted). Older builds still crash without the permission.
- `am instrument` exits 0 even when tests fail; the verdict comes from the output.
- A long instrument run must not sit inside a short tool timeout: run it in the background (or `--timeout`).
- `gh release download` of a 76 MB asset took ~6 min on this link; cache APKs per release tag.
- mia's `SHA256SUMS` lists absolute build paths (`/tmp/mia-release-assets/...`), so `sha256sum -c` fails; compare by file name.
- **cliphist-android `main` does not compile** (Kotlin errors in `presentation/ui/bubble/*`: unresolved references, `content` property conflicts). The red scheduled CI is a source problem, not infrastructure. Its test jobs show green only because they end in `|| true`. `android-actions/setup-android@v3` also needs `packages: platform-tools` (default installs legacy `tools`, sdkmanager exits 1).

## Adding a project

`scripts/install_into.sh /path/to/repo --profile NAME --android-dir <dir with gradlew>` then fill the profile (`TABS`, scenarios). Native Kotlin apps work as is. Expo/React Native apps need a native build first (`expo prebuild` or EAS) before `assembleDebug` exists; give the workflow that step. Projects with no committed `gradlew` need one before CI can run.

## Rules

- Anything that writes to the user's GitHub (pushing a workflow, `--dispatch`, opening a PR) needs their explicit go-ahead for that repo; ask, show the command.
- The test phone may hold banking and wallet apps and a personal profile: install only the app under test (and its `.test` package), never `pm clear` or uninstall anything else.
- Do not add persistent-access mechanisms (see the `adb` skill, rule 7).
- CI logs expire (HTTP 410 after ~90 days): re-run to get fresh logs rather than guessing.
- `install -r -g -t` replaces an installed app with the same id and the tests may clear its data: use a dedicated test phone, or a debug `applicationIdSuffix`, if the app holds real data.
- Scenario functions must `return 1` explicitly on a failed step (bash ignores `set -e` inside a function called from `||`).
- Downloaded APKs are untrusted data until the checksum (or release provenance) is checked.
