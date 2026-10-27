#!/usr/bin/env python3
"""Validate local 8BitDo dump transcripts and compare recovered application files.

No HID library, hardware access, flash operation, or transmitted command exists
in this program. All inputs are previously saved files.
"""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import struct

BASE = 0x08000000
APP_OFFSET = 0x3400
LENGTH = 0x20000


def digest(data):
    return hashlib.sha256(data).hexdigest()


def address(value):
    return f"0x{value:08x}"


def ranges(indices):
    out = []
    for i in indices:
        if out and out[-1][1] == i:
            out[-1][1] += 1
        else:
            out.append([i, i + 1])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("backup", type=Path)
    ap.add_argument("--v205", type=Path, required=True)
    ap.add_argument("--v204", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    files = {}
    main_copies = []
    for name in ("flash_pass1.bin", "flash_pass2.bin", "flash_backup.bin"):
        data = (args.backup / name).read_bytes()
        assert len(data) == LENGTH, (name, len(data))
        main_copies.append(data)
        files[name] = {"bytes": len(data), "sha256": digest(data)}
    assert main_copies[0] == main_copies[1] == main_copies[2]
    flash = main_copies[0]
    expected = {}
    probes = {}
    for label, offset, size in (("metadata", 0x3000, 40), ("boot", 0, 32), ("app", APP_OFFSET, 32)):
        for n in (1, 2):
            phase = f"probe_{label}_pass{n}"
            data = (args.backup / f"{phase}.bin").read_bytes()
            assert len(data) == size
            assert data == flash[offset:offset + size], phase
            expected[phase] = (BASE + offset, data)
        probes[label] = {"start": address(BASE + offset), "bytes": size,
                         "both_probe_passes_match_full_dump": True,
                         "sha256": digest(expected[f"probe_{label}_pass1"][1])}
    expected["flash_pass1"] = (BASE, flash)
    expected["flash_pass2"] = (BASE, flash)

    transcript_path = args.backup / "raw_requests_replies.jsonl"
    transcript_raw = transcript_path.read_bytes()
    events = [json.loads(line) for line in transcript_raw.splitlines()]
    event_counts = Counter(e["event"] for e in events)
    assert event_counts.keys() <= {"initial_drain_complete", "request", "response", "accepted"}
    assert events[0]["event"] == "initial_drain_complete" and events[0]["discarded_reports"] == 0
    assert event_counts["initial_drain_complete"] == 1
    assert (len(events) - 1) % 3 == 0
    sequence = 0
    reconstructed = {name: bytearray() for name in expected}
    requests_by_phase = Counter()
    for i in range(1, len(events), 3):
        req, rsp, accepted = events[i:i + 3]
        assert [e["event"] for e in (req, rsp, accepted)] == ["request", "response", "accepted"]
        sequence += 1
        assert req["sequence"] == rsp["sequence"] == accepted["sequence"] == sequence
        phase = req["phase"]
        start, target = expected[phase]
        completed = len(reconstructed[phase])
        count = min(23, len(target) - completed)
        assert count > 0 and req["count"] == count
        assert int(req["address"], 16) == start + completed
        wire = bytes.fromhex(req["request_wire_hex"])
        assert len(wire) == 64 and wire[:3] == bytes((8, 0, 0x31))
        assert struct.unpack_from("<H", wire, 3)[0] == count + 4
        assert struct.unpack_from("<I", wire, 5)[0] == start + completed
        assert wire[9:] == bytes(55)
        assert bytes.fromhex(req["hid_write_hex"]) == bytes(1) + wire
        reply = bytes.fromhex(rsp["response_wire_hex"])
        assert rsp["count"] == len(reply) == 64
        assert reply[:3] == bytes((count + 9, 0, 0x14))
        assert struct.unpack_from("<H", reply, 3)[0] == count + 4
        payload = reply[5:5 + count]
        assert payload.hex() == accepted["data_hex"]
        assert reply[5 + count:9 + count].hex() == accepted["excluded_four_bytes_hex"]
        assert payload == target[completed:completed + count]
        reconstructed[phase].extend(payload)
        requests_by_phase[phase] += 1
    phases = {}
    for phase, (start, target) in expected.items():
        assert bytes(reconstructed[phase]) == target
        phases[phase] = {"start": address(start), "end_exclusive": address(start + len(target)),
                         "bytes": len(target), "requests": requests_by_phase[phase],
                         "contiguous_complete_coverage": True, "payload_matches_file": True,
                         "sha256": digest(target)}

    references = {}
    for version, path in (("v2.05", args.v205), ("v2.04", args.v204)):
        reference = path.read_bytes()
        installed = flash[APP_OFFSET:APP_OFFSET + len(reference)]
        differing = [i for i, pair in enumerate(zip(installed, reference)) if pair[0] != pair[1]]
        spans = ranges(differing)
        references[version] = {"compared_bytes": len(reference), "reference_sha256": digest(reference),
                               "installed_range_sha256": digest(installed), "different_bytes": len(differing),
                               "different_spans": len(spans)}
        with (args.out / f"{version}_differences.csv").open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["start", "end_exclusive", "bytes", "reference_hex", "installed_hex"])
            for first, end in spans:
                writer.writerow([address(BASE + APP_OFFSET + first), address(BASE + APP_OFFSET + end),
                                 end - first, reference[first:end].hex(), installed[first:end].hex()])
        if version == "v2.05":
            assert spans == [[0x1C, 0x28], [0x34, 0x38]]
            assert len(differing) == 16
            references[version]["all_differences"] = [
                {"start": address(BASE + APP_OFFSET + first), "end_exclusive": address(BASE + APP_OFFSET + end),
                 "reference_hex": reference[first:end].hex(), "installed_hex": installed[first:end].hex()}
                for first, end in spans]
            assert installed[0x1C:0x28] == bytes.fromhex("f975ca555052a0d011b6ef60")
            assert struct.unpack_from("<I", installed, 0x34)[0] == 205
            upper_reference = reference[0x10000 - APP_OFFSET:]
            upper_installed = flash[0x10000:APP_OFFSET + len(reference)]
            assert upper_reference == upper_installed

    regions = []
    for name, lo, hi in (("bootloader_reservation", 0, 0x3000), ("metadata_page", 0x3000, 0x3400),
                         ("installed_application", 0x3400, 0x1BA00), ("remaining_tail", 0x1BA00, LENGTH)):
        data = flash[lo:hi]
        non_erased = [i for i, value in enumerate(data) if value != 0xFF]
        regions.append({"name": name, "start": address(BASE + lo), "end_exclusive": address(BASE + hi),
                        "bytes": len(data), "non_ff_bytes": len(non_erased), "sha256": digest(data),
                        "last_non_ff_address": address(BASE + lo + non_erased[-1]) if non_erased else None})
    assert flash[0x3030:0x3400] == bytes([0xFF]) * 0x3D0
    assert flash[0x1BA00:] == bytes([0xFF]) * (LENGTH - 0x1BA00)
    assert flash[:0x10000] != flash[0x10000:]
    with (args.out / "flash_pages_1024.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["start", "bytes", "non_ff_bytes", "sha256"])
        for offset in range(0, LENGTH, 1024):
            page = flash[offset:offset + 1024]
            writer.writerow([address(BASE + offset), len(page), sum(x != 0xFF for x in page), digest(page)])
    report = {
        "schema": "8bitdo-full-backup-validation-v1", "files": files,
        "three_main_files_identical": True, "validated_main_range": [address(BASE), address(BASE + LENGTH)],
        "transcript": {"bytes": len(transcript_raw), "sha256": digest(transcript_raw),
                       "event_counts": dict(event_counts), "only_request_opcode": "0x31",
                       "ordered_request_response_accepted_triplets": True,
                       "all_request_padding_zero": True, "all_addresses_lengths_framing_and_payloads_valid": True,
                       "phases": phases},
        "probe_comparisons": probes, "application_comparisons": references,
        "capacity_evidence": {"readable_address_bytes": LENGTH, "lower_upper_64k_identical": False,
                              "lower_upper_64k_differing_byte_positions": sum(x != y for x, y in zip(flash[:0x10000], flash[0x10000:])),
                              "upper_app_range_matching_v205": ["0x08010000", "0x0801ba00"],
                              "upper_app_bytes_matching_v205": len(upper_reference),
                              "simple_64k_read_alias_ruled_out": True,
                              "density_register_read": False, "write_erase_capacity_tested": False,
                              "interpretation": "Stable, distinct readable flash contents above 64 KiB; not a destructive erase/program qualification or a factory density-register reading."},
        "regions": regions,
        "vector_reserved_words": {"boot_tag_0800001c": [address(v) for v in struct.unpack_from("<3I", flash, 0x1C)],
                                  "app_tag_0800341c": [address(v) for v in struct.unpack_from("<3I", flash, 0x341C)],
                                  "boot_word_08000028": address(struct.unpack_from("<I", flash, 0x28)[0]),
                                  "app_word_08003428": address(struct.unpack_from("<I", flash, 0x3428)[0]),
                                  "boot_version_08000034": struct.unpack_from("<I", flash, 0x34)[0],
                                  "app_version_08003434": struct.unpack_from("<I", flash, 0x3434)[0]},
        "metadata": {"start": "0x08003000", "first_48_hex": flash[0x3000:0x3030].hex(),
                     "first_40_match_probe": True, "next_8_zero": flash[0x3028:0x3030] == bytes(8),
                     "3030_through_33ff_all_ff": True, "semantics_not_inferred_from_bytes_alone": True},
        "limitations": ["This dump covers main flash only; it excludes option bytes, unique-ID/density registers, factory system ROM and controller-internal state.",
                        "The all-FF tail is preserved evidence of its current contents, not proof it is safe to erase or program.",
                        "No physical-device access or firmware operation occurred during this offline validation."]}
    (args.out / "backup_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"main_sha256": digest(flash), "requests": sequence,
                      "requests_per_full_pass": requests_by_phase["flash_pass1"],
                      "v205_different_bytes": references["v2.05"]["different_bytes"],
                      "v204_different_bytes": references["v2.04"]["different_bytes"],
                      "report": str(args.out / "backup_validation.json")}, indent=2))


if __name__ == "__main__":
    main()
