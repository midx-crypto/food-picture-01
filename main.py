#!/usr/bin/env python3
"""Write the vendored food picture to /output/entry.png, byte for byte.

The picture this entry serves is a smash burger photographed close up:
a glossy toasted brioche bun, melted cheddar dripping down the sides,
a charred beef patty, fresh green lettuce, a red tomato slice and
crinkle-cut pickles, in warm dramatic light on a dark wooden board.
It lives in this repository as entry.png (a JPEG file under that name,
1024 by 1024 pixels, under 1 MiB).

The program does nothing but copy that file. It never touches the
network and never edits a pixel, so the two runs the grader performs
write exactly the same bytes. The copy is written to a temporary file
in the destination directory first and then moved into place, so a
run that is interrupted can never leave a half-written entry.png
behind; after the move the program re-reads both files and refuses
to exit cleanly unless their hashes match.
"""

import argparse
import hashlib
import os
import sys
import tempfile

IMAGE_NAME = "entry.png"
JPEG_MAGIC = b"\xff\xd8\xff"
MAX_BYTES = 1_048_576
CHUNK_SIZE = 65_536


def source_path() -> str:
    """Absolute path of the vendored image next to this file."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, IMAGE_NAME)


def destination_dir(argv: argparse.Namespace) -> str:
    """Where the entry goes: flag first, then env, then /output."""
    if argv.output_dir:
        return argv.output_dir
    return os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")


def fail(message: str) -> "SystemExit":
    """A clean failure: one line on stderr, exit code 1."""
    return SystemExit(f"food-picture-01 entry failed: {message}")


def sha256_file(path: str) -> str:
    """Hex SHA-256 of a file, streamed in chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def check_source(path: str) -> int:
    """Sanity-check the vendored image before copying it.

    Returns the file size. The file must exist, be a JPEG (the gate
    tells the format from its first bytes), and fit the 1 MiB cap.
    """
    if not os.path.isfile(path):
        raise fail(
            f"vendored {IMAGE_NAME} is missing (expected at {path}); "
            "refusing to write an empty output"
        )
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        raise fail(
            f"vendored {IMAGE_NAME} is {size} bytes, over the "
            f"{MAX_BYTES} byte cap; refusing to copy it"
        )
    with open(path, "rb") as handle:
        head = handle.read(len(JPEG_MAGIC))
    if head != JPEG_MAGIC:
        raise fail(
            f"vendored {IMAGE_NAME} does not start with the JPEG magic "
            "bytes; refusing to copy a file the gate would reject"
        )
    return size


def copy_atomic(src: str, dst: str) -> None:
    """Copy src to dst via a temp file in the destination directory.

    The temp file is flushed and synced, then renamed over dst in one
    step, so dst is either the old file or the complete new one.
    """
    directory = os.path.dirname(dst)
    os.makedirs(directory, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".entry-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as out:
            with open(src, "rb") as handle:
                while True:
                    chunk = handle.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    out.write(chunk)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp_path, dst)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def verify_copy(src: str, dst: str) -> None:
    """Re-read both files and demand identical hashes."""
    if not os.path.isfile(dst):
        raise fail(f"output {dst} is missing after the copy")
    if sha256_file(src) != sha256_file(dst):
        raise fail("output hash does not match the vendored image")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Command line: --output-dir and a read-only --verify mode."""
    parser = argparse.ArgumentParser(
        description="Copy the vendored food picture to the output directory."
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="destination directory (default: $MAKEFUN_OUTPUT_DIR or /output)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="only check that the existing output matches the source",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    src = source_path()
    dst = os.path.join(destination_dir(args), IMAGE_NAME)
    size = check_source(src)
    if args.verify:
        verify_copy(src, dst)
        print(f"verified: {dst} matches the vendored image ({size} bytes)")
        return 0
    copy_atomic(src, dst)
    verify_copy(src, dst)
    print(f"wrote {dst} ({size} bytes, sha256 {sha256_file(dst)[:16]}...)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
