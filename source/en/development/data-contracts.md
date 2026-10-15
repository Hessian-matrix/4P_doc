# Data Contracts

This page records the data formats, fields, and time semantics that users can rely on. Undisclosed physical orientation, coordinate systems, extrinsics, and hardware-sync capabilities are explicitly listed as limitations and are not fabricated in the documentation.

## Camera Images and RTSP

| Item | Contract |
|---|---|
| `libsc132.so` / camera callback raw frame | NV12; native `1280x1088` or VSE-scaled `640x480`/`720x480`/`1280x720`; rotation `0/180` keeps width/height unchanged, `90/270` swaps width/height |
| RTSP external stream | H.264 default; H.265 supported |
| FOV | V1 cameras A/B historically specified horizontal `148.4°`/`115.6°`, vertical `126.6°`/`96.8°`, diagonal `193.8°`/`157.2°`; V2 lens/sub-board and FOV pending verification. |
| camera FPS | Default `30fps`, supports `25fps`, `30fps`, `40fps`, `50fps`, and `60fps`; other values rejected before startup side effects |
| RTSP path | `/PRR` |
| Port mapping | Software cam0/cam1/cam2/cam3 -> `554/555/556/557`; V2 physical connector mapping pending verification. |

The `libsc132.so` callback exposes NV12 raw frames, while RTSP carries H.264/H.265 encoded video. Frame information includes `width`, `height`, `stride`, `vstride`, Y/UV virtual/physical addresses, and sizes. Rotation `90/270` swaps dimensions; consumers must use each frame's metadata and stride/size for alignment rather than assume compact `1280x1088`. V1 A/B FOV values cannot be applied directly to V2 camera sub-boards.

## Frame Set Fields

| Field | Meaning |
|---|---|
| `camera_count` | Number of cameras in the current frame group; full four-camera is `4`. |
| `group_id` | Frame-group sequence number. |
| `group_timestamp_ns` | Frame-group timestamp in `ns`. |
| `max_skew_ns` | The maximum timestamp skew actually observed in the current frame group, in `ns`. |
| `items[i].camera_id` | Software camera ID, range `0..3`; V2 physical connector-to-software mapping is pending board verification, not inherited from V1 silkscreen. |
| `items[i].frame_id` | Normalized frame ID. |
| `items[i].timestamp_ns` | Single-channel frame timestamp in `ns`. |

`sc132_frame_set_config_t.max_skew_ns` is the frame-group admission upper bound; its default is `10000000 ns (10ms)`, used to cover the four-channel exposure-time difference.

## Trigger Modes

| Mode | Current status | Public contract |
|---|---|---|
| `vin_lpwm` | Default VIN hardware trigger | Drives the VIN hardware `lpwm_attr` output, bypassing the FSYNC software-GPIO path. |
| `none` | Explicit free-run diagnostics | Does not guarantee four-channel hardware triggering. |

In `software_gpio` mode (main-repo internal debug only, not public), the demo's external `camera_ts_ns` and RTSP PTS are mapped to the `system_realtime` epoch with the startup-frozen offset; the explicit `none` diagnostic mode retains the SC132 native time domain. The C API's underlying `timestamp_ns` is not guaranteed to share the wall-clock domain. V1 validation of these time semantics does not replace V2 board acceptance.

## IMU

| Item | Contract |
|---|---|
| Device path | `/dev/spidev2.0` |
| SPI mode/speed | mode `0`, `4 MHz` |
| INT1 DRDY | `34120000.gpio` offset `8`; not old GPIO395 |
| Read mode | sensor timestamp FIFO |
| FIFO watermark | `1` |
| Native ODR | `25/50/100/200/400/800/1600Hz`, default `800Hz`; old `500/1000/2000Hz` configurations are rejected, not resampled |
| FSYNC | V2 input shares the camera common trigger net; IMU does not drive this net or claim sample/exposure alignment. |

Field semantics:

| Field | Unit / semantics |
|---|---|
| `sample_sequence` / demo `sample_seq` | IMU sample sequence number. |
| `temperature_c` / demo `temp_c` | Degrees Celsius. |
| `accel_mps2` | `m/s^2`. |
| `gyro_rps` | `rad/s`. |
| `host_timestamp_ns` | Paired INT1 edge in host `CLOCK_MONOTONIC_RAW` nanoseconds; not the sample timestamp. |
| `sample_timestamp_ns` | Per-sample timestamp mapped from FIFO TMST; underlying `CLOCK_MONOTONIC_RAW` domain. |
| demo `ts_ns` | Sample timestamp mapped to the `system_realtime` epoch by the frozen `CLOCK_REALTIME - CLOCK_MONOTONIC_RAW` offset. |
| `reserved0` | Count of observed FIFO timestamp low-16-bit rollovers in this session; not V1 20-bit SPI snapshot rollovers. |
| `timestamp_uncertainty_us` | Per-sample time-mapping uncertainty, in microseconds. |
| `gpio_event_gap_count` / `fifo_overflow_count` / `mapper_failure_count` | Cumulative counts of edge gaps, FIFO overflows, and mapping failures in the current session. |

The IMU samples continuously on an independent path. Although the V2 FSYNC input shares the camera trigger net, the public interface does not provide camera/IMU synchronized sample associations, exposure times, TF extrinsics, or calibration. Follow the public header for per-sample time domains; neither the host INT1 timestamp nor an FSYNC delta is the sample time.

