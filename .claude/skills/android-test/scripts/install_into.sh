#!/usr/bin/env bash
# Vendor the android-test skill into an Android project so it works for anyone who clones it.
#
#   install_into.sh REPO_DIR --profile NAME [--android-dir DIR] [--no-workflow]
#
# - copies this skill to REPO_DIR/.claude/skills/android-test (scripts, references, profiles)
# - requires profiles/NAME.env to exist (copy profiles/template.env first)
# - unless --no-workflow or the repo already has .github/workflows/device-apks.yml, writes
#   .github/workflows/device-apks.yml from references/device-apks.yml with --android-dir
#   (the directory holding gradlew, default "."; use "." not "./")
# Never commits or pushes; review `git status` in REPO_DIR afterwards.
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
repo="${1:-}"; shift || true
profile="" adir="." wf=1
while [ $# -gt 0 ]; do
  case "$1" in
    --profile) profile=$2; shift 2;; --android-dir) adir=$2; shift 2;; --no-workflow) wf=0; shift;;
    -h|--help) sed -n '2,12p' "$0"; exit 0;; *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done
[ -d "$repo/.git" ] || { echo "REPO_DIR must be a git checkout" >&2; exit 2; }
[ -f "$here/profiles/$profile.env" ] || { echo "no profile '$profile' in $here/profiles" >&2; exit 2; }
[ -f "$repo/$adir/gradlew" ] || echo "warning: $repo/$adir/gradlew not found; the workflow will generate a wrapper (commit one for reproducible builds)" >&2

dest="$repo/.claude/skills/android-test"
if [ "$(realpath "$here")" = "$(realpath -m "$dest")" ]; then echo "source and destination are the same" >&2; exit 2; fi
mkdir -p "$dest"
cp -r "$here/SKILL.md" "$here/scripts" "$here/references" "$dest/"
mkdir -p "$dest/profiles"
cp "$here/profiles/$profile.env" "$here/profiles/template.env" "$dest/profiles/"
chmod +x "$dest"/scripts/*.sh
echo "skill vendored: $dest (profile $profile)"

if [ "$wf" = 1 ]; then
  out="$repo/.github/workflows/device-apks.yml"
  if [ -e "$out" ]; then echo "kept existing $out"
  else
    mkdir -p "$(dirname "$out")"
    prefix=""; [ "$adir" = "." ] || prefix="${adir%/}/"
    sed -e "s#__ANDROID_DIR__#$adir#g" -e "s#__ANDROID_PREFIX__#$prefix#g" "$here/references/device-apks.yml" >"$out"
    echo "wrote $out"
  fi
fi
