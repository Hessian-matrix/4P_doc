# 产品介绍

```{figure} ../../image/main.png
:alt: RoboBaton 4P 主控板连接四个相机模组的产品总览

V1 历史产品图：发布前必须替换为实际 V2 产品与接口图；不可用于 V2 接线。
```

RoboBaton 4P 是面向 X5 平台的四目相机产品，提供 non-ROS RTSP/IMU/UART 示例，以及 ROS2 图像和 IMU topic 的使用路径。
产品发布边界、版本和兼容性信息见 [产品版本与兼容性](product-and-compatibility.md)，本页只保留产品入门所需的组成、参数和安装顺序。

## 产品组成

| 组成 | 数量 | 说明 |
| --- | --- | --- |
| RoboBaton 4P 主控板 | 1 | 主控与接口板 |
| 相机模组 | 4 | 四路相机输入 |
| 线材和附件 | 4 条同轴线 | 线缆用于连接相机和主板 |

## 主要参数

| 项目 | 公开信息 |
| --- | --- |
| 平台 | 地瓜 X5，8 核 ARM Cortex-A55 @ 1.5 GHz |
| 内存 | 4 GB（系统和硬件固定占用 1 GB） |
| 存储 | 32 GB |
| 相机数量 | 4 路：CAM1、CAM2、CAM3、CAM4 |
| 图像标准输出 | NV12；native `1280x1088`，支持 VSE 缩放至 `640x480`/`720x480`/`1280x720`；旋转 `90/270` 对外宽高交换 |
| non-ROS相机帧率 | 默认`30fps`；支持`25fps`、`30fps`、`40fps`、`50fps`和`60fps` |
| FOV | 相机 A/B 参数保持不变：水平 `148.4°`/`115.6°`、垂直 `126.6°`/`96.8°`、对角 `193.8°`/`157.2°`。 |
| IMU | V2 TDK ICM-42670-P，原生 `25/50/100/200/400/800/1600Hz`，默认 `800Hz`；旧 `500/1000/2000Hz` 不兼容。 |
| non-ROS | RTSP 端口 `554..557`，path `/PRR`，H.264 默认、H.265 可选；同时提供 IMU/UART 示例 |
| ROS2 | raw/compressed 图像、CameraInfo、IMU、温度 topic；compressed 使用 X5 硬件 JPEG；ROS2 路径不提供 RTSP |

相机部分与 V1 保持一致：CAM1..CAM4 依次对应软件 cam0..cam3；相机 A/B 与 FOV 参数不变。参见[硬件连接与安全](hardware-and-safety.md#相机接口)。

## 尺寸安装孔位图

以下 V1 尺寸图发布前必须替换为实际 V2 安装资料；当前不可作为 V2 主板开孔依据。

```{figure} ../../image/size.png
:alt: RoboBaton 4P 主控板和相机板安装尺寸图，单位为毫米

V1 安装图（mm）：V2 实际主板/接口与安装图待替换，发布前必改。
```

## 安装

1. 阅读 [硬件连接与安全](hardware-and-safety.md)，确认供电、DEBUG_UART、UART1/UART7 和散热要求。
2. 在断电状态安装主控板和相机模组。
3. 断电连接相机同轴线、网络线；相机/FPC/同轴线不支持热插拔，通用 USB-UART 适配器默认只接 TX/RX/GND。
4. 检查固定、线缆、散热和供电后上电。
5. 进入 [首次上电与开机使用](first-boot.md) 和 [快速开始](../quick-start.md)。
