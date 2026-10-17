# 硬件连接与安全

```{warning}
相机线束和 UART 默认断电接线。UART1/UART7 逻辑电平保持 `3.3V`，DEBUG_UART 保持 `1.8V`；禁止误接 5V TTL、RS-232 或反灌。V2 5pin 线序必须以正式接口标识为准，不能按 V1 4pin 照片接线。供电额定值和热插拔条件仍以 V2 正式硬件资料为准，不继承 V1 `500 mA` 或热插拔验收。
```

## 相机接口

相机部分及物理映射与 V1 保持一致：

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
| 主板供电 | V2 额定输入范围、负载、反灌保护和 USB-C 电源角色以正式硬件资料为准；不继承 V1 DC `12V ~ 24V` 声明。 |
| 相机 FPC / 同轴线 | 断电插拔，不支持热插拔。 |
| UART | UART1/UART7 `3.3V`；完整 5pin 线序和供电脚额定负载以 V2 标识为准；不承诺热插拔。 |
| 散热 | 保持散热器与风道畅通；V2 温控与满负载散热能力须按实际系统验证。 |

## UART

```{figure} ../../image/uart.jpg
:alt: V1 UART 历史照片，V2 产品发布前必须替换

V1 历史接口图：发布前必须替换为实际 V2 5pin 接口图及线序；不是 V2 接线或 IMU 轴向依据。
```

| 接口 | 用途 | 板端设备 | 电平与连接器 |
|---|---|---|---|
| UART1 | 普通用户串口 | `/dev/ttyS1` | `3.3V`，CN2 5pin |
| UART7 | 普通用户串口，独立 IO 默认 PPS 输入 | `/dev/ttyS7` | `3.3V`，CN3 5pin |
| DEBUG_UART | 系统控制台，不用于 `serial_port_demo` | 调试终端 `921600` baud | `1.8V`，3pin |

V2 UART7 的独立 PPS IO 不占用 RX/TX，系统默认配置为 PPS 输入，无需 UART→PPS 复用或引脚切换。完整针脚序号与方向以正式 V2 标识为准，不猜测新增脚位，也不把它当作 RTS/CTS。PPS 源必须满足输入电平并共地，不匹配时使用合适电平转换，见[PPS 同步](../time-sync/pps-sync.md)。

USB-UART 默认只连接 TX/RX/GND，不接 VCC；确认 TX/RX 交叉、适配器电平与共地，防止向板端电源轨反灌。

## 触发与采样

所有相机采集入口统一使用 VIN LPWM 硬件触发。相机与 IMU FSYNC 的物理触发线已统一到同一 IO，不使用软件 GPIO 触发。IMU INT1 为 `34120000.gpio` offset `8`。共用触发线不自动建立 IMU FIFO 样本与图像曝光的一一对应；时钟域、触发捕获和样本关联必须分别验证，不能把到帧时刻当作 LPWM 触发时刻。

## 相机应用资源约束

- 保持相机依赖 `cam-service` 运行，不停止或重配该服务。
- 切换 `sensor_demo`、`cam_demo`、ROS2 或自研相机应用前，先正常退出旧应用，不能同时占用 camera/VIO/编码资源。
- 单颗诊断使用 `cam_demo --camera-id 0/1/2/3 --diagnostics`，每次只运行一个相机 demo。
