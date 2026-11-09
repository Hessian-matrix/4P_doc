# 公开 Demo 源码编译

本页说明如何在开发机交叉编译公开 demo 仓库中的示例代码。X5 板端只运行编译产物，不建议在板端原生编译。

适用范围：

- [`RoboBaton_4p_demo`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/tree/V2_main)：non-ROS 四目 RTSP、标定环视 JPEG/Web、IMU、UART 和 SocketCAN CAN 示例。
- [`RoboBaton_4P_ROS2_demo`](https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo/tree/V2_main)：ROS2 四目 NV12/raw+compressed 图像、CameraInfo、曝光观测、IMU、温度及IMU 时钟元数据 topic 示例。

V2 源码与文档统一使用 `V2_main` 主分支，以下 clone 命令显式选择该分支；已有 checkout 也须切换到 `V2_main` 后再构建。

## 1. 编译边界

公开 demo 仓库编译的是用户侧示例程序：

```text
RoboBaton_4p_demo
├── cam_demo
├── mosaic_rtsp_demo
├── panorama_demo
├── sensor_demo
├── imu_reader_demo
├── serial_port_demo
└── can_demo

RoboBaton_4P_ROS2_demo
├── robobaton_sensors_node
├── robobaton_imu_rate_monitor
└── robobaton_nv12_compressed_image_transport（共享插件）
```

公开 demo 仓库已经携带编译所需的公开头文件和匹配的预编译运行库：

- non-ROS：`include/`、`lib/libicm42670.so*`、`lib/libsc132.so*`、`lib/libprrtsp.so*`；还需要匹配 X5 SDK 的媒体头文件（如 `hbn_api.h`）、`libhbmem.so` 和 `libmultimedia.so`，由交叉编译包提供，不由此 consumer 仓编译。
- ROS2：`include/robobaton_4p_ros2_demo/`、`lib/libicm42670.so*`、`lib/libsc132.so*`，构建时还需要 X5 交叉编译包提供目标侧 ROS2、`hb_media_codec.h`、`libmultimedia.so.1`、`libhbmem.so.1` 和 `libalog.so.1`。

这些仓库不编译底层 ICM42670、SC132 或 PRRTSP producer 源码。如果没有 X5 交叉编译工具链，不能重新编译源码，只能直接使用仓库里的 `demo/` 或已生成的 install 包部署运行。

系统 USB 摄像头程序 `x5-uvc-mosaic` 不在上述根 CMake 编译目标中；其完整后端、独立构建和离线安装工具位于公开 `RoboBaton_4p_demo` 的 [`scripts/env_setup/x5_usb/`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/tree/V2_main/scripts/env_setup/x5_usb)。该构建不需要 Web 服务的 Rust 工具链，但需要匹配的 X5 SDK 和 SC132 ABI3 库。修改其他 non-ROS 拼图或 JPEG 示例不会更新系统 USB 摄像头；源码/函数链接、独立构建命令、离线 `--package` 安装及已有板卡的安全更新见{ref}`USB 开发修改入口 <usb-uvc-development>`。

每套库固定为一份普通文件 `libNAME.so.M.m.p`，加两个同目录相对链接 `libNAME.so.M -> libNAME.so.M.m.p`、`libNAME.so -> libNAME.so.M`。non-ROS 使用 ICM42670、SC132、PRRTSP；ROS2 只使用前两者。同步、打包和 install 保留链接，verifier 拒绝展开别名、错误/绝对/断裂链接。完整复制使用 `tar`、`cp -a` 或 `rsync -a`，不要解引用链接。

non-ROS `runtime-provenance.json` 使用 v3：普通文件字节与链接原始文本分别绑定，源码输入中的链接按链接文本哈希。旧 provenance 的运行包须用当前脚本重新生成；软件版本与 SONAME/ABI 不因此改变。两个 SHA-256 manifest 仍包含别名解析后的字节哈希，不能单独代替链接元数据检查。

