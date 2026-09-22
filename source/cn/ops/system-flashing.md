# 系统烧录

(system-flashing)=

```{note}
系统烧录是把 RoboBaton 4P 出厂系统镜像写入板载EMMC的整机级操作，用于恢复出厂系统、升级系统版本或修复无法正常启动的系统。该操作会覆盖板载系统分区，与运行包（`/root/demo`、`/root/ros2_demo`）的部署、升级与回滚不同，后者见 [部署、升级与回滚](../development/deployment-and-upgrade.md)。
```

```{warning}
烧录会覆盖板载 eMMC 并清除其中的全部用户数据。写入期间必须保持供电稳定，严禁断电、拔掉烧录介质或强制重启，否则设备可能无法启动。只使用本页发布的 `v1.3.0` 镜像，不要使用其他 X5 板型的镜像。
```

## 1. 适用范围

本烧录流程只适用于本产品原装板卡；出厂系统镜像只适用于原产品原板，不保证其他目标板的兼容性，见 [产品版本与兼容性](../getting-started/product-and-compatibility.md)。

需要系统烧录的典型场景：

| 场景 | 说明 |
|---|---|
| 系统无法正常启动 | 无法通过 [故障排查](../troubleshooting.md) 恢复，需要重新写入系统 |
| 恢复出厂系统 | 把板载系统恢复到出厂状态 |
| 系统版本升级 | 把系统升级到新的出厂镜像版本 |

只升级 non-ROS demo 或 ROS2 运行包时**不需要**烧录系统；运行包采用整包部署、校验和回滚流程，见 [部署、升级与回滚](../development/deployment-and-upgrade.md)。

## 2. 当前镜像发布状态

- 板端软件 `v1.3.0` 配套的系统镜像已随本版发布，镜像包名 `product-20260918-v1.3.0.tar.gz`。
- 镜像只适用于原产品原板，不保证其他目标板的兼容性（[产品版本与兼容性](../getting-started/product-and-compatibility.md)）。

## 3. 镜像获取与校验

镜像地址:[V1.3.0镜像](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/product-20260918-v1.3.0.tar.gz)
烧录工具地址:[地瓜官方烧录工具](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/xburn-gui_1.2.1_x64-setup.exe)

## 4. 烧录前准备

- 下载烧录工具和镜像文件。
- 安装烧录工具，直接双击 xburn-gui_1.2.1_x64-setup.exe 安装到电脑本地。
- 安装对应驱动：

  ```{figure} ../../image/driver.png
  :alt: xburn 烧录工具要求的驱动安装界面

  xburn 烧录工具要求的驱动安装界面。
  ```

- 烧录会清除板载存储中的全部用户数据，先备份需要保留的数据（例如 `/userdata/` 下的现场配置和证据）。
- 确认镜像与目标板匹配：镜像来自本页 `v1.3.0` 链接，板端为原装板卡。

## 5. 烧录步骤

1. 连接板端 debug-uart 和 usb-c。
2. 选择好串口号和镜像地址：

   ```{figure} ../../image/burn.png
   :alt: xburn 烧录工具主界面，配置串口号与镜像路径

   xburn 烧录工具主界面，配置串口号与镜像路径。
   ```

3. 点击烧录，等待烧录完成。
4. 烧录完成后重启即可。

注意：只使用本页发布的 `v1.3.0` 镜像，不要自行刷写未确认的镜像。

## 6. 烧录后验收

烧录完成后按 [首次上电与开机使用](../getting-started/first-boot.md) 完成最小系统检查：

```bash
hostname
date
df -h /
pgrep -a cam-service
```

## 7. 问题未解决时

烧录后无法启动或系统异常时，停止反复烧录、保留现场，并收集：

- `board_id` 与 `/etc/version`；
- 镜像来源与校验结果；
- 烧录工具输出与退出码；
- 是否实际执行过重启及重启后的现象；
- 如可获得，DEBUG_UART/串口现场信息。

连同 [发布、授权与支持](../release-and-support.md) 的反馈清单提交产品支持。不要在没有产品支持确认的情况下使用其他 X5 镜像重复烧录。