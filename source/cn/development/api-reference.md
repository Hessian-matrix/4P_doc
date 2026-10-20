# API 参考

本页覆盖当前公开头文件中的 C ABI/API。示例只展示最小集成骨架，不复制底层 producer 源码。版本字符串 getter 不需要初始化硬件；运行健康快照 getter 只在最近一次采集成功 stop 后有效。

## 发布版本查询

产品发布版本遵循SemVer，并与SO的SONAME/ABI版本相互独立。版本字符串 getter 无需初始化硬件，返回进程静态只读字符串，调用方不得修改或释放：

```c
const char *camera_version = sc132_get_version();
const char *imu_version = icm42670_get_version();
const char *rtsp_version = prrtsp_get_version();
```

交付可执行文件也支持`--version`。non-ROS的`cam_demo`/`sensor_demo`以及ROS2的`robobaton_sensors_node`会同时打印其实际加载的自研SO版本，从而发现不同版本程序和SO混装。ROS2 compressed image_transport插件额外导出`robobaton_nv12_compressed_image_transport_get_version()`。

## `libsc132.so`

头文件：`include/sc132camera.h`。ABI：`SC132_ABI_VERSION_MAJOR=2`，`SC132_ABI_VERSION_MINOR=2`；real SO 为 `libsc132.so.2.0.0`，SONAME 仍为 `libsc132.so.2`。

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

所有公开相机 `timestamp_ns` 与 `group_timestamp_ns` 均为硬件触发沿映射后的 `CLOCK_REALTIME` Unix 纳秒时间，运行中跟随校时并允许回拨；不是到帧/IRQ 或曝光中心。需要 X5 `/dev/mem` 只读权限，映射缺失/超窗即停止。详见[时间数据合同](data-contracts.md)。

ABI 2.2 在 `sc132_frame_info_t` 尾部增加 `exposure`（`sc132_exposure_info_t`）。`sc132_frame_get_info()` 接受当前 `sizeof(info)` 或不含 `exposure` 的旧前缀尺寸，只写调用方声明的尺寸并原样返回 `struct_size`；新 consumer 必须与新头文件/SO 成套使用。

