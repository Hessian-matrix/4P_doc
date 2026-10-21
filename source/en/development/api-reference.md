# API Reference

This page covers the C ABI/API in the current public headers. Examples only show the minimal integration skeleton and do not reproduce the underlying producer source. The version-string getters do not require hardware initialization; the runtime-health-snapshot getter is only valid after the most recent acquisition has successfully stopped.

## Release Version Query

The product release version follows SemVer and is independent of the SO SONAME/ABI version. The version-string getters require no hardware initialization and return a process-static read-only string that the caller must not modify or free:

```c
const char *camera_version = sc132_get_version();
const char *imu_version = icm42670_get_version();
const char *rtsp_version = prrtsp_get_version();
```

Delivered executables also support `--version`. The non-ROS `cam_demo`/`sensor_demo` and the ROS2 `robobaton_sensors_node` print the versions of the in-house SOs they actually load, to detect mixing programs and SOs of different versions. The ROS2 compressed image_transport plugin additionally exports `robobaton_nv12_compressed_image_transport_get_version()`.

## `libsc132.so`

Header: `include/sc132camera.h`. ABI: `SC132_ABI_VERSION_MAJOR=2`, `SC132_ABI_VERSION_MINOR=2`; the real SO is `libsc132.so.2.0.0`, SONAME still `libsc132.so.2`.

Status codes:

| Status code | Meaning |
|---|---|
| `SC132_STATUS_OK` | Success |
| `SC132_STATUS_INVALID_ARGUMENT` | Invalid argument |
| `SC132_STATUS_INVALID_STATE` | Invalid lifecycle state |
| `SC132_STATUS_STARTUP_FAILED` | Startup failed |

Core structures:

| Structure | Purpose |
|---|---|
| `sc132_frame_info_t` | Single-frame NV12 addresses, physical addresses, size, stride/vstride, timestamp. |
| `sc132_frame_set_item_t` | Single-channel entry in a frame group. |
| `sc132_frame_set_t` | The four frames of one group, `group_id`, `group_timestamp_ns`, and the actually observed `max_skew_ns`. |
| `sc132_frame_set_config_t` | frame-set callback, camera count, size, timeout, and group-admission skew upper bound. |

By default public camera `timestamp_ns` and `group_timestamp_ns` values are hardware trigger-edge times mapped to `CLOCK_REALTIME` Unix nanoseconds, following runtime clock corrections including backward steps, not arrival/IRQ or exposure-midpoint times. The opt-in {ref}`Exposure-Midpoint Test Switch <test-exposure-midpoint>` adds half exposure duration. Read-only X5 `/dev/mem` access is required; missing/out-of-window mappings stop acquisition. See [Time Data Contracts](data-contracts.md).

ABI 2.2 appends `exposure` (`sc132_exposure_info_t`) to `sc132_frame_info_t`. `sc132_frame_get_info()` accepts the current `sizeof(info)` or the old prefix size ending before `exposure`, writes only the declared size, and returns `struct_size` unchanged. New consumers require matching headers/SOs.

(camera-output-structures)=
### Public Image Output Structures and Fields

The camera C acquisition API outputs **NV12 images**, not sensor RAW10 or H.264/H.265 bitstreams. The callback receives a frame group, `sc132_frame_set_t`; each entry carries an opaque `sc132_frame_t *` handle. Call `sc132_frame_get_info()` to obtain pixel addresses and per-frame metadata. The declarations below match the current public header; integrations should include the delivered header instead of copying these definitions.

