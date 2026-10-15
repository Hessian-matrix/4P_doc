# 公开 Demo 源码编译

本页说明如何在开发机交叉编译公开 demo 仓库中的示例代码。X5 板端只运行编译产物，不建议在板端原生编译。

适用范围：

- [`RoboBaton_4p_demo`](https://github.com/Hessian-matrix/RoboBaton_4p_demo)：non-ROS 四目 RTSP、IMU 和 UART 示例。
- [`RoboBaton_4P_ROS2_demo`](https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo)：ROS2 四目 NV12/raw+compressed 图像、CameraInfo、IMU 和温度 topic 示例。

## 1. 编译边界

公开 demo 仓库编译的是用户侧示例程序：

```text
RoboBaton_4p_demo
├── cam_demo
├── mosaic_rtsp_demo
├── sensor_demo
├── imu_reader_demo
└── serial_port_demo

RoboBaton_4P_ROS2_demo
├── robobaton_sensors_node
├── robobaton_imu_rate_monitor
└── robobaton_nv12_compressed_image_transport（共享插件）
```

公开 demo 仓库已经携带编译所需的公开头文件和匹配的预编译运行库：

- non-ROS：`include/`、`lib/libicm42670.so*`、`lib/libsc132.so*`、`lib/libprrtsp.so*`。
- ROS2：`include/robobaton_4p_ros2_demo/`、`lib/libicm42670.so*`、`lib/libsc132.so*`，构建时还需要 X5 交叉编译包提供目标侧 ROS2、`hb_media_codec.h`、`libmultimedia.so.1`、`libhbmem.so.1` 和 `libalog.so.1`。

这些仓库不编译底层 ICM42670、SC132 或 PRRTSP producer 源码。如果没有 X5 交叉编译工具链，不能重新编译源码，只能直接使用仓库里的 `demo/` 或已生成的 install 包部署运行。

## 2. 准备交叉编译环境

验证主机为 **Ubuntu 22.04 x86_64**，目标为 **X5 AArch64**。工具包固定使用包内 Arm GNU 11.3.Rel1 编译器；无需安装主机系统 AArch64 交叉编译器。

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake git python3 file binutils pkg-config curl
```

ROS2 构建还需按照 [ROS Humble 官方 Ubuntu 安装说明](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) 配置软件源，然后安装主机工具：

```bash
sudo apt-get install -y ros-humble-ros-base python3-colcon-common-extensions
source /opt/ros/humble/setup.bash
/usr/bin/python3 -c 'import ament_package, catkin_pkg, em, colcon_core'
```

主机 ROS 提供 Python/ament/colcon 构建工具；AArch64 ROS 头、库和导出配置由交叉工具包提供。不要在主机 source 包内目标 ROS 的 setup，也不要用主机 `/opt/ros/humble/lib` 链接 X5 程序。使用系统 Python；若正在使用虚拟环境，先退出。

### 获取与校验 X5 交叉编译包

下载 [x5_4cam_cross_toolchain_20261009.tar.gz](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/x5_4cam_cross_toolchain_20261009.tar.gz)：`2,058,709,673 bytes`（约 `1.92 GiB`），SHA-256 为 `f708547c8936dddc0ce32e0d4a6dfbb605ff7bfc9d711b036ffd0ed982e6b035`。该版本补齐目标 ROS Humble（含 image_transport/pluginlib）、交叉环境脚本、sysroot 链接入口和可搬迁 CMake 导出；仅保证本页两个 consumer 仓库的构建范围。

下载后按下列步骤校验并构建：

```bash
curl -fL --retry 3 -O \
  "https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/x5_4cam_cross_toolchain_20261009.tar.gz"
```

```bash
test "$(stat -c %s x5_4cam_cross_toolchain_20261009.tar.gz)" -eq 2058709673
printf '%s  %s\n' \
  f708547c8936dddc0ce32e0d4a6dfbb605ff7bfc9d711b036ffd0ed982e6b035 \
  x5_4cam_cross_toolchain_20261009.tar.gz | sha256sum -c -
tar -tzf x5_4cam_cross_toolchain_20261009.tar.gz >/dev/null
mkdir -p cross_compile_toolchain
tar -xzf x5_4cam_cross_toolchain_20261009.tar.gz -C cross_compile_toolchain
export X5_TOOLCHAIN_ROOT="$PWD/cross_compile_toolchain/x5_4cam_cross_toolchain_20261009"
source "$X5_TOOLCHAIN_ROOT/setup_4cam_cross_env.sh"
test -f "$TOOLCHAIN_FILE"
test -f "$TARGET_ROS_PREFIX/share/image_transport/cmake/image_transportConfig.cmake"
file -L "$TARGET_ROS_PREFIX/lib/librclcpp.so"
"$CC" --version
```

`file` 应显示 `ARM aarch64`。环境脚本统一设置 `X5_CROSS_ROOT` 为包内 `cross_compile/new`，两个命名的 CMake 工具链使用同一编译器和查找规则。移动工具包后重新 source，并使用新的构建目录。

## 3. 编译 non-ROS demo

获取源码：

```bash
git clone https://github.com/Hessian-matrix/RoboBaton_4p_demo.git
cd RoboBaton_4p_demo
```

完整编译五个 demo：

```bash
cmake -S . -B build_x5 \
  -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN_FILE"
cmake --build build_x5 -j
```

也可以只编译单个目标：

```bash
cmake --build build_x5 --target cam_demo -j
cmake --build build_x5 --target mosaic_rtsp_demo -j
cmake --build build_x5 --target sensor_demo -j
cmake --build build_x5 --target imu_reader_demo -j
cmake --build build_x5 --target serial_port_demo -j
```

仓库也提供了等价脚本入口：

```bash
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_cam_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_mosaic_rtsp_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_sensor_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_imu_reader_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_serial_port_demo.sh
```

编译产物位于：

```text
build_x5/cam_demo
build_x5/mosaic_rtsp_demo
build_x5/sensor_demo
build_x5/imu_reader_demo
build_x5/serial_port_demo
```

检查目标架构：

```bash
file build_x5/cam_demo
file build_x5/mosaic_rtsp_demo
file build_x5/sensor_demo
file build_x5/imu_reader_demo
file build_x5/serial_port_demo
```

期望输出包含 `ARM aarch64`。如果输出是 `x86-64`，说明没有使用 X5 交叉 toolchain file。

## 4. 重新生成 non-ROS 运行包

如果需要把重新编译的 demo 发布到仓库的 `demo/` 运行包，使用打包脚本：

```bash
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/package_runtime.sh
```

该脚本会：

1. 重新配置并编译五个 consumer demo。
2. 从当前仓库的 `lib/` 复制匹配的运行库。
3. 生成顶层启动脚本、`env.sh`、`config/sensor_config.yaml` 和 `bin/`。
4. 写入并校验 `manifest.sha256` 和 `runtime-provenance.json`；独立克隆仓库绑定当前源提交及文件哈希，组合仓库还绑定父仓 gitlink。
5. 输出 `Runtime package generated and verified: <demo-dir>`。

手动校验已生成运行包：

```bash
python3 scripts/verify_runtime_package.py demo
```

自定义 `--build-dir` 必须位于源码仓库内，例如 `build_public_cross`。源码或运行包发生变化后需重新打包；来源验证会拒绝与打包快照不一致的文件。

部署到 X5 时不要直接删除 `/root/demo`，也不要把外层 `demo/` 目录复制成 `/root/demo/demo/`。请统一使用 [部署、升级与回滚](deployment-and-upgrade.md) 中的安全入口：唯一临时目录、完整 `manifest.sha256` 校验、旧应用退出检查、旧目录备份、原子切换、help/smoke 验证和失败回滚。

## 5. 编译 ROS2 demo

获取源码：

```bash
git clone https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo.git
cd RoboBaton_4P_ROS2_demo
```

在已完成第 2 节主机准备与工具包解压的终端中构建：

```bash
source /opt/ros/humble/setup.bash
source "$X5_TOOLCHAIN_ROOT/setup_4cam_cross_env.sh"
CMAKE_BUILD_PARALLEL_LEVEL=4 script/build_x5_ros2.sh \
  --cross-root "$X5_CROSS_ROOT" --parallel-workers 1
```

`X5_CROSS_ROOT` 指向包内 `cross_compile/new`，目标 ROS 位于其 `target_ros/humble`。脚本默认使用这套交叉环境；显式 `--toolchain-file` 优先于环境脚本。无需准备其他业务 overlay 或开发机私有目录。切换工具包后使用新的 `--build-root`，避免复用旧缓存。

脚本会显式传入 X5 CMake toolchain file，并把 colcon 产物固定到本包：

```text
1.ros2_build/
├── build/
├── install/
└── log/
```

install 包位于 `1.ros2_build/install`，默认使用 merged install 布局，并在 install 根目录提供 `robobaton_ros2_env.bash` 作为板端推荐运行入口。构建完成后运行 install verifier：

```bash
python3 script/verify_install.py 1.ros2_build/install
```

该 verifier 检查 ROS2 install runtime 文件、可执行文件、NV12 compressed image_transport 插件、相关动态库、RUNPATH、runtime 环境脚本、relocatable Bash setup 和 `abi_manifest.sha256`。它不替代板端 topic、NV12 布局或 IMU 频率检查。

常用覆盖项：

```bash
script/build_x5_ros2.sh \
  --install-base install_x5 \
  --parallel-workers 1 \
  -- --event-handlers console_direct+
```

相对 `--build-base`、`--install-base` 和 `--log-base` 会按 ROS2 demo 仓根目录解析。

部署到 X5 时不要直接 streaming tar，也不要只依赖 `abi_manifest.sha256` 判断完整 install tree。ROS2 install 部署使用确定性 archive checksum + runtime ABI 子集校验流程，详见 [ROS2 Demo 使用](../usage/ros2-demo.md) 与 [部署、升级与回滚](deployment-and-upgrade.md)。

## 6. 常见问题

| 现象 | 处理 |
|---|---|
| `Missing ... libicm42670/libsc132/libprrtsp` | 确认公开 demo 仓库的 `lib/` 完整；公开 demo 只编译 consumer 示例，不从源码生成 producer 库。 |
| `Missing consumer toolchain file` | 检查 `TOOLCHAIN_FILE` 是否指向真实的 `aarch64_x5_host_toolchain.cmake`。 |
| `file build_x5/...` 显示 `x86-64` | 重新配置 CMake，确保传入 `-DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN_FILE"`。 |
| 只复制 `build_x5/` 下的单个可执行文件后板端找不到库 | 使用 `scripts/package_runtime.sh` 生成完整 `demo/`，并完整部署 `demo/` 内容。 |
| ROS2 构建找不到 `ament_package` | 先 `source /opt/ros/humble/setup.bash`，确认 `/usr/bin/python3` 能导入 `ament_package`。 |
| ROS2 install verifier 失败 | 使用完整 `1.ros2_build/install`，不要只复制单个节点或单个 `.so`。 |
