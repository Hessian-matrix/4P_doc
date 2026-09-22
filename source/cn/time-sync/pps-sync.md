# PPS 同步

出厂默认没有开放PPS接口，需要把默认 **UART7 RX** 引脚切换为 Linux PPS 输入。切换工具是 non-ROS Demo 仓库中的 `x5-pps-pin.sh`，配套内核模块是 `x5pps.ko`。

## 1. 文件、版本和前置条件

从公开 non-ROS Demo 仓库取得：

```text
scripts/env_setup/x5-pps-pin.sh
scripts/env_setup/x5pps.ko
```

当前配套模块信息：

| 项目 | 值 |
|---|---|
| 模块文件 | `x5pps.ko` |
| 文件大小 | `13160` bytes |
| SHA-256 | `50337d81b40a62c9bfb5d1b81a55b931a87138a276136f11a130b8056521797f` |
| vermagic | `6.1.83-DR-PL5.1_V1.1.2 SMP preempt mod_unload aarch64` |
| PPS 输入 | 默认 UART7 RX，GPIO `379`，板上 `pin10` |
| Linux PPS 设备 | `/dev/pps2` |
| 默认边沿 | `rising` |

`x5pps.ko` 必须与板端 `uname -r` 匹配。脚本会使用固定 `pps_id=2` 注册 Linux PPS 设备；如果 `/dev/pps2` 已被其他 provider 占用，切换应失败，不要使用 `--force` 绕过设备冲突。

建议把脚本和模块放在重启后仍然存在的 `/userdata` 分区，例如 `/userdata/x5-pps/`。脚本的持久模式文件、开机日志和禁用开关也位于脚本所在目录。

开发机上传：

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
cd /path/to/RoboBaton_4p_demo
ssh root@${X5_IP} "mkdir -p /userdata/x5-pps"
scp scripts/env_setup/x5-pps-pin.sh scripts/env_setup/x5pps.ko \\
  root@${X5_IP}:/userdata/x5-pps/
