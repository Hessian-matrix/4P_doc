# 产品介绍

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
| FOV | 相机 A/B：水平 `148.4°`/`115.6°`、垂直 `126.6°`/`96.8°`、对角 `193.8°`/`157.2°`。 |
| IMU | V2 TDK ICM-42670-P，原生 `25/50/100/200/400/800/1600Hz`，默认 `800Hz`；不支持的速率明确拒绝。 |
| non-ROS | RTSP 端口 `554..557`，path `/PRR`，H.264 默认、H.265 可选；IMU/UART/CAN 示例、互斥 bag/MP4 保存、曝光观测及IMU 时钟元数据 |
| ROS2 | raw/compressed 图像、CameraInfo、曝光观测、IMU、温度及IMU 时钟元数据 topic；compressed 使用 X5 硬件 JPEG；ROS2 路径不提供 RTSP、TF 或标定 |

CAM1..CAM4 依次对应软件 cam0..cam3；相机 A/B 的 FOV 参数见上表。参见[硬件连接与安全](hardware-and-safety.md#相机接口)。

相机仅完整四路或单颗诊断，不支持 2/3 路；旋转 `180` 仅允许 `30fps`。参数可配置不等于持续速率、压力、全数据无损或长录已验收，当前限制见{ref}`能力与验证边界 <capability-verification-boundary>`。

## 尺寸安装孔位图

下图只提供相机板尺寸；V2 主板尺寸、接口和安装孔位资料待确认，不据此推断主板开孔位置。

```{figure} ../../image/size.png
:alt: RoboBaton 4P 相机板安装尺寸图，单位为毫米

相机板安装尺寸（mm）。
```

## 安装

1. 阅读 [硬件连接与安全](hardware-and-safety.md)，确认供电、DEBUG_UART、UART1/UART7 和散热要求。
2. 在断电状态安装主控板和相机模组。
3. 断电连接相机同轴线、网络线；相机/FPC/同轴线不支持热插拔，通用 USB-UART 适配器默认只接 TX/RX/GND。
4. 检查固定、线缆、散热和供电后上电。
5. 进入 [首次上电与开机使用](first-boot.md) 和 [快速开始](../quick-start.md)。
