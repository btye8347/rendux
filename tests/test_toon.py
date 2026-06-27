from __future__ import annotations

import pytest

from rendux.core.toon import ToonFormatError, decode_toon, encode_toon


def test_encode_and_decode_roundtrip():
    data = [
        {"id": "1", "title": "Fix routing", "priority": "critical"},
        {"id": "2", "title": "Write mapper, test csv formatting", "priority": "high"},
    ]

    toon_str = encode_toon(data)
    assert "[2]{id,title,priority}:" in toon_str
    assert "1,Fix routing,critical" in toon_str
    assert '2,"Write mapper, test csv formatting",high' in toon_str

    decoded = decode_toon(toon_str)
    assert decoded == data


def test_encode_empty():
    assert encode_toon([]) == "[0]{}:"


def test_decode_empty():
    assert decode_toon("") == []
    assert decode_toon("[0]{}:") == []


def test_invalid_formats():
    with pytest.raises(ToonFormatError):
        encode_toon("invalid")

    with pytest.raises(ToonFormatError):
        decode_toon("invalid header shape")
