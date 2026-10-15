# 产品介绍

```{figure} ../../image/main.png
:alt: RoboBaton 4P 主控板连接四个相机模组的产品总览

RoboBaton 4P 历史产品组成示意；不作为 V2 板卡照片、接口映射和接线依据。
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
| FOV | V1 相机 A/B 形态曾分别标称水平 `148.4°`/`115.6°`、垂直 `126.6°`/`96.8°`、对角 `193.8°`/`157.2°`；V2 子板、镜头与实际 FOV 待确认。 |
| IMU | V2 TDK ICM-42670-P，原生 `25/50/100/200/400/800/1600Hz`，默认 `800Hz`；旧 `500/1000/2000Hz` 不兼容。 |
| non-ROS | RTSP 端口 `554..557`，path `/PRR`，H.264 默认、H.265 可选；同时提供 IMU/UART 示例 |
| ROS2 | raw/compressed 图像、CameraInfo、IMU、温度 topic；compressed 使用 X5 硬件 JPEG；ROS2 路径不提供 RTSP |

cam0..cam3 是软件相机 ID；V2 物理接口/丝印与 ID 的对应关系及 A/B FOV 是否沿用旧相机子板尚待核实，不要依赖旧照片或旧 FOV 选型。参见[硬件连接与安全](hardware-and-safety.md#相机接口)。

## 尺寸安装孔位图

以下是历史主控板和相机板安装图，不代表已核实的 V2 外形/孔位；V2 安装尺寸与 FPC/线束版本待确认。

```{figure} ../../image/size.png
:alt: RoboBaton 4P 主控板和相机板安装尺寸图，单位为毫米

RoboBaton 4P 历史安装尺寸参考（mm），不可作为 V2 开孔尺寸。
```

## 安装

1. 阅读 [硬件连接与安全](hardware-and-safety.md)，确认供电、DEBUG_UART、UART1/UART7 和散热要求。
2. 在断电状态安装主控板和相机模组。
3. 断电连接相机同轴线、网络线；相机/FPC/同轴线不支持热插拔，通用 USB-UART 适配器默认只接 TX/RX/GND。
4. 检查固定、线缆、散热和供电后上电。
5. 进入 [首次上电与开机使用](first-boot.md) 和 [快速开始](../quick-start.md)。
