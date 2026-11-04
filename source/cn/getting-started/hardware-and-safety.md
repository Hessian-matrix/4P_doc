# 硬件连接与安全

```{warning}
相机线束和 UART 默认断电接线。UART1/UART7 逻辑电平为 `3.3V`，DEBUG_UART 为 `1.8V`；禁止误接 5V TTL、RS-232 或反灌。V2 完整 5pin 线序、供电额定值和热插拔条件仍待正式硬件资料确认；接线前必须核实正式接口标识、对端电平及共地，不猜测针脚用途，不承诺 UART 热插拔。
```

## 相机接口

相机物理接口与软件映射如下：

| 物理丝印 | 软件相机 ID | 默认 RTSP 端口 | ROS2 prefix |
|---|---:|---:|---|
| CAM1 | cam0 / camera ID 0 | `554` | `/robobaton/cam0` |
| CAM2 | cam1 / camera ID 1 | `555` | `/robobaton/cam1` |
| CAM3 | cam2 / camera ID 2 | `556` | `/robobaton/cam2` |
| CAM4 | cam3 / camera ID 3 | `557` | `/robobaton/cam3` |

RTSP path 为 `/PRR`，H.264 默认、H.265 可选。NV12 native `1280x1088`，可经 VSE 整幅缩放至 `640x480`/`720x480`/`1280x720`；旋转 `90/270` 时宽高交换。相机 A/B 水平 FOV 保持 `148.4°`/`115.6°`，其余相机参数见[产品介绍](Product_Introduction.md)。

## 供电、热插拔与散热

| 项目 | 公开结论 |
|---|---|
| 主板供电 | V2 额定输入范围、负载、反灌保护和 USB-C 电源角色仍待正式硬件资料确认；只使用产品支持确认匹配的电源。 |
| 相机 FPC / 同轴线 | 断电插拔，不支持热插拔。 |
| UART | UART1/UART7 `3.3V`；完整 5pin 线序和供电脚额定负载待正式 V2 硬件资料确认；默认断电接线，不承诺热插拔。 |
| 散热 | 保持散热器与风道畅通；V2 温控与满负载散热能力须按实际系统验证。 |

## UART

| 接口 | 用途 | 板端设备 | 电平与连接器 |
|---|---|---|---|
| UART1 | 普通用户串口 | `/dev/ttyS1` | `3.3V`，CN2 5pin |
| UART7 | 普通用户串口，独立 IO 默认 PPS 输入 | `/dev/ttyS7` | `3.3V`，CN3 5pin |
| DEBUG_UART | 系统控制台，不用于 `serial_port_demo` | 调试终端 `921600` baud | `1.8V`，3pin |

V2 UART7 的独立 PPS IO 不占用 RX/TX，系统默认配置为 PPS 输入，无需 UART→PPS 复用或引脚切换。完整针脚序号与方向以正式 V2 标识为准，不猜测新增脚位，也不把它当作 RTS/CTS。PPS 源必须满足输入电平并共地，不匹配时使用合适电平转换，见[PPS 同步](../time-sync/pps-sync.md)。

USB-UART 默认只连接 TX/RX/GND，不接 VCC；确认 TX/RX 交叉、适配器电平与共地，防止向板端电源轨反灌。

## 触发与采样

所有相机采集入口使用 VIN LPWM 硬件触发，不使用软件 GPIO。IMU SPI/INT1 由内核 IIO 驱动拥有，应用不得同时以其他路径占用。当前软件不使用 FSYNC 关联；物理共线不提供样本/曝光同步，不把帧到达或主机赋时当实际曝光时刻。

## 相机应用资源约束

- 保持相机依赖 `cam-service` 运行，不停止或重配该服务。
- 切换 `sensor_demo`、`cam_demo`、ROS2 或自研相机应用前，先正常退出旧应用，不能同时占用 camera/VIO/编码资源。
- 单颗诊断使用 `cam_demo --camera-id 0/1/2/3 --diagnostics`，每次只运行一个相机 demo。
