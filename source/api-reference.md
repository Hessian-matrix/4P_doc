# API 参考

本页覆盖当前公开头文件中的 C ABI/API。示例只展示最小集成骨架，不复制底层 producer 源码。

## 发布版本查询

产品发布版本遵循SemVer，并与SO的SONAME/ABI版本相互独立。所有getter都无需初始化硬件，返回进程静态只读字符串，调用方不得修改或释放：

```c
const char *camera_version = sc132_get_version();
const char *imu_version = icm42688_get_version();
const char *rtsp_version = prrtsp_get_version();
```

交付可执行文件也支持`--version`。non-ROS的`cam_demo`/`sensor_demo`以及ROS2的`robobaton_sensors_node`会同时打印其实际加载的自研SO版本，从而发现不同版本程序和SO混装。ROS2 compressed image_transport插件额外导出`robobaton_nv12_compressed_image_transport_get_version()`。

## `libsc132.so`

头文件：`include/sc132camera.h`。ABI：`SC132_ABI_VERSION_MAJOR=2`，`SC132_ABI_VERSION_MINOR=0`。

状态码：

| 状态码 | 含义 |
|---|---|
| `SC132_STATUS_OK` | 成功 |
| `SC132_STATUS_INVALID_ARGUMENT` | 参数非法 |
| `SC132_STATUS_INVALID_STATE` | 生命周期状态非法 |
| `SC132_STATUS_STARTUP_FAILED` | 启动失败 |

核心结构：

| 结构 | 用途 |
|---|---|
| `sc132_frame_info_t` | 单帧 NV12 地址、物理地址、尺寸、stride/vstride、时间戳。 |
| `sc132_frame_set_item_t` | 帧组中的单路条目。 |
| `sc132_frame_set_t` | 同一组四路帧、`group_id`、`group_timestamp_ns` 和实际观测到的 `max_skew_ns`。 |
| `sc132_frame_set_config_t` | frame-set callback、相机数量、尺寸、超时和配组放行 skew 上限。 |

生命周期和所有权：

- `sc132_start_frame_set()` 启动 frame-set callback。
- callback 中的 `frame_set`、`items[]` 和 `items[i].frame` 都是借用引用，仅在 callback 期间有效。
- 需要跨 callback 保存帧时，必须先 `sc132_frame_retain()`，使用完成后 `sc132_frame_release()`。
- `sc132_request_stop()` 只请求停止；普通 owner 线程随后调用 blocking `sc132_stop()` 完成 drain/join。
- `sc132_stop()` 不应被当作“立刻返回”的 API；真实清理完成前不要卸载库或重新 start。

最小骨架：

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
    /* 只在当前 frame 引用有效期间读取 info.y_data/info.uv_data。 */
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

  /* 应用主循环在这里运行。 */

  sc132_request_stop();
  sc132_stop();
  return 0;
}
```

## `libicm42688.so`

头文件：`include/icm42688_driver.h`。ABI：`ICM42688_ABI_VERSION_MAJOR=2`，`ICM42688_ABI_VERSION_MINOR=0`。

状态码：

| 状态码 | 含义 |
|---|---|
| `ICM42688_STATUS_OK` | 成功 |
| `ICM42688_STATUS_INVALID_ARGUMENT` | 参数非法 |
| `ICM42688_STATUS_INVALID_STATE` | 生命周期状态非法 |
| `ICM42688_STATUS_IO_ERROR` | I/O 错误 |
| `ICM42688_STATUS_INTERNAL_ERROR` | 内部错误 |

核心结构与约束：

- `icm42688_config_t` 默认 `sample_rate_hz=1000`、`fifo_watermark_samples=1`、`read_mode=ICM42688_READ_MODE_SENSOR_TIMESTAMP_FIFO`。
- 当前只接受 sensor timestamp FIFO 读取模式。
- callback 由采集线程串行调用；`sample` 是借用引用。
- `stop/destroy` 会等待采集线程，不得从 callback 中调用。
- `user_data` 必须保持有效直到 `icm42688_stop()` 返回。

最小骨架：

```c
#include "icm42688_driver.h"

static void on_imu_sample(const icm42688_sample_t *sample, void *user_data) {
  (void)user_data;
  /* sample_timestamp_ns/host_timestamp_ns 为底层时间域，demo 打印前会另行映射。 */
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

  /* 应用主循环在这里运行。 */

  icm42688_stop(handle);
  icm42688_destroy(handle);
  return 0;
}
```

## `libprrtsp.so`

头文件：`include/prrtsp_v2.h`。

状态码：

| 状态码 | 含义 |
|---|---|
| `PRRTSP_OK` | 成功 |
| `PRRTSP_E_INVALID_ARGUMENT` | 参数非法 |
| `PRRTSP_E_UNSUPPORTED` | 不支持 |
| `PRRTSP_E_NO_MEMORY` | 内存不足 |
| `PRRTSP_E_BUSY` | 资源忙 |
| `PRRTSP_E_STATE` | 状态非法 |
| `PRRTSP_E_CODEC` | 编码错误 |
| `PRRTSP_E_RTSP` | RTSP 错误 |
| `PRRTSP_E_TIMEOUT` | 超时 |
| `PRRTSP_E_INTERNAL` | 内部错误 |
| `PRRTSP_E_CLEANUP_REQUIRED` | 需要清理 |

核心结构：

| 结构 | 用途 |
|---|---|
| `prrtsp_stream_config_v2` | 宽高、fps、码率、旋转、端口、path、codec。 |
| `prrtsp_nv12_frame_v2` | NV12 Y/UV 地址、物理地址、stride/vstride、size、时间戳。 |
| `prrtsp_stream_status_v2` | stream 状态、错误和计数。 |

外部 NV12：

- `PRRTSP_STREAM_FLAG_EXTERNAL_NV12` 需要 `struct_size >= PRRTSP_STREAM_CONFIG_V2_1_SIZE`。
- `prrtsp_stream_send_external()` 借用调用方的 NV12 地址。
- `release_callback` 非空时，函数在所有返回路径都会消费帧租约，并最终恰好回调一次。
- release callback 可能在发送函数返回前执行，也可能延迟到输入槽回收或 stream close；不得重入同一 stream。
- `prrtsp_stream_get_status()` 可在 stream 生命周期内读取状态、错误和计数。
- `prrtsp_stream_close()` 接收 `prrtsp_stream_t **`；成功关闭后该指针应清空，调用方不得继续使用旧 stream。

最小骨架：

```c
#include <stdio.h>
#include "prrtsp_v2.h"

int open_rtsp(prrtsp_stream_t **stream) {
  prrtsp_stream_config_v2 config = {0};
  config.struct_size = PRRTSP_STREAM_CONFIG_V2_1_SIZE;
  config.flags = PRRTSP_STREAM_FLAG_EXTERNAL_NV12;
  config.width = 1280;
  config.height = 1088;
  config.fps_num = 60;
  config.fps_den = 1;
  config.bitrate_kbps = 4000;
  config.port = 554;
  config.codec = PRRTSP_CODEC_H264;
  config.operation_timeout_ms = 1000;
  snprintf(config.path, sizeof(config.path), "%s", "/PRR");
  return prrtsp_stream_open(&config, stream);
}
```

## 成套部署要求

`libsc132.so`、`libicm42688.so`、`libprrtsp.so`、公开头文件和 demo 程序必须来自同一公开交付包。不要把当前 `.so` 单独替换到未迁移程序；ROS2 install 路径使用 `RoboBaton_4P_ROS2_demo` 自身携带的公开头文件、运行库和 manifest，不要与 non-ROS `/root/demo` 运行包混用。
