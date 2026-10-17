# Data Contracts

This page records the data formats, fields, and time semantics that users can rely on. Undisclosed physical orientation, coordinate systems, extrinsics, and hardware-sync capabilities are explicitly listed as limitations and are not fabricated in the documentation.

## Camera Images and RTSP

| Item | Contract |
|---|---|
| `libsc132.so` / camera callback raw frame | NV12; native `1280x1088` or VSE-scaled `640x480`/`720x480`/`1280x720`; rotation `0/180` keeps width/height unchanged, `90/270` swaps width/height |
| RTSP external stream | H.264 default; H.265 supported |
| FOV | Camera A/B retain horizontal `148.4°`/`115.6°`, vertical `126.6°`/`96.8°`, diagonal `193.8°`/`157.2°`. |
| camera FPS | Default `30fps`, supports `25fps`, `30fps`, `40fps`, `50fps`, and `60fps`; other values rejected before startup side effects |
| RTSP path | `/PRR` |
| Port mapping | CAM1..CAM4 map respectively to software cam0..cam3 and `554/555/556/557`, unchanged from V1. |

The `libsc132.so` callback exposes NV12 raw frames, while RTSP carries H.264/H.265 encoded video. Frame information includes `width`, `height`, `stride`, `vstride`, Y/UV virtual/physical addresses, and sizes. Rotation `90/270` swaps dimensions; consumers must use each frame's metadata and stride/size rather than assume compact `1280x1088`.

## Frame Set Fields

| Field | Meaning |
|---|---|
| `camera_count` | Number of cameras in the current frame group; full four-camera is `4`. |
| `group_id` | Frame-group sequence number. |
| `group_timestamp_ns` | Frame-group timestamp in `ns`. |
| `max_skew_ns` | The maximum timestamp skew actually observed in the current frame group, in `ns`. |
| `items[i].camera_id` | Software ID `0..3`, mapping respectively to physical CAM1..CAM4, unchanged from V1. |
| `items[i].frame_id` | Normalized frame ID. |
| `items[i].timestamp_ns` | Single-channel frame timestamp in `ns`. |

`sc132_frame_set_config_t.max_skew_ns` is the frame-group admission upper bound; its default is `10000000 ns (10ms)`. It limits trigger-capture differences, not exposure alignment accuracy.

## Trigger Modes

| Mode | Current status | Public contract |
|---|---|---|
| `vin_lpwm` | The only supported trigger for all camera applications and the library | Camera and IMU FSYNC share the LPWM IO; camera `timestamp_ns` is the frame-propagated `trig_tv` hardware capture. Missing capture stops acquisition rather than falling back to frame arrival time. |

LPWM `timestamp_ns` uses the SIF hardware-counter domain, converting microsecond `trig_tv` to ns. It is not `CLOCK_MONOTONIC_RAW`, UTC, or the exposure midpoint. The group time is the minimum capture value; items retain individual captures. `max_skew_ns` measures capture-value differences, not exposure or camera/IMU alignment accuracy. Non-ROS camera diagnostics, RTSP PTS, saved image times, and ROS2 image `header.stamp` preserve this native domain. Consumers retain IMU FIFO TMST mapped to RAW without converting to realtime. Camera SIF-to-RAW mapping is not implemented; do not subtract camera and IMU timestamps. Shared FSYNC has no public sample-association interface yet.

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
| demo `ts_ns` | Sample timestamp retained directly in the `CLOCK_MONOTONIC_RAW` domain, in ns, without a realtime offset. `host_ts_ns` also retains RAW. |
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

Bag payload stamps are separate from record time: image and first-frame CameraInfo `header.stamp` preserve camera capture values; IMU payloads retain RAW sample stamps. Bag record time uses an independent `CLOCK_MONOTONIC_RAW` arrival/write clock, nondecreasing in write order, never a numeric comparison between sensor epochs. Session config declares `camera_timestamp_domain="sc132_native"`, `imu_timestamp_domain="monotonic_raw"`, and `record_timestamp_domain="monotonic_raw"`.

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

ROS2 `header.stamp` is not publication time: LPWM cameras retain the SIF trigger-counter domain; IMU retains RAW `sample_timestamp_ns`, not `host_timestamp_ns`. These domains still differ and cannot be paired directly by ROS timestamp, or subtracted from node `now()`, Unix time, or simulation `/clock`. RAW is local to this device and boot, not a cross-device or cross-reboot epoch. PTP does not automatically convert SIF/RAW counters or associate FSYNC samples.

ROS2 currently does not publish RTSP, TF extrinsics, or calibration; camera/IMU hardware sync is still not provided. For general visualization, prefer subscribing to `/image_raw/compressed` and do not assume raw NV12 can be displayed directly by ordinary RGB/BGR tools.

## UART

| Item | Contract |
|---|---|
| Default device | `/dev/ttyS1` |
| Switchable example | `/dev/ttyS7` or another site device |
| Baud rate | `serial_port_demo` defaults to `115200`; DEBUG_UART uses `921600`. |
| serial_port_demo data format | 8N1, raw, no flow control |
| demo modes | `tx`, `rx`, `txrx`, `echo` |
| UART1/UART7 TX/RX signal logic level | Unchanged `3.3V`; DEBUG_UART uses `1.8V`. |
| UART1/UART7 power pins | V2 CN2/CN3 power function, voltage, rated load, and hot-plug limits pending confirmation; do not reuse the V1 `500 mA` total limit. |
| Historical V1 boundary | UART1/UART7 were validated on V1; this is not proof of V2 electrical or harness compatibility. |

V2 UART1/UART7 use CN2/CN3 5-pin connectors and `/dev/ttyS1`, `/dev/ttyS7`. CN3 has an independent IO enabled as PPS input by default, without RX/TX mux switching; discover the enumerated PPS device. Use official V2 labeling for complete pin order and power-pin function. DEBUG_UART is not a user serial port. Wire with power off after checking TX/RX/GND, peer voltage, and common ground; leave adapter VCC disconnected and prevent reverse feed. See [Hardware Connection and Safety](../getting-started/hardware-and-safety.md#uart).
