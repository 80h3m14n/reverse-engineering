#!/usr/bin/env python3

"""
hex-to-bin.py - Convert hexadecimal or bitstream text to binary data.

Originally written by Didier Stevens.
Original source: https://DidierStevens.com
Original code was released into the public domain.

Python 3 modernization:
- Removed all Python 2 compatibility code.
- Replaced optparse with argparse.
- Uses pathlib for file handling.
- Uses native Python 3 bytes handling.
- Improved command-line help.
- Improved error handling and option validation.

Practical use cases:
- reconstructing a binary from textual evidence.

NOTE:
Tools like xxd already provide the functionality of this script i.e

# Binary → hex
xxd input.bin > output.hex

# Hex → binary
xxd -r output.hex > output.bin

The reason to retain this script is its dump extraction capabilities (-a and -x). Those are more specialized than xxd -r.
"""

from __future__ import annotations

import argparse
import binascii
import codecs
import signal
import sys
from io import BytesIO
from pathlib import Path


__description__ = "Convert hexadecimal or bitstream text to binary data."
__author__ = "Didier Stevens"
__version__ = "1.0.0"
__date__ = "2026/09/15"


MANUAL = r"""
HEX-TO-BIN
==========

Convert hexadecimal text or a stream of 0s and 1s into binary data.

INPUT
-----

By default, the program expects hexadecimal data.

For example:

    4D 5A 90 00

Whitespace is ignored, so this is equivalent:

    4D5A9000

Input can be read from a file or from standard input.

EXAMPLES
--------

Convert a hexadecimal file to binary:

    hex-to-bin.py input.txt > output.bin

Convert hexadecimal text from standard input:

    echo "4D 5A 90 00" | python hex-to-bin.py > output.bin

Extract a Didier Stevens Hex/ASCII dump:

    python hex-to-bin.py -a dump.txt > output.bin

Extract a generic hexadecimal dump:

    python hex-to-bin.py -x dump.txt > output.bin

List available Didier Stevens dumps:

    python hex-to-bin.py -l dump.txt

List generic hexadecimal dumps:

    python hex-to-bin.py -x -l dump.txt

Select the second dump:

    python hex-to-bin.py -x -s 2 dump.txt > output.bin

Process a bitstream:

    echo "01001000 01101001" | hex-to-bin.py -b

Keep only hexadecimal characters:

    echo "Data: 4D 5A 90 00" | hex-to-bin.py -H > output.bin

Accept only uppercase hexadecimal characters:

    echo "DATA: 4D 5A" | hex-to-bin.py -H --upperonly > output.bin

Accept only lowercase hexadecimal characters:

    echo "data: 4d 5a" | hex-to-bin.py -H --loweronly > output.bin

Decode UTF-16 input before processing:

    hex-to-bin.py -t utf-16 input.txt > output.bin


DIDIER STEVENS HEX/ASCII DUMPS
------------------------------

With -a/--asciidump, the program searches for dumps beginning with:

    00000000:

For example:

    00000000: 4D 5A 90 00 03 00 00 00  04 00 00 00 FF FF 00 00
    00000010: B8 00 00 00 00 00 00 00  40 00 00 00 00 00 00 00

Use -s to select a particular dump when several dumps are present.


GENERIC HEX DUMPS
-----------------

With -x/--hexdump, the program searches for hexadecimal dumps produced
by other tools.

A hexadecimal dump must contain at least 16 consecutive hexadecimal
bytes to be recognized.

Use -l/--list together with -x to display all detected dumps.


BITSTREAM MODE
--------------

With -b/--bitstream, the input is interpreted as a sequence of 0 and 1
characters.

Every group of 8 bits is converted to one byte.

The left-most bit is the most significant bit.

If the number of bits is not divisible by 8, the final byte is padded
on the right with zero bits.

For example:

    01001000 01101001

becomes:

    Hi


HEX-ONLY MODE
-------------

With -H/--hexonly, every character that is not a hexadecimal digit is
discarded.

By default both uppercase and lowercase hexadecimal letters are
accepted.

Use --upperonly to accept only uppercase hexadecimal letters.

Use --loweronly to accept only lowercase hexadecimal letters.


TEXT TRANSLATION
----------------

The -t/--translate option decodes text using a Python codec before the
hexadecimal data is processed.

For example:

    python hex-to-bin.py -t utf-16 input.txt > output.bin

Common values include:

    utf-8
    utf-16
    utf-16-le
    utf-16-be
    latin-1
    ascii


ERROR HANDLING
--------------

Invalid hexadecimal characters cause an error.

The offending characters and their hexadecimal values are displayed
on standard error.

Binary output is written to standard output.

This means it is safe to redirect the output to a file:

    python hex-to-bin.py input.txt > output.bin
"""


