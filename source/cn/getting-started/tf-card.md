# TF 卡（microSD）使用

## 1. 用途与安全边界

TF 卡可作为已烧录系统的数据盘；使用数据盘不需要重新烧录系统，也不改变系统启动介质。本文面向带 TF 卡槽、且 BSP 已启用 SD 控制器的板型，不是 TF 卡启动或烧录教程。

```{warning}
TF 热插拔硬件修复已由用户确认，但不代表所有板卡/BSP/卡型号均已认证，也不允许录制或写入中拔卡。取卡前结束采集和保存，等待收尾、同步并成功卸载；未确认适用修复的硬件仍采用关机断电插拔。卡内有数据时先备份。不要对尚未确认身份的设备执行分区、格式化、修复或裸设备写入，尤其不要操作系统 eMMC。本文不提供自动格式化或开机自动挂载脚本。
```

“卡已插入”“控制器存在”“出现 SD 块设备”“文件系统已挂载”“读写和录制成功”是不同状态。只有创建目录或看到 `/media`，不代表 TF 已挂载；`/media` 本身可能只是 tmpfs，挂载失败后继续保存会写到内存或系统盘。

## 2. 只读确认系统是否识别

在板端终端执行：

```sh
cat /proc/partitions
lsblk -o NAME,MAJ:MIN,RM,SIZE,RO,TYPE,FSTYPE,MOUNTPOINT
for d in /sys/class/block/mmcblk*; do
    [ -f "$d/device/type" ] || continue
    printf '%s: ' "${d##*/}"
    cat "$d/device/type"
done
cat /proc/mounts
```

按类型区分，不只看设备名或 `RM` 列：

| 观测 | 含义与下一步 |
|---|---|
| 整盘 `device/type` 为 `MMC` | 通常为板载 eMMC；结合根分区与挂载核对，不能当 TF 格式化。 |
| 整盘 `device/type` 为 `SD`，出现 `/dev/mmcblkN` | TF 已枚举；继续确认分区、文件系统与挂载。编号不保证固定。 |
| 出现 `/dev/mmcblkNp1` | 已解析到第一个分区，不代表已挂载或可以写入。 |
| 只有 MMC，没有任何 SD 块设备 | TF 尚未枚举；不是单纯“未挂载”，先排查第 7 节，不执行挂载或格式化。 |
| MMC 总线上只有额外的 `SDIO` 设备 | 可能是无线模块，不是 TF 存储盘。 |

例如，若 `/dev/mmcblk0p9` 挂载为 `/`，且 `mmcblk0/device/type` 是 `MMC`，该设备是系统盘；不能因为它显示约 32GB 就把它当作插入的卡。

## 3. 选择设备与文件系统

**只有上一节已确认 SD 设备后才继续。** 下列变量是示例，必须按现场结果修改；后续各段在同一个板端 shell 中执行：

```sh
TF_DISK=mmcblk1             # 改成 type=SD 的整盘名
TF_DEV=/dev/mmcblk1p1       # 改成该卡实际文件系统所在分区
TF_MOUNT=/media/tfcard      # 专用挂载点，不覆盖已有业务目录
cat "/sys/class/block/$TF_DISK/device/type"
lsblk -o NAME,MAJ:MIN,SIZE,RO,TYPE,FSTYPE,MOUNTPOINT "/dev/$TF_DISK"
blkid -p "$TF_DEV"
findmnt -rn -S "$TF_DEV" -o SOURCE,TARGET,FSTYPE,OPTIONS
cat /proc/filesystems
```

未挂载时 `findmnt -S` 无输出并返回非零是正常情况。若已有挂载，先确认其用途，使用已确认的挂载点，不重复挂载或覆盖它。若卡为整盘文件系统而没有分区，仅在 `blkid -p /dev/mmcblkN` 确认后将 `TF_DEV` 改为整盘路径；不要猜测或创建 `p1`。`blkid` 无法识别文件系统时先备份并在电脑上检查，不直接格式化。

