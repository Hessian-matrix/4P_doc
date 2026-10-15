# Product Introduction

```{figure} ../../image/main.png
:alt: RoboBaton 4P main board connected to four camera modules, product overview

Historical RoboBaton 4P product-composition illustration; not V2 board photography, interface mapping, or wiring guidance.
```

RoboBaton 4P is a four-camera product for the X5 platform. It provides non-ROS RTSP/IMU/UART examples, plus ROS2 image and IMU topic usage paths.
For release boundaries, versions, and compatibility, see [Product Version and Compatibility](product-and-compatibility.md). This page only covers the composition, parameters, and installation order needed to get started.

## Product composition

| Item | Quantity | Description |
| --- | --- | --- |
| RoboBaton 4P main board | 1 | Main control and interface board |
| Camera module | 4 | Four camera inputs |
| Cables and accessories | 4 coaxial cables | Cables connecting the cameras to the main board |

## Main parameters

| Item | Public information |
| --- | --- |
| Platform | D-Robotics X5, 8-core ARM Cortex-A55 @ 1.5 GHz |
| Memory | 4 GB (1 GB fixed for system and hardware) |
| Storage | 32 GB |
| Camera count | 4: CAM1, CAM2, CAM3, CAM4 |
| Standard image output | NV12; native `1280x1088`, with VSE scaling to `640x480`/`720x480`/`1280x720`; rotation `90/270` swaps external width/height |
| non-ROS camera fps | default `30fps`; supports `25fps`, `30fps`, `40fps`, `50fps`, and `60fps` |
| FOV | V1 camera forms A/B historically specified horizontal `148.4°`/`115.6°`, vertical `126.6°`/`96.8°`, diagonal `193.8°`/`157.2°`; V2 sub-board, lens, and actual FOV pending confirmation. |
| IMU | V2 TDK ICM-42670-P, native `25/50/100/200/400/800/1600Hz`, default `800Hz`; old `500/1000/2000Hz` rates are incompatible. |
| non-ROS | RTSP ports `554..557`, path `/PRR`, H.264 default with H.265 optional; also provides IMU/UART examples |
| ROS2 | raw/compressed image, CameraInfo, IMU, and temperature topics; compressed uses X5 hardware JPEG; the ROS2 path does not provide RTSP |

cam0..cam3 are software camera IDs; V2 physical connector/silkscreen mapping and whether A/B FOV values carry over to the new camera sub-board remain unverified. Do not select wiring or FOV using old images. See [Hardware Connection and Safety](hardware-and-safety.md#camera-interface).

## Dimensions and mounting holes

These are historical main-board and camera-board mounting views, not verified V2 dimensions or hole positions; V2 mounting dimensions and FPC/harness revision are pending confirmation.

```{figure} ../../image/size.png
:alt: RoboBaton 4P main board and camera board mounting dimensions in millimeters

Historical RoboBaton 4P mounting reference (mm); not valid as V2 drilling dimensions.
```

## Installation

1. Read [Hardware Connection and Safety](hardware-and-safety.md) to confirm power, DEBUG_UART, UART1/UART7, and thermal requirements.
2. Install the main board and camera modules with power off.
3. Connect the camera coaxial cables and network cable with power off; the camera FPC/coaxial cables do not support hot-plug, and generic USB-UART adapters only connect TX/RX/GND by default.
4. After checking fixation, cables, thermal, and power, power on the device.
5. Proceed to [First Power-On](first-boot.md) and [Quick Start](../quick-start.md).
