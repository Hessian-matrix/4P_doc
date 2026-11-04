# API Reference

This page covers current public C ABI/API headers. Version getters require no hardware initialization; runtime health can report terminal diagnostics including obtained failed-stop diagnostics. Examples show integration lifecycle only; the application owns data consumption and runtime waiting.

Header contracts and target-environment verification are separate layers. See {ref}`Capability and Verification Boundaries <capability-verification-boundary>` for current capabilities and throughput/pressure/long-recording limits. Callable APIs or passing package verification do not establish system acceptance.

## Release Version Query

The product release version follows SemVer and is independent of the SO SONAME/ABI version. The version-string getters require no hardware initialization and return a process-static read-only string that the caller must not modify or free:

```c
const char *camera_version = sc132_get_version();
const char *imu_version = icm42670_get_version();
const char *rtsp_version = prrtsp_get_version();
```

Delivered executables also support `--version`. The non-ROS `cam_demo`/`sensor_demo` and the ROS2 `robobaton_sensors_node` print the versions of the in-house SOs they actually load, to detect mixing programs and SOs of different versions. The ROS2 compressed image_transport plugin additionally exports `robobaton_nv12_compressed_image_transport_get_version()`.

## `libsc132.so`

Header: `include/sc132camera.h`. ABI: `SC132_ABI_VERSION_MAJOR=3`, `SC132_ABI_VERSION_MINOR=0`; real SO `libsc132.so.3.0.0`, SONAME `libsc132.so.3`, symbol node `LIBSC132_3.0`. Consumers must follow the current headers' time-domain, trigger-mode, and frame-info field semantics. Consumers of other ABIs must be rebuilt and relinked as a complete set; a `.so.2 -> .so.3` compatibility link is forbidden.

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

Public camera `timestamp_ns` and `group_timestamp_ns` use `CLOCK_REALTIME` Unix nanoseconds and follow clock corrections, including backward steps. Startup `SC132_TIMESTAMP_PATH=observer` (default) selects the existing bounded SIF mapping; `official` selects the same frame's RAW IRQ `timestamps − (tv − trig_tv) × 1000`, without starting the SIF observer and without a physical-error bound. Consumers set the environment from their startup selector; invalid values fail startup and changes require stop/restart. Observer requires read-only X5 `/dev/mem` and retains `500µs` window admission. Official reports timing validity `0`/uncertainty `UINT32_MAX`; neither path falls back to the other. Timestamps are trigger estimates by default; the opt-in {ref}`Exposure-Midpoint Test Switch <test-exposure-midpoint>` adds half exposure, not a certified physical midpoint. See [Time Data Contracts](data-contracts.md).

ABI 3.0 appends `exposure` (`sc132_exposure_info_t`) to `sc132_frame_info_t`. `sc132_frame_get_info()` accepts the current `sizeof(info)` or the old prefix size ending before `exposure`, writes only the declared size, and returns `struct_size` unchanged. New consumers require matching headers/SOs.

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
| 0 | `SC132_GROUP_RAW_LO` | Low 32 bits of the earliest selected trigger RAW estimate: bounded observer mapping or official IRQ-derived estimate. |
| 1 | `SC132_GROUP_RAW_HI` | High 32 bits of the same RAW time. |
| 2 | `SC132_GROUP_UNCERTAINTY_NS` | Observer group-mapping uncertainty in ns, including skew; official is `UINT32_MAX` (unknown), not a physical-accuracy claim. |
| 3 | `SC132_GROUP_GENERATION` | Acquisition generation distinguishing sessions; never mix across generations. |
| 4 | `SC132_GROUP_TIMING_VALID` | Observer uses `SC132_GROUP_TIMING_MAGIC` for bounded mapping metadata; official is `0` and must not be treated as bounded-valid. |
| 5..7 | — | Reserved, without a public business meaning. |

For bounded use first require `SC132_GROUP_TIMING_MAGIC`; official values are diagnostic estimates only, with unknown uncertainty. The selected RAW estimate can be reconstructed below; it is not Unix time and zero official validity must never be promoted to a timing certificate:

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

non-ROS header: `include/icm42670_driver.h`; ROS2: `include/robobaton_4p_ros2_demo/icm42670_driver.h`. ABI `5.0`, real file `libicm42670.so.5.0.0`, SONAME `libicm42670.so.5`; all nine C exports use only `ICM42670_X5_5.0`. This is a layout- and semantics-incompatible cutover from ABI4. Synchronize headers, library, and every rebuilt consumer; remove old-major libraries without cross-major links or old symbol aliases. A matched kernel IIO V3 capture module is required; V2 is incompatible even for host mode. Software VERSION remains independent.

| Export | Contract |
|---|---|
| `icm42670_create` | Validate config and create an opaque handle |
| `icm42670_set_callback` | Register the serial callback and user_data before start; return `INVALID_STATE` during capture/STOP drain until join completes, including callback-side calls |
| `icm42670_start` | Require a non-null registered callback or return `INVALID_STATE`; enumerate the unique IIO instance, validate scan/control identity, and start capture |
| `icm42670_stop` | Keep callback admission open, drain the STOP cohort, and join; repeated calls retain terminal state |
| `icm42670_is_running` | Query running state, not a replacement for stop/join |
| `icm42670_get_runtime_health` | Query terminal state including obtained failed-stop diagnostics; check status and generation |
| `icm42670_destroy` | Stop and release the handle; never call from a callback |
| `icm42670_get_version` | Hardware-independent static read-only product version; do not modify or free |
| `icm42670_status_message` | Static read-only status text; do not modify or free |

