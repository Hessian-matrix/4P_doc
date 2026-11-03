# Product Introduction

RoboBaton 4P V2 is a four-camera product for the X5 platform. It provides non-ROS RTSP/IMU/UART examples, plus ROS2 image and IMU topic usage paths.
For release boundaries, versions, and compatibility, see [Product Version and Compatibility](product-and-compatibility.md). This page only covers the composition, parameters, and installation order needed to get started.

## Browser Workspace

```{figure} ../_static/4P_overview_en.png
:alt: RoboBaton 4P English browser workspace with four cameras, attitude, six-axis telemetry, and recording controls
:width: 100%
:align: center

English browser workspace: four cameras, attitude, six-axis telemetry, and recording controls share one homepage. Images, values, and recording state are interface examples; use the current device state.
```

The supplied system starts the combined application automatically at boot. See {ref}`First Power-On <first-boot-web>` and [non-ROS Demo Usage](../usage/non-ros-demo.md) for operation. Use the top-right `CH` / `EN` toggle to switch language. Attitude is a browser six-axis fusion preview, not proof of absolute heading or hardware synchronization.

**Phone and tablet preview**: connect the mobile device to the same LAN with network access to the board, then open the device page in its browser to preview four cameras, attitude, and six-axis data. No dedicated app is required. Narrow screens stack the panels vertically; see {ref}`First Power-On <first-boot-web>` for connection steps and browser limits.

The supplied Ethernet cable is for testing and temporary connections, not reliable Gigabit transmission. See [Gigabit Ethernet](hardware-and-safety.md#gigabit-ethernet) for cable limitations and wiring.

## Product composition

````{container} product-composition
| Item | Quantity | Description |
| --- | --- | --- |
| RoboBaton 4P V2 main board | 1 | Main control and interface board |
| Camera module | 4 | Four camera inputs |
| Coaxial cable | 4 | Cables connecting the cameras to the main board |
| Accessory cables | 6 | GH1.25 8P to RJ45 cable, GH1.25 4P, GH1.25, SH1.0 2P, SH1.0 3P, and XT30 power cable with XT30 female connector |
| Power supply | 1 | DC 12 V / 1.5 A adapter |
````

## Main parameters

````{container} product-parameters
| Item | Public information |
| --- | --- |
| Platform | D-Robotics X5, 8-core ARM Cortex-A55 @ 1.5 GHz |
| Memory | 4 GB (1 GB fixed for system and hardware) |
| Storage | 32 GB |
| Cameras | 4 RGB cameras: CAM1, CAM2, CAM3, CAM4 |
| Standard image output | NV12; native `1280x1088`, with VSE scaling to `640x480` / `720x480` / `1280x720`; rotation `90/270` swaps external width/height |
| Camera frame rate | Default `30fps`; supports `25fps`, `30fps`, `40fps`, `50fps`, and `60fps` |
| FOV | Camera A / B: horizontal 148.4° / 115.6°, vertical 126.6° / 96.8°, diagonal 193.8° / 157.2° |
| IMU | V2 TDK ICM-42670-P; native `25/50/100/200/400/800/1600Hz`; default YAML: `1600Hz` for non-ROS, `800Hz` for ROS2 |
| USB | USB-C 3.0 |
| Ethernet | Gigabit Ethernet, GH1.25 8P connector |
| CAN | SH1.0 2P connector, CAN FD supported |
| TF card slot | Supports up to 512 GB |
| Other interfaces | User UART × 2, PPS input × 1, DEBUG UART × 1 |
| Dimensions | 55 × 40 × 23 mm |
| non-ROS | RTSP ports `554..557`, path `/PRR`, H.264 default with H.265 optional; IMU / UART / CAN examples, mutually exclusive bag / MP4 saving, exposure observations |
| ROS2 | raw / compressed images, CameraInfo, exposure observations, IMU, temperature; compressed uses X5 hardware JPEG; no RTSP, TF, or calibration |
````

`CAM1`–`CAM4` map to software `cam0`–`cam3` in order; camera A / B FOV specifications are listed above. See [Hardware Connection and Safety](hardware-and-safety.md#camera-interface).

Cameras support only full four-camera operation or single-sensor diagnostics, not 2/3 cameras; rotation `180` requires `30fps`. Configurable parameters do not establish sustained rates, pressure, lossless delivery of all data, or long-recording acceptance. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.

## Dimensions and mounting holes

The following drawings show dimensions and mounting-hole positions for the V2 main board and camera board. All dimensions are in millimeters. Use the annotations in the drawing for the corresponding board when locating mounting holes.

````{container} dimension-drawings
```{figure} ../../image/board_size.png
:alt: RoboBaton 4P V2 main-board dimensions and four mounting holes in millimeters
:width: 320px
:align: center

V2 main-board dimensions and mounting holes (mm).
```

```{figure} ../../image/cam_size.png
:alt: RoboBaton 4P camera-board dimensions and mounting holes in millimeters
:width: 320px
:align: center

Camera-board dimensions and mounting holes (mm).
```
````

## Installation

1. Read [Hardware Connection and Safety](hardware-and-safety.md) to confirm power, DEBUG_UART, UART1/UART7, and thermal requirements.
2. Install the main board and camera modules with power off.
3. Connect the camera coaxial cables and network cable with power off; the camera FPC/coaxial cables do not support hot-plug, and generic USB-UART adapters only connect TX/RX/GND by default.
4. After checking fixation, cables, thermal, and power, power on the device.
5. Proceed to [First Power-On](first-boot.md) and [Quick Start](../quick-start.md).
