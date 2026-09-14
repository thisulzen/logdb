import pytest

from logdb.record import CorruptRecord, deserialize, serialize


def roundtrip(key: bytes, value: bytes):
    return deserialize(serialize(key, value))


def test_simple_pair():
    assert roundtrip(b"name", b"Alice") == (b"name", b"Alice")


def test_empty_value():
    # A key set to nothing is different from a key that was never set.
    assert roundtrip(b"name", b"") == (b"name", b"")


def test_empty_key():
    assert roundtrip(b"", b"Alice") == (b"", b"Alice")


def test_utf8_bytes():
    # 6 bytes, 5 characters. The length written must be the byte length.
    key = "héllo".encode("utf-8")
    assert roundtrip(key, b"world") == (key, b"world")


def test_value_containing_newlines_and_nulls():
    # The reason the format uses length prefixes instead of a separator:
    # a value is allowed to contain any byte at all, including ones that
    # would otherwise look like the end of a record.
    value = b"line one\nline two\x00\xff\n"
    assert roundtrip(b"k", value) == (b"k", value)


def test_large_value():
    value = b"x" * 10_000
    assert roundtrip(b"k", value) == (b"k", value)


def test_serialize_returns_bytes():
    assert isinstance(serialize(b"k", b"v"), bytes)


def test_records_are_self_delimiting():
    # Two records written back to back must not bleed into each other.
    first = serialize(b"a", b"1")
    second = serialize(b"b", b"22")
    assert deserialize(first + second) == (b"a", b"1")


def test_corrupted_payload_is_rejected():
    # Flip a bit in the value. The checksum is the only thing standing
    # between this and silently returning wrong data.
    record = bytearray(serialize(b"name", b"Alice"))
    record[-1] ^= 0xFF
    with pytest.raises(CorruptRecord):
        deserialize(bytes(record))


def test_truncated_record_is_rejected():
    # This is what a record looks like when the process died mid-write.
    record = serialize(b"name", b"Alice")
    with pytest.raises(CorruptRecord):
        deserialize(record[:-3])
