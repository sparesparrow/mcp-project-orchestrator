#!/usr/bin/env bash
# Read-only preflight for the adb skill. Prints what is present/missing; installs nothing.
set -u
ok=0; miss=0
chk() { # name, cmd, hint, [optional]
  if command -v "$2" >/dev/null 2>&1; then printf '  [ok]   %-16s %s\n' "$1" "$(command -v "$2")"; ok=$((ok+1))
  elif [ "${4:-}" = optional ]; then printf '  [opt]  %-16s missing (optional) hint: %s\n' "$1" "$3"
  else printf '  [MISS] %-16s hint: %s\n' "$1" "$3"; miss=$((miss+1)); fi
}
echo "== tools =="
chk adb adb "sudo apt install adb  (or Google platform-tools zip -> ~/.local/opt/platform-tools)"
chk fastboot fastboot "sudo apt install fastboot  (or platform-tools zip)"
chk python3 python3 "sudo apt install python3"
chk unzip unzip "sudo apt install unzip"
chk curl curl "sudo apt install curl"
chk sha256sum sha256sum "coreutils"
chk aapt aapt "sudo apt install aapt  (APK verification)" optional
chk simg2img simg2img "sudo apt install android-sdk-libsparse-utils (sparse firmware images)" optional
chk lsusb lsusb "sudo apt install usbutils"
echo "== versions =="
command -v adb >/dev/null 2>&1 && adb version | head -2
command -v fastboot >/dev/null 2>&1 && fastboot --version | head -1
ptv=$(adb version 2>/dev/null | sed -n 's/^Version \([0-9]*\)\..*/\1/p' | head -1)
if [ -n "$ptv" ] && [ "$ptv" -lt 37 ]; then
  echo "  [WARN] platform-tools $ptv < 37 (recommended for wireless pairing / ADB Wi-Fi 2.0; USB adb/fastboot still OK)"
  echo "         upgrade (user runs): d=\$(mktemp -d); curl -fL -o \"\$d/pt.zip\" https://dl.google.com/android/repository/platform-tools-latest-linux.zip"
  echo "         && unzip -q \"\$d/pt.zip\" -d ~/.local/opt && export PATH=~/.local/opt/platform-tools:\$PATH"
else
  echo "  (platform-tools >= 37 recommended for wireless pairing / ADB Wi-Fi 2.0)"
fi
echo "== linux usb access =="
if ls /etc/udev/rules.d/*android* /usr/lib/udev/rules.d/*android* /lib/udev/rules.d/*android* >/dev/null 2>&1; then
  echo "  [ok]   android udev rules present"
else
  echo "  [WARN] no android udev rules found (apt: android-sdk-platform-tools-common)"
fi
id -nG | tr ' ' '\n' | grep -qxE 'plugdev|adbusers' && echo "  [ok]   user in plugdev/adbusers" || echo "  [info] user not in plugdev/adbusers (usually fine if udev uses uaccess)"
echo "== if 'fastboot devices' is empty while the phone shows the bootloader screen =="
echo "  udev: sudo apt install android-sdk-platform-tools-common; sudo udevadm control --reload-rules; replug"
echo "  check: lsusb (Motorola fastboot is usually 22b8:...); try another USB port and a data cable"
echo "  old fastboot: use Google platform-tools (see upgrade hint above / developer.android.com/tools/releases/platform-tools)"
echo "  prefer fixing udev over running fastboot with sudo"
echo "== summary: $ok ok, $miss missing =="
[ "$miss" -eq 0 ]
