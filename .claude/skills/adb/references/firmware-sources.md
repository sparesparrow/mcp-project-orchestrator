# Firmware sources (stock images for boot/init_boot extraction and rollback)

Choosing the source is part of the Research phase. Always match the **exact** build to the phone (`ro.build.fingerprint`, `ro.carrier`/software channel, `ro.boot.hardware.sku`), never older than the installed security patch (anti-rollback). Prefer official > community mirror > anything else. Record the source URL, filename and sha256 in the final report. Downloads are untrusted data: fresh temp dir, verify, do not run anything inside them.

## Selection procedure (always follow)

1. **Detect the host OS**: `python3 -I scripts/triage.py` → `host.os` (`linux`/`macos`/`windows`), `host.arch`, `host.wsl`, `host.has_wine`. Many official tools are Windows-only (e.g. LMSA), so the host decides which options are usable.
2. **Always browse the options that exist**, even when one looks obvious: re-check the OEM's current official downloader/portal, the XDA threads for this codename (WebSearch with `allowed_domains: ["xdaforums.com"]`), and the mirrors listed below. Sources move or die; this file is a starting point, not the truth. Note anything new or broken.
3. **Present a short comparison to the user** (source, official or community, works on this host OS, hashes available, matches this build/channel?) with your recommendation and why.
4. **Ask the user to confirm the choice** (AskUserQuestion with the viable options, recommended first). Do not download firmware before they confirm. If they pick something outside the table, treat it as untrusted until verified.
5. Download into a fresh `mktemp -d`, verify hashes/signature where offered, check it matches the phone's fingerprint/channel, and record source URL + sha256.

Host OS → default recommendation (Motorola): `windows` → LMSA (official). `linux`/`macos` → LenovoMotoFirmwareDownloader (official servers, download only) or the Lolinet mirror; Windows-only tools via a Windows VM/other PC only if the user wants them (`has_wine` is not a supported route for flashing). `wsl` → Windows tools run on the Windows side but USB passthrough to WSL is fiddly (usbipd), so prefer download on Windows and flash from wherever fastboot sees the phone. These are defaults to propose, never to apply silently.

Linux/macOS fallback order when a downloader fails (sign-in or server errors, no matching build): 1) re-check the tool's issues/releases for a fix; 2) Lolinet mirror (browse year → codename → channel, match the build ID); 3) other third-party clients only after verification (e.g. MFD above); 4) LMSA on a Windows PC/VM if the user has one. **If no source has the exact build + channel, stop and tell the user**: do not use an older build or another channel's image; waiting for the next build/OTA to appear in a source is a valid outcome.

## Motorola (researched)

