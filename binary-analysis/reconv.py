#!/usr/bin/env python3
"""
reconv.py - Portable reverse-engineering conversion utility.

Examples:
  ./reconv.py "/bin/bash"
  ./reconv.py "/bin/bash" --format hex
  ./reconv.py "/bin/bash" -o hex0x
  ./reconv.py 0x2f62696e2f62617368 -i hex -o text

  ./reconv.py "0x2f62696e2f62617368" --format text
  ./reconv.py "0x68732f6e69622f2f" --format text --little

Supported formats:
  text, hex, bytes, binary, octal, base64, int
"""

import argparse
import base64
import binascii
import re
import sys


def parse_hex(value):
    value = value.strip()
    value = re.sub(r"^0[xX]", "", value)
    value = re.sub(r"[\s:_-]", "", value)

    if not re.fullmatch(r"[0-9a-fA-F]+", value):
        raise ValueError("invalid hexadecimal value")

    if len(value) % 2:
        value = "0" + value

    return bytes.fromhex(value)


def parse_binary(value):
    value = re.sub(r"[\s_]", "", value)
    value = re.sub(r"^0[bB]", "", value)

    if not re.fullmatch(r"[01]+", value):
        raise ValueError("invalid binary value")

    if len(value) % 8:
        value = value.zfill((len(value) + 7) // 8 * 8)

    return int(value, 2).to_bytes(len(value) // 8, "big")


def parse_octal(value):
    value = re.sub(r"[\s_]", "", value)
    value = re.sub(r"^0[oO]", "", value)

    if not re.fullmatch(r"[0-7]+", value):
        raise ValueError("invalid octal value")

    n = int(value, 8)
    length = max(1, (n.bit_length() + 7) // 8)
    return n.to_bytes(length, "big")


def parse_base64(value):
    try:
        return base64.b64decode(value, validate=True)
    except Exception:
        raise ValueError("invalid Base64 value")


def format_output(data, fmt):
    if fmt == "text":
        return data.decode("utf-8", errors="replace")

    if fmt == "hex":
        return data.hex()

    if fmt == "hex0x":
        return "0x" + data.hex()

    if fmt == "bytes":
        return " ".join(f"{b:02x}" for b in data)

    if fmt == "binary":
        return " ".join(f"{b:08b}" for b in data)

    if fmt == "octal":
        return " ".join(f"{b:03o}" for b in data)

    if fmt == "base64":
        return base64.b64encode(data).decode()

    if fmt == "int-be":
        return str(int.from_bytes(data, "big", signed=False))

    if fmt == "int-le":
        return str(int.from_bytes(data, "little", signed=False))

    if fmt == "c-string":
        return '"' + "".join(
            f"\\x{b:02x}" if b < 32 or b >= 127 or b == 34 or b == 92
            else chr(b)
            for b in data
        ) + '"'

    if fmt == "python-bytes":
        return repr(data)

    raise ValueError(f"unknown output format: {fmt}")


def parse_input(value, fmt):
    if fmt == "text":
        return value.encode("utf-8")

    if fmt == "hex":
        return parse_hex(value)

    if fmt == "binary":
        return parse_binary(value)

    if fmt == "octal":
        return parse_octal(value)

    if fmt == "base64":
        return parse_base64(value)

    if fmt == "int":
        value = value.strip()
        base = 0 if value.lower().startswith(("0x", "0o", "0b")) else 10
        n = int(value, base)

        if n < 0:
            raise ValueError("negative integers are not supported")

        length = max(1, (n.bit_length() + 7) // 8)
        return n.to_bytes(length, "big")

    if fmt == "bytes":
        return parse_hex(value)

    raise ValueError(f"unknown input format: {fmt}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert values between common reverse-engineering formats."
    )

    parser.add_argument("value", help="value to convert")

    parser.add_argument(
        "-i", "--input",
        choices=["text", "hex", "bytes", "binary", "octal", "base64", "int"],
        default="text",
        help="input format (default: text)"
    )

    parser.add_argument(
        "-o", "--output",
        choices=[
            "text", "hex", "hex0x", "bytes", "binary",
            "octal", "base64", "int-be", "int-le",
            "c-string", "python-bytes"
        ],
        default="hex",
        help="output format (default: hex)"
    )

    parser.add_argument(
        "--little",
        action="store_true",
        help="reverse bytes before output"
    )

    args = parser.parse_args()

    try:
        data = parse_input(args.value, args.input)

        if args.little:
            data = data[::-1]

        print(format_output(data, args.output))

    except (ValueError, binascii.Error) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
