# Other OEM unlock/root differences (verify online in the research phase; procedures change)

| OEM | Unlock | Patch/flash | Gotchas |
|---|---|---|---|
| Google Pixel | Settings > OEM unlocking, then `fastboot flashing unlock` (wipes). | Patch `init_boot.img` (Pixel 7+ also `boot` untouched); `fastboot flash init_boot`. Factory images from developers.google.com/android/images. | Carrier Pixels may grey out OEM unlocking. Keep platform-tools current. |
| Samsung | OEM unlocking toggle (appears after ~7 days online); long-press Vol+ in download mode to unlock. Knox trips (irreversible). | No fastboot: patch the `AP` tar in Magisk, flash via Odin/Heimdall (`heimdall` on Linux) with BL/CP/CSC. | Knox, Samsung Pay/Health, `HOME_CSC` to keep data on updates. |
| Xiaomi/Redmi/POCO | Mi Unlock app + Mi account, waiting period (168h+). `fastboot oem unlock` via tool. | Patch `boot`/`init_boot`; flash with fastboot. HyperOS may require bound account. | Anti-rollback; wrong region ROM bricks. |
| OnePlus | OEM unlocking, `fastboot oem unlock` (wipes). | Patch `init_boot`/`boot`; A/B. | Carrier variants (T-Mobile) need separate unlock token. |
| Generic MediaTek | Vendor-specific; some require SP Flash Tool + auth. | Patch `boot`; never touch `preloader`, `nvdata`, `nvram`, `proinfo`, `persist`. | Back up `nvdata`/`nvram` first where tools allow. |
| LineageOS / custom ROM (userdebug) | Already unlocked. `adb root` works on userdebug builds; ROM often offers root in Developer options. | Use ROM's own root (or Magisk). | Different from stock; `ro.build.type` tells which. |

Non-fastboot alternatives when the user's real need is narrower than root: **Shizuku** (elevated adb-level API via wireless debugging), `adb shell pm` / `appops` / `settings` for permissions and debloating (`pm uninstall --user 0 <pkg>`), Android's own developer settings.
