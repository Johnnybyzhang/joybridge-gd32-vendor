#!/usr/bin/env python3
"""Standard-library-only checks. Never imports hid or opens hardware."""
import json
from pathlib import Path
import struct
import tempfile

import usb_readonly_backup as tool

RESULTS = []


def test(name):
    def register(function):
        try:
            function()
            RESULTS.append({"test": name, "passed": True})
        except Exception as exc:
            RESULTS.append({"test": name, "passed": False, "error": str(exc)})
        return function
    return register


def must_reject(function):
    try:
        function()
    except tool.ProbeError:
        return
    raise AssertionError("Malformed input unexpectedly accepted")


PACKETS = {p["frame"]: bytes.fromhex(p["wire_hex"]) for p in json.loads(
    Path(__file__).with_name("captured_read_exchanges.json").read_text())}
METADATA = bytes.fromhex(
    "50 23 6d 95 7c 7a 01 ff 0f 00 0f 00 00 00 00 00 5a b2 eb b1 37 7b f4 "
    "76 1b 06 da 74 a9 f3 be b0 00 00 00 00 00 00 4d 84")
LIVE_PROBE = json.loads(Path(__file__).with_name("live_probe_01_replay.json").read_text())


@test("two_captured_read_exchanges")
def captured():
    got = []
    for request_frame, response_frame, address, count in (
            (13835, 13837, 0x08003000, 23), (13839, 13841, 0x08003017, 17)):
        request = tool.build_read_request(address, count)
        assert len(request) == 64
        assert request[:9] == PACKETS[request_frame][:9]
        # Captured bytes after address were stale output-buffer contents. The new
        # tool deliberately zero-fills them; they are outside the command length.
        assert request[9:] == bytes(55)
        got.append(tool.parse_read_response(PACKETS[response_frame], count))
    assert b"".join(got) == METADATA


@test("four_trailing_bytes_are_excluded")
def trailing():
    reply = bytearray(PACKETS[13837])
    reply[28:32] = b"\xde\xad\xbe\xef"
    assert tool.parse_read_response(reply, 23) == METADATA[:23]


@test("malformed_response_shapes_rejected")
def malformed():
    good = PACKETS[13837]
    for reply in (good[:-1], b"\0" + good, b"", good[:5]):
        must_reject(lambda: tool.parse_read_response(reply, 23))
    for offset, value in ((0, 31), (1, 1), (2, 0x16), (3, 0x1A), (4, 1)):
        bad = bytearray(good)
        bad[offset] = value
        must_reject(lambda: tool.parse_read_response(bad, 23))
    must_reject(lambda: tool.parse_read_response(good, 17))


@test("read_boundaries_and_chunk_limit")
def boundaries():
    for address, count in ((0x08000000, 0), (0x08000000, 24),
                           (0x07FFFFFF, 1), (0x08020000, 1), (0x0801FFFF, 2)):
        must_reject(lambda: tool.build_read_request(address, count))
    assert tool.build_read_request(0x0801FFFF, 1)[2] == 0x31


@test("identity_rejects_wrong_interface_or_usage")
def identity():
    base = {"vendor_id": 0x0483, "product_id": 0x5760,
            "interface_number": 0, "usage_page": 0x8C, "path": b"fixture"}
    assert tool.device_description(base, 0)["eligible"]
    for updates in ({"interface_number": 1}, {"usage_page": 0xFF00},
                    {"vendor_id": 0x1234}, {"interface_number": -1, "usage_page": 0}):
        assert not tool.device_description({**base, **updates}, 0)["eligible"]


class FakeHid:
    """Deterministic test transport; it has no relationship to host USB devices."""
    def __init__(self, fail_at=None):
        self.memory = bytearray((i * 37 + 11) & 255 for i in range(0x20000))
        struct.pack_into("<II", self.memory, 0, 0x20004FF0, 0x08000101)
        struct.pack_into("<II", self.memory, 0x3400, 0x20003FB8, 0x08003571)
        self.memory[0x3000:0x3028] = METADATA
        self.pending, self.writes, self.fail_at = None, [], fail_at

    def write(self, output):
        assert len(output) == 65 and output[0] == 0 and output[3] == 0x31
        assert output[10:] == bytes(55)
        self.writes.append(output)
        self.pending = output[1:]
        return 65

    def read(self, count, timeout):
        assert count == 64
        if self.pending is None:
            return []
        request, self.pending = self.pending, None
        if len(self.writes) == self.fail_at:
            return []
        n, address = struct.unpack_from("<HI", request, 3)
        n -= 4
        reply = bytearray(64)
        reply[:3] = bytes((n + 9, 0, 0x14))
        struct.pack_into("<H", reply, 3, n + 4)
        offset = address - 0x08000000
        reply[5:5 + n] = self.memory[offset:offset + n]
        return list(reply)

    def close(self):
        pass


@test("same_connection_probe_and_two_complete_reads")
def simulated_success():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        device = FakeHid()
        session = tool.ReadSession(device, directory / "raw.jsonl", 100)
        status = {"probe_passed": False}
        try:
            must_reject(lambda: tool.run_dump(session, directory, status, 0x08000000, 64))
            session.drain_initial_input()
            tool.run_probe(session, directory, status)
            tool.run_dump(session, directory, status, 0x08000000, 64)
            assert (directory / "flash_backup.bin").read_bytes() == device.memory[:64]
            assert status["dump"]["two_full_reads_match"]
            assert all(output[3] == 0x31 for output in device.writes)
        finally:
            session.close()