def print_manual() -> None:
    """Print the detailed program manual."""
    print(MANUAL.strip())


def fix_pipe() -> None:
    """Use the default SIGPIPE behavior where supported."""
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (AttributeError, ValueError):
        pass


def stdout_write_chunked(data: bytes) -> None:
    """
    Write binary data to stdout.

    stdout.buffer is used because the program produces binary output.
    """
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def file_to_bytes(filename: str) -> bytes:
    """Read a file as bytes."""
    try:
        return Path(filename).read_bytes()
    except OSError as exc:
        raise SystemExit(
            f"Error: unable to read '{filename}': {exc}"
        ) from exc


def find_begin_hex_ascii_dump(data: bytes) -> list[int]:
    """
    Find the beginning of Didier Stevens Hex/ASCII dumps.

    A dump begins with '00000000: ' at the beginning of a line.
    """
    positions: list[int] = []
    marker = b"00000000: "
    position = 0

    while True:
        position = data.find(marker, position)

        if position == -1:
            break

        if position == 0 or data[position - 1] == ord("\n"):
            positions.append(position)

        position += 1

    return positions


def extract_hex_ascii_dump(data: bytes, select: int) -> bytes:
    """
    Extract a selected Didier Stevens Hex/ASCII dump.

    The hexadecimal portion occupies 48 characters after the colon.
    """
    position_colon = 8
    length_hexadecimal = 48

    positions = find_begin_hex_ascii_dump(data)

    if not positions:
        return b""

    if select < 1 or select > len(positions):
        raise ValueError(
            f"Dump number {select} does not exist. "
            f"Found {len(positions)} dump(s)."
        )

    result = bytearray()

    selected_data = data[positions[select - 1]:]

    for line in selected_data.splitlines():
        line = line.strip()

        if len(line) <= position_colon:
            break

        if line[position_colon:position_colon + 1] == b":":
            start = position_colon + 2

            result.extend(
                line[start:start + length_hexadecimal]
            )
            result.extend(b"\n")
        else:
            break

    return bytes(result)


def is_relevant(item: bytes) -> bool:
    """
    Determine whether an item contains a letter or digit.

    This preserves the behavior of the original script when detecting
    possible hexadecimal dump fields.
    """
    if not item:
        return False

    for char in item:
        character = chr(char)

        if character.lower() in "abcdefghijklmnopqrstuvwxyz":
            return True

        if character in "0123456789":
            return True

    return False


def is_hex_byte(item: bytes) -> bool:
    """Return True if item consists of exactly two hex characters."""
    if len(item) != 2:
        return False

    try:
        int(item, 16)
        return True
    except ValueError:
        return False


def extract_contiguous_hex_bytes(line: bytes) -> list[bytes]:
    """
    Extract contiguous two-character hexadecimal bytes from a line.
    """
    line = line.rstrip(b"\r\n")

    line = (
        line
        .replace(b"\t", b" ")
        .replace(b",", b" ")
        .replace(b":", b" ")
    )

    items = [
        item
        for item in line.split()
        if is_relevant(item)
    ]

    result: list[bytes] = []

    for item in items:
        if is_hex_byte(item):
            result.append(item)
        elif result:
            return result

    return result


def hex_dump_extract_or_produce_list(
    data: bytes,
    select: int,
    produce_list: bool,
) -> bytes:
    """
    Extract or list generic hexadecimal dumps.

    A dump begins when a line contains at least 16 hexadecimal bytes.
    """
    hexdump = bytearray()
    counter = 0

    for line in data.split(b"\n"):
        result = extract_contiguous_hex_bytes(line)

        if hexdump:
            if not result:
                if counter == select and not produce_list:
                    return bytes(hexdump)

                hexdump = bytearray()
            else:
                hexdump.extend(b"".join(result))

        elif len(result) >= 16:
            counter += 1

            if produce_list:
                display_line = line.decode(
                    "ascii",
                    errors="replace",
                )
                print(f"{counter}: {display_line}")

            hexdump.extend(b"".join(result))

    return bytes(hexdump)


def list_hex_ascii_dumps(data: bytes) -> None:
    """List all Didier Stevens Hex/ASCII dumps."""
    positions = find_begin_hex_ascii_dump(data)

    if not positions:
        print("No Didier Stevens Hex/ASCII dumps found.")
        return

    for index, position in enumerate(positions, start=1):
        first_line = data[position:].split(b"\n", 1)[0]

        display_line = first_line.decode(
            "ascii",
            errors="replace",
        )

        print(f"{index}: {display_line}")