```c
typedef struct sc132_frame sc132_frame_t;

typedef struct sc132_exposure_info {
  uint32_t status;
  uint32_t source_frame_id;
  uint64_t duration_ns;
  uint64_t source_timestamp;
  uint64_t observed_raw_ns;
} sc132_exposure_info_t;

typedef struct sc132_frame_info {
  uint32_t struct_size;
  uint32_t camera_id;
  uint64_t sequence;
  uint32_t frame_id;
  uint32_t raw_frame_id;
  uint64_t timestamp_ns;
  const void *y_data;
  const void *uv_data;
  uint64_t y_phys;
  uint64_t uv_phys;
  uint64_t y_size;
  uint64_t uv_size;
  uint32_t width;
  uint32_t height;
  uint32_t stride;
  uint32_t vstride;
  sc132_exposure_info_t exposure;
} sc132_frame_info_t;

typedef struct sc132_frame_set_item {
  sc132_frame_t *frame;
  uint32_t camera_id;
  uint32_t frame_id;
  uint64_t sequence;
  uint64_t timestamp_ns;
  uint32_t width;
  uint32_t height;
} sc132_frame_set_item_t;

typedef struct sc132_frame_set {
  uint32_t struct_size;
  uint32_t camera_count;
  uint64_t group_id;
  uint64_t group_timestamp_ns;
  uint64_t max_skew_ns;
  sc132_frame_set_item_t items[SC132_FRAME_SET_MAX_CAMERAS];
  uint32_t reserved[8];
} sc132_frame_set_t;

typedef void (*sc132_frame_set_callback_t)(
    const sc132_frame_set_t *frame_set, void *user_data);
```

#### Single-Frame Identity, Addresses, and Layout

| `sc132_frame_info_t` field | Meaning and units |
|---|---|
| `struct_size` | Set to `sizeof(sc132_frame_info_t)` before calling; bounds library writes and returns the caller-declared size unchanged. See the old-prefix compatibility rule above. |
| `camera_id` | Software camera ID; `0..3` maps to CAM1..CAM4, not the callback array index. |
| `sequence` | Per-camera software acquisition counter; the current implementation resets it at startup and advances it before warmup/grouping. The first delivered value need not be zero, gaps are possible, and values can differ between cameras. |
| `frame_id` | Normalized frame ID after grouping against each camera's original-frame baseline; identical within an output group. Not a saved-file frame index. |
| `raw_frame_id` | Original frame ID from the SDK output-image metadata; raw here does not mean RAW10 pixels. |
| `timestamp_ns` | This camera's LPWM trigger edge mapped to realtime Unix time in ns by default, allowing backward clock steps. Test mode adds half this frame's exposure duration; not arrival, callback, or IRQ time. |
| `y_data` | Read-only CPU virtual address of the Y luma plane. |
| `uv_data` | Read-only CPU virtual address of the UV chroma plane; NV12 interleaves U/V, unlike NV21's V/U. |
| `y_phys` / `uv_phys` | Physical/DMA address of each plane for compatible hardware interfaces, not a dereferenceable CPU pointer. |
| `y_size` / `uv_size` | Buffer size of each plane in bytes, possibly including alignment padding; not the effective pixel-byte count. |
| `width` / `height` | Effective delivered width/height in pixels, using the current frame's actual output orientation and dimensions. |
| `stride` | Byte distance between adjacent row starts; current NV12 Y/UV planes share this stride, which can exceed the effective width. |
| `vstride` | Y-plane vertical layout in rows, possibly exceeding effective height for alignment; not the number of effective image rows. |
| `exposure` | Latest ISP exposure observation frozen with the frame; fields and limitations follow below. |

`sequence`, `raw_frame_id`, and `frame_id` describe the software counter, original SDK identity, and normalized grouping identity respectively. They are not interchangeable or directly usable as an MP4 `frame_index`.

NV12 is 8-bit YUV420 semi-planar: the effective Y region has `height` rows of `width` bytes; the effective UV region has `height / 2` rows of `width` bytes, with each U/V pair corresponding to a 2×2 Y-pixel block. Compute effective row starts as follows, read only the effective width per row, and first check pointers and `y_size`/`uv_size` bounds:

```c
const uint8_t *y_row =
    (const uint8_t *)info.y_data + (size_t)row * info.stride;
const uint8_t *uv_row =
    (const uint8_t *)info.uv_data + (size_t)row * info.stride;
```

