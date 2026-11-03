# PPS 同步

## V2 独立 PPS 输入

UART7 接口 CN2（GH1.25 5pin）的 **4 号针为 PPS 输入，5 号针为 GND**，见{ref}`接口接线示意图 <wiring-diagram>`。出厂系统默认已配置 PPS 输入。

```{warning}
PPS 使用 **3.3V 逻辑电平**并须共地；1.8V、5V TTL 或 RS-232 输出须先通过适配的电平转换，不能直接连接。3.3V 是标称逻辑电平，不代表允许过压或支持 5V 输入。

先禁用或隔离信号源输出与外部上拉，再断电接线；板端电源稳定后才启用 PPS。板端掉电或休眠时禁止反灌，停止脉冲但保持高电平不等于隔离。针号不代表插合面中的左右顺序，须按接线图和实物标识核对。
```

## 使用样例：接收外部 1 Hz PPS

本例用于确认外部脉冲已进入 Linux PPS，不修改系统时钟，也不配置相机或 IMU 触发。

### 1. 接线与准备

1. 准备可输出 1 Hz PPS 的外部设备，例如 GNSS 接收机或信号源；确认输出与上述 3.3V 逻辑输入兼容，不兼容时先进行电平转换。
2. 先禁用或隔离信号源输出与外部上拉，再断电接线：将 PPS 输出连接至 UART7 接口 CN2 的 4 号针，双方 GND 接至 5 号针。不要连接未经确认的供电脚。
3. 板端上电稳定后，再启用信号源的 1 Hz 输出，以 `root` 登录 X5。检查镜像是否提供 `ppstest`：

```bash
command -v ppstest
```

若找不到命令，请获取包含 `pps-tools` 的匹配系统镜像或联系产品支持；不要加载虚拟 PPS provider 代替外部输入。

### 2. 识别 PPS 设备

枚举镜像实际注册的 provider，不固定设备编号：

```bash
for p in /sys/class/pps/pps*; do
  [ -d "$p" ] || continue
  printf '%s: ' "$p"
  cat "$p/name"
  cat "$p/path"
done
```

根据 `name`、`path` 和匹配镜像的硬件说明，确认哪一个 provider 对应外部独立 PPS IO；`path` 可能为空，不能仅凭编号或名称中的 `pps` 作判断。没有对应 provider 或无法确定映射时，联系产品支持。

### 3. 观察输入事件

将下列 `N` 替换为上一步已确认的编号，再执行：

```bash
PPS_DEV=/dev/ppsN
ppstest "$PPS_DEV"
```

下面引用 [LinuxPPS 官方文档](https://docs.kernel.org/driver-api/pps.html) 的输出格式示例，仅用于判读字段，不是本产品的实测记录；时间和序号以实际输出为准：

```text
source 0 - assert 1186592699.388832443, sequence: 364 - clear  0.000000000, sequence: 0
source 0 - assert 1186592700.388931295, sequence: 365 - clear  0.000000000, sequence: 0
source 0 - assert 1186592701.389032765, sequence: 366 - clear  0.000000000, sequence: 0
```

- `source 0` 是 `ppstest` 的第一个输入源，不表示设备一定是 `/dev/pps0`。
- `assert` 是捕获事件的时间戳，格式为“秒.纳秒”；其小数位数不等于 UTC 授时精度。
- 已知 1 Hz 输入下，assert sequence 应持续递增，系统时钟稳定时相邻事件时间戳间隔应接近 1 秒。序号不必从 1 开始。
- 只捕获 assert 的 provider 中，`clear` 时间戳和序号可以一直为 0，不据此判定无输入。

保持接线不动，从信号源端停止 PPS 输出，assert sequence 应停止增长，`ppstest` 可能提示等待超时；恢复输出后应继续增长。仅设备节点存在、反复显示同一个时间戳，或虚拟 provider 周期增长，都不能证明接收到外部脉冲。若要更改接线，先断电。

按 `Ctrl+C` 退出 `ppstest`；退出只停止观察，不关闭 PPS 输入配置。持续无事件或等待超时时，依次核对已选 provider、信号源是否启用、电平与共地，以及正式 PPS 接线标识。

## 时间同步边界

PPS 只提供边沿事件，不包含日期/秒号，也不会自动校准系统时钟。NTP、PPS 与 PTP 的组合见[时间同步](system-time-sync.md)。相机和 IMU 的公共 LPWM 触发线与这里的外部 1Hz PPS 输入不是同一合同；PPS 事件通过不等于相机/IMU 样本已对齐。