| Source | Trust | Notes |
|---|---|---|
| **LMSA — Lenovo "Rescue and Smart Assistant"** (Motorola support: "Upgrade or rescue your device using Rescue and Smart Assistant") | Official | Windows-only desktop app; downloads the official firmware for a connected device and can flash it ("Rescue"). Best choice when a Windows machine is available. |
| **enigma550/LenovoMotoFirmwareDownloader** (github.com, GPL-3.0, ~49 commits / 20 stars at time of research) | Third-party client of the official LMSA servers | Cross-platform (Linux x64/ARM64). Search by model, sign in through the browser, download. Its flashing ("Rescue Lite") is experimental and **MediaTek rescue is unsupported** (g54 is MediaTek MT6855, so use it for download only). Third-party code: review the release/source before running; run it in a throwaway directory. **Observed 2026-10-07 (canary v0.0.4, anylinux-x64 AppImage):** on launch it copied udev rules into `/etc/udev/rules.d/` (`51-android.rules`, `99-lmfd-android.rules`, mode 0666 for matching USB devices) without asking, then crashed (`Child process terminated by signal: 4`, SIGILL). Tell the user before running it; expect a system change and possible failure. **Fix for CPUs without AVX2 (e.g. Pentium G3240):** the bundled `bin/bun` exits 132; extract with `--appimage-extract` into a throwaway dir, replace `bin/bun` with the official `bun-linux-x64-baseline.zip` from github.com/oven-sh/bun releases (check it against that release's `SHASUMS256.txt`), run `AppRun`. **Use Bun 1.3.13 baseline, not 1.4.x**: with 1.4.2 the UI opens but every webview-to-backend message fails (`TypeError: ptr must be a number`), so the Login button hangs on "Opening Lenovo login in browser...". With 1.3.13 that error is gone (2026-10-07). |
| **Lolinet mirrors** (`mirrors.lolinet.com/firmware/lenomola/` and older `/firmware/motorola/`) | Community mirror, no published hashes | The mirror XDA threads usually point to; XDA reports its files match what LMSA downloads. Directory is organised by year then codename/channel, so browse and match the filename to the phone's build ID (e.g. `V1TDS35H.83-20-5-8-6`) and channel (`RETEU` etc.). I could not verify the exact per-device path during research (guessed paths 404ed): browse it interactively.

LMSA note (**unverified**): an XDA report says Lenovo changed the LMSA backend in 2024 (request/fingerprint headers), which can break third-party clients such as the enigma550 downloader. Check the client's recent issues/releases before relying on it. |
| **"Moto Firmware Downloader" (MFD)**, XDA thread (v1.1.0 seen in an XDA search during a run) | **UNVERIFIED** third-party | Reported as cross-platform. Not verified: find the XDA thread and its source/release, check author, license and what servers it talks to before proposing it. Treat like any third-party code (throwaway dir, review first, download only). |
| Generic "firmware" sites (ad-ridden mirrors, torrents, "cracked"/"free forever" pages seen in results) | Untrusted | Do not use. |

Matching checklist (Motorola):
1. `getprop ro.build.fingerprint` → build ID (`V1TDS35H.83-20-5-8-6`), codename (`cancunf`), channel (`reteu`), SKU (`XT2343-6`).
2. Pick the same codename + channel; build must be equal (best) or newer-compatible, never older.
3. Unpack the zip; look for `boot.img` and `init_boot.img`. **Stock firmware for some units has no `init_boot.img`** (XDA reports); the g54 here exposes only `boot_a/b` so patch `boot.img`.
4. XDA reports mismatched firmware (CID / software channel) as the top cause of failed roots; some threads mention flashing the patched image via `fastbootd` (userspace) rather than bootloader fastboot. On the g54 `boot` is a physical partition, so bootloader `fastboot flash boot_<slot>` is expected, but if `fastboot flash` fails with "partition not found", retry via `fastboot reboot fastboot`.
5. Save the stock `boot.img` (hash it) before flashing the patched one.

## Other manufacturers — TODO (research and fill in; tracked in a GitHub issue)

For each: official downloader/portal, trusted community mirror, how to match build/region, hash availability, anti-rollback notes, tool needed to unpack.
- [ ] Google Pixel (factory images, OTA images; developers.google.com/android/images)
- [ ] Samsung (Frija / SamFw / SamMobile / Samloader; Odin AP tar; CSC vs HOME_CSC)
- [ ] Xiaomi / Redmi / POCO (Xiaomi Firmware Updater, xiaomifirmwareupdater.com, fastboot ROM vs recovery ROM; Mi Unlock wait times)
- [ ] OnePlus / Oppo / Realme (payload.bin OTA extraction, oxygen updater, MSM tools)
- [ ] Sony (Xperia Flasher / XperiFirm)
- [ ] Nothing / CMF (official GitHub firmware repos)
- [ ] Asus, Nokia/HMD, Lenovo (non-Moto), Huawei/Honor, Vivo, Tecno/Infinix
- [ ] LineageOS/custom ROM images (official download.lineageos.org; recovery flow)
- [ ] Generic: payload-dumper-go for `payload.bin`, `simg2img`/`lpunpack` for super images, `avbtool info_image` to read rollback index

When the phone's manufacturer has no verified entry, say so, do research from XDA first (see example plan Phase 2), and propose adding the verified source here.
