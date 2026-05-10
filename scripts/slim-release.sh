#!/usr/bin/env bash
#
# Build a slim release zip suitable for uploading to vim.org.
#
# Downloads the GitHub auto-generated source zip for the given tag, strips
# files that bloat the archive (GIFs under doc/), and repacks the result as
# ultisnips-<tag>-vim.zip in the current directory. vim.org has an upload
# size limit that the full repo zip exceeds; this script produces an archive
# small enough to upload.
#
# Usage: scripts/slim-release.sh <tag>
#   e.g. scripts/slim-release.sh 4.0
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <tag>" >&2
    exit 2
fi

tag="$1"
out="$(pwd)/ultisnips-${tag}-vim.zip"
url="https://github.com/SirVer/ultisnips/archive/refs/tags/${tag}.zip"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "Downloading ${url}"
curl -fSL "$url" -o "$tmp/src.zip"

echo "Unzipping"
unzip -q "$tmp/src.zip" -d "$tmp"

# GitHub names the extracted directory ultisnips-<tag>.
src_dir="$(find "$tmp" -mindepth 1 -maxdepth 1 -type d | head -n1)"
if [[ -z "$src_dir" ]]; then
    echo "Could not find extracted source directory" >&2
    exit 1
fi

echo "Stripping bloat from $src_dir"
find "$src_dir" -type f -name '*.gif' -print -delete

rm -f "$out"
(cd "$tmp" && zip -qr "$out" "$(basename "$src_dir")")

echo "Wrote $out"
ls -lh "$out"
