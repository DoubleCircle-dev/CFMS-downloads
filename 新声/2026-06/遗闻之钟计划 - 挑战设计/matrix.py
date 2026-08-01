from __future__ import annotations

from ipaddress import IPv4Address
from random import Random
import secrets
from typing import Sequence
import pprint

WEIGHTS = (1, 3, 7, 9)


def layer_path(
    maps: int,
    size: int,
    kernel: int,
    count: int,
    *,
    partial: bool = False,
) -> list[int]:
    """Return zero-based matrix columns for one layer."""
    start = (maps - 1) % 7
    direction = 1 if size % 2 == 0 else -1

    cycle = [(start + direction * index * kernel) % 7 for index in range(7)]

    if partial:
        return [cycle[index] for index in (0, 2, 4)]

    return cycle[:count]


PATHS = (
    layer_path(6, 28, 5, 3),  # C1
    layer_path(6, 14, 2, 3),  # S2
    layer_path(16, 10, 5, 3, partial=True),  # C3
    layer_path(16, 5, 2, 3),  # S4
    layer_path(120, 1, 5, 5),  # C5
)


def checksum_digit(payload: str) -> int:
    """Calculate the decimal checksum class."""
    total = sum(
        int(digit) * WEIGHTS[index % len(WEIGHTS)]
        for index, digit in enumerate(payload)
    )
    return (-total) % 10


def hamming74(value: int) -> list[int]:
    """Encode a decimal digit as a systematic Hamming(7,4) word."""
    if not 0 <= value <= 9:
        raise ValueError("RBF class must be between 0 and 9")

    d1 = (value >> 3) & 1
    d2 = (value >> 2) & 1
    d3 = (value >> 1) & 1
    d4 = value & 1

    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4

    return [p1, p2, d1, p3, d2, d3, d4]


RBF_CODES = tuple(hamming74(value) for value in range(10))


def encode(
    ip: str,
    port: int,
    *,
    revision: int = 1,
    decoy_key: str = "726791",
) -> list[list[int]]:
    """Generate a 7×7 puzzle matrix."""
    octets = list(IPv4Address(ip).packed)

    if not 0 <= port <= 65_535:
        raise ValueError("Port must fit in five decimal digits")

    fields = [
        *(f"{octet:03d}" for octet in octets),
        f"{port:05d}",
    ]
    payload = "".join(fields)

    # The random values are only decoys, not cryptographic material.
    random = Random(f"{decoy_key}|{revision}|{ip}|{port}")
    matrix = [[random.randrange(10) for _ in range(7)] for _ in range(7)]

    for row, (columns, field) in enumerate(zip(PATHS, fields)):
        for column, digit in zip(columns, field):
            matrix[row][column] = int(digit)

    check = checksum_digit(payload)

    # F6
    matrix[5] = hamming74(check)

    # RBF: 10 maps to one-based column 3.
    matrix[6][(10 - 1) % 7] = check

    return matrix


def decode(matrix: Sequence[Sequence[int]]) -> dict[str, object]:
    """Decode and validate a puzzle matrix."""
    if len(matrix) != 7 or any(len(row) != 7 for row in matrix):
        raise ValueError("Matrix must be exactly 7×7")

    fields = [
        "".join(str(matrix[row][column]) for column in columns)
        for row, columns in enumerate(PATHS)
    ]

    octets = [int(field) for field in fields[:4]]
    port = int(fields[4])
    payload = "".join(fields)

    expected_check = checksum_digit(payload)

    f6 = list(matrix[5])
    if any(bit not in (0, 1) for bit in f6):
        raise ValueError("F6 row must contain only zeroes and ones")

    distances = [
        sum(actual != target for actual, target in zip(f6, code)) for code in RBF_CODES
    ]
    nearest_distance = min(distances)
    nearest_classes = [
        value
        for value, distance in enumerate(distances)
        if distance == nearest_distance
    ]

    rbf_class = nearest_classes[0] if len(nearest_classes) == 1 else None
    stored_class = matrix[6][(10 - 1) % 7]

    ranges_valid = all(0 <= octet <= 255 for octet in octets) and 0 <= port <= 65_535
    checksum_valid = rbf_class == expected_check and stored_class == expected_check

    return {
        "endpoint": f"{'.'.join(map(str, octets))}:{port}",
        "octets": octets,
        "port": port,
        "checksum": expected_check,
        "rbf_class": rbf_class,
        "rbf_distance": nearest_distance,
        "valid": ranges_valid and checksum_valid,
    }


def transpose_matrix(matrix: list[list[int]]) -> list[list[int]]:
    """Transpose a square matrix."""
    if not matrix or any(len(row) != len(matrix) for row in matrix):
        raise ValueError("Matrix must be non-empty and square")

    return [list(column) for column in zip(*matrix)]


if __name__ == "__main__":
    original = encode("127.0.0.1", 7573, decoy_key=secrets.token_hex(16))
    matrix = transpose_matrix(original)
    pprint.pprint(matrix)
    pprint.pprint(decode(original))
