#!/usr/bin/env python3
"""Read-only device triage. Prints one JSON object. Usage: python3 -I triage.py [serial]"""
import json
import re
import subprocess
import sys

PROPS = {
    "manufacturer": "ro.product.manufacturer",
    "brand": "ro.product.brand",
    "model": "ro.product.model",
    "device": "ro.product.device",
    "android": "ro.build.version.release",
    "sdk": "ro.build.version.sdk",
    "patch": "ro.build.version.security_patch",
    "fingerprint": "ro.build.fingerprint",
    "build_type": "ro.build.type",
    "soc": "ro.board.platform",
    "hardware": "ro.hardware",
    "abi": "ro.product.cpu.abi",
    "flash_locked": "ro.boot.flash.locked",
    "verified_boot": "ro.boot.verifiedbootstate",
    "slot_suffix": "ro.boot.slot_suffix",
    "oem_unlock_supported": "ro.oem_unlock_supported",
    "dynamic_partitions": "ro.boot.dynamic_partitions",
    "oem_unlock_allowed_prop": "sys.oem_unlock_allowed",  # hint only; fastboot get_unlock_data/getvar is the real check
    "carrier": "ro.carrier",
    "carrier_boot": "ro.boot.carrier",
    "sku": "ro.boot.hardware.sku",
    "vbmeta_state": "ro.boot.vbmeta.device_state",
}


def run(cmd, timeout=15):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return 127, str(e)


def parse_devices(out):
    devs = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and not line.startswith("*"):
            devs.append({"serial": parts[0], "state": parts[1], "info": " ".join(parts[2:])})
    return devs


def main():
    serial = sys.argv[1] if len(sys.argv) > 1 else None
    import platform
    import shutil
    sysname = platform.system()
    res = {
        "host": {
            "os": {"Linux": "linux", "Darwin": "macos", "Windows": "windows"}.get(sysname, sysname.lower()),
            "arch": platform.machine(),
            "wsl": "microsoft" in platform.release().lower(),
            "has_wine": bool(shutil.which("wine")),
        },
        "adb_devices": [], "fastboot_devices": [], "usb": [], "selected": None, "props": {}, "verdict": "",
    }

    _, out = run(["adb", "devices", "-l"])
    res["adb_devices"] = parse_devices(out)
    rc, out = run(["fastboot", "devices"])
    res["fastboot_devices"] = [l.split()[0] for l in out.splitlines()
                               if rc == 0 and l.strip() and re.match(r"^\S+\s+(fastboot|fastbootd)\b", l)]
    _, out = run(["lsusb"])
    keys = ("google", "motorola", "samsung", "xiaomi", "oneplus", "mediatek", "qualcomm", "18d1", "22b8", "04e8", "2717", "0e8d", "05c6")
    res["usb"] = [l for l in out.splitlines() if any(k in l.lower() for k in keys)]

    ready = [d for d in res["adb_devices"] if d["state"] == "device"]
    if serial:
        ready = [d for d in ready if d["serial"] == serial]
    if len(ready) > 1 and not serial:
        res["verdict"] = "multiple_devices: re-run with a serial"
    elif ready:
        s = ready[0]["serial"]
        res["selected"] = s
        for k, p in PROPS.items():
            _, v = run(["adb", "-s", s, "shell", "getprop", p])
            res["props"][k] = v
        rc, v = run(["adb", "-s", s, "shell", "command -v su"])
        res["props"]["su_present"] = bool(v) and rc == 0
        _, v = run(["adb", "-s", s, "shell", "dumpsys battery | grep -m1 level"])
        res["props"]["battery"] = v.replace("level:", "").strip()
        _, v = run(["adb", "-s", s, "shell", "ls /dev/block/by-name 2>/dev/null"])
        names = v.split()
        _, v = run(["adb", "-s", s, "shell", "settings get global oem_unlock_allowed"])
        res["props"]["oem_unlock_allowed_setting"] = v  # often "null"; ambiguous, do not treat as proof
        # Exact boot-image partitions only (excludes bootloader1/2, boot_para, etc.).
        img = re.compile(r"^(boot|init_boot|vendor_boot|recovery|vbmeta|vbmeta_system|vbmeta_vendor)(_[ab])?$")
        bparts = [n for n in names if img.match(n)]
        res["props"]["boot_partitions"] = bparts
        bases = {img.match(n).group(1) for n in bparts}
        res["props"]["patch_target"] = (
            "init_boot" if "init_boot" in bases else "boot" if "boot" in bases else "unknown")
        res["verdict"] = "adb_ready"
    elif res["fastboot_devices"]:
        res["verdict"] = "fastboot_mode"
    elif any(d["state"] == "unauthorized" for d in res["adb_devices"]):
        res["verdict"] = "unauthorized: unlock phone and accept RSA dialog"
    elif any(d["state"] == "offline" for d in res["adb_devices"]):
        res["verdict"] = "offline: adb kill-server, replug"
    elif res["usb"]:
        res["verdict"] = "usb_seen_but_no_adb: USB debugging off, charge-only cable/mode, or udev perms"
    else:
        res["verdict"] = "no_device: check cable (data), port, unlock screen"
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
