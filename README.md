# JoyBridge-GD32 vendor inputs

Third-party files needed to build [JoyBridge-GD32](https://github.com/Johnnybyzhang/joybridge-gd32) that cannot be pulled from a public Git upstream. The main repository mounts this repository as the `vendor/` submodule.

| Path | Contents | Origin |
| --- | --- | --- |
| `gd32/GD32F10x_DFP_2.0.3/` | Device headers and standard peripheral drivers | GigaDevice `GD32F10x_DFP` 2.0.3 CMSIS pack (`Device/`, `Flash/`, `SVD/`, `.pdsc`) |
| `gd32/GD32F10x_Firmware_Library_V2.7.0/` | `Firmware/` tree, including the USBD library | GigaDevice GD32F10x Firmware Library 2.7.0, archive SHA-256 `3494fcb21df8710335cb49dffafd6722c5f2c9dadf5c942bc5369a30ca163b4f` |
| `rda5876/` | `rdabt_r12_init.c` (RDA5876 R12 ROM patches and PSKEY table) and `hci_initialization_tables.json` (receiver RF/clock/UART values) | RDA8955 IDH tree `b2b6287e8fa9a9f49b679a357b49beb1c31d821c`, see `rda5876/SOURCE.txt`; board values extracted from the receiver |
| `research/` | Reverse-engineering notes: bootloader analysis, MCU access kit, pin/radio analysis. Firmware images and flash dumps are not included. | Original analysis of one GD32F103C8T6 + RDA5876 receiver |

Files are stored unmodified (`.gitattributes` disables line-ending conversion). Each third-party file keeps its own license or notice; nothing here is relicensed. The GigaDevice files are covered by `SOFTWARE LICENSE AGREEMENT SLA-GD0001-version1.1.pdf` and the BSD-3-Clause headers in the sources. The RDA source is included for interoperability.