当前成套库为 ICM42670 `libicm42670.so.6.0.0`、SONAME `libicm42670.so.6`、九个导出均为 `ICM42670_X5_6.0`；SC132 `libsc132.so.3.0.0`、SONAME `libsc132.so.3`、`LIBSC132_3.0`；PRRTSP `libprrtsp.so.2.0.1`、SONAME `libprrtsp.so.2`、`LIBPRRTSP_2.0`。同步公开头文件与库，移除 ICM42670 旧 `.2/.3/.4/.5` 及 SC132 旧 `.2` 库，成套重建所有 consumer，不建立跨 major 链接。四种启动时间戳组合使用相同二进制/IIO 采集，不构建方案专属二进制，见 [non-ROS 使用](../usage/non-ros-demo.md) 与 [ROS2 使用](../usage/ros2-demo.md)。每种 IMU 模式均要求匹配的内核 IIO V4 capture 模块，现有 V2/V3 模块不兼容；公开 demo 构建/package verifier 不构建、安装或升级内核模块。软件 `2.0.0`、硬件 V2.2、文档修订及 SO ABI 独立。当前 non-ROS HO 短窗证据及未验收范围见{ref}`能力与验证边界 <capability-verification-boundary>`。编译成功不认证四组合运行、吞吐、压力或长录，见{ref}`能力与验证边界 <capability-verification-boundary>`。

当前匹配的 Buildroot 镜像负责提供 `/usr/bin/python3`、C++/SDK 运行库及 `/opt/ros/humble`；应用包负责各自程序、配置、匹配 producer 和工具。ROS2 install 还携带指定的传递依赖与 NumPy 所需 BLAS/LAPACK/Fortran 库，不是只有两个 producer；它不替代系统解释器或 BSP。烧录设备已检查 Python `3.10.12`、non-ROS 实际加载及 ROS2 包环境下版本/包查询。构建和 package/install verifier 不等于全部运行路径已验证，见[当前镜像组成](../ops/system-flashing.md)。

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
git clone --branch V2_main https://github.com/Hessian-matrix/RoboBaton_4p_demo.git
cd RoboBaton_4p_demo
```

### 环视静态依赖与主机离线构建

`panorama_demo` 的 YAML 解析与 JPEG 编解码使用静态 LibYAML/JPEG。正常 X5 配置必须能在工具链的目标搜索路径中找到 AArch64 `yaml.h`、`jpeglib.h`、`libyaml.a` 和 `libjpeg.a`；缺少时先补齐匹配工具链／sysroot，不能链接主机 x86_64 库。需要显式指定时，CMake 接受 `PANORAMA_YAML_INCLUDE_DIR`、`PANORAMA_JPEG_INCLUDE_DIR`、`PANORAMA_YAML_LIBRARY`、`PANORAMA_JPEG_LIBRARY`，均指向对应目标的开发头或静态归档。标准打包重新配置构建目录，因此目标依赖也须在其工具链搜索路径中可发现，不能只依赖将被移除的旧 CMake cache。

只处理主机 JPEG 时，在独立终端使用主机编译器与主机开发包，不传 X5 toolchain：

```bash
sudo apt-get install -y build-essential cmake libyaml-dev libjpeg-dev
cmake -S . -B build_panorama_host -DPANORAMA_OFFLINE_ONLY=ON
cmake --build build_panorama_host --target panorama_demo -j
./build_panorama_host/panorama_demo --calibration config/calibration.yaml \
  --images /path/to/group --once --output /path/to/new-panorama.jpg
```

`PANORAMA_OFFLINE_ONLY=ON` 仅配置环视 JPEG/Web 目标，在 Rust Web、X5 SDK 和 producer 查找之前返回，因此不需要 Rust、cargo-zigbuild、Zig、X5 或传感器 SO；它不是可用于板端采集的完整运行包。主机也必须有静态 `libyaml.a`／`libjpeg.a`，仅运行时共享库不足。输入为同一组的 `cam0.jpg`～`cam3.jpg`，必须匹配标定像素方向和尺寸；程序不从文件名认证同步。去掉 `--once` 使用可信 LAN 静态 Web；输出不得覆盖已有文件。完整参数和算法限制见{ref}`标定环视 <non-ros-panorama>`。

正常 X5 全量构建保持 `PANORAMA_OFFLINE_ONLY=OFF`（默认），仍需要下文固定 Rust Web 工具链及目标静态 YAML/JPEG 依赖；运行包内带 `panorama_demo` launcher／ELF、`config/calibration.yaml` 和 `licenses/panorama/THIRD_PARTY_NOTICES.txt`。板端无需另装这两个静态库，JPEG notice 包含 Independent JPEG Group 的许可说明。本入口不是系统 UVC 后端，不采集 IMU、不录制、不做深度重建；编译或 package verifier 通过不表示实板、性能或接缝精度验收。

完整编译七个 demo 及应用拥有的 `sensor_web`，额外需要主机上精确的 Rust `1.95.0`、cargo-zigbuild `0.23.0`、Zig `0.16.0` 和 `aarch64-unknown-linux-musl` target；板端无需编译器。先在允许联网的依赖准备阶段安装上述工具，并预取 Cargo.lock 依赖；实际构建使用 frozen/offline，不自动安装工具链或依赖。

```bash
export CARGO=/path/to/rust1.95/bin/cargo # 改为已安装的工具链
export PATH="$(dirname "$CARGO"):$PATH" # 同一套 Rust 的 rustc/cargo 与 cargo-zigbuild 必须可发现
rustc --version # 必须为 rustc 1.95.0 (59807616e 2026-04-14)
"$CARGO" fetch --locked --manifest-path web/server/Cargo.toml
cmake -S . -B build_x5 \
  -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN_FILE" \
  -DSENSOR_WEB_CARGO_EXECUTABLE="$CARGO"
