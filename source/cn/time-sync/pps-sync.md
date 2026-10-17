# PPS 同步

## V2 独立 PPS 输入

V2 UART7 是 5pin 接口，其中包含一个独立的 PPS 输入 IO。出厂系统默认将该 IO 配置为 PPS 输入，不需要切换 UART7 RX/TX、解绑串口、加载旧模块或安装启动钩子。UART7 串口与独立 PPS 输入不互相复用。

```{warning}
V1 的 UART7→PPS 切换方法不适用于 V2。不要运行旧版引脚切换工具，也不要依据 V1 GPIO 号、`/dev/pps2` 或 4pin 照片接线。产品图和接口图须在发布前替换为实际 V2 资料；以正式 5pin 线序标识识别独立 PPS IO，不猜测针脚序号。
```

串口电平保持不变：UART1/UART7 为 `3.3V`，DEBUG_UART 为 `1.8V`；PPS 输入的接线、电平转换与共地要求见[硬件连接与安全](../getting-started/hardware-and-safety.md)。不要输入 5V TTL 或 RS-232 电平。

## 检查输入事件

先识别镜像实际注册的 PPS provider，不固定设备编号：

```bash
for p in /sys/class/pps/pps*; do
  [ -d "$p" ] || continue
  printf '%s: ' "$p"
  cat "$p/name"
  cat "$p/path"
done
```

确认 provider 对应外部独立 PPS IO 后，用其设备节点观察事件（以下 `N` 必须替换为已确认的编号）：

```bash
ppstest /dev/ppsN
```

接入已知 1Hz 信号时，assert sequence 应连续增长，间隔接近 1 秒；断开信号后应停止。设备节点存在或虚拟 provider 周期增长不证明接收到外部脉冲。没有对应 provider 时，核对匹配的 V2 镜像与接线并联系支持，不回退到 V1 UART 复用方案。

## 时间同步边界

PPS 只提供边沿事件，不包含日期/秒号，也不会自动校准系统时钟。NTP、PPS 与 PTP 的组合见[时间同步](system-time-sync.md)。相机和 IMU 的公共 LPWM 触发线与这里的外部 1Hz PPS 输入不是同一合同；PPS 事件通过不等于相机/IMU 样本已对齐。
