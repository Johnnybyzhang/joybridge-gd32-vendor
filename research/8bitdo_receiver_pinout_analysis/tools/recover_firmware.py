#!/usr/bin/env python3
"""Recover an 8BitDo GD32 update from the supplied USBPcap .pcapng capture.

Local, read-only input processing. Does not access or flash USB devices.
Uses Python's standard library and the separately bundled MIT-licensed
cryptdo8.py by AeroModes (https://github.com/aeromodes/8cryptdo).

Example:
  python recover_firmware.py Updatev205.pcapng --dat v2.05.dat --out recovered

The capture contains encrypted firmware, not the decoded machine code.
The data is first reconstructed and optionally compared with the .dat; then
the known GD32 cipher is removed and an exact encryption round trip checked.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import struct

import cryptdo8


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def pcapng_packets(raw):
    """Yield numbered Enhanced Packet Blocks, checking framing and link type."""
    offset = frame = 0
    endian = None
    interfaces = []
    while offset < len(raw):
        if offset + 12 > len(raw):
            raise ValueError(f"Truncated pcapng block at {offset}")
        if raw[offset:offset + 4] == b"\x0a\x0d\x0d\x0a":
            magic = raw[offset + 8:offset + 12]
            if magic == b"\x4d\x3c\x2b\x1a":
                endian = "<"
            elif magic == b"\x1a\x2b\x3c\x4d":
                endian = ">"
            else:
                raise ValueError("Invalid pcapng byte-order magic")
            interfaces = []
        if endian is None:
            raise ValueError("Missing pcapng section header")
        kind, length = struct.unpack_from(endian + "II", raw, offset)
        if length < 12 or length % 4 or offset + length > len(raw):
            raise ValueError(f"Invalid block length {length} at {offset}")
        if struct.unpack_from(endian + "I", raw, offset + length - 4)[0] != length:
            raise ValueError(f"Mismatching block trailer at {offset}")
        if kind == 1:
            interfaces.append(struct.unpack_from(endian + "H", raw, offset + 8)[0])
        elif kind == 6:
            frame += 1
            interface, ts_hi, ts_lo, caplen, origlen = struct.unpack_from(
                endian + "IIIII", raw, offset + 8)
            if interface >= len(interfaces):
                raise ValueError("Invalid interface index")
            if offset + 28 + caplen > offset + length - 4:
                raise ValueError(f"Packet exceeds block at frame {frame}")
            if interfaces[interface] == 249:  # LINKTYPE_USBPCAP
                if caplen != origlen:
                    raise ValueError(f"Truncated USB packet at frame {frame}")
                yield frame, offset + 28, raw[offset + 28:offset + 28 + caplen]
        offset += length


def usbpcap_packet(frame, packet_offset, packet):
    if len(packet) < 27:
        raise ValueError(f"Short USBPcap header at frame {frame}")
    header_length = struct.unpack_from("<H", packet, 0)[0]
    irp_id = struct.unpack_from("<Q", packet, 2)[0]
    status = struct.unpack_from("<I", packet, 10)[0]
    function = struct.unpack_from("<H", packet, 14)[0]
    info = packet[16]
    bus, device = struct.unpack_from("<HH", packet, 17)
    endpoint, transfer = packet[21:23]
    data_length = struct.unpack_from("<I", packet, 23)[0]
    if header_length + data_length != len(packet):
        raise ValueError(f"USBPcap data length mismatch at frame {frame}")
    return dict(frame=frame, packet_offset=packet_offset,
                payload_offset=packet_offset + header_length, irp_id=irp_id,
                status=status, function=function, info=info, bus=bus,
                device=device, endpoint=endpoint, transfer=transfer,
                data=packet[header_length:])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("capture", type=Path)
    ap.add_argument("--dat", type=Path,
                    help="Optional original .dat, used for byte-exact verification")
    ap.add_argument("--out", type=Path, default=Path("recovered"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    raw = args.capture.read_bytes()
    packets = [usbpcap_packet(*p) for p in pcapng_packets(raw)]
    starts = [p for p in packets if p["info"] == 0 and
              p["endpoint"] == 1 and len(p["data"]) == 64 and
              p["data"][:8] == bytes.fromhex("2300161f00011c00")]
    if len(starts) != 1:
        raise ValueError(f"Expected one update header, found {len(starts)}")
    start = starts[0]
    usb_header = start["data"][8:36]
    version, base, length = struct.unpack_from("<III", usb_header)
    selected = [p for p in packets if p["bus"] == start["bus"] and
                p["device"] == start["device"] and p["frame"] > start["frame"]]
    blocks = [p for p in selected if p["info"] == 0 and p["endpoint"] == 1 and
              len(p["data"]) == 64 and
              p["data"][:8] == bytes.fromhex("2700162300002000")]
    ciphertext = b"".join(p["data"][8:40] for p in blocks)
    if len(ciphertext) != length:
        raise ValueError(f"Captured {len(ciphertext)} bytes, expected {length}")
    if any(p["status"] for p in blocks):
        raise ValueError("An update packet has nonzero USB status")

    # .dat reserved fields are zero; the USB header fills these with transport
    # metadata. Compare the shared first three words and the entire payload.
    canonical = struct.pack("<III", version, base, length) + bytes(16) + ciphertext
    comparison = None
    if args.dat:
        source_dat = args.dat.read_bytes()
        comparison = dict(name=args.dat.name, bytes=len(source_dat),
                          sha256=sha256(source_dat),
                          first_12_header_bytes_equal=source_dat[:12] == canonical[:12],
                          payload_equal=source_dat[28:] == ciphertext,
                          canonical_dat_equal=source_dat == canonical)
        if not all(comparison[k] for k in ("first_12_header_bytes_equal",
                                          "payload_equal", "canonical_dat_equal")):
            raise ValueError("Captured data does not match the supplied .dat")
    section = cryptdo8.parse_image(canonical)[0]
    plain = cryptdo8.decrypt_section(canonical, section, cryptdo8.GD32())
    roundtrip = cryptdo8.build_section(plain, cryptdo8.GD32(), version, addr=base,
                                      length=length) == canonical
    if not roundtrip:
        raise ValueError("Encryption round trip failed")
    sp, reset = struct.unpack_from("<II", plain)
    if not (0x20000000 <= sp < 0x20020000 and reset & 1 and
            base <= reset - 1 < base + length):
        raise ValueError("Decoded vector table is not plausible Cortex-M firmware")
    prefix = f"v{version // 100}.{version % 100:02d}"
    (args.out / f"{prefix}_usb_payload.bin").write_bytes(ciphertext)
    (args.out / f"{prefix}_decrypted.bin").write_bytes(plain)
    with (args.out / "packet_provenance.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["block_index", "frame_number", "pcap_file_offset",
                         "firmware_offset", "flash_address", "byte_count",
                         "ciphertext_hex"])
        for index, p in enumerate(blocks):
            writer.writerow([index, p["frame"], p["payload_offset"] + 8,
                             index * 32, f"0x{base + index * 32:08x}", 32,
                             p["data"][8:40].hex()])
    summary = dict(
        capture=dict(name=args.capture.name, bytes=len(raw), sha256=sha256(raw),
                     usbpcap_packets=len(packets)),
        session=dict(bus=start["bus"], device=start["device"],
                     update_header_frame=start["frame"],
                     usb_update_header_hex=usb_header.hex(),
                     data_endpoint="0x01", data_first_frame=blocks[0]["frame"],
                     data_last_frame=blocks[-1]["frame"], packet_count=len(blocks),
                     bytes_per_packet=32, packet_payload_offset=8),
        firmware=dict(version=version, load_address=f"0x{base:08x}",
                      end_address_exclusive=f"0x{base + length:08x}", bytes=length,
                      encrypted_sha256=sha256(ciphertext),
                      decrypted_sha256=sha256(plain),
                      initial_stack_pointer=f"0x{sp:08x}",
                      reset_vector=f"0x{reset:08x}",
                      cipher="8CryptDo GD32", encryption_roundtrip_exact=roundtrip),
        dat_comparison=comparison,
        limitations=["The USB wire data remains encrypted; plaintext requires decryption.",
                     "This is an application update, not a full flash dump or bootloader backup.",
                     "The script reads local files only and never accesses the target device."])
    (args.out / "recovery_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
