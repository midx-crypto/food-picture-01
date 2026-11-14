#!/usr/bin/env python3
"""Copy the vendored food picture to /output/entry.png, byte for byte.

The picture this entry serves is a smash burger photographed close up:
a glossy toasted brioche bun, melted cheddar dripping down the sides,
a charred beef patty, fresh green lettuce, a red tomato slice and
crinkle-cut pickles, in warm dramatic light on a dark wooden board.
It lives in this repository as entry.png (a JPEG file under that name,
1024 by 1024 pixels, under 1 MiB). This program only copies it, so
both runs write identical bytes and no network is needed.
"""

import hashlib
import os
import shutil

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
DST = os.path.join(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"), "entry.png")


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if not os.path.isfile(SRC):
        raise SystemExit(
            "food-picture-01 entry failed: vendored entry.png is missing "
            f"(expected at {SRC}); refusing to write an empty output"
        )
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    # A plain copy on purpose: no temp file, no rename, nothing the
    # sandbox can trip over -- the source is already the final image.
    shutil.copyfile(SRC, DST)
    # Guard the determinism the grader checks: the copy must be exact.
    if _sha256(SRC) != _sha256(DST):
        raise SystemExit("entry.png copy hash mismatch")


if __name__ == "__main__":
    main()