`accel_mps2` outputs `[X, Y, Z]`. The V2 PCB mounting direction and acceleration signs still require on-board six-face/rotation verification; do not inherit the V1 top-view `[0, 0, -9.8]` or left/front axis claims.

## non-ROS Save Output

| Output | Contract |
|---|---|
| ROS bag | `sensor_demo --record-bag <absolute .bag>` saves four-channel JPEG images, camera parameters, and IMU data; incomplete stress/abnormal runs use an explicit `.partial.bag` recovery file. |
| MP4 session | `sensor_demo --record-mp4-dir <absolute directory>` saves four H.264 MP4s, four timestamp CSVs, `imu.csv`, `camera_params.yaml`, `session_status.json`, and `publication_receipt.json`. |
| MP4 path conflict | When the configured final directory or a same-named `.partial` already exists, the actual output automatically switches to the sibling `<name>-YYYYMMDDTHHMMSSZ[-NNNN]`; follow `SENSOR_MP4_RESULT path=`. |
| `.partial` | Keeps the recovery namespace; a `.partial` MP4 session can be extracted for inspection but is not declared complete. |

MP4 mode only supports H.264 and the full four-channel camera mask `0x0f`, and cannot be enabled together with bag saving or frame-skip. The MP4 file frame timing is the container's nominal timing; precise nanosecond camera timestamps are in the same session's `cameraN_timestamps.csv`, aligned to the MP4 metadata by `frame_index`. A `published_complete` source must carry a matching `publication_receipt.json` and a complete four-channel MP4/index inventory.

## ROS2 Topics

| Topic | Message type | Contract |
|---|---|---|
| `/robobaton/cam0..3/image_raw` | `sensor_msgs/msg/Image` | Four raw NV12 images, `encoding="nv12"`. |
| `/robobaton/cam0..3/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | Standard compressed transport JPEG; the current plugin uses X5 media codec hardware JPEG encoding. |
| `/robobaton/cam0..3/camera_info` | `sensor_msgs/msg/CameraInfo` | Only contains the current frame width/height; calibration fields are empty. |
| `/robobaton/imu/data` | `sensor_msgs/msg/Imu` | ICM-42670-P gyro/accel; orientation unavailable. |
| `/robobaton/imu/temperature` | `sensor_msgs/msg/Temperature` | ICM-42670-P temperature, reusing the IMU sample stamp. |

ROS2 QoS:

| Data | QoS |
|---|---|
| raw Image | Reliable + KeepLast(8) |
| compressed Image | Follows the raw publisher, also Reliable + KeepLast(8) |
| CameraInfo | Reliable + Transient Local + KeepLast(1) |
| IMU | `SensorDataQoS`, keep last 100 |
| Temperature | `SensorDataQoS`, keep last 10 |

ROS2 raw `Image.step` uses the underlying DMA buffer's stride; `data.size()` uses the underlying Y/UV buffer size, which may be larger than the compact `width * height * 3 / 2`. Subscribers must not index the UV plane directly under the compact-NV12 assumption.

ROS2 `header.stamp` is not the publish moment. In `software_gpio` mode, the node freezes the `CLOCK_REALTIME - CLOCK_MONOTONIC_RAW` offset and maps the camera SC132 raw timestamp and IMU `sample_timestamp_ns` to system realtime/ROS stamps; explicit `none` diagnostics retain the native SC132 time domain. The IMU does not use `host_timestamp_ns` as the message time; V1 time validation cannot establish V2 camera/IMU alignment.

ROS2 currently does not publish RTSP, TF extrinsics, or calibration; camera/IMU hardware sync is still not provided. For general visualization, prefer subscribing to `/image_raw/compressed` and do not assume raw NV12 can be displayed directly by ordinary RGB/BGR tools.

## UART

| Item | Contract |
|---|---|
| Default device | `/dev/ttyS1` |
| Switchable example | `/dev/ttyS7` or another site device |
| Baud rate | `serial_port_demo` defaults to `115200`; V2 DEBUG_UART console settings pending confirmation. |
| serial_port_demo data format | 8N1, raw, no flow control |
| demo modes | `tx`, `rx`, `txrx`, `echo` |
| UART1/UART7 TX/RX signal logic level | V2 GPIO_VREF/BOM and actual connector voltage pending confirmation; do not wire based on V1 `3.3V`. |
| UART1/UART7 power pins | V2 CN2/CN3 power function, voltage, rated load, and hot-plug limits pending confirmation; do not reuse the V1 `500 mA` total limit. |
| Historical V1 boundary | UART1/UART7 were validated on V1; this is not proof of V2 electrical or harness compatibility. |

On V2, UART1/UART7 correspond to CN2/CN3 5-pin connectors; the additional signals must not be assumed to be RTS/CTS or PPS wiring. `serial_port_demo` defaults to `/dev/ttyS1` and can select `/dev/ttyS7`, but V2 physical signal order, tty mapping, TX/RX levels, and power direction still need on-board confirmation. The V1 PPS script's `/dev/pps2` mux instructions do not promise V2 PPS support. DEBUG_UART is not a user UART; do not attach an external adapter until its V2 levels have been checked. Wire with power off by default, verify board TX/RX/GND and peer voltage first, and prevent miswiring or reverse feed. See [Hardware Connection and Safety](../getting-started/hardware-and-safety.md#uart).
