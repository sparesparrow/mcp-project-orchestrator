#!/usr/bin/env bash
# Download the latest official Magisk APK (HTTPS, github.com/topjohnwu/Magisk) into a fresh temp dir and print its sha256.
# Never installs. Usage: fetch_magisk.sh [--dry-run]
set -euo pipefail
api="https://api.github.com/repos/topjohnwu/Magisk/releases/latest"
meta=$(curl -fsSL "$api")
url=$(printf '%s' "$meta" | python3 -I -c 'import json,sys
d=json.load(sys.stdin)
print(next(a["browser_download_url"] for a in d["assets"] if a["name"].endswith(".apk") and a["name"].lower().startswith("magisk")))')
tag=$(printf '%s' "$meta" | python3 -I -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])')
case "$url" in https://github.com/topjohnwu/Magisk/releases/*) ;; *) echo "unexpected URL: $url" >&2; exit 1;; esac
echo "release: $tag"; echo "url: $url"
[ "${1:-}" = "--dry-run" ] && exit 0
dir=$(mktemp -d)
curl -fsSL -o "$dir/Magisk-$tag.apk" "$url"
file "$dir/Magisk-$tag.apk"
sha256sum "$dir/Magisk-$tag.apk"
echo "saved: $dir/Magisk-$tag.apk  (install with: adb install <path> after user confirmation)"
