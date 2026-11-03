# 产品介绍

RoboBaton 4P V2 是面向 X5 平台的四目相机产品，提供 non-ROS RTSP/IMU/UART 示例，以及 ROS2 图像和 IMU topic 的使用路径。
产品发布边界、版本和兼容性信息见 [产品版本与兼容性](product-and-compatibility.md)，本页只保留产品入门所需的组成、参数和安装顺序。

## 网页效果图

```{figure} ../../image/4P_overview.png
:alt: RoboBaton 4P 中文网页工作台，包含四路相机、惯性姿态、六轴遥测及录制与保存
:width: 100%
:align: center

中文网页工作台：四路相机、惯性姿态、六轴遥测与录制控制集中在同一首页。画面、数值和录制状态仅为界面示例，以当前设备为准。
```

随板系统开机自动启动联合应用；网页操作见{ref}`首次上电与开机使用 <first-boot-web>`和 [non-ROS Demo 使用](../usage/non-ros-demo.md)。右上角可切换 `CH` / `EN`；姿态是浏览器六轴融合预览，不代表绝对航向或硬件同步验收。

**手机和平板也可预览**：移动设备接入与板卡互通的同一局域网后，可直接用浏览器打开设备网页查看四路影像、姿态和六轴数据，无需安装专用 App。窄屏页面按纵向排列；连接步骤和浏览器限制见{ref}`首次上电 <first-boot-web>`。

配套千兆网线仅用于测试和临时连接，不适合可靠千兆传输；线缆限制与接线说明见 [千兆以太网](hardware-and-safety.md#千兆以太网)。

## 产品组成

````{container} product-composition
| 组成 | 数量 | 说明 |
| --- | --- | --- |
| RoboBaton 4P V2 主控板 | 1 | 主控与接口板 |
| 相机模组 | 4 | 四路相机输入 |
| 同轴线 | 4 | 用于连接相机和主板 |
| 配套线材 | 6 | GH1.25 8P 转 RJ45 线、GH1.25 4P、GH1.25、SH1.0 2P、SH1.0 3P、XT30 电源线 + XT30 母头 |
| 电源 | 1 | DC 12 V / 1.5 A 适配器 |
````

## 主要参数

````{container} product-parameters
| 项目 | 公开信息 |
| --- | --- |
| 平台 | RDK X5，8 核 ARM Cortex-A55 @ 1.5 GHz |
| 内存 | 4 GB（系统和硬件固定占用 1 GB） |
| 存储 | 32 GB |
| 电源输入 | 12~27V |
| 相机 | 4 路 RGB：CAM1、CAM2、CAM3、CAM4 |
| 图像输出 | NV12；原生 `1280x1088`，支持 VSE 缩放至 `640x480` / `720x480` / `1280x720`；旋转 `90/270` 对外宽高交换 |
| 相机帧率 | 默认 `30fps`；支持 `25fps`、`30fps`、`40fps`、`50fps` 和 `60fps` |
| FOV | 相机 A：193.8°(D)，126.6°(H)，148.4°(V) ，相机B:157.2°(D)，96.8°(H)，115.6°(V) |
| IMU | TDK ICM-42670-P；原生 `25/50/100/200/400/800/16000Hz`；默认 `800Hz` |
| USB | USB-C 3.0 |
| 网口 | 千兆以太网，GH1.25 8P 接口 |
| CAN | SH1.0 2P 接口，支持 CAN FD |
| TF 卡槽 | 最高支持 512 GB |
| 其他接口 | 用户 UART × 2、PPS 输入 × 1、DEBUG UART × 1 |
| 尺寸 | 55 × 40 × 23 mm |
| 主体重量 | 65 g |
| non-ROS | RTSP 端口 `554..557`，path `/PRR`，H.264 默认、H.265 可选；IMU / UART / CAN 示例、互斥 bag / MP4 保存、曝光观测 |
| ROS2 | raw / compressed 图像、CameraInfo、曝光观测、IMU、温度；compressed 使用 X5 硬件 JPEG；ROS2 路径不提供 RTSP、TF 或标定 |
````

`CAM1`～`CAM4` 依次对应软件 `cam0`～`cam3`；相机 A / B 的 FOV 参数见上表。参见 [硬件连接与安全](hardware-and-safety.md#相机接口)。

相机仅完整四路或单颗诊断，不支持 2/3 路；旋转 `180` 仅允许 `30fps`。参数可配置不等于持续速率、压力、全数据无损或长录已验收，当前限制见{ref}`能力与验证边界 <capability-verification-boundary>`。

## 尺寸安装孔位图

以下分别为 V2 主板和相机板的尺寸及安装孔位图，单位均为毫米。安装孔位以对应板卡图中的标注为准。

````{container} dimension-drawings
```{figure} ../../image/board_size.png
:alt: RoboBaton 4P V2 主板尺寸及四个安装孔位图，单位为毫米
:width: 320px
:align: center

V2 主板尺寸及安装孔位（mm）。
```

```{figure} ../../image/cam_size.png
:alt: RoboBaton 4P 相机板尺寸及安装孔位图，单位为毫米
:width: 320px
:align: center

相机板尺寸及安装孔位（mm）。
```
````

## 安装

1. 阅读 [硬件连接与安全](hardware-and-safety.md)，确认供电、DEBUG_UART、UART1/UART7 和散热要求。
2. 在断电状态安装主控板和相机模组。
3. 断电连接相机同轴线、网络线；相机/FPC/同轴线不支持热插拔，通用 USB-UART 适配器默认只接 TX/RX/GND。
4. 检查固定、线缆、散热和供电后上电。
5. 进入 [首次上电与开机使用](first-boot.md) 和 [快速开始](../quick-start.md)。