`exposure.status=1`（`SC132_EXPOSURE_ESTIMATED`）表示采集时冻结的最新 ISP 曝光观测，不证明该帧实际生效曝光，也没有误差上界；`0`（`SC132_EXPOSURE_UNAVAILABLE`）表示查询失败或数值非法，其余曝光字段全零，不沿用上一帧。`duration_ns` 是 SDK 积分秒数转换后的纳秒；`source_frame_id/source_timestamp` 是非原子查询返回的 SDK 当前标识，后者是 opaque 值，不是 RAW/realtime；`observed_raw_ns` 是查询完成时的 `CLOCK_MONOTONIC_RAW`，不是积分起止时间。详见[曝光观测合同](data-contracts.md#逐帧曝光观测)。

配置函数：

| 函数 | 合同 |
|---|---|
| `sc132_set_fps(uint32_t fps)` | 在启动前设置相机帧率；当前公开值为 `25/30/40/50/60`。运行中或停止未完成时不得重新配置。 |
| `sc132_set_output_rotation(uint32_t rotate_clockwise_degrees)` | 在启动前设置顺时针旋转，接受 `0/90/180/270`；`0/180` 交付画布不交换宽高，`90/270` 交换宽高。软件旋转（180/270）在缩放之后由 Nano2D 完成。产品 demo 还限制 `180` 仅用于 `30fps`。 |

`sc132_frame_set_config_t.width/height` 声明交付画布尺寸；公开支持原生 `1280x1088` 与 VSE 硬件整幅缩放的 `640x480`、`720x480`、`1280x720`，两种轴向写法均合法，其余组合拒绝。缩放不改变 FOV：整幅拉伸到目标尺寸，横纵比相对原生画布改变。交付帧尺寸恒等于 frame-set config。

生命周期和所有权：

- `sc132_start_frame_set()` 启动 frame-set callback。
- callback 中的 `frame_set`、`items[]` 和 `items[i].frame` 都是借用引用，仅在 callback 期间有效。
- 需要跨 callback 保存帧时，必须先 `sc132_frame_retain()`，使用完成后 `sc132_frame_release()`。
- `sc132_request_stop()` 只线性化停止、禁止新的采集/callback admission 并唤醒等待者；它不 drain frame、不调用 vendor API、不 join 线程，也不表示 callback 已退出。
- idle 状态调用 `sc132_request_stop()` 也会进入 STOPPING；必须再由非 callback 线程调用 blocking `sc132_stop()` 完成本次 stop generation，之后才能重新配置或启动。
- `sc132_start_frame_set()` 返回 `SC132_STATUS_STARTUP_FAILED` 后，也必须由外部非 callback 线程调用 `sc132_stop()` 完成 quiescence；在此之前不得重新 start/config 或卸载库。
- `sc132_stop()` 负责 drain pending/queued frame、等待 inflight callback、join 库线程并关闭 I2C，不能当作立即返回 API。若 internal join 失败，它会保持 STOPPING 和资源所有权；外部非 callback 线程必须重试，成功前禁止 restart 或 `dlclose`。
- 从 dispatcher callback 线程调用 `sc132_stop()` 时只会发布 stop request 并立即返回；必须由外部非 callback owner 再调用一次完成 drain/join，避免 self-deadlock。

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

## `libicm42670.so`

non-ROS 头文件：`include/icm42670_driver.h`；ROS2：`include/robobaton_4p_ros2_demo/icm42670_driver.h`；producer：`include/icm42670_x5/icm42670_driver.h`。ABI 为 `2.1`；real SO `libicm42670.so.2.0.0`、SONAME `libicm42670.so.2` 不变。原九个 C 函数保留 `ICM42670_X5_2.0` 节点，新增 `icm42670_set_fsync_callback()` 使用 `ICM42670_X5_2.1`。与 V1 ICM-42688 不兼容；头文件、SO 和 consumer 必须成套迁移。

状态码：

| 状态码 | 含义 |
|---|---|
| `ICM42670_STATUS_OK` | 成功 |
| `ICM42670_STATUS_INVALID_ARGUMENT` | 参数非法 |
| `ICM42670_STATUS_INVALID_STATE` | 生命周期状态非法 |
| `ICM42670_STATUS_IO_ERROR` | I/O 错误 |
| `ICM42670_STATUS_INTERNAL_ERROR` | 内部错误 |

核心结构与约束：

- `icm42670_config_t` 默认 `sample_rate_hz=800`、`fifo_watermark_samples=1`、`read_mode=ICM42670_READ_MODE_SENSOR_TIMESTAMP_FIFO`。
- `sample_rate_hz` 只接受原生 `25/50/100/200/400/800/1600`；旧 `500/1000/2000Hz` 和其他非法值明确拒绝，不会自动重采样；当前只接受 sensor timestamp FIFO 读取模式。
- `sample_timestamp_ns` 为 FIFO TMST→RAW→`CLOCK_REALTIME`，`host_timestamp_ns` 为同域 INT1 边沿；发布时刷新桥接，不冻结 offset，允许系统校时回拨。同域不保证 FSYNC 样本/曝光同步。
- callback 由采集线程串行调用；`sample` 是借用引用。
- `stop/destroy` 会等待采集线程，不得从 callback 中调用。
- `user_data` 必须保持有效直到 `icm42670_stop()` 返回。
- `icm42670_get_runtime_health()` 只在最近一次 start generation 成功 stop 后读取；未成功 stop 时不应把输出结构当作有效快照。
- `icm42670_is_running()` 返回当前 handle 是否处于运行状态，可用于状态查询；它不替代 `icm42670_stop()`/`destroy()` 的生命周期顺序。
- `icm42670_status_message(status)` 把状态码映射为进程静态只读文本；返回指针不得修改或释放。
- `config.reserved[ICM42670_CONFIG_FSYNC_ENABLE_INDEX]=1` 显式开启上升沿 FSYNC，默认 `0`；开启仅支持 `800/1600Hz`。调用 `icm42670_set_fsync_callback(handle, callback, user_data)` 接收独立 `icm42670_fsync_event_t`，不改变 sample/config 结构尺寸。
- FSYNC callback 在同一已接纳样本的 sample callback 之后串行调用，事件为借用引用，异常与 stop/destroy 规则相同。`sample_sequence` 和 `sample_timestamp_ns` 标识该实际样本；`fsync_to_sample_ns` 为硬件 delay，`uncertainty_ns` 包含缺失 TMST 重建误差。RAW 字段只用于关联；对外时间仍为 realtime。
- 成功 stop 后，health `reserved[ICM42670_HEALTH_FSYNC_CAPTURED_INDEX]` 表示捕获硬件标记数，`reserved[ICM42670_HEALTH_FSYNC_DROPPED_INDEX]` 表示未发布关联的标记数（含退出时缺少后继绝对 TMST 的尾包）。`fsync_sequence` 计入丢弃标记，不保证连续；匹配与状态合同见[数据合同](data-contracts.md)。

`icm42670_runtime_health_t` 使用 `ICM42670_RUNTIME_HEALTH_INIT` 初始化。字段含义为：`session_generation`（最近一次 start generation）、`published_samples`（producer 发布样本数）、`gpio_event_gap_count`（GPIO 边沿缺口）、`fifo_overflow_count`（FIFO 溢出）、`mapper_failure_count`（时间映射失败）、`uncertainty_over_200_drop_count`（不确定度超过 200 us 而丢弃的样本数）、`max_consecutive_timing_drop_count`（连续 timing drop 最大值）和 `invalid_packet_drop_count`（无效 FIFO 包丢弃数，包含最后一次样本发布后的尾部丢弃）。使用成功 stop 后的最终快照，不以最后一个 sample 的计数代替。调用返回非 `ICM42670_STATUS_OK` 时，不要读取输出结构作为有效快照。

```c
icm42670_runtime_health_t health = ICM42670_RUNTIME_HEALTH_INIT;
int health_ret = icm42670_get_runtime_health(handle, &health);
if (health_ret != ICM42670_STATUS_OK) {
  /* 只有最近一次 start 已成功且 stop 已完成后，快照才有效。 */
  return health_ret;
}
```

最小骨架：

```c
#include "icm42670_driver.h"

static void on_imu_sample(const icm42670_sample_t *sample, void *user_data) {
  (void)user_data;
  /* sample_timestamp_ns/host_timestamp_ns 已为 CLOCK_REALTIME；消费端原样保留。 */
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

  /* 应用主循环在这里运行。 */

  icm42670_stop(handle);
  icm42670_destroy(handle);
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

配置结构按 `struct_size` 向后兼容：

| 版本 | `struct_size` | 新增能力 |
|---|---:|---|
| V2.0 | `PRRTSP_STREAM_CONFIG_V2_0_SIZE` (`232`) | 基础 stream 配置；`PRRTSP_CODEC_DEFAULT` 为 H.264。 |
| V2.1 | `PRRTSP_STREAM_CONFIG_V2_1_SIZE` (`240`) | 增加显式 `codec`，并允许 `PRRTSP_STREAM_FLAG_EXTERNAL_NV12`。 |
| V2.2 | `PRRTSP_STREAM_CONFIG_V2_2_SIZE` (`256`) | 增加 `encoded_frame_callback` 和 `encoded_frame_user`。 |

调用方必须把 `struct_size` 设置为自己实际提供的版本大小；不得用较小结构声明较新字段，也不得假设旧库识别 V2.2 扩展。

V2.2 encoded callback：

- `prrtsp_encoded_frame_v2` 描述编码后的一个 access unit，`codec` 指明 H.264/H.265，`PRRTSP_ENCODED_FRAME_FLAG_KEY_FRAME` 标识关键帧；
- `data_address` 只借用到 callback 返回，callback 不得保存该地址、长时间阻塞或重入同一 stream；需要异步持有时必须在 callback 内复制；
- `timestamp_ns` 保留对应输入 NV12 帧的原始 ns 值，不使用编码器微秒 PTS 反推，也不自动改变时间域。

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

## 成套部署要求

`libsc132.so`、`libicm42670.so`、`libprrtsp.so`、公开头文件和 demo 程序必须来自同一公开交付包。不要把当前 `.so` 单独替换到未迁移程序；ROS2 install 路径使用 `RoboBaton_4P_ROS2_demo` 自身携带的公开头文件、运行库和 manifest，不要与 non-ROS `/root/demo` 运行包混用。
