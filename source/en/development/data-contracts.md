# Data Contracts

This page records the data formats, fields, and time semantics that users can rely on. Undisclosed physical orientation, coordinate systems, extrinsics, and hardware-sync capabilities are explicitly listed as limitations and are not fabricated in the documentation.

## Camera Images and RTSP

| Item | Contract |
|---|---|
| `libsc132.so` / camera callback raw frame | NV12; native `1280x1088` or VSE-scaled `640x480`/`720x480`/`1280x720`; rotation `0/180` keeps width/height unchanged, `90/270` swaps width/height |
| RTSP external stream | H.264 default; H.265 supported |
| FOV | Form A: horizontal `148.4°`, vertical `126.6°`, diagonal `193.8°`; Form B: horizontal `115.6°`, vertical `96.8°`, diagonal `157.2°` |
| camera FPS | Default `30fps`, supports `25fps`, `30fps`, `40fps`, `50fps`, and `60fps`; other values rejected before startup side effects |
| RTSP path | `/PRR` |
| Port mapping | CAM1/CAM2/CAM3/CAM4 -> cam0/cam1/cam2/cam3 -> `554/555/556/557` |

The `libsc132.so` callback exposes NV12 raw frames; the RTSP client receives the H.264/H.265 encoded stream, and RTSP does not directly carry NV12 raw frames. Frame information includes `width`, `height`, `stride`, `vstride`, Y/UV virtual addresses, Y/UV physical addresses, and Y/UV size. Rotation `90/270` swaps the external width/height, and the output canvas can be `640x480`/`720x480`/`1280x720`; consumers must read per-frame metadata and cannot fixedly assume `1280x1088`. NV12 consumers also cannot assume buffers are compact; use the `stride`, `vstride`, and size fields to handle alignment. A/B are product-form versions that differ only in FOV; select the corresponding FOV by the product identifier.

## Frame Set Fields

| Field | Meaning |
|---|---|
| `camera_count` | Number of cameras in the current frame group; full four-camera is `4`. |
| `group_id` | Frame-group sequence number. |
| `group_timestamp_ns` | Frame-group timestamp in `ns`. |
| `max_skew_ns` | The maximum timestamp skew actually observed in the current frame group, in `ns`. |
| `items[i].camera_id` | Software camera ID, range `0..3`; physical silkscreen mapping is CAM1 -> cam0, CAM2 -> cam1, CAM3 -> cam2, CAM4 -> cam3. |
| `items[i].frame_id` | Normalized frame ID. |
| `items[i].timestamp_ns` | Single-channel frame timestamp in `ns`. |

`sc132_frame_set_config_t.max_skew_ns` is the frame-group admission upper bound; its default is `10000000 ns (10ms)`, used to cover the four-channel exposure-time difference.

## Trigger Modes

| Mode | V1 status | Public contract |
|---|---|---|
| `software_gpio` | Verified; the only V1 stable mode | Default mode, using GPIO417 software trigger. |
| `none` | Experimental, not part of the V1 stable configuration. | The CLI/config still accepts the value, but it is not part of the V1 stable release contract. |

In the V1-verified `software_gpio` mode, the demo's external-diagnostic `camera_ts_ns` and RTSP PTS are mapped to the `system_realtime` epoch corresponding to the frozen offset at startup. With the explicit `none` diagnostic mode, timestamps keep the SC132 native time domain and are not declared as a V1 wall/realtime contract. The `timestamp_ns` in the underlying C API header is not guaranteed to share the wall-clock domain; do not mix the demo-printed time with the underlying raw time domain.

## IMU

| Item | Contract |
|---|---|
| Device path | `/dev/spidev2.0` |
| SPI mode/speed | mode `0`, `4 MHz` |
| DRDY | GPIO395 |
| Read mode | sensor timestamp FIFO |
| FIFO watermark | `1` |
| ODR | `25/50/100/200/500/1000/2000Hz`, default `1000Hz` |
| Not used | GPIO397, FSYNC, `icm42688_pulse_fsync()` |

Field semantics:

| Field | Unit / semantics |
|---|---|
| `sample_sequence` / demo `sample_seq` | IMU sample sequence number. |
| `temperature_c` / demo `temp_c` | Degrees Celsius. |
| `accel_mps2` | `m/s^2`. |
| `gyro_rps` | `rad/s`. |
| `host_timestamp_ns` | GPIO395 DRDY edge anchor; underlying `CLOCK_MONOTONIC_RAW` domain. |
| `sample_timestamp_ns` | Per-sample timestamp mapped from FIFO TMST; underlying `CLOCK_MONOTONIC_RAW` domain. |
| demo `ts_ns` | Sample timestamp mapped to the `system_realtime` epoch by the frozen `CLOCK_REALTIME - CLOCK_MONOTONIC_RAW` offset. |

