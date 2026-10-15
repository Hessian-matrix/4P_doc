# Hardware Connection and Safety

```{warning}
Handle V2 camera harnesses, UART, and all unconfirmed interfaces with power off. V2 pinout, electrical ratings, and hot-plug conditions are pending product confirmation; do not inherit V1 4-pin UART images, the `500 mA` limit, or hot-plug claims. Do not wire until connectors, signal order, voltage, common ground, and power direction are confirmed; prevent 5V TTL/RS-232 misconnection or reverse feed.
```

## Camera Interface

The table retains only software ID, port, and topic associations; CAM1..CAM4 are historical V1 labels. V2 silkscreen and J4/J7/J5/J6-to-software mapping, camera sub-board/FPC revision, pin11/pin17 function, and electrical timing remain unverified.

| Physical silkscreen | Software camera ID | Default RTSP port | ROS2 prefix |
|---|---:|---:|---|
| CAM1 | cam0 / camera ID 0 | `554` | `/robobaton/cam0` |
| CAM2 | cam1 / camera ID 1 | `555` | `/robobaton/cam1` |
| CAM3 | cam2 / camera ID 2 | `556` | `/robobaton/cam2` |
| CAM4 | cam3 / camera ID 3 | `557` | `/robobaton/cam3` |

RTSP path is `/PRR`; H.264 is default and H.265 optional. Camera callbacks expose NV12: native `1280x1088`, VSE-scaled `640x480`/`720x480`/`1280x720`, with swapped dimensions at `90/270` rotation. V1 A/B FOV and connector illustrations do not establish V2 camera-sub-board, harness, or mechanical compatibility; actual models and connections need confirmation.

## Power, Hot-Plug, and Thermal

| Item | Public conclusion |
|---|---|
| Main-board power | V2 rated input range, load, reverse-feed protection, and USB-C power/role boundaries pending confirmation; neither V1 DC `12V ~ 24V` nor “USB-C is not a power input” carries over. |
| Camera FPC / coaxial cable | Power off before connecting; V2 harness and orientation pending confirmation. |
| UART wiring | V2 actual voltage, signal order, power direction, and rated current pending confirmation; do not wire from old images or assume hot-plug support. |
| Thermal | V2 fan/thermal thresholds and full-load thermal capability pending confirmation; keep heatsink and airflow clear. |

## UART

```{figure} ../../image/uart.jpg
:alt: Historical V1 UART top view, not applicable to V2 wiring

Historical V1 photograph for old-product identification only; not a V2 UART position, voltage, or IMU-axis reference. V2 photographs and verified pinouts are pending publication.
```

| Interface | Purpose | On-device node | Connector |
|---|---|---|---|
| UART1 | Normal user UART; V2 pin voltage pending | Software example `/dev/ttyS1`; board mapping pending | V2 CN2 5-pin; full pinout pending |
| UART7 | Normal user UART; V2 PPS mux pending | Software example `/dev/ttyS7`; board mapping pending | V2 CN3 5-pin; full pinout pending |
| DEBUG_UART | System console/debug; not for `serial_port_demo` | V2 node, baud rate, and recovery channel pending | Schematic uses 3 pins; V2 hardware and signal order pending |

### Physical View, Signal Order, and Power Semantics

V2 CN2/CN3 changed to 5-pin connectors; added signals must not be assumed to provide hardware flow control or PPS. The V1 `GND/TX/RX/3V3` order is no longer a V2 pinout. The schematic retains `1.8V` for DEBUG_UART, but actual UART GPIO_VREF/BOM, adapter voltage, and connector direction still require confirmation.

Until the complete V2 pinout, voltage, and power semantics are confirmed, no rated output-current or hot-plug promise is made. Wire with power off by default and leave USB-UART VCC disconnected; confirm crossed TX/RX, common ground, and prevent reverse feed into board power rails.

The producer resolves camera common trigger `34130000.gpio` offset `0` and drives it exclusively; IMU INT1 uses `34120000.gpio` offset `8`. V2 IMU FSYNC input shares the camera trigger net, but waveform/electrical limits and exposure correspondence still need acceptance; this does not establish camera/IMU hardware sample alignment.

## Camera Application Resource Constraints

- `cam-service` is a dependency of camera operation; the user must not stop it.
- Camera applications require exclusive camera/VIO/encoding resources; before switching between `sensor_demo`, `cam_demo`, ROS2 nodes, or a custom camera application, exit the old application normally first.
- Single-sensor diagnostics use `cam_demo --camera-id 0/1/2/3 --diagnostics`; run only one camera demo at a time.