ssh root@${X5_IP} "chmod 755 /userdata/x5-pps/x5-pps-pin.sh && chmod 644 /userdata/x5-pps/x5pps.ko"
```

板端确认：

```bash
cd /userdata/x5-pps
uname -r
sha256sum x5pps.ko
```

## 2. 切换为 PPS

先停止使用 UART7 的串口程序，并准备可靠的 SSH 或其他恢复入口。然后在 X5 板端执行：

```bash
cd /userdata/x5-pps
./x5-pps-pin.sh --check
./x5-pps-pin.sh pps
./x5-pps-pin.sh status
```

脚本会：

1. 检查 `x5pps.ko` 和 kernel vermagic；
2. 检查 UART7 资源和 console 占用；
3. 解绑 UART7 平台设备；
4. 将默认 UART7 RX mux 切换为 GPIO/PPS 功能；
5. 加载 `x5pps.ko`，参数为 `gpio=379 pps_id=2 edge=rising`；
6. 创建真实 PPS 设备 `/dev/pps2`；
7. 尝试保存持久模式并维护 `/userdata/startup.sh` 开机钩子。

运行时 mux、模块加载与持久化是两个阶段。脚本可能已经完成本次 PPS 运行时切换，但随后因 `mode` 文件或 `/userdata/startup.sh` 写入失败而没有建立重启持久化。命令结束后必须查看完整输出并运行 `status`，分别确认当前 mux/provider 和持久模式/开机钩子。

切换后使用 `status` 确认：

```text
x5pps 已加载: gpio=379 ... pps_id=2 ...
pps2 name=x5pps ...
```

系统中可能同时存在名为 `hobot-pps` 的虚拟/伪 PPS provider。验收必须确认 `/dev/pps2` 对应的 `name` 为 `x5pps`，不能只看设备节点存在。

## 3. 验证 PPS 输入

把外部 PPS 信号接入默认 UART7 RX PPS 输入后执行：

```bash
./x5-pps-pin.sh test --secs 10
```

脚本会比较测试前后的：

- `x5pps` GPIO IRQ 计数；
- PPS assert 计数；
- `/dev/pps2` 的 PPS sequence 计数。

正常结果应在约 10 秒内收到接近 1 Hz 的事件。`test` 通过只证明外部边沿到达当前 GPIO/PPS provider，不证明 NTP/PTP 已锁定，也不证明相机/IMU 时间同步。

PPS 输入应满足产品硬件资料规定的电气条件。当前输入域按 3.3V 处理；1.8V PPS 源不能直接接入，必须使用合适的电平转换。信号源与 X5 必须共地。

如果 `test` 失败，按顺序检查：

1. 外部信号确实接入默认 UART7 RX PPS 引脚；
2. mux 已切换到 GPIO/PPS；
3. 信号边沿与 `rising` 配置一致；
4. 电平、共地和线束正确；
5. `status` 中 `/dev/pps2` 的 provider 名称为 `x5pps`；
6. `/proc/interrupts` 中对应 IRQ 是否增长。

断开外部 PPS 信号后再次运行短测试时，`x5pps` 的事件计数应停止增长；这一步用于排除虚拟 PPS 源误报。

## 4. 还原 UART7

需要恢复普通 UART7 功能时，在板端执行：

```bash
cd /userdata/x5-pps
./x5-pps-pin.sh uart
./x5-pps-pin.sh status
ls -l /dev/ttyS7
```

脚本会卸载 `x5pps`、尝试恢复 UART7 RX/TX mux，并回绑 UART7 平台设备。恢复日志中的 mux 或 tty 警告不能当作成功；恢复后再运行 `serial_port_demo` 前，必须确认 RX/TX mux 均为 UART 功能、`/dev/ttyS7` 存在、持久模式/开机钩子符合预期且没有其他程序占用。

只恢复本次运行、不修改已有重启模式：

```bash
./x5-pps-pin.sh uart --once
```

如果需要让以后每次重启都保持普通 UART7，执行不带 `--once` 的 `uart`。

## 5. UART7 TX 作为可编程 GPIO/IO

PPS 模式使用 UART7 RX 作为 `/dev/pps2` 输入；脚本同时释放 UART7 TX 的 GPIO mux，使 TX 可作为普通 GPIO/IO 由后续应用使用。当前 X5 device tree 中，UART7 TX 对应 GPIO 全局号 `380`，在 LSIO GPIO0 控制器内是 line offset `1`；GPIO chip 的设备编号可能因系统枚举顺序变化，不能直接假定一定是 `/dev/gpiochip0`。

切换 PPS 后先确认脚本状态：

```bash
./x5-pps-pin.sh status
```

应能看到类似：

```text
UART7 TX IO mux: GPIO380 LSIO_UART7_TX = ALT2 (pin8)
```

再在目标板通过 `gpioinfo` 找到代表 LSIO GPIO0 的 GPIO chip，并确认 line offset `1` 没有被其他 consumer 占用：

```bash
gpioinfo
```

下面用变量表示已确认的 chip；不要在未通过 `gpioinfo` 确认前直接假设 `gpiochip0`：

```bash
GPIOCHIP=/dev/gpiochip0   # 替换为 gpioinfo 确认的 LSIO GPIO0 chip
GPIO_LINE=1               # GPIO 全局 380 - GPIO0 base 379
```

### 5.1 软件 1Hz 试验脉冲

确认 `gpioset` 存在：

```bash
command -v gpioset
```

单次输出一个约 100ms 的高电平脉冲：

```bash
gpioset --chip "$GPIOCHIP" \
  --consumer pps-io-test \
  --hold-period 100ms \
  "$GPIO_LINE"=1
```

循环输出近似 1Hz 的软件脉冲：

```bash
while :; do
  gpioset --chip "$GPIOCHIP" \
    --consumer pps-io-test \
    --hold-period 100ms \
    "$GPIO_LINE"=1
  sleep 0.900
done
```

该示例用于验证 TX 线的 GPIO 输出能力和外部接收端，不是硬件定时器/PHC/MCU 产生的精密 PPS 输出。用户态进程启动、调度和 GPIO request/release 都会引入边沿抖动，不能把它作为 NTP/PTP 参考脉冲或相机/IMU 同步源。

### 5.2 输入捕获和 IO 状态识别

确认 `gpiomon` 存在后，可以捕获 TX 线上升沿、下降沿或双边沿：

```bash
command -v gpiomon
gpiomon --chip "$GPIOCHIP" \
  --consumer pps-io-capture \
  --edges both \
  --event-clock monotonic \
  --num-events 10 \
  "$GPIO_LINE"
