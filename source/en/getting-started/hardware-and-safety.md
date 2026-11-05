# Hardware Connection and Safety

```{warning}
Connect camera harnesses and UART with power off. UART1/UART7 use `3.3V` logic; DEBUG_UART uses `1.8V`. Never apply 5V TTL or RS-232 levels or back-feed power. Pin numbers and signal order are shown below; check physical interface labeling, peer voltage, and common ground before wiring. UART power-pin load ratings and hot-plug conditions still await confirmation; do not assume UART hot-plug support.
```

(wiring-diagram)=
## Interface Wiring Diagram

The diagram shows power, DEBUG_UART, UART1/UART7, CAN, Gigabit Ethernet, USB-C, the TF card, and the fan connector. Check the physical silkscreen and matching harness before use.

```{figure} ../_static/V2.3_board_connected_en.png
:alt: RoboBaton 4P interface wiring diagram showing XT30 power, UART pin order, PPS, CAN, Ethernet, USB-C, TF card insertion, and the factory-connected fan
:width: 100%
:align: center

Interface wiring and matching cable plugs. Circled numbers are schematic pin numbers; dashed lines indicate mating connections.
```

{download}`View or download the full-resolution wiring diagram (PNG) <../_static/V2.3_board_connected_en.png>`.

- Plugs are drawn with wires spread out, not as mating-face or crimp-face views. Before crimping, verify terminal numbers, housing polarity, and continuity; do not wire solely by left-to-right placement.
- TX/RX directions are relative to this board: cross TX/RX at the peer and connect common ground. Except for Ethernet T568B colors, wire colors only distinguish signals and do not identify pins or polarity.
- Wire XT30 by the physical `+` / `−` markings; leave UART `3V3` power pins disconnected by default. The two-pin CAN connector has no GND pin; verify bus reference ground and termination separately.

## Gigabit Ethernet

The board uses a GH1.25 8P connector, connected to RJ45 through the supplied cable. In the wiring diagram, GH1.25 pins run from top to bottom as `8, 7, 6, 5, 4, 3, 2, 1`, with signals, wire colors, and RJ45 annotations following the same pin order. Connect the RJ45 end using the shown T568B pin numbers and colors. When preparing a cable, verify terminal numbers, housing orientation, and continuity.

```{warning}
The supplied Gigabit Ethernet cable is not twisted pair and may suffer packet loss during transmission. It is for testing and temporary use only. For a reliable Gigabit Ethernet connection, prepare your own suitable twisted-pair Ethernet cable and connect GH1.25 to RJ45 according to the wiring diagram. Negotiating a Gigabit link does not by itself establish reliable transmission.
```

## Camera Interface

Camera physical interfaces map to software as follows:

| Physical silkscreen | Software camera ID | Default RTSP port | ROS2 prefix |
|---|---:|---:|---|
| CAM1 | cam0 / camera ID 0 | `554` | `/robobaton/cam0` |
| CAM2 | cam1 / camera ID 1 | `555` | `/robobaton/cam1` |
| CAM3 | cam2 / camera ID 2 | `556` | `/robobaton/cam2` |
| CAM4 | cam3 / camera ID 3 | `557` | `/robobaton/cam3` |

RTSP uses `/PRR`, H.264 by default with optional H.265. NV12 native output is `1280x1088`, with VSE full-frame scaling to `640x480`/`720x480`/`1280x720`; rotation `90/270` swaps width and height. Camera A/B horizontal FOV remains `148.4°`/`115.6°`; see [Product Introduction](Product_Introduction.md) for the remaining camera specifications.

## Power, Hot-Plug, and Thermal

| Item | Public conclusion |
|---|---|
| Main-board power | Confirmed XT30 input range: `9~27V DC`; follow physical polarity markings. Full-load current, reverse-feed protection, and the USB-C power role still await confirmation. Use only a power supply confirmed compatible by product support; do not treat the USB-C data interface as a power input. |
| Camera FPC / coaxial cable | Connect with power off; hot-plug is not supported. |
| UART | UART1/UART7 use `3.3V`; see the diagram and table below for pin numbers and signal order. Power-pin load ratings and hot-plug conditions await confirmation. Wire with power off by default; no hot-plug promise. |
| Thermal | The fan is connected at the factory. Keep heatsink and airflow clear; verify V2 thermal control and full-load cooling on the actual system. |

## UART

| Interface | Purpose | On-device node | Logic level and connector | Schematic pin numbers and signals |
|---|---|---|---|---|
| UART1 | Normal user serial port | `/dev/ttyS1` | `3.3V`, CN1, GH1.25 4-pin | 1: 3V3; 2: RX; 3: TX; 4: GND |
| UART7 | Normal serial port, independent IO defaults to PPS input | `/dev/ttyS7` | `3.3V`, CN2, GH1.25 5-pin | 1: 3V3; 2: TX; 3: RX; 4: PPS input; 5: GND |
| DEBUG_UART (D-UART in the diagram) | System console; not for `serial_port_demo` | Debug terminal `921600` baud | `1.8V`, SH1.0 3-pin | 1: TX; 2: RX; 3: GND |

UART7 pin 4 is the independent PPS input, enabled by default without consuming RX/TX or requiring pin switching; it is not RTS/CTS. Check pin numbers and signal order against the diagram and physical labels. PPS uses **3.3V logic** and common ground; adapt 1.8V, 5V TTL, or RS-232 outputs before connecting them. Wire with power off, and disable or isolate external PPS and its pull-up while the board is unpowered or asleep to prevent back-feed. See [PPS Sync](../time-sync/pps-sync.md) for wiring and input checks.

Generic USB-UART adapters connect only TX/RX/GND by default, not VCC. Check crossed TX/RX, adapter voltage, and common ground to prevent reverse feed into board power rails.

## Trigger and Sampling

All camera entries use VIN LPWM hardware triggering, not software GPIO. The kernel IIO driver owns IMU SPI/INT1; applications must not claim them through another path. Current software provides no FSYNC association. Shared wiring does not establish sample/exposure synchronization; frame arrival and host-assigned time are not physical exposure time.

## Camera Application Resource Constraints

- Keep the required `cam-service` running; do not stop or reconfigure it.
- Exit the old application normally before switching between `sensor_demo`, `cam_demo`, ROS2, or custom camera applications. Do not share camera/VIO/encoding resources concurrently.
- Use `cam_demo --camera-id 0/1/2/3 --diagnostics` for single-camera diagnostics, with only one camera demo running.
