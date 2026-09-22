# API Reference

This page covers the C ABI/API in the current public headers. Examples only show the minimal integration skeleton and do not reproduce the underlying producer source. The version-string getters do not require hardware initialization; the runtime-health-snapshot getter is only valid after the most recent acquisition has successfully stopped.

## Release Version Query

The product release version follows SemVer and is independent of the SO SONAME/ABI version. The version-string getters require no hardware initialization and return a process-static read-only string that the caller must not modify or free:

```c
const char *camera_version = sc132_get_version();
const char *imu_version = icm42688_get_version();
const char *rtsp_version = prrtsp_get_version();
```

Delivered executables also support `--version`. The non-ROS `cam_demo`/`sensor_demo` and the ROS2 `robobaton_sensors_node` print the versions of the in-house SOs they actually load, to detect mixing programs and SOs of different versions. The ROS2 compressed image_transport plugin additionally exports `robobaton_nv12_compressed_image_transport_get_version()`.

## `libsc132.so`

Header: `include/sc132camera.h`. ABI: `SC132_ABI_VERSION_MAJOR=2`, `SC132_ABI_VERSION_MINOR=0`; the real SO is `libsc132.so.2.0.1`, SONAME still `libsc132.so.2`.

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

Configuration functions:

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

## `libicm42688.so`

Header: `include/icm42688_driver.h`. ABI: `ICM42688_ABI_VERSION_MAJOR=2`, `ICM42688_ABI_VERSION_MINOR=1`; the real SO is `libicm42688.so.2.1.0`, SONAME still `libicm42688.so.2`.

Status codes:

| Status code | Meaning |
|---|---|
| `ICM42688_STATUS_OK` | Success |
| `ICM42688_STATUS_INVALID_ARGUMENT` | Invalid argument |
| `ICM42688_STATUS_INVALID_STATE` | Invalid lifecycle state |
| `ICM42688_STATUS_IO_ERROR` | I/O error |
| `ICM42688_STATUS_INTERNAL_ERROR` | Internal error |

Core structures and constraints:

- `icm42688_config_t` defaults to `sample_rate_hz=1000`, `fifo_watermark_samples=1`, `read_mode=ICM42688_READ_MODE_SENSOR_TIMESTAMP_FIFO`.
- `sample_rate_hz` accepts only `25/50/100/200/500/1000/2000`; currently only the sensor timestamp FIFO read mode is accepted.
- The callback is invoked serially by the acquisition thread; `sample` is a borrowed reference.
- `stop/destroy` wait for the acquisition thread and must not be called from the callback.
- `user_data` must remain valid until `icm42688_stop()` returns.
- `icm42688_get_runtime_health()` reads only after the most recent start generation has successfully stopped; before a successful stop, do not treat the output structure as a valid snapshot.
- `icm42688_is_running()` returns whether the current handle is in the running state and can be used for state queries; it does not replace the `icm42688_stop()`/`destroy()` lifecycle order.
- `icm42688_status_message(status)` maps a status code to a process-static read-only string; the returned pointer must not be modified or freed.

`icm42688_runtime_health_t` is initialized with `ICM42688_RUNTIME_HEALTH_INIT`. Field meanings: `session_generation` (the most recent start generation), `published_samples` (samples published by the producer), `gpio_event_gap_count` (GPIO edge gaps), `fifo_overflow_count` (FIFO overflows), `mapper_failure_count` (time-mapping failures), `uncertainty_over_200_drop_count` (samples dropped because uncertainty exceeded 200 us), and `max_consecutive_timing_drop_count` (maximum consecutive timing drops). When the call returns a non-`ICM42688_STATUS_OK` value, do not read the output structure as a valid snapshot.

```c
icm42688_runtime_health_t health = ICM42688_RUNTIME_HEALTH_INIT;
int health_ret = icm42688_get_runtime_health(handle, &health);
if (health_ret != ICM42688_STATUS_OK) {
  /* The snapshot is valid only after the most recent start succeeded and the stop completed. */
  return health_ret;
}
```

Minimal skeleton:

```c
#include "icm42688_driver.h"

static void on_imu_sample(const icm42688_sample_t *sample, void *user_data) {
  (void)user_data;
  /* sample_timestamp_ns/host_timestamp_ns are in the underlying time domain; the demo maps them separately before printing. */
  (void)sample->sample_timestamp_ns;
  (void)sample->accel_mps2[0];
}

int run_imu(void) {
  icm42688_config_t config = ICM42688_CONFIG_INIT;
  config.sample_rate_hz = 1000;
  config.fifo_watermark_samples = 1;

  icm42688_handle_t *handle = 0;
  int ret = icm42688_create(&config, &handle);
  if (ret != ICM42688_STATUS_OK) {
    return ret;
  }
  ret = icm42688_set_callback(handle, on_imu_sample, 0);
  if (ret != ICM42688_STATUS_OK) {
    icm42688_destroy(handle);
    return ret;
  }
  ret = icm42688_start(handle);
  if (ret != ICM42688_STATUS_OK) {
    icm42688_destroy(handle);
    return ret;
  }

  /* The application main loop runs here. */

  icm42688_stop(handle);
  icm42688_destroy(handle);
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

`libsc132.so`, `libicm42688.so`, `libprrtsp.so`, the public headers, and the demo programs must come from the same public delivery package. Do not replace the current `.so` alone into unmigrated programs; the ROS2 install path uses the public headers, runtime libraries, and manifest carried by `RoboBaton_4P_ROS2_demo` itself, and must not be mixed with the non-ROS `/root/demo` runtime package.
