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

## Driving a dialog: screenshot, read, tap (worked for Magisk's "Requires additional setup")
1. `adb -s S exec-out screencap -p > shot.png`, then look at it (Read the PNG).
2. Coordinates: the image viewer may show a scaled copy (e.g. "original 1080x2400, displayed at 900x2000, multiply by 1.20"). `adb shell wm size` gives the real size. Tap in **real** pixels: `adb -s S shell input tap <x*scale> <y*scale>` (displayed OK at (751,1084) -> `input tap 901 1301`).
3. More robust than guessing pixels: `adb -s S exec-out uiautomator dump /dev/tty`, find the node by `text="OK"` and tap the centre of its `bounds="[x1,y1][x2,y2]"`. The `adb` MCP has `dump_ui`, `find_elements`, `tap_element` for the same.
4. Screenshot again to confirm the result; a reboot button drops adb for ~1 min, so poll `adb get-state` and `getprop sys.boot_completed` before the next step.
5. Locked screen: `input keyevent 224` (wake), swipe up, `input text <PIN>`, `input keyevent 66`. Take the PIN from the user for this session only; never write it to a file or repo.

## Network / services
`dumpsys wifi | grep -E 'mWifiInfo|SSID'` · `svc wifi enable|disable` · `adb forward tcp:8080 tcp:8080` · `adb reverse tcp:3000 tcp:3000` · (root) `su -c 'netstat -tlnp'`

## Logs / debugging
`adb logcat -d` · `logcat -s TAG` · `logcat -c` · `adb bugreport out.zip` · `dumpsys activity activities | grep mResumedActivity`

## Reboot (confirm first)
`adb reboot` · `adb reboot recovery` · `adb reboot bootloader`

## Risky (confirm, explain)
`mount -o remount,rw /system` (usually impossible on dynamic partitions) · `setenforce 0` · `adb root` (only userdebug/eng builds).
