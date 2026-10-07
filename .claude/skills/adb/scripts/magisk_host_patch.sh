#!/usr/bin/env bash
# Patch a stock boot image with Magisk entirely on the Linux host (no phone UI needed).
# Mirrors Magisk's own assets/boot_patch.sh, using the static host magiskboot from the APK.
#
# Usage: magisk_host_patch.sh --apk Magisk.apk --boot stock_boot.img --out patched.img \
#          [--preinit metadata] [--abi arm64-v8a]
#
#   --preinit   Pre-init partition name. Get it from the running phone BEFORE an unlock wipe:
#               adb push <apk-lib>/arm64-v8a/libmagisk.so /data/local/tmp/magisk   (must be named "magisk")
#               adb shell 'cd /data/local/tmp && chmod 755 magisk && ./magisk --preinit-device'
#               (works unprivileged; moto g54 5G prints "metadata"). Omit if unknown (root still works).
#
# Output: --out file (same size as the input) and its sha256. Never flashes anything.
set -euo pipefail
apk= boot= out= preinit= abi=arm64-v8a
while [ $# -gt 0 ]; do
  case "$1" in
    --apk) apk=$2; shift 2;; --boot) boot=$2; shift 2;; --out) out=$2; shift 2;;
    --preinit) preinit=$2; shift 2;; --abi) abi=$2; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done
[ -f "$apk" ] && [ -f "$boot" ] && [ -n "$out" ] || { sed -n '2,20p' "$0"; exit 2; }
case "$(uname -m)" in x86_64) hostabi=x86_64;; aarch64) hostabi=arm64-v8a;; *) echo "unsupported host arch" >&2; exit 1;; esac

w=$(mktemp -d); trap 'rm -rf "$w"' EXIT
unzip -q -o "$apk" "lib/$hostabi/libmagiskboot.so" "lib/$abi/libmagisk.so" "lib/$abi/libmagiskinit.so" \
  "lib/$abi/libinit-ld.so" "assets/stub.apk" -d "$w/apk"
cp "$w/apk/lib/$hostabi/libmagiskboot.so" "$w/magiskboot"
cp "$w/apk/lib/$abi/libmagisk.so" "$w/magisk"
cp "$w/apk/lib/$abi/libmagiskinit.so" "$w/magiskinit"
cp "$w/apk/lib/$abi/libinit-ld.so" "$w/init-ld"
cp "$w/apk/assets/stub.apk" "$w/stub.apk"
chmod 755 "$w/magiskboot" "$w/magisk" "$w/magiskinit"
cp "$boot" "$w/boot.img"
cd "$w"
export KEEPVERITY=false KEEPFORCEENCRYPT=false PATCHVBMETAFLAG=false

mkdir u && cd u
../magiskboot unpack ../boot.img >/dev/null || { echo "unpack failed (rc=$?)" >&2; exit 1; }
ramdisk=ramdisk.cpio
[ -e "$ramdisk" ] || { echo "no ramdisk in this image; Magisk would need recovery mode (see Magisk docs)" >&2; exit 1; }
set +e; ../magiskboot cpio "$ramdisk" test; st=$?; set -e
[ "$st" = 0 ] || { echo "ramdisk status $st (1=already Magisk patched, 2=unsupported patcher): use an unpatched stock image" >&2; exit 1; }
SHA1=$(../magiskboot sha1 ../boot.img)
cp -af "$ramdisk" ramdisk.cpio.orig
../magiskboot compress=xz ../magisk magisk.xz
../magiskboot compress=xz ../stub.apk stub.xz
../magiskboot compress=xz ../init-ld init-ld.xz
{ echo "KEEPVERITY=false"; echo "KEEPFORCEENCRYPT=false"; echo "RECOVERYMODE=false"; echo "VENDORBOOT=false"
  [ -n "$preinit" ] && echo "PREINITDEVICE=$preinit"; echo "SHA1=$SHA1"; } > config

../magiskboot cpio "$ramdisk" \
  "add 0750 init ../magiskinit" \
  "mkdir 0750 overlay.d" \
  "mkdir 0750 overlay.d/sbin" \
  "add 0644 overlay.d/sbin/magisk.xz magisk.xz" \
  "add 0644 overlay.d/sbin/stub.xz stub.xz" \
  "add 0644 overlay.d/sbin/init-ld.xz init-ld.xz" \
  "patch" \
  "backup ramdisk.cpio.orig" \
  "mkdir 000 .backup" \
  "add 000 .backup/.magisk config"

for dt in dtb kernel_dtb extra; do
  [ -f "$dt" ] || continue
  ../magiskboot dtb "$dt" test || { echo "$dt was patched by an old Magisk" >&2; exit 1; }
  ../magiskboot dtb "$dt" patch || true
done
if [ -f kernel ]; then
  patched=false
  ../magiskboot hexpatch kernel 49010054011440B93FA00F71E9000054010840B93FA00F7189000054001840B91FA00F7188010054 \
    A1020054011440B93FA00F7140020054010840B93FA00F71E0010054001840B91FA00F7181010054 && patched=true || true
  ../magiskboot hexpatch kernel 821B8012 E2FF8F12 && patched=true || true
  ../magiskboot hexpatch kernel 70726F63615F636F6E66696700 70726F63615F6D616769736B00 && patched=true || true
  $patched || rm -f kernel
fi
../magiskboot repack ../boot.img >/dev/null
cd "$OLDPWD"
cp "$w/u/new-boot.img" "$out"
echo "in : $(stat -c %s "$boot") bytes  sha256 $(sha256sum "$boot" | cut -d' ' -f1)"
echo "out: $(stat -c %s "$out") bytes  sha256 $(sha256sum "$out" | cut -d' ' -f1)"
echo "preinit=${preinit:-<none>}"
