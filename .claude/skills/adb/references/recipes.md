# Recipes (everyday tasks)

Prefer the `adb` MCP tools (structured JSON, quoted args, scoped destructive ops) for these; fall back to the CLI commands below. Use `-s <serial>` when more than one device is attached. Quote remote args: `adb shell "ls -la '/sdcard/My Files'"`.

## Device info
`adb shell getprop ro.product.model` · `dumpsys battery` · `ip addr show wlan0` · `uptime` · `df -h` · `free -m`

## Files
`adb push <local> <remote>` · `adb pull <remote> <local>` · `adb shell ls -la <path>` · as root (only if `su` exists): `adb shell su -c '<cmd>'`

## Apps
`pm list packages [-3]` · `adb install -r [-g] [-t] [-d] <apk>` · `adb install-multiple a.apk b.apk` · `adb uninstall <pkg>` (confirm) · `am force-stop <pkg>` · `monkey -p <pkg> -c android.intent.category.LAUNCHER 1` · `pm clear <pkg>` (confirm) · `dumpsys package <pkg> | grep versionName`

## APK sourcing (strict)
1. Check installed: `adb shell pm list packages | grep -i <name>`.
2. Prefer F-Droid > GitHub Releases > APKMirror > vendor URL the user gives. HTTPS only; never APKPure/blogs/file-hosts; never trust search snippets/redirects, fetch the source page.
3. Download into a fresh dir: `d=$(mktemp -d); curl -fL -o "$d/app.apk" "<url>"`.
4. Verify: `file`, `aapt dump badging` (package, version, native-code vs `ro.product.cpu.abi`), sha256.
5. Show source URL, package, version, size; get confirmation; then `adb install -r`. Verify with `pm list packages`; remove temp dir.

## Screen / input
`adb exec-out screencap -p > shot_$(date +%s).png` · `screenrecord /sdcard/r.mp4` then pull · `input tap|swipe|text|keyevent` (HOME=3 BACK=4 POWER=26 VOL+=24 VOL-=25) · UI tree: `adb exec-out uiautomator dump /dev/tty`

## Network / services
`dumpsys wifi | grep -E 'mWifiInfo|SSID'` · `svc wifi enable|disable` · `adb forward tcp:8080 tcp:8080` · `adb reverse tcp:3000 tcp:3000` · (root) `su -c 'netstat -tlnp'`

## Logs / debugging
`adb logcat -d` · `logcat -s TAG` · `logcat -c` · `adb bugreport out.zip` · `dumpsys activity activities | grep mResumedActivity`

## Reboot (confirm first)
`adb reboot` · `adb reboot recovery` · `adb reboot bootloader`

## Risky (confirm, explain)
`mount -o remount,rw /system` (usually impossible on dynamic partitions) · `setenforce 0` · `adb root` (only userdebug/eng builds).
