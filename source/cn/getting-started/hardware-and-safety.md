# 硬件连接与安全

```{warning}
V2 相机线束、UART 与任何不明接口都应在断电状态下处理。V2 pinout、电气额定值和热插拔条件尚待产品确认，不能沿用 V1 的 4P UART 图、`500 mA` 限制或热插拔结论。确认连接器、信号顺序、电平、共地与供电方向前不要接线；禁止误接 5V TTL、RS-232 或反灌。
```

## 相机接口

下表仅保留软件 ID、端口和 topic 对应关系；CAM1..CAM4 是 V1 历史标识。V2 物理丝印、J4/J7/J5/J6 与软件 ID 的对应关系、相机子板/FPC 版本、pin11/pin17 功能和电气时序仍待核实。

| 物理丝印 | 软件相机 ID | 默认 RTSP 端口 | ROS2 prefix |
|---|---:|---:|---|
| CAM1 | cam0 / camera ID 0 | `554` | `/robobaton/cam0` |
| CAM2 | cam1 / camera ID 1 | `555` | `/robobaton/cam1` |
| CAM3 | cam2 / camera ID 2 | `556` | `/robobaton/cam2` |
| CAM4 | cam3 / camera ID 3 | `557` | `/robobaton/cam3` |

RTSP path 固定为 `/PRR`；H.264 默认，H.265 可选。Camera callback 暴露 NV12：native `1280x1088`，可经 VSE 缩放至 `640x480`/`720x480`/`1280x720`；旋转 `90/270` 时宽高交换。V1 A/B FOV 和连接器示意不能证明 V2 相机子板、线材或机械兼容性，实际型号和接法待确认。

## 供电、热插拔与散热

| 项目 | 公开结论 |
|---|---|
| 主板供电 | V2 额定输入范围、负载、电源反灌保护和 USB-C 供电/角色边界待确认；不继承 V1 DC `12V ~ 24V` 或“USB-C 非供电口”声明。 |
| 相机 FPC / 同轴线 | 默认断电插拔；V2 线束和方向待确认。 |
| UART 接线 | V2 实际电平、线序、供电方向和额定电流待确认；不能按旧图接线，不声明热插拔支持。 |
| 散热 | V2 风扇/温控阈值和满负载散热能力待确认；保持散热器与风道畅通。 |

## UART

```{figure} ../../image/uart.jpg
:alt: V1 历史 UART 顶视图，不适用于 V2 接线

V1 历史照片，仅用于识别旧产品；不是 V2 UART 位置、电平或 IMU 轴向参考。V2 照片与经核实的 pinout 尚待公布。
```

| 接口 | 用途 | 板端设备 | 连接器 |
|---|---|---|---|
| UART1 | 普通用户 UART；V2 引脚电平待确认 | 软件示例 `/dev/ttyS1`，实板映射待确认 | V2 CN2 5P，完整 pinout 待确认 |
| UART7 | 普通用户 UART；V2 PPS 复用待确认 | 软件示例 `/dev/ttyS7`，实板映射待确认 | V2 CN3 5P，完整 pinout 待确认 |
| DEBUG_UART | 系统控制台/调试，不适用于 `serial_port_demo` | V2 节点、波特率与恢复通道待确认 | 图纸为 3P，V2 实物与线序待确认 |

### 物理视图、信号顺序与供电语义

V2 CN2/CN3 已改为 5P，新增信号不能默认用作硬件流控或 PPS；V1 `GND/TX/RX/3V3` 排列不再是 V2 pinout。DEBUG_UART 图纸沿用 `1.8V`，UART 实际 GPIO_VREF/BOM、适配器电平及连接方向仍须核实。

在确认完整 V2 pinout、电平和供电语义前，不公开供电电流额定值或热插拔承诺。默认断电接线，USB-UART 的 VCC 不连接；确认 TX/RX 交叉、共地，并禁止向板端电源轨反灌。

相机公共触发由 producer 解析 `34130000.gpio` offset `0` 并独占输出；IMU INT1 为 `34120000.gpio` offset `8`。V2 IMU FSYNC 输入与相机触发共网，但其波形/电气边界与曝光关联仍需验收，不代表相机/IMU 硬件样本对齐。

## 相机应用资源约束

- `cam-service` 是相机运行依赖，用户不能停止它。
- 相机应用需要独占 camera/VIO/编码资源；切换 `sensor_demo`、`cam_demo`、ROS2 节点或用户自研相机应用前，先正常退出旧应用。
- 单颗诊断使用 `cam_demo --camera-id 0/1/2/3 --diagnostics`，每次只运行一个相机 demo。
