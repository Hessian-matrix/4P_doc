# Hardware Connection and Safety

```{warning}
RoboBaton 4P camera FPC/coaxial cables, first-time UART wiring, and any unconfirmed harness rewiring should all be handled with power off. When using a confirmed UART1/UART7 compliant connection, follow the hot-plug contract below; do not interpret hot-plug support as permission for live miswiring. DEBUG_UART only supports `1.8V` logic; UART1/UART7 are user-programmable `3.3V` UARTs. Do not connect `3.3V` or `5V` logic to DEBUG_UART, and do not connect 5V TTL or RS-232 to UART1/UART7.
```

## Camera Interface

| Physical silkscreen | Software camera ID | Default RTSP port | ROS2 prefix |
|---|---:|---:|---|
| CAM1 | cam0 / camera ID 0 | `554` | `/robobaton/cam0` |
| CAM2 | cam1 / camera ID 1 | `555` | `/robobaton/cam1` |
| CAM3 | cam2 / camera ID 2 | `556` | `/robobaton/cam2` |
| CAM4 | cam3 / camera ID 3 | `557` | `/robobaton/cam3` |

The RTSP path is fixed to `/PRR`; H.264 is the default codec, H.265 optional. The camera callback exposes NV12 raw frames: native `1280x1088`, with VSE scaling to `640x480`/`720x480`/`1280x720`; rotation `90/270` swaps the external width/height; the RTSP client receives the H.264/H.265 encoded stream of the same picture. A/B are product form versions that differ only in FOV: form A is horizontal `148.4°`, vertical `126.6°`, diagonal `193.8°`; form B is horizontal `115.6°`, vertical `96.8°`, diagonal `157.2°`. Users select the matching FOV by the form-version marking on the received product. The coaxial-cable connectors snap directly onto the sockets on the main board and camera board.

## Power, Hot-Plug, and Thermal

| Item | Public conclusion |
|---|---|
| Camera power | DC `12V ~ 24V` (3S-6S), supply current recommended no less than `600 mA`. The USB-C port is for user development only and is not a power input. |
| Camera FPC / coaxial cable | Does not support hot-plug; power off before connecting or disconnecting. |
| UART wiring | Does not support live miswiring; before wiring, distinguish DEBUG_UART `1.8V` from UART1/UART7 `3.3V`, and confirm TX/RX crossover and common ground. |
| Thermal | Fan is temperature-controlled: starts when CPU temperature `> 55°C`, stops when it drops below `< 50°C`; before long four-camera encoding, confirm heatsink, airflow, and ambient temperature. |

## UART

```{figure} ../../image/uart.jpg
:alt: DEBUG_UART, UART1, and UART7 interface positions and voltage domains in the board top view

Board top view UART interface reference: DEBUG_UART is the `1.8V` system debug port, UART1/UART7 are `3.3V` user-programmable serial ports. When this top view is used as the IMU acceleration sign reference, the top of the image (the side away from the large Ethernet/USB connectors at the bottom) is the product front and the left of the image is the product left. This reference only explains the IMU sign and does not define the transform between the IMU and camera, base, optical frame, or other coordinate systems.
```

| Interface | Purpose | On-device node | Connector |
|---|---|---|---|
| UART1 | User-programmable UART | `/dev/ttyS1` | GH1.25-4P |
| UART7 | Normal mode is a user-programmable UART; PPS mode RX is PPS and TX is GPIO/IO | `/dev/ttyS7` / `/dev/pps2` | GH1.25-4P |
| DEBUG_UART | System console/debug | Not applicable to `serial_port_demo` | GH1.25-3P |

### Physical View, Signal Order, and Power Semantics

The current public image shows the **interface positions and signal order in the board top view**:

| Interface | Signal order in the board top view |
|---|---|
| `UART1` | `GND / TX / RX / 3V3` |
| `UART7` | `GND / TX / RX / 3V3` |
| `DEBUG_UART` | `TX / RX / GND ` |

The following electrical contracts still apply:

DEBUG_UART is the system console/debug port and must use a `1.8V` USB-UART adapter only; set the debug terminal baud rate to `921600`. UART1 and UART7 are user-programmable `3.3V` UARTs; `serial_port_demo` applies only to UART1/UART7, not to DEBUG_UART. When wiring, connect the board TX to the peer RX, the board RX to the peer TX, and always share ground.

The `3V3` pins on both UART1 and UART7 support input/output and can power peripherals, with a product limit of `500 mA` total and hot-plug support under compliant connection; this does not permit wrong-level input, paralleling two external power supplies, or reverse-feeding the board. Above the total limit, use an independent power supply; the independent supply must still share ground with the board and must not reverse-feed the board 3.3V rail. Generic USB-UART adapters only connect TX/RX/GND by default and leave the adapter VCC disconnected.

## Camera Application Resource Constraints

- `cam-service` is a dependency of camera operation; the user must not stop it.
- Camera applications require exclusive camera/VIO/encoding resources; before switching between `sensor_demo`, `cam_demo`, ROS2 nodes, or a custom camera application, exit the old application normally first.
- Single-sensor diagnostics use `cam_demo --camera-id 0/1/2/3 --diagnostics`; run only one camera demo at a time.
