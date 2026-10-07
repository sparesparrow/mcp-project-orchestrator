# Bootloader unlock and Magisk root

Read `safety.md` first. Everything here is gated by it.

## Generic flow (any A/B or A-only device)

1. **Triage** (see SKILL.md). Record model, `ro.build.fingerprint`, Android version, slot suffix, `ro.boot.flash.locked`.
2. **Prereqs on phone:** Developer options > USB debugging ON, OEM unlocking ON. If OEM unlocking is greyed out the bootloader can't be unlocked (carrier lock / needs internet + 7 days on some brands) — stop and tell the user.
3. **Reboot to bootloader:** `adb reboot bootloader` (confirm first), then `fastboot devices` and `fastboot getvar all 2>&1 | head -60`.
4. **Unlock** per vendor (below). Unlock factory-resets the phone. After it, redo setup and re-enable USB debugging.
5. **Get stock firmware** matching the exact fingerprint/build and region (same or newer-compatible; never older than the installed security patch/rollback index). Verify checksum if the source provides one. Extract `boot.img`, and `init_boot.img` if the device ships one (Android 13+ devices launched with 13 often do; check for it in the firmware and `fastboot getvar all`).
6. **Patch on the device:** `adb push boot.img /sdcard/Download/`; user installs the Magisk app (official release from github.com/topjohnwu/Magisk/releases), Install > Select and Patch a File. `adb pull /sdcard/Download/magisk_patched-*.img`.
   - Patch `init_boot.img` if present, else `boot.img`. If the device has no boot ramdisk, patch `recovery.img` instead (Magisk docs).
7. **Flash (gated):** `adb -s <serial> reboot bootloader` (own confirmation; if the bootloader answers "Preflash validation failed" or `getvar unlocked` is "not found", use fastbootd instead: `fastboot -s <serial> reboot fastboot`), read `fastboot getvar current-slot` **at this moment** (an OTA after the unlock wipe can switch slot/build), then `scripts/flash_guarded.sh <init_boot|boot>_<slot> magisk_patched.img --serial <serial> --product <codename>` (dry run, then exact-command yes). `flash_guarded.sh` refuses any slot other than `current-slot`.
8. **vbmeta:** only if the device fails verification/bootloops: `fastboot flash vbmeta --disable-verity --disable-verification vbmeta.img` (the stock vbmeta from the same firmware). Magisk docs warn this may wipe data. Not a default step.
9. `fastboot reboot`, then verify: Magisk app shows installed; `adb shell su -c id` returns `uid=0` (approve prompt on phone).
10. Keep the stock images. Updating: restore stock boot, OTA, re-patch (Magisk "Install to inactive slot" workflow for A/B).

## Recovery
- **Bootloop after flash:** `fastboot flash <part> stock_boot.img` then `fastboot reboot`; if still bad, flash full stock firmware with the vendor flash tool/script.
- **Can't enter fastboot:** hold Power + Volume Down from off.
- **Return to stock/relock:** flash all stock images then `fastboot oem lock` only on a fully stock, matching build (relocking a modified device bricks it).

## Motorola (incl. moto g54 5G, MediaTek Dimensity 7020)

- Model codes: moto g54 5G is the XT2343-x family (variants vary by region; verify with `ro.product.model` / `ro.product.device`).
- Unlock method: official portal — `fastboot oem get_unlock_data` prints a multi-line string; the user joins the lines (no spaces/`(bootloader)` prefixes) and submits it at the Motorola unlock page (needs the user's Motorola ID/email); the portal returns a 20-character key; then `fastboot oem unlock <KEY>`. **Claude never invents keys.** Portal steps follow `browser-steps.md`: Claude may drive a browser tool, but the user types passwords, solves CAPTCHA/2FA and accepts the legal notice, and says yes to the exact string before it is submitted.
- Carrier variants (e.g. T-Mobile/Verizon branded) may be refused a key; the portal will say "your device is not eligible". Report and stop.
- Firmware: obtain the stock ROM for the exact retail channel/build (a verified mirror such as the community-maintained Motorola firmware archive; confirm hash/filename against `ro.build.fingerprint`). Unpack with `unzip`/`simg2img` as needed; extract `boot.img` (and `init_boot.img` if present).
- Flash targets are slot-suffixed (`boot_a` / `boot_b`, or `init_boot_a` / `init_boot_b`).
- MediaTek caveat: do not touch `nvdata`, `nvram`, `protect1/2`, `persist`, `preloader` (IMEI/baseband loss).
- Community guides list `fastboot flash boot_a/boot_b patched.img` and say OTAs are lost after root; they often omit vbmeta, so follow the Magisk procedure above and treat community guides as secondary.
- Some Motorola builds show an "N/A" / "bad key" bootloader warning screen after unlock; this is normal.