cmake --build build_x5 -j
```

`sensor_web` 为静态 Linux ARM64 musl 可执行程序，嵌入页面和 str0m；`sensor_demo` 目标依赖它。运行包包含 `licenses/sensor_web/` 的完整 notice 和 crate 锁。修改 Web 源码/资源/锁后必须重建；verifier 交叉核对 ELF 的 `.sensor_web`、运行时实际读取的 `.sensor_web_runtime` 和当前源码/锁，检查两节均由可加载段覆盖，拒绝仅刷新身份 JSON 的旧 binary。保留这些节及完整运行包来源记录；此一致性检查不是数字签名或独立的编译器真实性证明。独立构建使用 `scripts/build_sensor_web.sh --cargo "$CARGO" --output build_x5/sensor_web`；完整打包可用 `scripts/package_runtime.sh --cargo "$CARGO"`。HTTP、四路 WebRTC、IMU SSE 与录制控制入口保持不变；开销变化须在同设备、同负载下测量，语言替换不等于已获得性能提升。

最终链接由固定 Rust 工具链自带的 `rust-lld` 完成，使用该 ARM64 target 随附的 musl `1.2.5` / mallocng；cargo-zigbuild/Zig 仅编译原生 C/汇编依赖，不提供最终 libc。verifier 另外检查 mallocng 原生符号；不得对 `sensor_web` 执行移除这些符号的 strip，否则运行包验证失败。mallocng 可归还空闲分配组，但不保证关闭网页后 RSS 为零或完全回到初始值，也不构成任意时长无泄漏证明。更新需完整重建运行包并正常重启应用。

也可以只编译单个目标：

```bash
cmake --build build_x5 --target cam_demo -j
cmake --build build_x5 --target mosaic_rtsp_demo -j
cmake --build build_x5 --target panorama_demo -j
cmake --build build_x5 --target sensor_demo -j
cmake --build build_x5 --target imu_reader_demo -j
cmake --build build_x5 --target serial_port_demo -j
cmake --build build_x5 --target can_demo -j
```

仓库也提供了等价脚本入口：

```bash
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_cam_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_mosaic_rtsp_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_sensor_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_imu_reader_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_serial_port_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_can_demo.sh
```

编译产物位于：

```text
build_x5/cam_demo
build_x5/mosaic_rtsp_demo
build_x5/panorama_demo
build_x5/sensor_demo
build_x5/imu_reader_demo
build_x5/serial_port_demo
build_x5/can_demo
```

检查目标架构：

```bash
file build_x5/cam_demo
file build_x5/mosaic_rtsp_demo
file build_x5/panorama_demo
file build_x5/sensor_demo
file build_x5/imu_reader_demo
file build_x5/serial_port_demo
file build_x5/can_demo
```

期望输出包含 `ARM aarch64`。如果输出是 `x86-64`，说明没有使用 X5 交叉 toolchain file。

## 4. 重新生成 non-ROS 运行包

如果需要把重新编译的 demo 发布到仓库的 `demo/` 运行包，使用打包脚本：

```bash
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/package_runtime.sh
```

该脚本会：

1. 重新配置并编译七个 consumer demo 及 `sensor_web`。
2. 从当前仓库的 `lib/` 复制匹配的运行库。
3. 生成顶层启动脚本、`env.sh`、`config/sensor_config.yaml`、`config/calibration.yaml`、环视许可证和 `bin/`。
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
git clone --branch V2_main https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo.git
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