| 文件系统 | 使用建议 |
|---|---|
| ext4 | Linux 长时间采集优先考虑；Windows 默认不能直接读取。首次准备卡时须考虑目标内核对 ext4 特性的支持。 |
| exFAT | 便于与电脑交换大文件；须确认当前 BSP 内核或配套驱动支持，不能仅凭电脑可读认定板端支持。 |
| FAT32（`vfat`） | 单文件最大 `4GiB−1` 字节，不适合可能超过此限制的 bag 或单路 MP4。不能假设 recorder 会自动分卷。 |

卡容量、速度等级和型号兼容范围须按实际板型与 BSP 验证；文件系统驱动存在不等于卡已识别，更不等于已通过持续写入验收。准备新卡应先在电脑备份数据，确认选中的是 TF 卡，再使用合适工具分区和格式化，不能套用系统盘设备名。

## 4. 手动挂载

以下是用户主动挂载步骤，会改变系统挂载状态。确认卡已识别、文件系统健康、挂载点空闲后执行；子 shell 中任一步失败即停止：

```sh
(
    set -eu
    test "$(cat "/sys/class/block/$TF_DISK/device/type")" = SD
    test -b "$TF_DEV"
    if [ "$TF_DEV" != "/dev/$TF_DISK" ]; then
        test "$(lsblk -ndo PKNAME "$TF_DEV")" = "$TF_DISK"
    fi
    if findmnt -rn -S "$TF_DEV"; then
        echo 'Device is already mounted; identify its purpose first.' >&2
        exit 1
    fi
    if mountpoint -q "$TF_MOUNT"; then
        echo 'Mountpoint is in use; identify its purpose first.' >&2
        exit 1
    fi
    mkdir -p "$TF_MOUNT"
    FSTYPE=$(blkid -p -s TYPE -o value "$TF_DEV")
    case "$FSTYPE" in
        ext4|exfat|vfat) ;;
        *) echo 'Filesystem is unidentified or outside this example.' >&2; exit 1 ;;
    esac
    mount -t "$FSTYPE" -o rw,nosuid,nodev,noexec "$TF_DEV" "$TF_MOUNT"
    findmnt -rn -M "$TF_MOUNT" -o SOURCE,TARGET,FSTYPE,OPTIONS
    df -h "$TF_MOUNT"
)
```

必须确认输出的 SOURCE 对应选定 TF 分区、文件系统符合预期且 OPTIONS 包含 `rw`，才能写数据。此挂载点仅用于数据，`noexec` 不用于运行卡上的程序。挂载点原有文件会被挂载遮住，所以只使用专用空目录。

如仅需查看已有文件，可将示例的 `rw,nosuid,nodev,noexec` 改为只读选项：ext4 使用 `ro,noload,nosuid,nodev,noexec`，exFAT/FAT32 使用 `ro,nosuid,nodev,noexec`。ext4 的单独 `ro` 仍可能回放日志而写卡；`noload` 跳过日志恢复，未干净卸载的卡可能呈现不一致数据，不适合直接作为正常使用验收。重要或损坏数据应先制作备份，再在未挂载状态下处理。

手动挂载不会自动跨重启恢复；每次开机或换卡后重新检查。不要直接复制通用 `/etc/fstab` 条目：BSP 的挂载时序、卡缺失处理、UUID 唯一性和应用启动前置条件都需要单独确认。

## 5. 保存采集数据到 TF 卡

先按[数据保存](../usage/save-data-guide.md)完成运行包、相机/IMU、`cam-service`、工具与容量检查。保持 `cam-service` 运行，不与其他相机应用并发；不要只把默认路径改成一个未挂载的目录。

以下示例在 TF 挂载身份及可写状态检查通过后，才创建数据目录并启动 MP4 录制：

```sh
(
    set -eu
    test "$(cat "/sys/class/block/$TF_DISK/device/type")" = SD
    test -b "$TF_DEV"
    if [ "$TF_DEV" != "/dev/$TF_DISK" ]; then
        test "$(lsblk -ndo PKNAME "$TF_DEV")" = "$TF_DISK"
    fi
    EXPECTED=$(lsblk -dnro MAJ:MIN "$TF_DEV")
    test -n "$EXPECTED"
    test "$(findmnt -rn -M "$TF_MOUNT" -o MAJ:MIN)" = "$EXPECTED"
    case ",$(findmnt -rn -M "$TF_MOUNT" -o OPTIONS)," in
        *,rw,*) ;;
        *) echo 'TF mount is not writable; stop saving.' >&2; exit 1 ;;
    esac
    df -h "$TF_MOUNT"
    mkdir -p "$TF_MOUNT/robobaton"
    cd /root/demo  # 改成实际完整运行包目录
    ./sensor_demo --fps 30 --codec h264 \
        --sample-rate-hz 800 --print-rate-hz 0 \
        --record-mp4-dir "$TF_MOUNT/robobaton/run_mp4"
)
```