Statuses are `OK=0`, `INVALID_ARGUMENT=-1`, `INVALID_STATE=-2`, `IO_ERROR=-3`, `INTERNAL_ERROR=-4` with the `ICM42670_STATUS_` prefix.

`icm42670_config_t` contains u32 `struct_size, sample_rate_hz, fifo_watermark_samples, buffer_capacity, sample_drop_policy, timestamp_mode, reserved[2]`. Use `ICM42670_CONFIG_INIT`: default `800Hz`, watermark `1`, buffer `4096`, `ALLOW_COUNTED`, `ICM42670_TIMESTAMP_MODE_HOST=0`; `ICM42670_TIMESTAMP_MODE_TMST=1` selects TMST. ODR accepts only `25/50/100/200/400/800/1600`; watermark must be1, buffer a power of two in256..8192, and reserved zero. Invalid mode values are rejected; set the mode when creating the handle and stop/recreate/restart to change it. `ALLOW_COUNTED`/`STRICT` govern invalid six-axis payloads, not timestamp precision. Both modes use the same IIO reads/owner, with no userspace SPI/spidev, module loading, DT changes, or fallback.

`icm42670_sample_t` contains u32 `struct_size/session_generation`, u64 `sample_monotonic_ns/sample_sequence`, u32 `burst_flags/fifo_tmst`, u64 `evidence_id/burst_complete_raw_ns/observation_monotonic_ns/estimated_period_ns`, u32 `timestamp_source/packet_flags`, double `temperature_c/accel_mps2[3]/gyro_rps[3]`, 16-byte `raw` (int16 temperature, accel[3], gyro[3], reserved), then u64 `sample_raw_ns` and u32 `timestamp_uncertainty_ns/timestamp_mode`. `fifo_tmst` is the raw u16 FIFO value zero-extended into u32. Both modes retain the original MONOTONIC host estimate and independent RAW burst completion; never directly subtract clock domains. Host leaves `sample_raw_ns=0` and uncertainty `UINT32_MAX`. TMST uses kernel-owned FIFO/UI transition evidence, userspace unwrapping, and bounded affine RAW mapping with `200µs` computational admission, not physical accuracy. Output adapters bridge the selected native sample clock to realtime and retain MONOTONIC and RAW bridge bases separately. See [IMU Data Contracts](data-contracts.md#imu) for fields, flags, schema v2, and every health field. No FSYNC API or trigger-to-sample association is restored.

A callback borrows the sample until return, must not throw, and must not call stop/destroy. Asynchronous consumers must copy it and keep user_data alive until stop returns. Samples may arrive during stop: drain concurrently rather than closing admission first. A record is ACKed only after all covered samples reach callbacks. `transport_complete` certifies only consumption/ACK of the stop cohort, excludes the physical tail beyond the fence, and does not cancel fatal errors. Evaluate stop status, health status, generation, errors, and counts together, not only the last sample.

The callback and user_data are fixed for one capture lifecycle, avoiding registration races with sample delivery. Replace or clear them only before start or after stop/join. Obtained terminal STOP/QUERY kernel diagnostics are retained independently before local scan/ACK reconciliation. Failed reconciliation still returns an error with `transport_complete=0`, without discarding those diagnostics or releasing undelivered records.

Calls to start or get_runtime_health from capture or STOP-tail callbacks return `INVALID_STATE` directly without waiting on the lifecycle lock. Query final health externally after stop/join.

Minimal lifecycle example (application consumption/waiting is caller-owned):

```c
#include "icm42670_driver.h"

static void on_sample(const icm42670_sample_t *sample, void *user) {
  (void)user;
  /* Borrowed native MONOTONIC sample; do not block or stop here. */
  (void)sample->sample_monotonic_ns;
  (void)sample->accel_mps2[0];
}

int run_imu(void) {
  icm42670_config_t config = ICM42670_CONFIG_INIT;
  icm42670_handle_t *handle = 0;
  int ret = icm42670_create(&config, &handle);
  if (ret != ICM42670_STATUS_OK) return ret;
  ret = icm42670_set_callback(handle, on_sample, 0);
  if (ret == ICM42670_STATUS_OK) ret = icm42670_start(handle);
  /* Run the application while callbacks are admitted. */
  int stopped = icm42670_stop(handle);
  icm42670_runtime_health_t health = ICM42670_RUNTIME_HEALTH_INIT;
  int queried = icm42670_get_runtime_health(handle, &health);
  if (ret == ICM42670_STATUS_OK) ret = stopped;
  if (ret == ICM42670_STATUS_OK) ret = queried;
  if (ret == ICM42670_STATUS_OK &&
      (!health.session_generation || !health.transport_complete ||
       health.fatal_reason || health.fatal_errno || health.quiesce_errno ||
       health.fifo_overflow_count || health.scan_push_failure_count ||
       health.evidence_full_count || health.records_consumed != health.records_acked))
    ret = ICM42670_STATUS_IO_ERROR;
  icm42670_destroy(handle);
  return ret;
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

The current library set is `libicm42670.so.5.0.0` / `ICM42670_X5_5.0`, `libsc132.so.3.0.0` / `LIBSC132_3.0`, and `libprrtsp.so.2.0.1` / `LIBPRRTSP_2.0`. Remove old ICM42670 `.2`/`.3`/`.4` and SC132 `.2` libraries and rebuild every consumer, without cross-major aliases; ROS2 does not carry PRRTSP. Application packages do not install the required matched IIO V3 kernel module.
