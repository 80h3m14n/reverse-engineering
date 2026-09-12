#!/usr/bin/env python3

"""
hexview.py - Small portable value/byte conversion utility.

This version handles common representations: hex, bytes, ASCII/UTF-8, integers, binary, octal, Base64, and both endian orders.

Examples:
  python3 hexview.py 0x68732f6e69622f2f
  python3 hexview.py 68732f6e69622f2f --little
  python3 hexview.py 41424344

TODO: add support for signed integers, 16/32/64-bit integer widths, IEEE-754 floats/doubles, UTF-16/UTF-32, escaped C/Python strings, and hexdump-style output.
"""

import argparse
import base64
import binascii
import re
import sys


def clean_hex(s):
    """Accept 0x1234, 12 34, 12:34, or 12-34."""
    s = s.strip()
    s = re.sub(r"^0[xX]", "", s)
    s = re.sub(r"[\s:_-]", "", s)

    if not re.fullmatch(r"[0-9a-fA-F]+", s):
        raise ValueError("not a valid hexadecimal value")

    if len(s) % 2:
        s = "0" + s

    return s.lower()


def printable_ascii(data):
    return "".join(chr(b) if 32 <= b < 127 else "." for b in data)


def show(data, label):
    print(f"\n[{label}]")
    print(f"Hex       : {data.hex()}")
    print(f"Hex (0x)  : 0x{data.hex()}")
    print(f"Bytes     : {' '.join(f'{b:02x}' for b in data)}")
    print(f"ASCII     : {printable_ascii(data)}")

    try:
        print(f"UTF-8     : {data.decode('utf-8')}")
    except UnicodeDecodeError:
        print("UTF-8     : <invalid UTF-8>")

    print(f"Binary    : {' '.join(f'{b:08b}' for b in data)}")
    print(f"Octal     : {' '.join(f'{b:03o}' for b in data)}")
    print(f"Base64    : {base64.b64encode(data).decode()}")

    # Interpret bytes as unsigned integers.
    print(f"uint BE   : {int.from_bytes(data, 'big')}")
    print(f"uint LE   : {int.from_bytes(data, 'little')}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert hexadecimal values into common reverse-engineering formats."
    )

    parser.add_argument(
        "value",
        help="hex value, e.g. 0x68732f6e69622f2f"
    )

    parser.add_argument(
        "--little",
        action="store_true",
        help="also display the bytes reversed (little-endian interpretation)"
    )

    args = parser.parse_args()

    try:
        h = clean_hex(args.value)
        data = bytes.fromhex(h)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    # Original byte sequence.
    show(data, "Original byte sequence")

    # Reversed byte sequence.
    if args.little:
        show(data[::-1], "Reversed byte sequence")


if __name__ == "__main__":
    main()
