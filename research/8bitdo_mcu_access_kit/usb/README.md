# Experimental USB readback for the original 8BitDo receiver

This is an **experimental, read-only probe and dumper for the vendor HID update
interface**, not USB DFU. It transmits only opcode `0x31`. It contains no command
for updating, writing, erasing, resetting, unlocking, changing protection or
entering update mode.

**A user-supplied live probe has now returned all 12 expected read replies:**
two matching copies each of the metadata, boot header and application header.
That session used only the read command. The original updater capture separately
contains two reads of 40 bytes at `0x08003000` after an update. Full-range reads,
physical capacity and read-protected device behavior remain unproven. The
author-side verification uses offline replay, with no hardware access. If the
probe fails, it stops; it does not try preparatory commands from the update
sequence. Successful reads do not establish write support; this tool has no
write-to-memory command.

## Requirements and device selection

Use Python 3 with the `hidapi` package, which provides `import hid`:

```text
python -m pip install hidapi
```

Enter the receiver's existing update mode manually, close the official updater
and other programs accessing it, and then run:

```text
python usb_readonly_backup.py list
```

The result is JSON. Select the intended device's explicit `index`. Candidates
must have VID `0483`, PID `5760`, and matching interface `0` / usage page `0x8c`
when those fields are available. A missing field is allowed only if the other
field verifies the expected identity; any contradictory field is rejected.
These identifiers alone do not establish the board model.

The optional `--path-sha256 HASH` argument pins the selection to the HID path
shown by `list`, avoiding index drift after reconnecting devices. If the path
changes, list and select again. On Windows, retain the working HID driver used
by the original updater. This tool does not require a DFU or WinUSB driver.

## Probe first

Replace `0` with the selected index. Output directories must be new:

```text
python usb_readonly_backup.py probe --device-index 0 --out probe-01
```

If the device currently runs the recovered v2.05 application, optionally check
its header against the **decrypted, unwrapped application**:

```text
python usb_readonly_backup.py probe --device-index 0 --out probe-02 --reference-app v2.05_decrypted.bin
```

Do not pass the scrambled `.dat`, a firmware container header, or a full-chip
dump as `--reference-app`. The file must start with the application vector table
linked at `0x08003400`.

The reference check requires an exact match for the first **28 bytes**. The next
32-bit word, at application offset `0x1c` / flash address `0x0800341c`, is an
installation ID slot. The live probe differs from the recovered image only in
this word, and its value matches the first word supplied by the captured
`SET_ENCODE_ID` update command. The tool allows that word to differ **only when
the reference contains the erased placeholder `0xFFFFFFFF`**. A reference with
an already programmed value requires an exact match for the word as well. Any
other mismatch stops the operation.

This exception does not alter any returned data: both 32-byte reads, their
hashes and the raw reports retain the installation ID exactly as received.
Status records both ID values and distinguishes `matched_exactly` from
`matched_except_installation_id`. The check validates this small header prefix,
not the entire application or its version; the recovered v2.04 and v2.05 images
share the same first 28 bytes.

The probe reads each of these regions twice, in sequence:

| Region | Address | Bytes per pass |
|---|---:|---:|
| Known metadata location | `0x08003000` | 40 |
| Main-flash boot vectors | `0x08000000` | 32 |
| Application vectors | `0x08003400` | 32 |

Every read uses chunks of at most 23 bytes, the largest observed read request.
Both copies of each region must match. Initial stack pointers must fall inside
the nominal 20 KiB SRAM and be word aligned. Boot reset vectors must be Thumb
addresses before `0x08003000`; application reset vectors must lie between
`0x08003400` and `0x08020000`. These are conservative checks for this firmware
layout. A valid different loader or memory layout can fail them; the bytes and
raw traffic remain available for analysis. Failure does not prove read
protection or that USB readback is impossible.

## Request a backup

The length is always explicit. This example requests 128 KiB to cover the
observed application beyond the nominal C8 64 KiB size; it **does not assert
that every requested address is implemented on the actual chip**:

```text
python usb_readonly_backup.py dump --device-index 0 --out backup-01 --length 0x20000 --reference-app v2.05_decrypted.bin
```

Omit `--reference-app` if the application version differs or is unknown. The
`dump` command opens the device once, performs its own complete probe, then
reads the requested range twice through that same connection. It compares the
two full byte sequences and checks all included probe regions against their
earlier samples. Only after these checks does it create `flash_backup.bin`.

`--start` defaults to `0x08000000`. All requests are constrained to
`[0x08000000, 0x08020000)`. No access to option bytes, peripheral registers or
system memory is implemented. The default per-response timeout is 3000 ms;
`--timeout-ms` may be adjusted. There are no automatic transaction retries.

Files retained in the output directory:

- `status.json`: outcome, device identity, checks, addresses, SHA-256 and errors.
- `raw_requests_replies.jsonl`: requests, responses and parser results, flushed
  after each event. It includes any discarded input queued before the first
  request, but the tool never sends a reset to clear the queue.
- `probe_*_pass1.bin` / `probe_*_pass2.bin`: the two copies of each probe region.
- `flash_pass1.bin` / `flash_pass2.bin`: completed requested-range reads.
- `*.partial`: accepted bytes from a read interrupted by timeout or failure.
- `flash_backup.bin`: created only after both full reads and probe comparisons
  pass.

The JSON field `author_hardware_tested: false` describes author-side testing;
user-run results are recorded independently:

- `session_read_succeeded` and `standalone_read_succeeded` become `true` once
  the two complete 40-byte metadata reads agree. These flags stay true if a
  later vector or reference check fails: a validation failure does not undo the
  successful readback.
- `probe_passed` becomes `true` only after every repeated read, vector check and
  supplied reference check passes. This is the gate for starting a dump.
- `probe.app.reference_header_check` records the comparison result, whether all
  32 bytes matched exactly, and the observed and reference installation words.

`capacity_verified: false` deliberately remains false:
repeatability and valid headers alone cannot prove unique physical storage at
every address. The response also has no validated address echo, sequence
number or checksum. Repeated reads and probe comparisons reduce the chance of
accepting stale or misaligned replies; they cannot eliminate it completely.

## Protocol and offline checks

All commands use a 64-byte HID wire report. HIDAPI output prepends a zero report
ID, giving a 65-byte `write`; the input is read as an unnumbered 64-byte report.

| Field | Request | Expected response |
|---|---|---|
| Byte 0: packet length | `8` | `n + 9` |
| Byte 1: packet type | `0` | `0` |
| Byte 2: operation | `0x31` | `0x14` |
| Bytes 3-4, little endian | `n + 4` | `n + 4` |
| Bytes 5 onward | 32-bit little-endian address | `n` returned memory bytes |

Four bytes following the returned data are excluded, matching the host DLL's
copy behavior. Their meaning is unverified. Request bytes after the address
are zeroed; the capture contains stale buffer contents there. Unexpected
lengths, report types, ACKs or timeouts stop processing.

Run the standard-library-only verification without connecting hardware:

```text
python verify_offline.py
```

It checks the actual request/response pairs from capture frames
`13835/13837` and `13839/13841`, malformed replies, identity/range rejection,
and simulated success/failure behavior. It also replays the exact 12 request /
response exchanges from the user's `probe-01.zip`, preserving all six probe
files byte for byte. Regression cases reject a change in the first 28 bytes and
a different non-placeholder reference ID while still reporting successful
readback.

`captured_read_exchanges.json` contains the four original updater reports.
`live_probe_01_replay.json` contains the live probe exchanges, expected probe
bytes, recovered reference header and source hashes. Test transports are
in-memory mocks; verification does not import `hid` or access USB. Passing
offline checks validates parsing and control flow. The live evidence supports
header reads on the tested receiver, not all models, firmware revisions or
flash addresses.
