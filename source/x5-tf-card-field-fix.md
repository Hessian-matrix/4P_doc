# X5 TF 卡无法识别的内核修复

本页用于处理部分 X5 板在插入 TF 卡后系统无法识别的问题。该问题属于板端 boot 分区中的设备树配置问题，不能通过重新挂载、格式化 TF 卡或重新部署 `/root/demo` 运行包解决。

```{warning}
本操作会写入 boot 分区并要求重启。写入期间必须保持供电稳定；严禁在脚本提示写入或校验时断电、拔电或强制重启。不要手工使用 `dd` 写 boot 分区，只使用本页指定的修复脚本。
```

## 1. 适用范围

本修复包为 `RoboBaton_4p_demo` 仓中的：

```text
patch/x5-fieldfix-buildroot-20260818.tar.gz
```

只对以下目标适用：

| 项目 | 要求 |
|---|---|
| 板型 | `board_id=0x0505` 或 `board_id=0x0506` |
| 根文件系统 | Buildroot，`/etc/version` 包含 `PL5.1` |
| 设备树 | `x5-md-v0p2.dts` 对应的板级布局 |
| boot 镜像 | 12,582,912 bytes，MD5 为 `df51ccd2b809ab85f5ceea52773ec894` |

脚本会在写入前自动检查板型、根文件系统、boot 分区设备、分区大小和镜像指纹。任一条件不匹配都会拒绝写盘。

本页面只描述 Buildroot 修复包。不要把它用于 `/etc/version` 包含 `PL5.2` 的 Ubuntu/Jammy 系统，也不要在无法读取 `board_id` 或 boot 分区的板上强行执行。

修复包同时包含风扇设备树修复，因此脚本验收时会额外输出风扇检查结果；本页的必验目标是 TF 卡能够被识别。

## 2. 修复前确认

先退出正在运行的相机应用和数据保存任务，确保板端没有正在进行的录制或其他需要保持的工作。保持 `cam-service` 运行，不要把停止 `cam-service` 作为修复步骤。

在开发机确认修复包来自产品交付包或已批准的 `RoboBaton_4p_demo` 源码包。归档文件的 SHA-256 应为：

```text
9859e221c46cb514190b64159db622e545cae9639ef8dfda3429b7d9840aa7b1
```

在保存归档文件的开发机目录执行：

```bash
sha256sum x5-fieldfix-buildroot-20260818.tar.gz
```

输出必须与上面的 SHA-256 一致。如果不一致，停止操作并重新获取修复包。开发机不解包修复文件，下一步直接把完整归档上传到 X5。

## 3. 上传归档并在板端解包

### 开发机终端

把完整归档直接上传到 X5 的 `/userdata/`，然后登录板端：

```bash
scp x5-fieldfix-buildroot-20260818.tar.gz root@<x5-ip>:/userdata/
ssh root@<x5-ip>
```

下面直到 `reboot` 之前的命令全部直接在这个 X5 SSH 终端中执行，不要在命令外再嵌套 `ssh root@<x5-ip> "..."`。

### X5 板端 SSH 终端

先校验上传后的归档，再在板端解包：

```bash
cd /userdata
sha256sum x5-fieldfix-buildroot-20260818.tar.gz
tar -tzf x5-fieldfix-buildroot-20260818.tar.gz
tar -xzf x5-fieldfix-buildroot-20260818.tar.gz
cd x5-fieldfix-buildroot-20260818
chmod +x x5-fieldfix.sh
```

板端归档 SHA-256 必须仍为：

```text
9859e221c46cb514190b64159db622e545cae9639ef8dfda3429b7d9840aa7b1
```

确认解包后的脚本、镜像、板型和系统版本：

```bash
test -x x5-fieldfix.sh
test -f boot.img
wc -c boot.img
md5sum boot.img
cat /sys/class/socinfo/board_id
cat /etc/version
readlink -f /dev/block/platform/by-name/boot
```

期望结果：

- `boot.img` 大小为 `12582912` bytes；
- `boot.img` MD5 为 `df51ccd2b809ab85f5ceea52773ec894`；
- `board_id` 为 `0x0505` 或 `0x0506`；
- `/etc/version` 包含 `PL5.1`；
- boot 链接指向有效块设备。

如果任一项不匹配，停止操作，不要执行修复脚本。脚本和 `boot.img` 必须位于同一目录；不要把其他 X5 板型的 boot 镜像放入该目录。

## 4. 先执行只读体检

继续在当前 X5 SSH 终端和解包目录中执行。只读体检不会写 boot 分区：

```bash
./x5-fieldfix.sh --check
echo "check_exit_code=$?"
```

根据退出码判断：