```

普通 IO 识别也应使用明确的 GPIO consumer，并先确认没有其他程序占用该 line。输入捕获得到的是 Linux GPIO event 的时间和边沿，不等同于外部信号的物理采样时间；需要更严格的边沿精度时，必须增加硬件捕获或示波器/逻辑分析仪验证。

### 5.3 所有权和恢复

- PPS 模式下不要同时运行 `serial_port_demo` 或其他 UART7 程序；
- 不要让两个 GPIO 工具同时请求同一 line；
- `gpioset`/`gpiomon` 结束后是否保持电平由 GPIO 工具和内核实现决定，业务程序需要自行设计安全默认电平；
- 恢复普通 UART7 时执行 `./x5-pps-pin.sh uart`，脚本会同时把 UART7 RX/TX mux 恢复为普通 UART 功能；
- 恢复后再检查 `/dev/ttyS7`，不要让 GPIO consumer 残留占用该 line。

## 6. 重启持久化

不带 `--once` 的 `pps`/`uart` 命令会尝试把模式写入脚本所在目录的 `mode` 文件，并在 `/userdata/startup.sh` 中维护带边界标记的开机钩子。原有 `startup.sh` 内容不会被覆盖。只有命令没有报告持久化错误，且 `status` 同时显示预期 `mode` 和已安装、可执行的开机钩子时，才能按下表判断后续重启行为。

| 操作 | 当前运行时 | 后续重启 |
|---|---|---|
| `pps` | UART7 RX 切到 PPS | 自动切到 PPS，并注册 `/dev/pps2` |
| `uart` | 恢复普通 UART7 | 保持普通 UART7 |
| `pps --once` | 本次切到 PPS | 保持已有持久模式 |
| `uart --once` | 本次恢复 UART7 | 保持已有持久模式 |
| `uninstall` | 不改变当前运行时 | 移除开机钩子和持久模式 |

查看状态：

```bash
./x5-pps-pin.sh status
```

紧急阻止开机钩子：

```bash
touch /userdata/x5-pps/DISABLE
```

恢复开机钩子：

```bash
rm -f /userdata/x5-pps/DISABLE
```

拆除本脚本的开机钩子和持久模式：

```bash
./x5-pps-pin.sh uninstall
```

`uninstall` 不会改变当前已经切换的运行时状态。需要立即恢复 UART7 时，先执行：

```bash
./x5-pps-pin.sh uart --once
./x5-pps-pin.sh uninstall
```

## 7. `--force` 和 `--keep-uart`

如果 UART7 被 Linux console 占用，脚本默认拒绝解绑。只有已经准备好 SSH 或其他恢复路径，并明确接受失去 console 的风险时，才考虑：

```bash
./x5-pps-pin.sh pps --force
```

`--force` 也会绕过模块 vermagic 不匹配的前置拒绝；它不是解决内核版本不匹配的方法。`--keep-uart` 会保留 UART 驱动但借用 mux，可能造成串口/console 无输出，或在电源管理恢复时被 UART 驱动重新抢回。普通切换不要使用：

```bash
./x5-pps-pin.sh pps --keep-uart
```

## 8. 常见问题

### 找不到模块或 vermagic 不匹配

```bash
./x5-pps-pin.sh --check
uname -r
sha256sum /userdata/x5-pps/x5pps.ko
```

不要使用 `--force` 代替匹配的内核模块。

### `/dev/pps2` 不存在或名称不对

执行：

```bash
./x5-pps-pin.sh status
cat /sys/module/x5pps/parameters/gpio
cat /sys/module/x5pps/parameters/pps_id
cat /proc/interrupts
```

只有当 `/dev/pps2` 对应的 sysfs `name` 为 `x5pps` 时，才可把它作为本脚本的真实 PPS 源。周期性增长的 `hobot-pps` 不代表外部 UART7 RX 已收到 PPS。

### UART7 还原后无法使用

确认 `uart` 的回绑日志、mux 状态和设备节点：

```bash
./x5-pps-pin.sh uart
./x5-pps-pin.sh status
ls -l /dev/ttyS7
```

不要在未确认资源归属时手工解绑其他平台设备。

## 9. 与其他时间同步方法的关系

- **PPS**：把外部 PPS 边沿接入 Linux `/dev/pps2`；本脚本和 `x5pps.ko` 负责 mux、模块和事件计数。
- **NTP**：通过网络 NTP server 纪律系统时间，见[系统时间同步](system-time-sync.md)。
- **PTP**：通过 LinuxPTP/PHC 与外部 PTP 对端建立时间关系，见系统时间同步章节中的 PTP 示例。
- **相机/IMU 采样同步**：需要独立的触发、采样身份和时间戳合同；PPS `test` 通过不代表相机/IMU 已硬同步。

当前 PTP master 示例由 `CLOCK_REALTIME` 驱动 PHC；NTP 可以作为该系统时钟的上游，但当前 NTP 脚本会停止 `phc2sys`。组合使用前必须按[时间同步](system-time-sync.md)重新建立并验证 PHC/PTP 链路。PPS 输入也不会自动替代 NTP/PTP。
