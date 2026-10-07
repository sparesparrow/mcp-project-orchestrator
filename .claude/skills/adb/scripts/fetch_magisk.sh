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
want=$(printf '%s' "$meta" | python3 -I -c 'import json,sys
d=json.load(sys.stdin)
a=next(a for a in d["assets"] if a["name"].endswith(".apk") and a["name"].lower().startswith("magisk"))
print((a.get("digest") or "").removeprefix("sha256:"))')
got=$(sha256sum "$dir/Magisk-$tag.apk" | cut -d' ' -f1)
if [ -n "$want" ] && [ "$want" != "$got" ]; then echo "REFUSED: sha256 $got does not match the release digest $want" >&2; exit 1; fi
[ -n "$want" ] && echo "sha256 matches the GitHub release digest" || echo "WARNING: release has no digest; verify the hash another way" >&2
sha256sum "$dir/Magisk-$tag.apk"
echo "saved: $dir/Magisk-$tag.apk  (install with: adb install <path> after user confirmation)"