| 退出码 | 含义 | 后续操作 |
|---:|---|---|
| `0` | 前置条件通过，当前需要刷写 | 执行正式修复 |
| `3` | 修复版 boot 已写入且当前内核已生效 | 不要重复刷写，可直接做 TF 卡验收 |
| `4` | 修复版 boot 已写入，但尚未重启 | 执行 `reboot`，再做验收 |
| `1` | 板型、版本、分区、镜像或权限检查失败 | 停止，不要绕过检查 |

体检报告中的当前 boot MD5 只是现状记录。它不是要求必须匹配某个旧版本；只要脚本确认目标板型、分区大小和待写镜像均匹配即可继续。

## 5. 执行修复

只有 `--check` 通过且返回 `0` 时，才继续在当前 X5 SSH 终端执行正式修复：

```bash
./x5-fieldfix.sh
```

脚本会依次完成：

1. 检查 root 权限、板型和 Buildroot 版本；
2. 按 `/dev/block/platform/by-name/boot` 定位 boot 分区；
3. 检查 boot 分区大小与镜像大小严格一致；
4. 校验 `boot.img` 大小和 MD5；
5. 将当前 boot 分区备份到 `/userdata/fieldfix/boot-backup-<旧MD5>.img`；
6. 写入新的 boot 镜像；
7. 清理缓存并回读 boot 分区校验；
8. 将验收脚本和修复记录保存到 `/userdata/fieldfix/`。

脚本具有幂等处理：如果目标 boot 已经写入但尚未重启，脚本会返回 `4`；如果目标 boot 已写入且已经生效，会返回 `3`，不会重复写盘。

看到“修复写入完成”或“已经是修复版本”的提示后，在当前板端终端执行：

```bash
reboot
```

不要在脚本完成前重启。脚本在写入或回读校验失败时会尝试自动回滚；如果自动回滚也失败，不要继续重复操作，应保留现场并联系产品支持。

## 6. 重启后验收 TF 卡

重启完成后插入一张已知可用的 TF 卡。从开发机重新登录 X5：

```bash
ssh root@<x5-ip>
```

进入新的 X5 SSH 终端后，直接执行持久目录中的验收脚本：

```bash
/userdata/fieldfix/x5-fieldfix.sh --verify
```

TF 卡修复通过应同时满足：

- 输出 `SD：cd-inverted 已消失`；
- 输出 `SD：已识别到 /dev/mmcblk1，卡可用`；
- `test -b /dev/mmcblk1` 返回成功。

在同一板端终端额外确认设备节点：

```bash
test -b /dev/mmcblk1
ls -l /dev/mmcblk1 /dev/mmcblk1p* 2>/dev/null || true
```

本系统不自动挂载 TF 卡。确认设备已出现后，按现场文件系统和挂载策略手工挂载对应分区；不要把“没有自动挂载”误判为“TF 卡没有识别”。

如果验收时提示没有插卡，先确认卡已插入，再重新执行 `--verify`。如果提示插卡状态存在但没有 `/dev/mmcblk1`，修复仍未完成，应确认是否已经重启并保留日志：

```bash
cat /userdata/fieldfix/fieldfix.log
```

`/etc/version` 在验收前后保持不变是预期行为，因为本修复不更新 rootfs。

## 7. 回滚

正式修复前，脚本会把原 boot 分区备份到 `/userdata/fieldfix/`，并记录在：

```text
/userdata/fieldfix/last-backup.path
```

如果修复后验收持续失败，且需要恢复修复前的 boot，请登录 X5 后直接在板端 SSH 终端执行：

```bash
/userdata/fieldfix/x5-fieldfix.sh --rollback
reboot
```

回滚脚本会校验备份文件名中的原始 MD5，并在写回后再次回读校验。找不到备份、备份损坏或板型/系统版本检查失败时，脚本会拒绝回滚；不要用手工 `dd` 替代它。

如果修复后板端已经无法启动，就不能通过 SSH 执行回滚，应停止继续上电尝试并联系产品支持，使用 DEBUG_UART/串口或正式救援流程处理。

## 8. 问题仍未解决时

登录 X5 后，在板端 SSH 终端按以下顺序收集信息，不要连续重复刷写：

```bash
cat /sys/class/socinfo/board_id
cat /etc/version
cat /userdata/fieldfix/fixed.info 2>/dev/null || true
cat /userdata/fieldfix/fieldfix.log 2>/dev/null || true
ls -l /dev/mmcblk1 /dev/mmcblk1p* 2>/dev/null || true
```

同时提供：

- 修复包 SHA-256；
- `--check`、正式修复和 `--verify` 的完整输出；
- 是否实际执行过 `reboot`；
- TF 卡型号、容量和文件系统；
- 如果发生无法启动，提供 DEBUG_UART/串口现场信息。

不要在未确认 board ID、rootfs 类型和 boot 分区大小之前使用其他 X5 镜像。该修复只针对本页列出的 Buildroot 板型和镜像指纹。