Use separate addresses for Y and UV. Do not assume contiguous planes, UV starting at `y_data + width * height`, or an always-compact `width * height * 3 / 2` byte frame.

#### Exposure Observation Fields

| `sc132_exposure_info_t` field | Meaning and limitations |
|---|---|
| `status` | `0` (`SC132_EXPOSURE_UNAVAILABLE`) means unavailable, with all other exposure fields zero and no carry-forward; `1` (`SC132_EXPOSURE_ESTIMATED`) is the latest ISP estimate, without an error bound or applied-frame guarantee. |
| `source_frame_id` | Current SDK frame identity returned by the ISP query; it can be compared with the original frame ID, but equality does not prove an atomic parameter-to-frame binding. |
| `duration_ns` | SDK-reported integration seconds converted to ns, not host waiting or acquisition duration. |
| `source_timestamp` | Opaque SDK source time, not defined as RAW/realtime and not usable for Unix-time alignment. |
| `observed_raw_ns` | Query completion in `CLOCK_MONOTONIC_RAW`, in ns; not integration start or end. |

Reading the same retained frame again does not replace the observation with a later frame's value; this still does not certify applied exposure. Trigger-to-integration-start delay is uncalibrated: test-mode trigger time plus half exposure is only an estimated midpoint, not a certified one. Do not add half exposure again to an already adjusted `timestamp_ns`. See [Exposure Observations](data-contracts.md#per-frame-exposure-observations).

#### Frame-Group and Entry Fields

| `sc132_frame_set_t` field | Meaning |
|---|---|
| `struct_size` | Frame-group structure size supplied by the library. |
| `camera_count` | Number of valid entries in a normal frame group: `4` for all cameras, `1` for single-camera diagnostics. |
| `group_id` | Output-group counter within the current acquisition session, currently starting at zero; not a hardware trigger count or single-frame ID. |
| `group_timestamp_ns` | Minimum delivered per-camera realtime timestamp in this group, in ns: trigger time by default, estimated exposure midpoint in test mode. Not a substitute for all per-camera stamps. |
| `max_skew_ns` | Actual trigger-capture span in this group, maximum minus minimum in ns; not a configuration threshold or exposure-sync error. |
| `items` | At most four entries; only the first `camera_count` entries are valid, packed by enabled camera. |
| `reserved` | Some slots are defined as group-time audit metadata; see below. |

`sc132_frame_set_item_t.frame` is the opaque frame handle for metadata queries and reference management. The remaining `camera_id`, `frame_id`, `sequence`, `timestamp_ns`, `width`, and `height` are snapshots of the corresponding per-frame fields. With only cam2 enabled, the valid entry is `items[0]` with `camera_id == 2`, not `items[2]`.

The output's actual skew differs from the configured admission limit: `sc132_frame_set_config_t.max_skew_ns` is the grouping threshold, default `10000000 ns (10ms)`, not exposure or camera/IMU alignment accuracy.

| `reserved[]` slot | Public macro | Meaning |
|---|---|---|
| 0 | `SC132_GROUP_RAW_LO` | Low 32 bits of the earliest hardware-trigger RAW time in this group. |
| 1 | `SC132_GROUP_RAW_HI` | High 32 bits of the same RAW time. |
| 2 | `SC132_GROUP_UNCERTAINTY_NS` | Group-mapping uncertainty in ns, including group skew; not an exposure-accuracy guarantee. |
| 3 | `SC132_GROUP_GENERATION` | Acquisition generation distinguishing sessions; never mix across generations. |
| 4 | `SC132_GROUP_TIMING_VALID` | Must equal `SC132_GROUP_TIMING_MAGIC` before reading the extended time metadata above. |
| 5..7 | — | Reserved, without a public business meaning. |

After checking the validity marker, reconstruct RAW time as follows; it is not Unix time:

```c
uint64_t group_raw_ns =
    ((uint64_t)set->reserved[SC132_GROUP_RAW_HI] << 32) |
    (uint64_t)set->reserved[SC132_GROUP_RAW_LO];
```

#### Reading and Pixel Lifetime