ROS1 bag 可将最后的 `--record-mp4-dir ...` 替换为 `--record-bag "$TF_MOUNT/robobaton/run.bag"`，不要同时启用两种保存模式。通过 YAML 使用时，将 `save_data.save_path` 设置为该 TF 挂载下的绝对路径，启动前仍须执行挂载身份检查。

用 `Ctrl+C` 正常结束前台录制，等待进程收尾；按数据保存说明核对退出码、`SENSOR_MP4_RESULT` 或 `SENSOR_BAG_RESULT` 和最终健康计数。文件出现、RTSP 可播放或挂载成功，都不能替代完整保存判据。正式长录前应以实际采集负载验证卡的持续吞吐、容量余量和数据完整性，不根据卡面标称速度承诺零丢失。

## 6. 卸载与取卡

1. 正常结束所有向卡写入的程序，等 recorder 完成收尾；不要停止 `cam-service` 来代替结束录制。
2. 让当前及其他终端离开挂载点，再同步、卸载：

   ```sh
   cd /
   sync
   umount "$TF_MOUNT"
   findmnt -rn -M "$TF_MOUNT"
   ```

3. 只有 `umount` 成功且最后一条命令无挂载记录，才算卸载完成。`target is busy` 时可用 `fuser -m "$TF_MOUNT"` 查看占用，再按程序自身协议正常退出；不要盲目杀进程或用强制/懒卸载绕过。
4. 匹配已确认 TF 硬件修复的设备，在成功卸载、确认没有使用者后再取卡；其他硬件先正常关机断电。不在写入过程中拔卡或断电，重新插卡后从第 2 节重新确认枚举与挂载身份。

## 7. 常见问题

| 现象 | 排查方法 |
|---|---|
| 卡已插入，但没有 SD 块设备 | 正常关机断电后检查插卡方向和是否到位；用读卡器检查原卡，或换已知正常卡。重新启动后查 `dmesg`、`/sys/class/mmc_host/` 和 `device/type`。不要用格式化解决未枚举问题。 |
| 有 MMC host，但没有 SD 设备 | host 只表示控制器存在。可读 `/sys/kernel/debug/mmcN/ios`（若 BSP 开放），查看时钟/电源状态；`0 Hz` 或 `power mode: off` 本身不能区分接触、检测信号、供电或驱动原因。由产品支持结合实际设备树和卡检测链路排查，不随意切 GPIO、解绑驱动或重扫。 |
| 已有 SD 设备，但没有 `p1` | 卡可能没有分区表，或分区表未解析；先用 `lsblk`/`blkid` 只读检查，备份后再处理。 |
| `unknown filesystem type` / `wrong fs type` | 核对实际分区、`blkid` 与内核支持；也可能是文件系统损坏。不要反复强挂、在线修复或立即格式化。 |
| `Read-only file system` / I/O error | 检查挂载选项、`lsblk` 的 RO 与内核日志。先停止保存并备份；不要强制 remount 来掩盖介质错误。 |
| 文件到约 4GiB 失败 | 检查是否为 FAT32；备份后考虑目标 BSP 支持的 ext4/exFAT。 |
| 重启后目录仍在，但卡未挂载 | 手动挂载不持久；按第 2～4 节重查。目录存在或 `df` 有剩余空间不证明 TF backing，须核对精确挂载点及设备号。 |

命令选项与 ext4 只读日志行为参考 [Linux mount(8)](https://man7.org/linux/man-pages/man8/mount.8.html)。TF 热插拔修复是用户确认，不是本页新增实板复测；不推导新的硬件版本或所有卡型号、容量、自动挂载与长时间录制均已验收。仍以实际系统识别和功能为准，见{ref}`能力与验证边界 <capability-verification-boundary>`。