IMU is an independent continuous sampling path. The current public delivery does not provide camera/IMU hardware sync, public TF extrinsics, or public calibration.

IMU acceleration `accel_mps2` outputs in `[X, Y, Z]` order, with the sign using the current board top view in [Hardware Connection and Safety](../getting-started/hardware-and-safety.md#uart) as the physical reference: when the device is still and level, `accel_mps2` is about `[0, 0, -9.8] m/s^2`; accelerating toward the left of the image makes X negative; accelerating toward the top of the image / product front makes Y negative. This description does not define the relationship of the IMU to the camera, base, optical frame, or other coordinate systems, nor provide TF or extrinsics.

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
| `/robobaton/imu/data` | `sensor_msgs/msg/Imu` | ICM-42688 gyro/accel; orientation unavailable. |
| `/robobaton/imu/temperature` | `sensor_msgs/msg/Temperature` | ICM-42688 temperature, reusing the IMU sample stamp. |

ROS2 QoS:

| Data | QoS |
|---|---|
| raw Image | Reliable + KeepLast(8) |
| compressed Image | Follows the raw publisher, also Reliable + KeepLast(8) |
| CameraInfo | Reliable + Transient Local + KeepLast(1) |
| IMU | `SensorDataQoS`, keep last 100 |
| Temperature | `SensorDataQoS`, keep last 10 |

ROS2 raw `Image.step` uses the underlying DMA buffer's stride; `data.size()` uses the underlying Y/UV buffer size, which may be larger than the compact `width * height * 3 / 2`. Subscribers must not index the UV plane directly under the compact-NV12 assumption.

ROS2 `header.stamp` is not the publish moment. In the V1-verified `software_gpio` mode, the node freezes the `CLOCK_REALTIME - CLOCK_MONOTONIC_RAW` offset at startup and maps the camera SC132 raw timestamp to system realtime/ROS stamp. The explicit `none` diagnostic mode keeps the underlying SC132 time domain and is not declared as a V1 wall/realtime contract. IMU `sample_timestamp_ns` is mapped to system realtime/ROS timestamps through the same frozen offset; IMU does not use `host_timestamp_ns` as the message time.

ROS2 currently does not publish RTSP, TF extrinsics, or calibration; camera/IMU hardware sync is still not provided. For general visualization, prefer subscribing to `/image_raw/compressed` and do not assume raw NV12 can be displayed directly by ordinary RGB/BGR tools.

## UART

| Item | Contract |
|---|---|
| Default device | `/dev/ttyS1` |
| Switchable example | `/dev/ttyS7` or another site device |
| Baud rate | `serial_port_demo` default `115200`; DEBUG_UART console uses `921600` |
| serial_port_demo data format | 8N1, raw, no flow control |
| demo modes | `tx`, `rx`, `txrx`, `echo` |
| UART1/UART7 TX/RX signal logic level | `3.3V` |
| UART1/UART7 3.3V power pins | The two power pins share `VCC3V3_SYS`; support input/output and peripheral power; the formal product limit is `500 mA` total, with hot-plug support |
| V1 delivery boundary | UART1/UART7 normal 3.3V hardware communication passed V1 acceptance; `serial_port_demo` is a public user example; DEBUG_UART is 1.8V; PPS mode occupies UART7 RX separately and releases UART7 TX GPIO/IO |

UART1/UART7 are `3.3V` user-programmable UARTs, corresponding to `/dev/ttyS1` and `/dev/ttyS7` respectively, with GH1.25-4P connectors; `serial_port_demo` applies only to normal UART mode. PPS mode occupies UART7 RX via [PPS Sync](../time-sync/pps-sync.md), fixedly registers `/dev/pps2`, and releases UART7 TX as GPIO/IO; do not run `serial_port_demo` in PPS mode. DEBUG_UART is the `1.8V` system debug UART with a GH1.25-3P connector and does not support `serial_port_demo`. See [Hardware Connection and Safety](../getting-started/hardware-and-safety.md#uart) for interface positions, levels, and power boundaries.

When connecting, the board TX connects to the peer RX, the board RX to the peer TX, and always share ground. DEBUG_UART accepts only `1.8V` logic; UART1/UART7 use `3.3V` logic. The `3V3` pins of UART1/UART7 support input/output and can power peripherals, with a shared `500 mA` total limit across the two interfaces and hot-plug support; above the total limit, use an independent supply, keep common ground, and do not reverse-feed the board 3.3V rail.
