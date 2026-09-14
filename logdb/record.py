"""On-disk record format.

A record is the smallest unit the database writes. The layout is:

    [checksum][key_len][value_len][key][value]

The three header fields are fixed-width so a reader always knows how many
bytes to read before it can find out how many bytes to read next. The
lengths are byte lengths, not character counts.

Nothing here touches a file. Keeping the format separate from the storage
layer means it can be tested on its own, which is the whole point of
starting here.
"""


class CorruptRecord(Exception):
    """Raised when a record's bytes do not match its checksum, or when the
    buffer is too short to hold the record its header describes."""


def serialize(key: bytes, value: bytes) -> bytes:
    """Pack one key/value pair into the on-disk record format.

    Both arguments are bytes, not str. Callers encode before they get here.
    """
    raise NotImplementedError


def deserialize(buf: bytes) -> tuple:
    """Unpack one complete record, returning (key, value).

    Raises CorruptRecord if the checksum does not match the payload, or if
    buf is shorter than the header claims the record should be.
    """
    raise NotImplementedError
