from __future__ import annotations

import csv
import io
import re
from typing import Any


class ToonFormatError(ValueError):
    """Raised when data violates TOON (Token-Oriented Object Notation) format rules."""
    pass


def encode_toon(data: Any) -> str:
    """Serialize a list of dicts to TOON format."""
    if not isinstance(data, list):
        if isinstance(data, dict):
            data = [data]
        else:
            raise ToonFormatError("Data must be a list of dictionaries or a single dictionary.")

    if not data:
        return "[0]{}:"

    first_item = data[0]
    if not isinstance(first_item, dict):
        raise ToonFormatError("List items must be dictionaries.")

    keys = list(first_item.keys())
    if not keys:
        return f"[{len(data)}]{{}}:"

    keys_str = ",".join(keys)
    header = f"[{len(data)}]{{{keys_str}}}:\n"

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    for item in data:
        if not isinstance(item, dict):
            raise ToonFormatError("All list items must be dictionaries.")
        row = [str(item.get(key, "")) for key in keys]
        writer.writerow(row)

    return header + output.getvalue().strip()


def decode_toon(toon_str: str) -> list[dict[str, Any]]:
    """Deserialize a TOON string back to a list of dicts."""
    toon_str = toon_str.strip()
    if not toon_str:
        return []

    match = re.match(r"^\[(\d+)\]\{([^}]*)\}:\s*(.*)$", toon_str, re.DOTALL)
    if not match:
        raise ToonFormatError("Invalid TOON header. Expected: '[count]{key1,key2}:\\nvalues'")

    count_str, keys_str, body = match.groups()
    count = int(count_str)
    keys = [k.strip() for k in keys_str.split(",") if k.strip()]

    if count == 0 or not keys:
        return []

    input_data = io.StringIO(body)
    reader = csv.reader(input_data)

    items = []
    for row in reader:
        if not row:
            continue
        item = {keys[idx]: (row[idx] if idx < len(row) else "") for idx in range(len(keys))}
        items.append(item)

    return items