See the minimal skeleton below: initialize `struct_size` and use the output only after `sc132_frame_get_info()` returns `SC132_STATUS_OK`. Copying `sc132_frame_info_t` copies metadata/pointers, not pixels, and does not extend frame lifetime.

Synchronous callback reads need no extra retain, and the library's borrowed reference must not be released. For asynchronous use, call `sc132_frame_retain()` inside the callback and `sc132_frame_release()` after the final use. Pixel addresses are always read-only and must not be freed by the consumer; do not pass them to `free()`. See lifecycle and ownership below for the complete stop order.

#### Differences from ROS2 and Encoded Output

| Public output | Structure and field mapping |
|---|---|
| SC132 C API | The frame-group/per-frame structures above, retaining separate Y/UV addresses, plane sizes, stride/vstride, and exposure observations. |
| ROS2 `image_raw` | `sensor_msgs/msg/Image`: `header.stamp` is the delivered per-camera time (trigger by default, estimated exposure midpoint in test mode), `width/height` are effective dimensions, `encoding="nv12"`, `is_bigendian=false`, `step=stride`; `data` copies the full Y buffer followed by the full UV buffer. |
| ROS2 `image_raw` layout limitation | No separate vstride/plane-size fields; do not infer the UV start or truncate data using compact-layout assumptions. See [ROS2 Data Contracts](data-contracts.md#ros2-topics). |
| ROS2 exposure | Separate `/robobaton/camN/exposure` JSON, not embedded in standard Image. |
| ROS2 `compressed` | `sensor_msgs/msg/CompressedImage`, currently JPEG, not an NV12 memory layout. |
| PRRTSP encoded callback | `prrtsp_encoded_frame_v2` describes an H.264/H.265 encoded access unit; data is borrowed only until callback return. See the PRRTSP API on this page. |

### Configuration, Lifecycle, and Integration Example

| Function | Contract |
|---|---|
| `sc132_set_fps(uint32_t fps)` | Set the camera frame rate before startup; current public values are `25/30/40/50/60`. Must not reconfigure while running or before a stop completes. |
| `sc132_set_output_rotation(uint32_t rotate_clockwise_degrees)` | Set clockwise rotation before startup, accepting `0/90/180/270`; `0/180` deliver canvas with unchanged width/height, `90/270` swap width/height. Software rotation (180/270) is done by Nano2D after scaling. The product demo additionally restricts `180` to `30fps` only. |

`sc132_frame_set_config_t.width/height` declares the delivered canvas size; public support includes native `1280x1088` and the VSE hardware full-frame scaled `640x480`, `720x480`, `1280x720`, either axial orientation is legal, and other combinations are rejected. Scaling does not change the FOV: the whole frame is stretched to the target size, and the aspect ratio changes relative to the native canvas. The delivered frame size always equals the frame-set config.

Lifecycle and ownership:

- `sc132_start_frame_set()` starts the frame-set callback.
- The `frame_set`, `items[]`, and `items[i].frame` in the callback are borrowed references, valid only during the callback.
- To keep a frame across callbacks, first call `sc132_frame_retain()`, and call `sc132_frame_release()` after use.
- `sc132_request_stop()` only linearizes the stop, forbids new acquisition/callback admission, and wakes waiters; it does not drain frames, does not call vendor APIs, does not join threads, and does not mean the callback has exited.
- Calling `sc132_request_stop()` in the idle state also enters STOPPING; a non-callback thread must then call the blocking `sc132_stop()` to complete this stop generation before reconfiguring or starting.
- After `sc132_start_frame_set()` returns `SC132_STATUS_STARTUP_FAILED`, an external non-callback thread must also call `sc132_stop()` to complete quiescence; before that, restart/config or library unload is forbidden.
- `sc132_stop()` is responsible for draining pending/queued frames, waiting for inflight callbacks, joining library threads, and closing I2C; it cannot be treated as an immediately-returning API. If the internal join fails, it keeps STOPPING and resource ownership; the external non-callback thread must retry, and restart or `dlclose` is forbidden before success.
- Calling `sc132_stop()` from the dispatcher callback thread only publishes the stop request and returns immediately; an external non-callback owner must call it once more to complete drain/join and avoid self-deadlock.

Minimal skeleton:

```c
#include "sc132camera.h"

static void on_frame_set(const sc132_frame_set_t *frame_set, void *user_data) {
  (void)user_data;
  for (uint32_t i = 0; i < frame_set->camera_count; ++i) {
    sc132_frame_info_t info = {0};
    info.struct_size = sizeof(info);
    if (sc132_frame_get_info(frame_set->items[i].frame, &info) != SC132_STATUS_OK) {
      continue;
    }
    /* Only read info.y_data/info.uv_data while the current frame reference is valid. */
  }
}

int run_camera(void) {
  sc132_frame_set_config_t config = SC132_FRAME_SET_CONFIG_INIT;
  config.callback = on_frame_set;
  config.camera_count = 4;
  config.width = SC132_NATIVE_OUTPUT_WIDTH;
  config.height = SC132_NATIVE_OUTPUT_HEIGHT;

  int32_t ret = sc132_start_frame_set(&config, 0x0f);
  if (ret != SC132_STATUS_OK) {
    sc132_stop();
    return (int)ret;
  }

  /* The application main loop runs here. */

  sc132_request_stop();
  sc132_stop();
  return 0;
}
```

## `libicm42670.so`

non-ROS header: `include/icm42670_driver.h`; ROS2: `include/robobaton_4p_ros2_demo/icm42670_driver.h`; producer: `include/icm42670_x5/icm42670_driver.h`. ABI is `2.1`; real SO `libicm42670.so.2.0.0` and SONAME `libicm42670.so.2` remain unchanged. The original nine C functions retain node `ICM42670_X5_2.0`; new `icm42670_set_fsync_callback()` uses `ICM42670_X5_2.1`. This is incompatible with V1 ICM-42688; migrate headers, SOs, and consumers together.

Status codes:

| Status code | Meaning |
|---|---|
| `ICM42670_STATUS_OK` | Success |
| `ICM42670_STATUS_INVALID_ARGUMENT` | Invalid argument |
| `ICM42670_STATUS_INVALID_STATE` | Invalid lifecycle state |
| `ICM42670_STATUS_IO_ERROR` | I/O error |
| `ICM42670_STATUS_INTERNAL_ERROR` | Internal error |

Core structures and constraints:

- `icm42670_config_t` defaults to `sample_rate_hz=800`, `fifo_watermark_samples=1`, `read_mode=ICM42670_READ_MODE_SENSOR_TIMESTAMP_FIFO`.
- `sample_rate_hz` accepts only native `25/50/100/200/400/800/1600`; old `500/1000/2000Hz` and other invalid values are explicitly rejected, not silently resampled. Only sensor timestamp FIFO read mode is accepted.
- `sample_timestamp_ns` follows FIFO TMST-to-RAW-to-`CLOCK_REALTIME`; `host_timestamp_ns` is the INT1 edge in the same domain. Bridges refresh at publication without a frozen offset and follow backward system-clock steps. A common domain does not guarantee FSYNC sample/exposure synchronization.
- The callback is invoked serially by the acquisition thread; `sample` is a borrowed reference.
- `stop/destroy` wait for the acquisition thread and must not be called from the callback.
- `user_data` must remain valid until `icm42670_stop()` returns.
- `icm42670_get_runtime_health()` reads only after the most recent start generation has successfully stopped; before a successful stop, do not treat the output structure as a valid snapshot.
- `icm42670_is_running()` returns whether the current handle is in the running state and can be used for state queries; it does not replace the `icm42670_stop()`/`destroy()` lifecycle order.
- `icm42670_status_message(status)` maps a status code to a process-static read-only string; the returned pointer must not be modified or freed.
- `config.reserved[ICM42670_CONFIG_FSYNC_ENABLE_INDEX]=1` explicitly enables rising-edge FSYNC; default is `0`. Only `800/1600Hz` are supported when enabled. Register a separate `icm42670_fsync_event_t` callback with `icm42670_set_fsync_callback(handle, callback, user_data)`; sample/config sizes are unchanged.
- FSYNC callback runs serially after the same admitted sample's callback. The event is borrowed, with the same exception and stop/destroy rules. `sample_sequence` and `sample_timestamp_ns` identify that actual sample; `fsync_to_sample_ns` is hardware delay, and `uncertainty_ns` includes missing-TMST reconstruction. RAW fields are association-only; public time remains realtime.
- After successful stop, health `reserved[ICM42670_HEALTH_FSYNC_CAPTURED_INDEX]` counts captured hardware tags; `reserved[ICM42670_HEALTH_FSYNC_DROPPED_INDEX]` counts tags without published associations, including tail packets missing a following absolute TMST. `fsync_sequence` includes dropped tags and may have gaps. See [Data Contracts](data-contracts.md) for matching and status semantics.

`icm42670_runtime_health_t` is initialized with `ICM42670_RUNTIME_HEALTH_INIT`. Field meanings: `session_generation` (the most recent start generation), `published_samples` (samples published by the producer), `gpio_event_gap_count` (GPIO edge gaps), `fifo_overflow_count` (FIFO overflows), `mapper_failure_count` (time-mapping failures), `uncertainty_over_200_drop_count` (samples dropped because uncertainty exceeded 200 us), `max_consecutive_timing_drop_count` (maximum consecutive timing drops), and `invalid_packet_drop_count` (invalid FIFO packets dropped, including drops after the last sample publication). Use the final snapshot after successful stop, not the last sample's counters. When the call returns a non-`ICM42670_STATUS_OK` value, do not read the output structure as a valid snapshot.

```c
icm42670_runtime_health_t health = ICM42670_RUNTIME_HEALTH_INIT;
int health_ret = icm42670_get_runtime_health(handle, &health);
if (health_ret != ICM42670_STATUS_OK) {
  /* The snapshot is valid only after the most recent start succeeded and the stop completed. */
  return health_ret;
}
```

Minimal skeleton:

```c
#include "icm42670_driver.h"

static void on_imu_sample(const icm42670_sample_t *sample, void *user_data) {
  (void)user_data;
  /* sample_timestamp_ns/host_timestamp_ns already use CLOCK_REALTIME; consumers preserve them. */
  (void)sample->sample_timestamp_ns;
  (void)sample->accel_mps2[0];
}

int run_imu(void) {
  icm42670_config_t config = ICM42670_CONFIG_INIT;
  config.sample_rate_hz = 800;
  config.fifo_watermark_samples = 1;

  icm42670_handle_t *handle = 0;
  int ret = icm42670_create(&config, &handle);
  if (ret != ICM42670_STATUS_OK) {
    return ret;
  }
  ret = icm42670_set_callback(handle, on_imu_sample, 0);
  if (ret != ICM42670_STATUS_OK) {
    icm42670_destroy(handle);
    return ret;
  }
  ret = icm42670_start(handle);
  if (ret != ICM42670_STATUS_OK) {
    icm42670_destroy(handle);
    return ret;
  }

  /* The application main loop runs here. */

  icm42670_stop(handle);
  icm42670_destroy(handle);
  return 0;
}
```

## `libprrtsp.so`

Header: `include/prrtsp_v2.h`.

Status codes:

| Status code | Meaning |
|---|---|
| `PRRTSP_OK` | Success |
| `PRRTSP_E_INVALID_ARGUMENT` | Invalid argument |
| `PRRTSP_E_UNSUPPORTED` | Unsupported |
| `PRRTSP_E_NO_MEMORY` | Out of memory |
| `PRRTSP_E_BUSY` | Resource busy |
| `PRRTSP_E_STATE` | Invalid state |
| `PRRTSP_E_CODEC` | Codec error |
| `PRRTSP_E_RTSP` | RTSP error |
| `PRRTSP_E_TIMEOUT` | Timeout |
| `PRRTSP_E_INTERNAL` | Internal error |
| `PRRTSP_E_CLEANUP_REQUIRED` | Cleanup required |

Core structures:

| Structure | Purpose |
|---|---|
| `prrtsp_stream_config_v2` | Width/height, fps, bitrate, rotation, port, path, codec. |
| `prrtsp_nv12_frame_v2` | NV12 Y/UV addresses, physical addresses, stride/vstride, size, timestamp. |
| `prrtsp_stream_status_v2` | stream state, error, and counts. |

Configuration structures are backward-compatible by `struct_size`:

| Version | `struct_size` | New capability |
|---|---:|---|
| V2.0 | `PRRTSP_STREAM_CONFIG_V2_0_SIZE` (`232`) | Basic stream configuration; `PRRTSP_CODEC_DEFAULT` is H.264. |
| V2.1 | `PRRTSP_STREAM_CONFIG_V2_1_SIZE` (`240`) | Adds an explicit `codec` and allows `PRRTSP_STREAM_FLAG_EXTERNAL_NV12`. |
| V2.2 | `PRRTSP_STREAM_CONFIG_V2_2_SIZE` (`256`) | Adds `encoded_frame_callback` and `encoded_frame_user`. |

Callers must set `struct_size` to the version size they actually provide; do not declare newer fields with a smaller structure, and do not assume an old library recognizes the V2.2 extension.

V2.2 encoded callback:

- `prrtsp_encoded_frame_v2` describes one encoded access unit; `codec` indicates H.264/H.265, and `PRRTSP_ENCODED_FRAME_FLAG_KEY_FRAME` marks key frames;
- `data_address` is only borrowed until the callback returns; the callback must not save that address, block for a long time, or re-enter the same stream; for async holding, copy within the callback;
- `timestamp_ns` keeps the original ns value of the corresponding input NV12 frame, does not reverse-engineer from the encoder microsecond PTS, and does not auto-change the time domain.

External NV12:

- `PRRTSP_STREAM_FLAG_EXTERNAL_NV12` requires `struct_size >= PRRTSP_STREAM_CONFIG_V2_1_SIZE`.
- `prrtsp_stream_send_external()` borrows the caller's NV12 addresses.
- When `release_callback` is non-null, the function consumes the frame lease on all return paths and finally calls back exactly once.
- The release callback may run before the send function returns, or be delayed until input-slot recycling or stream close; do not re-enter the same stream.
- `prrtsp_stream_get_status()` can read state, error, and counts during the stream's lifecycle.
- `prrtsp_stream_close()` takes a `prrtsp_stream_t **`; after a successful close, that pointer should be cleared and the caller must not use the old stream.

Minimal skeleton:

```c
#include <stdio.h>
#include "prrtsp_v2.h"

int open_rtsp(prrtsp_stream_t **stream) {
  prrtsp_stream_config_v2 config = {0};
  config.struct_size = PRRTSP_STREAM_CONFIG_V2_1_SIZE;
  config.flags = PRRTSP_STREAM_FLAG_EXTERNAL_NV12;
  config.width = 1280;
  config.height = 1088;
  config.fps_num = 30;
  config.fps_den = 1;

  config.bitrate_kbps = 4000;
  config.port = 554;
  config.codec = PRRTSP_CODEC_H264;
  config.operation_timeout_ms = 1000;
  snprintf(config.path, sizeof(config.path), "%s", "/PRR");
  return prrtsp_stream_open(&config, stream);
}
```

## Whole-Package Deployment Requirement

`libsc132.so`, `libicm42670.so`, `libprrtsp.so`, the public headers, and the demo programs must come from the same public delivery package. Do not replace the current `.so` alone into unmigrated programs; the ROS2 install path uses the public headers, runtime libraries, and manifest carried by `RoboBaton_4P_ROS2_demo` itself, and must not be mixed with the non-ROS `/root/demo` runtime package.
