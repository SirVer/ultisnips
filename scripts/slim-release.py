#!/usr/bin/env python3
"""Build a slim release zip suitable for uploading to vim.org.

Downloads the GitHub auto-generated source zip for the given tag, strips
files that bloat the archive (GIFs under doc/), and repacks the result as
ultisnips-<tag>-vim.zip in the current directory. vim.org has an upload
size limit that the full repo zip exceeds; this script produces an
archive small enough to upload.

Usage: scripts/slim-release.py <tag>
  e.g. scripts/slim-release.py 4.0
"""

import argparse
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

REPO = "SirVer/ultisnips"
STRIP_SUFFIXES = {".gif"}


def download(url: str, dest: Path) -> None:
    print(f"Downloading {url}")
    with urllib.request.urlopen(url) as r, dest.open("wb") as f:
        shutil.copyfileobj(r, f)


def strip_and_repack(src_dir: Path, out: Path) -> None:
    stripped = 0
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src_dir.rglob("*")):
            if path.is_dir():
                continue
            if path.suffix.lower() in STRIP_SUFFIXES:
                print(f"  stripped {path.relative_to(src_dir.parent)}")
                stripped += 1
                continue
            zf.write(path, path.relative_to(src_dir.parent))
    print(f"Stripped {stripped} file(s)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tag", help="git tag to package, e.g. 4.0")
    args = parser.parse_args()

    tag = args.tag
    url = f"https://github.com/{REPO}/archive/refs/tags/{tag}.zip"
    out = Path.cwd() / f"ultisnips-{tag}-vim.zip"

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        src_zip = tmp / "src.zip"
        download(url, src_zip)

        with zipfile.ZipFile(src_zip) as zf:
            zf.extractall(tmp)

        # GitHub names the extracted directory ultisnips-<tag>.
        extracted = [p for p in tmp.iterdir() if p.is_dir()]
        if len(extracted) != 1:
            print(f"Expected one extracted dir, got {extracted}", file=sys.stderr)
            return 1

        if out.exists():
            out.unlink()
        strip_and_repack(extracted[0], out)

    print(f"Wrote {out} ({out.stat().st_size // 1024} K)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
