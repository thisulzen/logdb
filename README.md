# logdb

A persistent key-value store written from scratch in Python, using only the standard library.

The interface is a dictionary that survives the process exiting:

```python
db.put(b"name", b"Alice")
db.get(b"name")        # b"Alice"
db.delete(b"name")
```

Everything interesting is in how that is made durable on disk.

## Status

In progress. The record format is specified and under test; the storage engine is not yet
written. See the roadmap below for what is planned and what is done.

This README will carry benchmark numbers once there is something to measure. Until then it
does not claim any.

## Design

The store is an **append-only log**. Writes are never made in place: `put` appends a new
record, `delete` appends a tombstone, and the most recent record for a key is the truth. A
read scans the log and keeps the last match.

Appending rather than overwriting buys two things. Writes are sequential, which is the access
pattern disks are fastest at. And a write can never damage data that was already correct,
because it never touches it, which is what makes crash recovery tractable.

The costs are that the file grows without bound and that reads are linear. Both are addressed
later in the roadmap, by an in-memory index and by compaction respectively.

This is the design behind [Bitcask](https://riak.com/assets/bitcask-intro.pdf), the storage
engine used by Riak.

### Record format

```
[checksum][key_len][value_len][key][value]
```

A file is an undelimited stream of bytes, so the format has to say where each record ends.
Using a separator byte would fail as soon as a value contained that byte, so the lengths are
written ahead of the payload instead. The three header fields are fixed-width, which means a
reader always knows how many bytes to read in order to find out how many bytes to read next.

Lengths are byte lengths, not character counts. The two differ as soon as a key is not ASCII.

The checksum covers the payload. A process killed partway through a write leaves a partial
record at the tail of the file, and the length fields in that partial record will contain
plausible-looking garbage. Recomputing the checksum on read is what distinguishes a real
record from a torn one.

## Roadmap

| Step | Description | Status |
|------|-------------|--------|
| 1 | Append-only log: `put`, `get`, `delete` with a binary record format | In progress |
| 2 | In-memory index mapping key to file offset, rebuilt from the log on startup | Planned |
| 3 | Crash safety: `SIGKILL` tests, torn-record recovery, `fsync` cost measurement | Planned |
| 4 | Compaction: rewrite the log without dead records, swapped in atomically | Planned |
| 5 | Benchmarks: throughput and p50/p95/p99 latency against SQLite and a plain `dict` | Planned |

Each step is a complete working program on its own.

## Running the tests

```bash
python -m venv .venv
source .venv/bin/activate
pip install pytest
pytest
```

The tests in `tests/test_record.py` define the record format contract: round-tripping
arbitrary bytes, values containing newlines and null bytes, byte-length correctness for
non-ASCII keys, and rejection of both corrupted and truncated records.

## Layout

```
logdb/
    record.py         Record serialisation and the on-disk format
tests/
    test_record.py    Format contract
```

## References

- Kleppmann, *Designing Data-Intensive Applications*, Chapter 3
- Sheehy and Smith, *Bitcask: A Log-Structured Hash Table for Fast Key/Value Data*
