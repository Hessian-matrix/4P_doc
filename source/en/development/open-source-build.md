# Building the Public Demo Source

This page explains how to cross-compile the example code in the public demo repositories on the host. The X5 device only runs the compiled artifacts; native compilation on the device is not recommended.

Scope:

- [`RoboBaton_4p_demo`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/tree/V2_main): non-ROS four-camera RTSP, IMU, UART, and SocketCAN CAN examples.
- [`RoboBaton_4P_ROS2_demo`](https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo/tree/V2_main): ROS2 four-camera NV12/raw+compressed images, CameraInfo, exposure observations, IMU, temperature, and IMU timing metadata topic examples.

V2 source and documentation use the `V2_main` main branch. The clone commands below select it explicitly; switch existing checkouts to `V2_main` before building too.

## 1. Build Boundary

The public demo repositories build the user-side example programs:

```text
RoboBaton_4p_demo
├── cam_demo
├── mosaic_rtsp_demo
├── sensor_demo
├── imu_reader_demo
├── serial_port_demo
└── can_demo

RoboBaton_4P_ROS2_demo
├── robobaton_sensors_node
├── robobaton_imu_rate_monitor
└── robobaton_nv12_compressed_image_transport (shared plugin)
```

The public demo repositories already carry the public headers and matching precompiled runtime libraries required for building:

- non-ROS: `include/`, `lib/libicm42670.so*`, `lib/libsc132.so*`, `lib/libprrtsp.so*`; also requires matching X5 SDK media headers such as `hbn_api.h`, `libhbmem.so`, and `libmultimedia.so` from the cross-compilation package, not built by this consumer repository.
- ROS2: `include/robobaton_4p_ros2_demo/`, `lib/libicm42670.so*`, `lib/libsc132.so*`; building also requires the target-side ROS2, `hb_media_codec.h`, `libmultimedia.so.1`, `libhbmem.so.1`, and `libalog.so.1` provided by the X5 cross-compilation package.

These repositories do not compile the underlying ICM42670, SC132, or PRRTSP producer source. Without the X5 cross-compilation toolchain, you cannot recompile the source and can only use the `demo/` in the repository or a pre-generated install package for deployment.