def translate(data: bytes, expression: str) -> bytes:
    """
    Decode input using a named Python codec.

    For compatibility with the original script, expressions beginning
    with '.' are also supported, for example:

        .decode("utf8")

    Named codecs are preferred.
    """
    try:
        codecs.lookup(expression)

        decoded = data.decode(expression)

        return decoded.encode()

    except LookupError:
        pass

    if not expression.startswith("."):
        raise ValueError(
            f"Unknown encoding: {expression!r}"
        )

    try:
        result = eval(
            f"data{expression}",
            {"data": data},
        )
    except Exception as exc:
        raise ValueError(
            f"Unable to apply translation "
            f"{expression!r}: {exc}"
        ) from exc

    if isinstance(result, str):
        return result.encode()

    if isinstance(result, bytes):
        return result

    raise ValueError(
        f"Translation returned unsupported type: "
        f"{type(result).__name__}"
    )


def decode_bitstream(bitstream: bytes) -> bytes:
    """
    Convert a stream of 0 and 1 characters into binary bytes.

    The final byte is padded on the right with zero bits when necessary.
    """
    invalid = set(bitstream) - {
        ord("0"),
        ord("1"),
    }

    if invalid:
        invalid_display = ", ".join(
            f"{chr(value)!r} (0x{value:02x})"
            for value in sorted(invalid)
        )

        raise ValueError(
            "Bitstream contains invalid characters: "
            + invalid_display
        )

    padding = (8 - len(bitstream) % 8) % 8
    bitstream += b"0" * padding

    output = BytesIO()

    for position in range(0, len(bitstream), 8):
        byte = bitstream[position:position + 8]
        value = int(byte, 2)

        output.write(bytes([value]))

    return output.getvalue()


def filter_hex_characters(
    content: bytes,
    upper_only: bool = False,
    lower_only: bool = False,
) -> bytes:
    """Keep only valid hexadecimal characters."""
    if upper_only:
        valid = b"0123456789ABCDEF"
    elif lower_only:
        valid = b"0123456789abcdef"
    else:
        valid = b"0123456789abcdefABCDEF"

    valid_set = set(valid)

    return bytes(
        char
        for char in content
        if char in valid_set
    )


def remove_whitespace(content: bytes) -> bytes:
    """
    Remove whitespace characters handled by the original program.

    Spaces, tabs, carriage returns, and newlines are ignored.
    """
    return (
        content
        .replace(b" ", b"")
        .replace(b"\t", b"")
        .replace(b"\r", b"")
        .replace(b"\n", b"")
    )


def report_invalid_hex(data: bytes) -> None:
    """Report non-hexadecimal characters found in input."""
    valid = set(b"0123456789abcdefABCDEF")
    reported: set[int] = set()

    print(
        "Error: the following non-hexadecimal "
        "characters were found:",
        file=sys.stderr,
    )

    for value in data:
        if value in valid or value in reported:
            continue

        reported.add(value)

        character = chr(value)

        print(
            f"  {character!r} (0x{value:02x})",
            file=sys.stderr,
        )


