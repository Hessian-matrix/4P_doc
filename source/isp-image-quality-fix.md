# ISP 图像质量修复

(isp-image-quality-fix)=

```{note}
本页提供更新版 SC132GS ISP 调优参数 `sc132gs_tuning.json`，用于改善四路相机在部分光照场景下的图像质量表现。该修复只替换板端 ISP 参数文件，不修改 Demo 运行包，不需要重新部署 `/root/demo`。
```

```{warning}
替换后必须重启 X5 才会生效。操作期间保持供电稳定；不要在正在执行保存任务或相机长测时替换。替换前必须备份原文件。
```

## 1. 适用范围

本修复包为 `RoboBaton_4p_demo` 仓中的：

```text
patch/sc132gs_tuning.json
```

只对以下目标适用：

| 项目 | 要求 |
|---|---|
| 板型 | `board_id=0x0505` 或 `board_id=0x0506`（已在 `0x0506` 验证，`0x0505` 待确认） |
| 根文件系统 | `/etc/version` 包含 `PL5.1` 的 Buildroot |
| 相机 | SC132GS 四目，板端存在 `/usr/hobot/lib/sensor/sc132gs_tuning.json` |

替换前必须确认 `/usr/hobot/lib/sensor/sc132gs_tuning.json` 存在；不存在说明该板的 ISP 参数布局不同，停止操作并联系产品支持。

## 2. 修复前确认

先退出正在运行的相机应用和数据保存任务。保持 `cam-service` 运行，不要把停止 `cam-service` 作为修复步骤。

在开发机确认修复包来自产品交付包或已批准的 `RoboBaton_4p_demo` 源码包。文件 SHA-256 应为：

```text
0424249f9dd100f0ae6e2926ebb6cb1a36eb6615ba03071fa705eec66a2f7589
```

在保存文件的开发机目录执行：

```bash
sha256sum sc132gs_tuning.json
```

输出必须与上面的 SHA-256 一致。如果不一致，停止操作并重新获取修复包。

## 3. 上传并替换板端文件

### 开发机终端

把文件上传到 X5，然后登录板端：

```bash
X5_IP=192.168.1.12  # 改成实际板卡地址
scp sc132gs_tuning.json root@${X5_IP}:/tmp/sc132gs_tuning.json.new
ssh root@${X5_IP}
```

下面直到 `reboot` 之前的命令全部直接在这个 X5 SSH 终端中执行。

### X5 板端 SSH 终端

备份原文件、校验新文件、再替换：

```bash
cp -p /usr/hobot/lib/sensor/sc132gs_tuning.json \
      /usr/hobot/lib/sensor/sc132gs_tuning.json.bak_$(date +%Y%m%d_%H%M%S)
sha256sum /tmp/sc132gs_tuning.json.new
mv /tmp/sc132gs_tuning.json.new /usr/hobot/lib/sensor/sc132gs_tuning.json
sha256sum /usr/hobot/lib/sensor/sc132gs_tuning.json
```

替换后的 SHA-256 必须仍为 `0424249f...`。备份文件与替换文件同目录，回滚时使用。

## 4. 重启生效

ISP 参数在相机初始化时加载，替换后必须重启：

```bash
reboot
```

重启完成后 `cam-service` 会随系统自动启动；重新启动你的相机应用（例如 `/root/demo/sensor_demo`）后即按新参数运行。

## 5. 验收

四路 RTSP 分别在 `554–557` 端口拉流观察，任选一路示例：

```bash
ffplay -rtsp_transport tcp rtsp://<X5_IP>:554/PRR
```

验收要点：

- 四路均能正常出流；
- 画面曝光正常，高光不过曝、暗部有层次；
- 无明显偏色，白平衡在光照条件变化后能收敛；
- 色彩还原和细节符合预期。

如果画面异常，先用回滚步骤恢复旧参数，再联系产品支持。

## 6. 效果说明

新参数相对旧参数更新了以下 ISP 模块的启用状态和参数（依据新旧文件差异整理）：

| 模块 | 变更 |
|---|---|
| AE 自动曝光 | 更新曝光时间表和增益阻尼参数，改善曝光收敛速度与稳定性 |
| AWB 白平衡 | 更新权重参数，改善混合光源下的白平衡准确性 |
| BLS 黑电平、LSC 镜头阴影校正、CCM 颜色矩阵 | 启用并更新参数，改善暗部层次与色彩还原 |
| DMSC/CPD/EE/GC 等细节与动态场景模块 | 更新参数，改善动态场景表现与边缘清晰度 |

效果以替换后四路实际画面为准；不同光照环境下表现可能不同。

## 7. 回滚

登录 X5 后在板端 SSH 终端执行：

```bash
ls -l /usr/hobot/lib/sensor/sc132gs_tuning.json.bak_*
mv /usr/hobot/lib/sensor/sc132gs_tuning.json.bak_<时间戳> \
   /usr/hobot/lib/sensor/sc132gs_tuning.json
reboot
```

回滚使用步骤 3 创建的备份文件；恢复后同样需要重启生效。

## 8. 问题仍未解决时

登录 X5 后收集以下信息联系产品支持：

```bash
cat /sys/class/socinfo/board_id
cat /etc/version
sha256sum /usr/hobot/lib/sensor/sc132gs_tuning.json
ls -l /usr/hobot/lib/sensor/sc132gs_tuning.json*
```

同时提供替换前后四路 RTSP 的截图或录屏。
