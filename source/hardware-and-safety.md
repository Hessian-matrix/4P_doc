# 硬件连接与安全

```{warning}
RoboBaton 4P 的相机 FPC/同轴线和 UART 接线都应在断电状态下处理。DEBUG_UART 仅支持 `1.8V` 逻辑；UART1/UART7 为用户可编程 `3.3V` UART。禁止把 `3.3V` 或 `5V` 逻辑接到 DEBUG_UART，禁止把 5V TTL 或 RS-232 接到 UART1/UART7。
```

## 相机接口

| 物理丝印 | 软件相机 ID | 默认 RTSP 端口 | ROS2 prefix |
|---|---:|---:|---|
| CAM1 | cam0 / camera ID 0 | `554` | `/robobaton/cam0` |
| CAM2 | cam1 / camera ID 1 | `555` | `/robobaton/cam1` |
| CAM3 | cam2 / camera ID 2 | `556` | `/robobaton/cam2` |
| CAM4 | cam3 / camera ID 3 | `557` | `/robobaton/cam3` |

RTSP path 固定为 `/PRR`；H.264 为默认编码，H.265 可选。Camera callback 暴露标准方向 NV12 `1280x1088` 原始帧；RTSP 客户端接收同一画面的 H.264/H.265 编码流。四路 FOV 均为 H `148.4°` / V `126.6°` / D `193.8°`。同轴线接口直接扣到主板和相机板的底座上面即可。

## 供电、热插拔与散热

| 项目 | 公开结论 |
|---|---|
| 相机供电 | DC `12V ~ 24V`（3S-6S），供电电流建议不低于 `600 mA`。USB-C 口只作为用户开发使用，不作为供电口。 |
| 相机 FPC / 同轴线 | 不支持热插拔；插拔前必须断电。 |
| UART 接线 | 不支持带电误接；接线前区分 DEBUG_UART `1.8V` 与 UART1/UART7 `3.3V`，并确认 TX/RX 交叉和共地关系。 |
| 散热 | 风扇温控，CPU 温度 `> 55°C` 时启动，温度降到`< 50°C`就会停；长时间四路编码前确认散热器、风道和环境温度。 |

## UART

```{figure} image/uart.jpg
:alt: 板卡顶视图中的 DEBUG_UART、UART1 和 UART7 接口位置及电平域

板卡顶视图 UART 接口示意：DEBUG_UART 为 `1.8V` 系统调试口，UART1/UART7 为 `3.3V` 用户可编程串口。以此图的当前顶视图为 IMU 加速度符号参考时，图片上方（远离图片底部 Ethernet/USB 大接口的一侧）为产品前方，图片左侧为产品左侧；该参考只用于说明 IMU 符号，不定义 IMU 与相机、base、optical frame 或其他坐标系之间的变换。
```

| 接口 | 用途 | 板端设备 | 连接器 |
|---|---|---|---|
| DEBUG_UART | 系统控制台/调试 | 不适用于 `serial_port_demo` | GH1.25-3P |
| UART1 | 用户可编程 UART | `/dev/ttyS1` | GH1.25-4P |
| UART7 | 用户可编程 UART | `/dev/ttyS7` | GH1.25-4P |

DEBUG_UART 是系统控制台/调试口，只能使用 `1.8V` USB-UART 适配器。UART1 和 UART7 是用户可编程 `3.3V` UART；`serial_port_demo` 只适用于 UART1/UART7，不适用于 DEBUG_UART。接线时板端 TX 接适配器 RX，板端 RX 接适配器 TX，并始终共地。

UART1 和 UART7 的 3.3V 供电脚共享 `VCC3V3_SYS`。V1 对外设供电额定边界为两个 UART 3.3V 供电脚合计 `500 mA`；外设总电流超过 `500 mA` 时必须使用独立电源。独立电源仍需与板端共地以保证 UART 信号参考一致，并且不得反向灌入板端 3.3V 电源轨。板上 3.3V buck 标注的 `3.3V@3A` 是整板电源轨总设计值，不是单个 UART 端口电流，也不是全部可对外使用的电流。通用 USB-UART 适配器仍默认只接 TX/RX/GND，并断开适配器 VCC。

## 相机应用资源约束

- `cam-service` 是相机运行依赖，用户不能停止它。
- 相机应用需要独占 camera/VIO/编码资源；切换 `sensor_demo`、`cam_demo`、ROS2 节点或用户自研相机应用前，先正常退出旧应用。
- 单颗诊断使用 `cam_demo --camera-id 0/1/2/3 --diagnostics`，每次只运行一个相机 demo。