@test("timeout_preserves_partial_and_sends_no_retry")
def simulated_failure():
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        device = FakeHid(fail_at=2)
        session = tool.ReadSession(device, directory / "raw.jsonl", 100)
        try:
            path = directory / "sample.bin"
            must_reject(lambda: session.read_file(0x08003000, 40, path, "test"))
            assert not path.exists()
            assert (directory / "sample.bin.partial").read_bytes() == METADATA[:23]
            assert len(device.writes) == 2
        finally:
            session.close()


@test("wrong_address_plausibility_rejected")
def vectors():
    app = struct.pack("<II", 0x20003FB8, 0x08003571) + bytes(24)
    assert tool.vector_check(app, "app")["plausible"]
    must_reject(lambda: tool.vector_check(app, "boot"))
    must_reject(lambda: tool.vector_check(bytes(32), "app"))


class LiveReplayHid:
    """Replays exactly the user's 12 captured replies; never accesses USB."""
    def __init__(self):
        self.exchanges = LIVE_PROBE["exchanges"]
        self.position, self.pending = 0, None

    def write(self, output):
        assert self.pending is None and self.position < len(self.exchanges)
        exchange = self.exchanges[self.position]
        assert output == b"\0" + bytes.fromhex(exchange["request_wire_hex"])
        self.pending = bytes.fromhex(exchange["response_wire_hex"])
        self.position += 1
        return len(output)

    def read(self, count, timeout):
        assert count == 64
        reply, self.pending = self.pending, None
        return list(reply) if reply is not None else []

    def close(self):
        pass


def replay_live_probe(reference, accepted):
    with tempfile.TemporaryDirectory() as temp:
        directory = Path(temp)
        device = LiveReplayHid()
        session = tool.ReadSession(device, directory / "raw.jsonl", 100)
        status = {"probe_passed": False, "session_read_succeeded": False,
                  "standalone_read_succeeded": False}
        try:
            session.drain_initial_input()
            if accepted:
                tool.run_probe(session, directory, status, reference)
            else:
                must_reject(lambda: tool.run_probe(session, directory, status, reference))
            assert device.position == 12 and device.pending is None
            assert session.read_succeeded and status["session_read_succeeded"]
            assert status["standalone_read_succeeded"]
            assert session.probe_passed == status["probe_passed"] == accepted
            assert status == json.loads((directory / "status.json").read_text())
            for filename, expected in LIVE_PROBE["expected_probe_files_hex"].items():
                assert (directory / filename).read_bytes() == bytes.fromhex(expected)
            return status["probe"]["app"]["reference_header_check"]
        finally:
            session.close()


@test("live_12_reply_replay_accepts_erased_reference_id_only")
def live_probe_success():
    reference = bytes.fromhex(LIVE_PROBE["reference_header_hex"])
    observed = bytes.fromhex(LIVE_PROBE["expected_probe_files_hex"]["probe_app_pass1.bin"])
    check = replay_live_probe(reference, True)
    assert check["accepted"] and check["first_28_bytes_match"]
    assert check["result"] == "matched_except_installation_id"
    assert not check["exact_32_bytes_match"]
    assert check["reference_installation_id"] == "0xffffffff"
    assert check["observed_installation_id"] == f"0x{struct.unpack_from('<I', observed, 28)[0]:08x}"
    exact = tool.compare_reference_header(observed, observed)
    assert exact["accepted"] and exact["result"] == "matched_exactly"
    # Other programmed IDs are accepted against an erased reference too; the
    # reader must not hard-code this receiver's installation-specific word.
    different_id = bytearray(observed)
    different_id[28:32] = b"\x12\x34\x56\x78"
    assert tool.compare_reference_header(different_id, reference)["accepted"]


@test("live_replay_rejects_prefix_mismatch_but_records_read_success")
def live_probe_wrong_prefix():
    reference = bytearray.fromhex(LIVE_PROBE["reference_header_hex"])
    reference[8] ^= 4
    check = replay_live_probe(reference, False)
    assert not check["accepted"] and not check["first_28_bytes_match"]
    assert check["result"] == "mismatch"


@test("live_replay_rejects_different_programmed_reference_id")
def live_probe_wrong_programmed_id():
    reference = bytearray.fromhex(LIVE_PROBE["expected_probe_files_hex"]["probe_app_pass1.bin"])
    reference[28] ^= 1
    check = replay_live_probe(reference, False)
    assert not check["accepted"] and check["first_28_bytes_match"]
    assert not check["reference_has_erased_placeholder"]
    assert check["result"] == "mismatch"


if __name__ == "__main__":
    print(json.dumps({"hardware_accessed": False, "hid_imported": False,
                      "passed": all(r["passed"] for r in RESULTS),
                      "tests": RESULTS}, indent=2, sort_keys=True))
    raise SystemExit(0 if all(r["passed"] for r in RESULTS) else 1)
