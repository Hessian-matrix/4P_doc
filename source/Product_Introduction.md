# 产品介绍

```{figure} image/main.png
:alt: RoboBaton 4P 主控板连接四个相机模组的产品总览

RoboBaton 4P 产品总览。本图用于展示产品组成，不作为接口映射和接线依据。
```

RoboBaton 4P 是面向 X5 平台的四目相机产品，提供 non-ROS RTSP/IMU/UART 示例，以及 ROS2 图像和 IMU topic 的使用路径。
产品发布边界、版本和兼容性信息见 [产品版本与兼容性](product-and-compatibility.md)，本页只保留产品入门所需的组成、参数和安装顺序。

## 产品组成

| 组成 | 数量 | 说明 |
| --- | --- | --- |
| RoboBaton 4P 主控板 | 1 | 主控与接口板 |
| 相机模组 | 4 | 四路相机输入 |
| 线材和附件 | 4 条同轴线 | 线缆、固定和辅助附件以正式包装清单为准 |

## 主要参数

| 项目 | 公开信息 |
| --- | --- |
| 平台 | 地瓜 X5，8 核 ARM Cortex-A55 @ 1.5 GHz |
| 内存 | 4 GB（系统和硬件固定占用 1 GB） |
| 存储 | 32 GB |
| 相机数量 | 4 路：CAM1、CAM2、CAM3、CAM4 |
| 图像标准输出 | NV12 `1280x1088` |
| 帧率 | 默认`30fps`；仅支持`25fps`和`30fps` |
| FOV | H `148.4°` / V `126.6°` / D `193.8°` |
| IMU | TDK ICM-42688-P，支持 `25/30Hz` 输出，默认 `30Hz` |
| non-ROS | RTSP 端口 `554..557`，path `/PRR`，H.264 默认、H.265 可选；同时提供 IMU/UART 示例 |
| ROS2 | raw/compressed 图像、CameraInfo、IMU、温度 topic；compressed 使用 X5 硬件 JPEG；ROS2 路径不提供 RTSP |

相机物理丝印与软件编号映射为 CAM1 -> cam0、CAM2 -> cam1、CAM3 -> cam2、CAM4 -> cam3；完整端口和 topic 映射见 [硬件连接与安全](hardware-and-safety.md#相机接口)。

## 尺寸安装孔位图

左图为主控板元件面顶视图，右图为相机板顶视图；尺寸仅作为安装参考。

```{figure} image/size.png
:alt: RoboBaton 4P 主控板和相机板安装尺寸图，单位为毫米

RoboBaton 4P 主控板和相机板安装尺寸参考图，单位为 mm。
```

## 安装

1. 阅读 [硬件连接与安全](hardware-and-safety.md)，确认供电、DEBUG_UART、UART1/UART7 和散热要求。
2. 在断电状态安装主控板和相机模组。
3. 断电连接相机同轴线、网络线；相机/FPC/同轴线不支持热插拔，通用 USB-UART 适配器默认只接 TX/RX/GND。
4. 检查固定、线缆、散热和供电后上电。
5. 进入 [首次上电与开机使用](first-boot.md) 和 [快速开始](quick-start.md)。
