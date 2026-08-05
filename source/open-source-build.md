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
├── sensor_demo
├── imu_reader_demo
└── serial_port_demo

RoboBaton_4P_ROS2_demo
├── robobaton_sensors_node
└── robobaton_imu_rate_monitor
```

公开 demo 仓库已经携带编译所需的公开头文件和匹配的预编译运行库：

- non-ROS：`include/`、`lib/libicm42688.so*`、`lib/libsc132.so*`、`lib/libprrtsp.so*`。
- ROS2：`include/robobaton_4p_ros2_demo/`、`lib/libicm42688.so*`、`lib/libsc132.so*`，构建时还需要 X5 交叉编译包提供目标侧 ROS2、`hb_media_codec.h`、`libmultimedia.so.1`、`libhbmem.so.1` 和 `libalog.so.1`。

这些仓库不编译底层 ICM42688、SC132 或 PRRTSP producer 源码。如果没有 X5 交叉编译工具链，不能重新编译源码，只能直接使用仓库里的 `demo/` 或已生成的 install 包部署运行。

## 2. 准备交叉编译环境

开发机需要主机侧工具：

- `cmake`
- `make` 或其他 CMake 可用的构建后端
- `python3`
- `readelf` / `file` 等 ELF 检查工具

### 下载 X5 交叉编译包

下载 [x5_4cam_cross_toolchain_20260708.tar.gz](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/x5_4cam_cross_toolchain_20260708.tar.gz)，大小为 `2,044,412,424 bytes`（约 `1.90 GiB`）。该包提供编译公开 demo 所需的 X5 aarch64 工具链、sysroot、平台头文件和运行库。

Linux 下载和可读性检查示例：

```bash
curl -fL --retry 3 -O \
  "https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/x5_4cam_cross_toolchain_20260708.tar.gz"
test "$(stat -c %s x5_4cam_cross_toolchain_20260708.tar.gz)" -eq 2044412424
tar -tzf x5_4cam_cross_toolchain_20260708.tar.gz >/dev/null
```

示例解压和环境变量：

```bash
mkdir -p cross_compile_toolchain
tar -xzf x5_4cam_cross_toolchain_20260708.tar.gz \
  -C cross_compile_toolchain

export X5_TOOLCHAIN_ROOT="$PWD/cross_compile_toolchain/x5_4cam_cross_toolchain_20260708"
export TOOLCHAIN_FILE="$X5_TOOLCHAIN_ROOT/cross_compile/new/toolchain/aarch64_x5_host_toolchain.cmake"

test -f "$TOOLCHAIN_FILE"
cmake --version
```

如果实际解压目录不同，只需要让 `TOOLCHAIN_FILE` 指向真实的 `aarch64_x5_host_toolchain.cmake`。

## 3. 编译 non-ROS demo

获取源码：

```bash
git clone https://github.com/Hessian-matrix/RoboBaton_4p_demo.git
cd RoboBaton_4p_demo
```

完整编译四个 demo：

```bash
cmake -S . -B build_x5 \
  -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN_FILE"
cmake --build build_x5 -j
```

也可以只编译单个目标：

```bash
cmake --build build_x5 --target cam_demo -j
cmake --build build_x5 --target sensor_demo -j
cmake --build build_x5 --target imu_reader_demo -j
cmake --build build_x5 --target serial_port_demo -j
```

仓库也提供了等价脚本入口：

```bash
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_cam_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_sensor_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_imu_reader_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_serial_port_demo.sh
```

编译产物位于：

```text
build_x5/cam_demo
build_x5/sensor_demo
build_x5/imu_reader_demo
build_x5/serial_port_demo
```

检查目标架构：

```bash
file build_x5/cam_demo
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

1. 重新配置并编译四个 consumer demo。
2. 从当前仓库的 `lib/` 复制匹配的运行库。
3. 生成顶层启动脚本、`env.sh`、`config/sensor_config.yaml` 和 `bin/`。
4. 写入并校验 `manifest.sha256`。
5. 输出 `Runtime package generated and verified: <demo-dir>`。

手动校验已生成运行包：

```bash
python3 scripts/verify_runtime_package.py demo
```

部署到 X5 时复制 `demo/` 目录里的内容到 `/root/demo/`，不要复制成 `/root/demo/demo/`；切换前确认旧 demo 已经退出：

```bash
ssh root@<x5-ip> "rm -rf /root/demo.new && mkdir -p /root/demo.new"
tar -C demo -cf - . | ssh root@<x5-ip> "tar -xf - -C /root/demo.new"
ssh root@<x5-ip> "cd /root/demo.new && sha256sum -c manifest.sha256"
ssh root@<x5-ip> "\
  set -e; \
  if pgrep -af 'sensor_demo|cam_demo|imu_reader_demo|serial_port_demo'; then \
    echo 'old non-ROS demo process is still running; exit it before switching'; \
    exit 2; \
  fi; \
  ts=\$(date +%Y%m%d-%H%M%S); \
  if [ -d /root/demo ]; then mv /root/demo /root/demo.bak.\$ts; fi; \
  mv /root/demo.new /root/demo; \
  chmod +x /root/demo/cam_demo /root/demo/sensor_demo /root/demo/imu_reader_demo /root/demo/serial_port_demo /root/demo/bin/*"
```


更完整的失败回滚步骤见 [部署、升级与回滚](deployment-and-upgrade.md)。

## 5. 编译 ROS2 demo

获取源码：

```bash
git clone https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo.git
cd RoboBaton_4P_ROS2_demo
```

准备 ROS Humble 主机环境和 X5 交叉编译包：

```bash
# 将下面路径替换为实际 X5 交叉编译包根目录
export X5_CROSS_ROOT=/absolute/path/to/cross_compile/new
set +u
source /opt/ros/humble/setup.bash
set -u
```

推荐使用包内脚本 clean build：

```bash
script/build_x5_ros2.sh --clean --cross-root "$X5_CROSS_ROOT"
```

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

部署到 X5 时不要直接 streaming tar，也不要只依赖 `abi_manifest.sha256` 判断完整 install tree。ROS2 install 部署使用确定性 archive checksum + runtime ABI 子集校验流程，详见 [ROS2 Demo 使用](ros2-demo.md) 与 [部署、升级与回滚](deployment-and-upgrade.md)。

## 6. 常见问题

| 现象 | 处理 |
|---|---|
| `Missing ... libicm42688/libsc132/libprrtsp` | 确认公开 demo 仓库的 `lib/` 完整；公开 demo 只编译 consumer 示例，不从源码生成 producer 库。 |
| `Missing consumer toolchain file` | 检查 `TOOLCHAIN_FILE` 是否指向真实的 `aarch64_x5_host_toolchain.cmake`。 |
| `file build_x5/...` 显示 `x86-64` | 重新配置 CMake，确保传入 `-DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN_FILE"`。 |
| 只复制 `build_x5/` 下的单个可执行文件后板端找不到库 | 使用 `scripts/package_runtime.sh` 生成完整 `demo/`，并完整部署 `demo/` 内容。 |
| ROS2 构建找不到 `ament_package` | 先 `source /opt/ros/humble/setup.bash`，确认 `/usr/bin/python3` 能导入 `ament_package`。 |
| ROS2 install verifier 失败 | 使用完整 `1.ros2_build/install`，不要只复制单个节点或单个 `.so`。 |