The system USB camera program `x5-uvc-mosaic` is not a root CMake target listed above. Its complete backend, standalone build, and offline installer are under [`scripts/env_setup/x5_usb/`](https://github.com/Hessian-matrix/RoboBaton_4p_demo/tree/V2_main/scripts/env_setup/x5_usb) in public `RoboBaton_4p_demo`. This build needs no Go, but requires the matching X5 SDK and SC132 ABI3 library. Editing other non-ROS mosaic or JPEG examples does not update the system USB camera. See {ref}`USB Development Entry Points <usb-uvc-development>` for source/function links, standalone commands, offline `--package` installation, and safe updates on an existing board.

Each library family has one regular `libNAME.so.M.m.p` file and two exact same-directory relative links: `libNAME.so.M -> libNAME.so.M.m.p`, `libNAME.so -> libNAME.so.M`. Non-ROS uses ICM42670, SC132, and PRRTSP; ROS2 uses only the first two. Synchronization, packaging, and install preserve links; verifiers reject flattened aliases and wrong, absolute, or broken links. Copy complete trees with `tar`, `cp -a`, or `rsync -a`, without dereferencing links.

Non-ROS `runtime-provenance.json` uses v3: regular-file bytes and raw link text are bound separately; source-input links are hashed by link text. Regenerate packages with older provenance using the current script. This does not change software versions or SONAME/ABI. Both SHA-256 manifests still include resolved-byte hashes for aliases; these do not replace link-metadata verification.

The current matched set is ICM42670 `libicm42670.so.5.0.0`, SONAME `libicm42670.so.5`, nine exports under `ICM42670_X5_5.0`; SC132 `libsc132.so.3.0.0`, SONAME `libsc132.so.3`, `LIBSC132_3.0`; PRRTSP `libprrtsp.so.2.0.1`, SONAME `libprrtsp.so.2`, `LIBPRRTSP_2.0`. Synchronize public headers and libraries, remove old ICM42670 `.2/.3/.4` and SC132 `.2` libraries, and rebuild every consumer without cross-major links. All four startup timestamp pairs use the same binaries/IIO capture, not separate scheme-specific builds; see [non-ROS Usage](../usage/non-ros-demo.md) and [ROS2 Usage](../usage/ros2-demo.md). Every IMU mode requires the matched kernel IIO V3 capture module; the existing V2 module is incompatible. Public demo builds/package verifiers do not build, install, or upgrade that kernel module. Software `2.0.0`, hardware V2.2, documentation revision, and SO ABI are independent. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>` for the current non-ROS HO short smoke and unverified scope. compilation does not certify four-way operation, throughput, pressure, or long recording. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>`.

The current matching Buildroot image supplies `/usr/bin/python3`, C++/SDK runtime libraries, and `/opt/ros/humble`. Application packages supply their programs, configuration, matched producers, and tools. The ROS2 install also carries selected transitive dependencies and NumPy's BLAS/LAPACK/Fortran libraries, not just the two producers; it does not replace the system interpreter or BSP. Checks on a flashed device cover Python `3.10.12`, actual non-ROS loading, and ROS2 version/package queries in the package environment. Builds and package/install verifiers do not validate every runtime path. See [Current Image Contents](../ops/system-flashing.md).

## 2. Prepare the Cross-Compilation Environment

The verified host is **Ubuntu 22.04 x86_64**; the target is **X5 AArch64**. The bundle always selects its Arm GNU 11.3.Rel1 compiler. A system AArch64 cross compiler is not required.

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake git python3 file binutils pkg-config curl
```

For ROS2 builds, configure the repositories using the [official ROS Humble Ubuntu installation instructions](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html), then install host tools:

```bash
sudo apt-get install -y ros-humble-ros-base python3-colcon-common-extensions
source /opt/ros/humble/setup.bash
/usr/bin/python3 -c 'import ament_package, catkin_pkg, em, colcon_core'
```

Host ROS supplies Python/ament/colcon build tools; the cross bundle supplies AArch64 ROS headers, libraries, and exports. Do not source the bundled target ROS setup on the host or link host `/opt/ros/humble/lib` into X5 programs. Use system Python; leave any active virtual environment first.

### Obtain and Verify the X5 Cross-Compilation Package

Download [x5_4cam_cross_toolchain_20261009.tar.gz](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/x5_4cam_cross_toolchain_20261009.tar.gz): `2,058,709,673 bytes` (about `1.92 GiB`), SHA-256 `f708547c8936dddc0ce32e0d4a6dfbb605ff7bfc9d711b036ffd0ed982e6b035`. This version adds target ROS Humble (including image_transport/pluginlib), cross-environment scripts, sysroot linker entries, and relocatable CMake exports. Its supported build scope is the two consumer repositories on this page.

Download, verify, and build using the following steps:

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

`file` should report `ARM aarch64`. The environment script sets `X5_CROSS_ROOT` to the bundled `cross_compile/new`; both named CMake toolchains use the same compiler and search rules. Source the environment again and use a new build directory after moving the bundle.

## 3. Build the non-ROS Demo

Get the source:

```bash
git clone --branch V2_main https://github.com/Hessian-matrix/RoboBaton_4p_demo.git
cd RoboBaton_4p_demo
```

Building all six demos and application-owned `sensor_web` additionally requires exact Go `1.27.3` on the host, not the device. Install and verify it first; use `go mod download` during a network-enabled dependency-provisioning step. Actual builds enforce `GOTOOLCHAIN=local`, an offline module cache, and readonly modules, without automatic compiler/dependency downloads.

```bash
export GO=/path/to/go1.27.3/bin/go # replace with the installed exact compiler
GOTOOLCHAIN=local "$GO" env GOVERSION # must be go1.27.3
(cd web/server && GOTOOLCHAIN=local "$GO" mod download)
cmake -S . -B build_x5 \
  -DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN_FILE" \
  -DSENSOR_WEB_GO_EXECUTABLE="$GO"
cmake --build build_x5 -j
```

`sensor_web` is a static Linux ARM64 executable embedding assets and Pion; the `sensor_demo` target depends on it. The runtime contains complete notices and the module lock under `licenses/sensor_web/`. Rebuild after changes to Web source/assets/locks. The verifier reads fixed Go/module identity, application version, and source digest from ELF and rejects stale binaries; do not strip this Go ELF or merely update sidecar hashes. Build it alone with `scripts/build_sensor_web.sh --go "$GO" --output build_x5/sensor_web`, or package everything with `scripts/package_runtime.sh --go "$GO"`.

Or build a single target:

```bash
cmake --build build_x5 --target cam_demo -j
cmake --build build_x5 --target mosaic_rtsp_demo -j
cmake --build build_x5 --target sensor_demo -j
cmake --build build_x5 --target imu_reader_demo -j
cmake --build build_x5 --target serial_port_demo -j
cmake --build build_x5 --target can_demo -j
```

The repository also provides equivalent script entries:

```bash
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_cam_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_mosaic_rtsp_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_sensor_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_imu_reader_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_serial_port_demo.sh
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/build_can_demo.sh
```

Build artifacts are at:

```text
build_x5/cam_demo
build_x5/mosaic_rtsp_demo
build_x5/sensor_demo
build_x5/imu_reader_demo
build_x5/serial_port_demo
build_x5/can_demo
```

Check the target architecture:

```bash
file build_x5/cam_demo
file build_x5/mosaic_rtsp_demo
file build_x5/sensor_demo
file build_x5/imu_reader_demo
file build_x5/serial_port_demo
file build_x5/can_demo
```

The expected output contains `ARM aarch64`. If the output is `x86-64`, the X5 cross toolchain file was not used.

## 4. Regenerate the non-ROS Runtime Package

To publish the recompiled demos to the repository's `demo/` runtime package, use the packaging script:

```bash
TOOLCHAIN_FILE="$TOOLCHAIN_FILE" scripts/package_runtime.sh
```

The script:

1. Reconfigures and builds the six consumer demos.
2. Copies matching runtime libraries from the current repository's `lib/`.
3. Generates the top-level launcher scripts, `env.sh`, `config/sensor_config.yaml`, and `bin/`.
4. Writes and verifies `manifest.sha256` and `runtime-provenance.json`; standalone clones bind the source commit and file hashes, while composition checkouts also bind the parent gitlink.
5. Outputs `Runtime package generated and verified: <demo-dir>`.

Manually verify the generated runtime package:

```bash
python3 scripts/verify_runtime_package.py demo
```

A custom `--build-dir` must remain inside the source repository, for example `build_public_cross`. Repackage after source or runtime changes; provenance verification rejects files that differ from the packaging snapshot.

When deploying to the X5, do not delete `/root/demo` directly, and do not copy the outer `demo/` directory as `/root/demo/demo/`. Use the safe entry in [Deployment, Upgrade, and Rollback](deployment-and-upgrade.md): unique temporary directory, full `manifest.sha256` verification, old-application-exit check, old-directory backup, atomic switch, help/smoke verification, and failure rollback.

## 5. Build the ROS2 Demo

Get the source:

```bash
git clone --branch V2_main https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo.git
cd RoboBaton_4P_ROS2_demo
```

Build in a terminal where the host preparation and bundle extraction in section 2 are complete:

```bash
source /opt/ros/humble/setup.bash
source "$X5_TOOLCHAIN_ROOT/setup_4cam_cross_env.sh"
CMAKE_BUILD_PARALLEL_LEVEL=4 script/build_x5_ros2.sh \
  --cross-root "$X5_CROSS_ROOT" --parallel-workers 1
```

`X5_CROSS_ROOT` identifies the bundled `cross_compile/new`; target ROS is in its `target_ros/humble`. The script uses this cross environment by default; an explicit `--toolchain-file` takes precedence over environment setup. No business overlay or private developer directory is needed. Use a new `--build-root` when switching bundles to avoid stale caches.

The scripte toolchain file and pins colcon artifacts to this package:

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
| `Missing ... libicm42670/libsc132/libprrtsp` | Confirm the public demo repository's `lib/` is complete; public demos only compile consumer examples and do not generate producer libraries from source. |
| `Missing consumer toolchain file` | Check whether `TOOLCHAIN_FILE` points at the real `aarch64_x5_host_toolchain.cmake`. |
| `file build_x5/...` shows `x86-64` | Reconfigure CMake and ensure `-DCMAKE_TOOLCHAIN_FILE="$TOOLCHAIN_FILE"` is passed. |
| After copying only a single executable under `build_x5/`, the device cannot find libraries | Use `scripts/package_runtime.sh` to generate the full `demo/` and deploy the complete `demo/` contents. |
| ROS2 build cannot find `ament_package` | First `source /opt/ros/humble/setup.bash`, and confirm `/usr/bin/python3` can import `ament_package`. |
| ROS2 install verifier fails | Use the full `1.ros2_build/install`, not just a single node or a single `.so`. |
