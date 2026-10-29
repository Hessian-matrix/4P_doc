# Hardware Connection and Safety

```{warning}
Connect camera harnesses and UART with power off. UART1/UART7 use `3.3V` logic; DEBUG_UART uses `1.8V`. Never apply 5V TTL or RS-232 levels or back-feed power. Complete V2 5-pin order, power ratings, and hot-plug conditions still await official hardware confirmation. Check official interface labeling, peer voltage, and common ground before wiring; do not guess pin functions or assume UART hot-plug support.
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
| Main-board power | V2 input range, load, reverse-feed protection, and USB-C power role still await official hardware confirmation; use only a power supply confirmed compatible by product support. |
| Camera FPC / coaxial cable | Connect with power off; hot-plug is not supported. |
| UART | UART1/UART7 use `3.3V`; complete 5-pin order and power-pin load ratings await official V2 hardware confirmation. Wire with power off by default; no hot-plug promise. |
| Thermal | Keep heatsink and airflow clear; verify V2 thermal control and full-load cooling on the actual system. |

## UART

| Interface | Purpose | On-device node | Logic level and connector |
|---|---|---|---|
| UART1 | Normal user serial port | `/dev/ttyS1` | `3.3V`, CN2 5-pin |
| UART7 | Normal serial port, independent IO defaults to PPS input | `/dev/ttyS7` | `3.3V`, CN3 5-pin |
| DEBUG_UART | System console; not for `serial_port_demo` | Debug terminal `921600` baud | `1.8V`, 3-pin |

The independent V2 UART7 PPS IO does not consume RX/TX. The system configures it as a PPS input by default, without UART-to-PPS multiplexing or pin switching. Use official V2 labeling for pin numbers and orientation; do not guess the added pin or treat it as RTS/CTS. Use a compatible PPS logic level and common ground, with level conversion when needed; see [PPS Sync](../time-sync/pps-sync.md).

Generic USB-UART adapters connect only TX/RX/GND by default, not VCC. Check crossed TX/RX, adapter voltage, and common ground to prevent reverse feed into board power rails.

## Trigger and Sampling

All camera acquisition entry points use VIN LPWM hardware triggering. Camera and IMU FSYNC physical trigger lines share the same IO; software GPIO triggering is not used. IMU INT1 uses `34120000.gpio` offset `8`. A shared trigger line does not automatically associate IMU FIFO samples one-to-one with image exposures. Verify clock domain, trigger capture, and sample association separately; frame arrival time is not LPWM trigger time.

## Camera Application Resource Constraints

- Keep the required `cam-service` running; do not stop or reconfigure it.
- Exit the old application normally before switching between `sensor_demo`, `cam_demo`, ROS2, or custom camera applications. Do not share camera/VIO/encoding resources concurrently.
- Use `cam_demo --camera-id 0/1/2/3 --diagnostics` for single-camera diagnostics, with only one camera demo running.
