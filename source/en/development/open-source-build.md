# Building the Public Demo Source

This page explains how to cross-compile the example code in the public demo repositories on the host. The X5 device only runs the compiled artifacts; native compilation on the device is not recommended.

Scope:

- [`RoboBaton_4p_demo`](https://github.com/Hessian-matrix/RoboBaton_4p_demo): non-ROS four-camera RTSP, IMU, and UART examples.
- [`RoboBaton_4P_ROS2_demo`](https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo): ROS2 four-camera NV12/raw+compressed images, CameraInfo, IMU, and temperature topic examples.

## 1. Build Boundary

The public demo repositories build the user-side example programs:

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

The public demo repositories already carry the public headers and matching precompiled runtime libraries required for building:

- non-ROS: `include/`, `lib/libicm42688.so*`, `lib/libsc132.so*`, `lib/libprrtsp.so*`.
- ROS2: `include/robobaton_4p_ros2_demo/`, `lib/libicm42688.so*`, `lib/libsc132.so*`; building also requires the target-side ROS2, `hb_media_codec.h`, `libmultimedia.so.1`, `libhbmem.so.1`, and `libalog.so.1` provided by the X5 cross-compilation package.

These repositories do not compile the underlying ICM42688, SC132, or PRRTSP producer source. Without the X5 cross-compilation toolchain, you cannot recompile the source and can only use the `demo/` in the repository or a pre-generated install package for deployment.

## 2. Prepare the Cross-Compilation Environment

The host needs host-side tools:

- `cmake`
- `make` or another CMake-supported build backend
- `python3`
- ELF inspection tools such as `readelf` / `file`

### Download the X5 Cross-Compilation Package

Download [x5_4cam_cross_toolchain_20260708.tar.gz](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/x5_4cam_cross_toolchain_20260708.tar.gz), size `2,044,412,424 bytes` (about `1.90 GiB`), SHA-256 `4ebc9cd8e7416ed6a7ce610421fd90509f368e26a9ffedd498a52171d1d16a1d`. This package provides the X5 aarch64 toolchain, sysroot, platform headers, and runtime libraries required to compile the public demos.

Linux download and readability-check example:

```bash
curl -fL --retry 3 -O \
  "https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/x5_4cam_cross_toolchain_20260708.tar.gz"
test "$(stat -c %s x5_4cam_cross_toolchain_20260708.tar.gz)" -eq 2044412424
printf '%s  %s\n' \
  4ebc9cd8e7416ed6a7ce610421fd90509f368e26a9ffedd498a52171d1d16a1d \
  x5_4cam_cross_toolchain_20260708.tar.gz | sha256sum -c -
tar -tzf x5_4cam_cross_toolchain_20260708.tar.gz >/dev/null
```

Extraction and environment variables example:

```bash
mkdir -p cross_compile_toolchain
tar -xzf x5_4cam_cross_toolchain_20260708.tar.gz \
  -C cross_compile_toolchain

export X5_TOOLCHAIN_ROOT="$PWD/cross_compile_toolchain/x5_4cam_cross_toolchain_20260708"
export TOOLCHAIN_FILE="$X5_TOOLCHAIN_ROOT/cross_compile/new/toolchain/aarch64_x5_host_toolchain.cmake"

test -f "$TOOLCHAIN_FILE"
cmake --version
```

If the actual extraction directory differs, just point `TOOLCHAIN_FILE` at the real `aarch64_x5_host_toolchain.cmake`.

## 3. Build the non-ROS Demo

Get the source:

```bash
git clone https://github.com/Hessian-matrix/RoboBaton_4p_demo.git
cd RoboBaton_4p_demo
```

Build all four demos:

```bash
cmake -S . -B build_x5 \
  -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN_FILE"
cmake --build build_x5 -j
```

Or build a single target:

```bash
cmake --build build_x5 --target cam_demo -j
cmake --build build_x5 --target sensor_demo -j
cmake --build build_x5 --target imu_reader_demo -j
cmake --build build_x5 --target serial_port_demo -j
```

The repository also provides equivalent script entries:

```bash
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_cam_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_sensor_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_imu_reader_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_serial_port_demo.sh
```

Build artifacts are at:

```text
build_x5/cam_demo
build_x5/sensor_demo
build_x5/imu_reader_demo
build_x5/serial_port_demo
```

Check the target architecture:

```bash
file build_x5/cam_demo
file build_x5/sensor_demo
file build_x5/imu_reader_demo
file build_x5/serial_port_demo
```

The expected output contains `ARM aarch64`. If the output is `x86-64`, the X5 cross toolchain file was not used.

## 4. Regenerate the non-ROS Runtime Package

To publish the recompiled demos to the repository's `demo/` runtime package, use the packaging script:

```bash
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/package_runtime.sh
```

The script:

1. Reconfigures and builds the four consumer demos.
2. Copies matching runtime libraries from the current repository's `lib/`.
3. Generates the top-level launcher scripts, `env.sh`, `config/sensor_config.yaml`, and `bin/`.
4. Writes and verifies `manifest.sha256`.
5. Outputs `Runtime package generated and verified: <demo-dir>`.

Manually verify the generated runtime package:

```bash
python3 scripts/verify_runtime_package.py demo
```

When deploying to the X5, do not delete `/root/demo` directly, and do not copy the outer `demo/` directory as `/root/demo/demo/`. Use the safe entry in [Deployment, Upgrade, and Rollback](deployment-and-upgrade.md): unique temporary directory, full `manifest.sha256` verification, old-application-exit check, old-directory backup, atomic switch, help/smoke verification, and failure rollback.

## 5. Build the ROS2 Demo

Get the source:

```bash
git clone https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo.git
cd RoboBaton_4P_ROS2_demo
```

Prepare the ROS Humble host environment and the X5 cross-compilation package:

```bash
# replace the path below with the actual X5 cross-compilation package root
export X5_CROSS_ROOT=/absolute/path/to/cross_compile/new
set +u
source /opt/ros/humble/setup.bash
set -u
```

A clean build with the in-package script is recommended:

```bash
script/build_x5_ros2.sh --clean --cross-root "$X5_CROSS_ROOT"
```

The script explicitly passes the X5 CMake toolchain file and pins colcon artifacts to this package:

```text
1.ros2_build/
├── build/
├── install/
└── log/
```

The install package is at `1.ros2_build/install`, uses the merged-install layout by default, and provides `robobaton_ros2_env.bash` in the install root as the recommended on-device run entry. After building, run the install verifier:

```bash
python3 script/verify_install.py 1.ros2_build/install
```

This verifier checks the ROS2 install runtime files, executables, the NV12 compressed image_transport plugin, related dynamic libraries, RUNPATH, the runtime environment script, relocatable Bash setup, and `abi_manifest.sha256`. It does not replace on-device topic, NV12-layout, or IMU-frequency checks.

Common overrides:

```bash
script/build_x5_ros2.sh \
  --install-base install_x5 \
  --parallel-workers 1 \
  -- --event-handlers console_direct+
```

Relative `--build-base`, `--install-base`, and `--log-base` are resolved against the ROS2 demo repository root.

When deploying to the X5, do not stream a tar directly, and do not rely only on `abi_manifest.sha256` to judge the complete install tree. ROS2 install deployment uses the deterministic archive checksum + runtime ABI subset verification flow; see [ROS2 Demo Usage](../usage/ros2-demo.md) and [Deployment, Upgrade, and Rollback](deployment-and-upgrade.md).

## 6. Common Issues

| Symptom | Handling |
|---|---|
| `Missing ... libicm42688/libsc132/libprrtsp` | Confirm the public demo repository's `lib/` is complete; public demos only compile consumer examples and do not generate producer libraries from source. |
| `Missing consumer toolchain file` | Check whether `TOOLCHAIN_FILE` points at the real `aarch64_x5_host_toolchain.cmake`. |
| `file build_x5/...` shows `x86-64` | Reconfigure CMake and ensure `-DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN_FILE"` is passed. |
| After copying only a single executable under `build_x5/`, the device cannot find libraries | Use `scripts/package_runtime.sh` to generate the full `demo/` and deploy the complete `demo/` contents. |
| ROS2 build cannot find `ament_package` | First `source /opt/ros/humble/setup.bash`, and confirm `/usr/bin/python3` can import `ament_package`. |
| ROS2 install verifier fails | Use the full `1.ros2_build/install`, not just a single node or a single `.so`. |