def hex_to_bin(
    filename: str,
    options: argparse.Namespace,
) -> None:
    """Read, process, convert, and output the input."""
    fix_pipe()

    if filename:
        content = file_to_bytes(filename)
    else:
        content = sys.stdin.buffer.read()

    # Translate/decode the input if requested.
    if options.translate:
        try:
            content = translate(
                content,
                options.translate,
            )
        except ValueError as exc:
            raise SystemExit(
                f"Error: {exc}"
            ) from exc

    # Listing mode does not produce binary output.
    if options.list:
        if options.hexdump:
            hex_dump_extract_or_produce_list(
                content,
                options.select,
                True,
            )
        else:
            list_hex_ascii_dumps(content)

        return

    # Extract a Didier Stevens Hex/ASCII dump.
    if options.asciidump:
        try:
            content = extract_hex_ascii_dump(
                content,
                options.select,
            )
        except ValueError as exc:
            raise SystemExit(
                f"Error: {exc}"
            ) from exc

        if not content:
            raise SystemExit(
                "Error: no Didier Stevens "
                "Hex/ASCII dump was found."
            )

    # Extract a generic hexadecimal dump.
    elif options.hexdump:
        content = hex_dump_extract_or_produce_list(
            content,
            options.select,
            False,
        )

        if not content:
            raise SystemExit(
                "Error: no suitable hexadecimal dump "
                "was found."
            )

    # Prepare input for conversion.
    if options.hexonly:
        content = filter_hex_characters(
            content,
            upper_only=options.upperonly,
            lower_only=options.loweronly,
        )
    else:
        content = remove_whitespace(content)

    # Convert bitstream.
    if options.bitstream:
        try:
            data = decode_bitstream(content)
        except ValueError as exc:
            raise SystemExit(
                f"Error: {exc}"
            ) from exc

    # Convert hexadecimal.
    else:
        try:
            data = binascii.unhexlify(content)
        except binascii.Error:
            report_invalid_hex(content)
            raise SystemExit(1)

    stdout_write_chunked(data)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="hex-to-bin.py",
        description=(
            "Convert hexadecimal text or a bitstream "
            "into binary data."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python %(prog)s input.txt > output.bin
  echo "4D 5A 90 00" | %(prog)s > output.bin
  python %(prog)s -a dump.txt > output.bin
  python %(prog)s -x dump.txt > output.bin
  python %(prog)s -x -s 2 dump.txt > output.bin
  python %(prog)s -x -l dump.txt
  echo "01001000 01101001" | python %(prog)s -b
  echo "Data: 4D 5A" | python %(prog)s -H > output.bin

Use --manual for a detailed explanation of every mode.
""",
    )

    parser.add_argument(
        "file",
        nargs="?",
        metavar="FILE",
        help=(
            "Input file. If FILE is omitted, "
            "read from standard input."
        ),
    )

    parser.add_argument(
        "-a",
        "--asciidump",
        action="store_true",
        help=(
            "Extract a Didier Stevens Hex/ASCII dump "
            "before converting it."
        ),
    )

    parser.add_argument(
        "-x",
        "--hexdump",
        action="store_true",
        help=(
            "Find and extract a generic hexadecimal dump. "
            "A dump must contain at least 16 hex bytes."
        ),
    )

    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help=(
            "List detected dumps instead of converting them. "
            "Use with -x for generic hex dumps."
        ),
    )

    parser.add_argument(
        "-s",
        "--select",
        type=int,
        default=1,
        metavar="N",
        help=(
            "Select dump number N for extraction "
            "(default: 1)."
        ),
    )

    parser.add_argument(
        "-t",
        "--translate",
        metavar="ENCODING",
        help=(
            "Decode input with ENCODING before processing, "
            "for example utf-16 or utf-8."
        ),
    )

    parser.add_argument(
        "-b",
        "--bitstream",
        action="store_true",
        help=(
            "Treat input as 0/1 bits instead of hexadecimal. "
            "Incomplete final bytes are padded with zero bits."
        ),
    )

    parser.add_argument(
        "-H",
        "--hexonly",
        action="store_true",
        help=(
            "Ignore all input characters except hexadecimal digits."
        ),
    )

    parser.add_argument(
        "--upperonly",
        action="store_true",
        help=(
            "With -H, accept only uppercase A-F "
            "(digits are still accepted)."
        ),
    )

    parser.add_argument(
        "--loweronly",
        action="store_true",
        help=(
            "With -H, accept only lowercase a-f "
            "(digits are still accepted)."
        ),
    )

    parser.add_argument(
        "-m",
        "--manual",
        action="store_true",
        help="Display the detailed manual.",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__} ({__date__})",
    )

    return parser


def validate_options(
    options: argparse.Namespace,
) -> None:
    """Validate command-line option combinations."""
    if options.select < 1:
        raise SystemExit(
            "Error: --select must be 1 or greater."
        )

    if options.upperonly and options.loweronly:
        raise SystemExit(
            "Error: --upperonly and --loweronly "
            "cannot be used together."
        )

    if (
        options.upperonly or options.loweronly
    ) and not options.hexonly:
        raise SystemExit(
            "Error: --upperonly and --loweronly "
            "require -H/--hexonly."
        )

    if options.asciidump and options.hexdump:
        raise SystemExit(
            "Error: --asciidump and --hexdump "
            "cannot be used together."
        )

    if options.bitstream and options.hexdump:
        raise SystemExit(
            "Error: --bitstream cannot be combined "
            "with --hexdump."
        )

    if options.bitstream and options.asciidump:
        raise SystemExit(
            "Error: --bitstream cannot be combined "
            "with --asciidump."
        )


def main() -> None:
    """Program entry point."""
    parser = build_parser()
    options = parser.parse_args()

    if options.manual:
        print_manual()
        return

    validate_options(options)

    try:
        hex_to_bin(
            options.file or "",
            options,
        )
    except BrokenPipeError:
        # Normal when stdout is piped into a program such as
        # head which closes the pipe before all output is written.
        pass


if __name__ == "__main__":
    main()
