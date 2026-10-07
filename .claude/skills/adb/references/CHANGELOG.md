# Changelog

## 2026-10-07: autonomous moto g54 5G root without Windows (field run)
- New references/field-notes-moto-g54-cancunf.md and a "Field notes" section at the end of SKILL.md: GKI-boot-image trick (match `ro.bootimage.build.fingerprint`/date/kernel instead of an exact firmware build), unlock and fastbootd quirks, USB-ID boot check, dead ends, verification checklist.
- New scripts: `magisk_host_patch.sh` (host-side Magisk patch, mirrors `boot_patch.sh`, static magiskboot from the APK, `--preinit`), `remote_zip_extract.py` (HTTP Range member extraction).
- firmware-sources.md: LenovoMotoFirmwareDownloader failure modes (SIGILL on non-AVX2 CPUs, Bun 1.3.13 baseline fix, "Missing device fingerprint"); playbooks/motorola.md: unlock and no-exact-firmware notes; SKILL.md rule 4 (user-pasted credential) and rule 7 (no persistent-access mechanisms in images).
- Not proven yet: `su` (needs USB debugging after the setup wizard).

## 2026-10-07: browser routes for website steps
- New references/browser-steps.md: ordered routes (connected browser MCP, Playwright MCP with system Chromium, scripted Playwright, manual), a who-does-what table, Motorola ID create / "Forgot password" flow, read-only Gmail verification-email rules.
- SKILL.md rule 4, bootloader-root.md and playbooks/motorola.md: the old "Claude must not do the portal step" is replaced by "Claude may drive a browser; the user types passwords, solves CAPTCHA/2FA, accepts the legal notice, and confirms the exact string before submit". Key-invention ban unchanged.
- questions.md: new question 6 (Browser). agents/adb.md: browser and read-only Gmail tools added.
- Flags confirmed with `npx @playwright/mcp --help`; `claude mcp add -s user playwright ...` ran and `claude mcp get playwright` reports Connected. Not yet exercised against a real page.

## 2026-10-07: review of "root my moto g54 5G" dry run (cancunf)

Source: reviewer findings (adb_run/review.md) and the run log. Gates only tightened; none relaxed.

| Change | File(s) | Finding |
|---|---|---|
| `flash_guarded.sh`: `--serial` and `--product` required with `--yes-i-confirmed`; serial must be in `fastboot devices`; `getvar product` must equal the codename; `unlocked` must be `yes`; A/B devices need an explicit suffix equal to `current-slot` (refuses a stale slot after an OTA); image header magic (`ANDROID!` for boot/init_boot/recovery, `VNDRBOOT` for vendor_boot, `AVB0` for vbmeta*); image must fit `partition-size`. Tested against a stub `fastboot` and dummy images only. | scripts/flash_guarded.sh, SKILL.md | S2 |
| Plans derive the slot from `fastboot getvar current-slot` right before flashing (no hard-coded `boot_b`); re-triage plus a fingerprint-vs-stock-image check before patching; turn off "Automatic system updates" during setup; any OTA means re-match firmware. | example-root-plan.md, bootloader-root.md, playbooks/motorola.md, safety.md, agents/adb.md | S3 |
| Old-phone Google backup moved from Phase 5b to Phase 4 and made a Gate 2 checklist item; Phase 5b compares the old phone's Android version. | example-root-plan.md, safety.md, agents/adb.md | S4, G6 |
| Gate 1 is stated to cover the plan only, not `adb reboot bootloader`, `fastboot oem unlock`, any flash, or later state-changing commands; `-s <serial>` on reboot/rollback commands. | example-root-plan.md, playbooks/motorola.md | S1, G9, S5 |
| Rollback: verify the stock image hash and flash the same slot via `flash_guarded.sh`. | example-root-plan.md, playbooks/motorola.md | S5 |
| `triage.py`: exact-name regex for `boot_partitions`/`patch_target` (drops `bootloader1/2`, `boot_para`); reports `oem_unlock_allowed_prop` (renamed from `oem_unlock_allowed`) and `oem_unlock_allowed_setting`; adds `carrier_boot` (`ro.boot.carrier`). | scripts/triage.py | S6, G3, G4 |
| Motorola playbook: unlock portal candidate URL marked "verify the current URL"; carrier/SIM-lock hint check; `oem_unlock_allowed` ambiguity explained (fastboot is the real check). | playbooks/motorola.md | G1, G3, G4 |
| `doctor.sh`: warns when platform-tools < 37 and prints the Google zip upgrade command; prints udev/USB hints for when fastboot cannot see the device. Example plan wording aligned to ">= 37". | scripts/doctor.sh, example-root-plan.md | G8 |
| firmware-sources.md: XDA "Moto Firmware Downloader" (MFD) added as an UNVERIFIED candidate; LMSA 2024 backend change noted as unverified; Linux fallback order ending in "no exact build, so stop". | references/firmware-sources.md | G2, the narrower part of claim 5 |

Rejected or narrowed:
- Claim 5 ("no Linux fallback when the downloader fails"): the reviewer found it wrong, because Lolinet was already listed as the Linux alternative. I added no new source on its basis. I added only the reviewer's narrower gap: what to do when no source matches the exact build (stop), plus an explicit ordering of the options that already exist.
- Claim 7 ("triage hard-codes patch_target boot"): wrong. The value is derived from `/dev/block/by-name`. Only the loose prefix match (S6) was fixed.
- The MFD version and LMSA backend claims were not verified. They are recorded as unverified and not recommended by default.
- The portal URL was not fetched and is labelled as a candidate to verify.
- vbmeta disable-flag handling in `flash_guarded.sh` was not added. The script has no flag passthrough, so raw vbmeta flashing stays under the safety.md command gate.

## Round 2 (interaction protocol + headless test)
- SKILL.md: plan mode first (EnterPlanMode) for state-changing tasks, then AskUserQuestion, then ExitPlanMode; headless/subagent fallback.
- New references/questions.md: question catalogue (backup method with 4 options, firmware source, root method, restore, carrier).
- agents/adb.md: points at the protocol.
- Headless test (`claude -p`, plan mode, fastboot/reboot/flash denied; fixtures in the test dir `adb_skill_test/inputs`): both runs read-only, XDA first, correct gating. Findings fixed: run A merged backup options instead of listing them (questions.md now requires verbatim options); both runs called an unverified Motorola URL "official" (motorola.md now lists both candidates as unverified).
