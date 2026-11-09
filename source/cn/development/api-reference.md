# API 参考

本页覆盖当前公开头文件的C ABI/API。版本getter无需硬件初始化；运行健康getter在采集终态可查询，包括已取得的失败stop诊断。示例仅展示集成生命周期，应用负责业务消费与运行等待。

头文件合同与目标环境验证是不同层次：当前能力、已知吞吐/压力/长录限制见{ref}`能力与验证边界 <capability-verification-boundary>`，不因 API 可调用或包校验通过而视为整机验收。

## 发布版本查询

产品发布版本遵循SemVer，并与SO的SONAME/ABI版本相互独立。版本字符串 getter 无需初始化硬件，返回进程静态只读字符串，调用方不得修改或释放：

```c
const char *camera_version = sc132_get_version();
const char *imu_version = icm42670_get_version();
const char *rtsp_version = prrtsp_get_version();
```

交付可执行文件也支持`--version`。non-ROS的`cam_demo`/`sensor_demo`以及ROS2的`robobaton_sensors_node`会同时打印其实际加载的自研SO版本，从而发现不同版本程序和SO混装。ROS2 compressed image_transport插件额外导出`robobaton_nv12_compressed_image_transport_get_version()`。

## `libsc132.so`

头文件：`include/sc132camera.h`。ABI：`SC132_ABI_VERSION_MAJOR=3`，`SC132_ABI_VERSION_MINOR=0`；real SO 为 `libsc132.so.3.0.0`，SONAME 为 `libsc132.so.3`，符号节点为 `LIBSC132_3.0`。consumer 必须遵循当前头文件的时间域、触发模式及 frame-info 字段语义；使用其他 ABI 的 consumer 必须成套重建并重新链接，禁止 `.so.2 -> .so.3` 兼容链接。

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

公开相机 `timestamp_ns` 与 `group_timestamp_ns` 使用 `CLOCK_REALTIME` Unix 纳秒，跟随系统校时并允许回拨。启动 `SC132_TIMESTAMP_PATH=observer`（默认）选择原有有界 SIF 映射，`official` 选择同帧 RAW IRQ `timestamps − (tv − trig_tv) × 1000`，不启动 SIF observer，物理误差上界未知。consumer 按启动 selector 设置环境；非法值启动失败，切换须停止/重启。observer 需要 X5 `/dev/mem` 只读权限，保留 `500µs` 窗口 admission。official 的 timing validity 为 `0`、uncertainty 为 `UINT32_MAX`，两路径均不回退。默认时间戳是触发估计；显式 {ref}`曝光中点测试开关 <test-exposure-midpoint>` 增加半曝光，不是已认证物理中点。详见[时间数据合同](data-contracts.md)。

ABI 3.0 在 `sc132_frame_info_t` 尾部增加 `exposure`（`sc132_exposure_info_t`）。`sc132_frame_get_info()` 接受当前 `sizeof(info)` 或不含 `exposure` 的旧前缀尺寸，只写调用方声明的尺寸并原样返回 `struct_size`；新 consumer 必须与新头文件/SO 成套使用。

(camera-output-structures)=
### 公开图像输出结构与字段

相机采集 C 接口输出 **NV12 图像**，不是 sensor RAW10，也不是 H.264/H.265 码流。callback 接收帧组 `sc132_frame_set_t`；每项携带不透明句柄 `sc132_frame_t *`，通过 `sc132_frame_get_info()` 取得像素地址和单帧元数据。以下声明对应当前公开头文件，集成时应包含交付包中的头文件，而不是复制这些定义。

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

#### 单帧身份、地址和布局

| `sc132_frame_info_t` 字段 | 含义与单位 |
|---|---|
| `struct_size` | 调用前设置为 `sizeof(sc132_frame_info_t)`；控制库可写范围，返回值保持调用方声明的尺寸。旧前缀兼容范围见上文。 |
| `camera_id` | 软件相机 ID，`0..3` 对应 CAM1..CAM4，不是 callback 数组下标。 |
| `sequence` | 每路软件采集序号；当前实现启动时清零，在 warmup/配组之前推进。首个交付值不保证为零，可能有缺口，各路不必相同。 |
| `frame_id` | 配组后的归一化帧号，以各路原始帧号基准配组；同一输出组内一致。不是保存文件的帧索引。 |
| `raw_frame_id` | SDK 输出图像元数据中的原始帧号；此处 raw 不表示 RAW10 像素。 |
| `timestamp_ns` | 默认是该路 LPWM 触发沿映射后的 realtime Unix 时间，单位 ns，允许校时回拨；测试模式增加该帧半曝光时长，不是到帧、callback 或 IRQ 时间。 |
| `y_data` | Y 亮度平面的只读 CPU 虚拟地址。 |
| `uv_data` | UV 色度平面的只读 CPU 虚拟地址；NV12 为交错 U/V，不是 NV21 的 V/U。 |
| `y_phys` / `uv_phys` | 对应平面的物理/DMA 地址，供兼容的硬件接口使用，不能当 CPU 指针解引用。 |
| `y_size` / `uv_size` | 对应平面 buffer 的字节数，可能含对齐 padding，不等于有效像素字节数。 |
| `width` / `height` | 交付图像的有效宽/高，单位像素，使用当前帧实际输出方向和尺寸。 |
| `stride` | 相邻行起点间的字节距离；当前 NV12 的 Y/UV 平面共用该行跨度，可能大于有效宽度。 |
| `vstride` | Y 平面垂直布局行数，单位行，可能因对齐大于有效高度，不是图像有效行数。 |
| `exposure` | 以相邻前一原始硬件帧 getter 估计并随目标帧冻结的曝光；不是同帧最新 getter，字段及限制见下表。 |

`sequence`、`raw_frame_id` 和 `frame_id` 分别描述软件计数、SDK 原始身份和归一化配组身份，不能混用，也不能直接作为 MP4 的 `frame_index`。

NV12 是 8 位 YUV420 半平面格式：有效 Y 区域为 `height` 行、每行 `width` 字节；有效 UV 区域为 `height / 2` 行、每行 `width` 字节，每对 U/V 对应一个 2×2 的 Y 像素块。有效行起点按以下方式计算，每行只读取有效宽度，并先检查指针和 `y_size`/`uv_size` 边界：

```c
const uint8_t *y_row =
    (const uint8_t *)info.y_data + (size_t)row * info.stride;
const uint8_t *uv_row =
    (const uint8_t *)info.uv_data + (size_t)row * info.stride;
```

Y、UV 必须分别使用各自地址；不能假设两平面连续、UV 从 `y_data + width * height` 开始，或整帧始终是紧凑的 `width * height * 3 / 2` 字节。

#### 曝光观测字段

| `sc132_exposure_info_t` 字段 | 含义与限制 |
|---|---|
| `status` | `0`（`SC132_EXPOSURE_UNAVAILABLE`）不可用，其余曝光字段全零；`1`（`SC132_EXPOSURE_ESTIMATED`）为固定单硬件帧关联估计，没有已测物理误差上界或实际生效曝光保证。 |
| `source_frame_id` | 相邻前驱采集时 getter 返回的原始 SDK 帧标识；不改写为目标图像，不用于硬件帧相邻匹配，也不证明原子参数绑定。 |
| `duration_ns` | SDK 报告的积分秒数转换为 ns，不是主机等待或采集耗时。 |
| `source_timestamp` | 更早 getter 的原始 opaque SDK 源时间，不改写为目标图像，不定义为 RAW/realtime，不能用于 Unix 时间对齐。 |
| `observed_raw_ns` | 更早 getter 完成时的原始 `CLOCK_MONOTONIC_RAW`，单位 ns；不改写为目标图像时间，也不是积分开始或结束时刻。 |

每个采集 worker 独占每次会话零初始化的状态，采集原始硬件帧 N 时取得的 getter 只估计 N+1。只按已采集原始硬件帧 ID 的 uint32 相邻关系（允许回绕）匹配，不按归一化帧号、组号或 SDK `source_frame_id`；frame-set warmup 中即预热，无额外图像缓冲或交付延迟。首个无前驱采集帧、硬件缺口或无效前驱查询均为不可用且全零，不跨缺口延用。N 查询失败使 N+1 不可用，有效前驱仍可估计 N。保留同一帧后再次读取不被后续查询覆盖。consumer 原样转发曝光，不得再移一帧。

默认触发时间戳、公开布局、SONAME 和软件版本不变。显式中点模式使用已匹配估计，不可用时仍停止；触发到积分起点尚未校准，“触发时间＋半曝光时长”不是实际生效曝光或真实中点证明，也不要对已调整的 `timestamp_ns` 重复加半曝光。详见[曝光观测合同](data-contracts.md#逐帧曝光观测)。

固定 N→N+1 只是估计关联规则；真实 AE 的有效滞后可能不同，不构成通用 AE 生效延迟或逐帧实际应用曝光保证。

#### 帧组和条目字段

| `sc132_frame_set_t` 字段 | 含义 |
|---|---|
| `struct_size` | 库输出的帧组结构大小。 |
| `camera_count` | 正常帧组中的有效条目数量，四目为 `4`，单摄诊断为 `1`。 |
| `group_id` | 当前采集会话的输出组序号，当前实现从零开始；不是硬件触发计数或单帧帧号。 |
| `group_timestamp_ns` | 本组各路交付 realtime 时间的最小值，单位 ns；默认是触发时间，测试模式是估算曝光中点，不能代替所有逐路时间。 |
| `max_skew_ns` | 本组实际触发捕获时间跨度，即最大值减最小值，单位 ns；不是配置阈值或曝光同步误差。 |
| `items` | 最多四项，仅前 `camera_count` 项有效，按启用相机紧凑排列。 |
| `reserved` | 部分槽位已定义为组时间审计元数据，见下表。 |

`sc132_frame_set_item_t.frame` 是用于查询元数据和管理引用的不透明帧句柄；其余 `camera_id`、`frame_id`、`sequence`、`timestamp_ns`、`width`、`height` 是对应单帧同名字段的快照。只开 cam2 时有效条目是 `items[0]`，其中 `camera_id == 2`，不是 `items[2]`。

输出的实际 skew 与配置的放行上限不同：`sc132_frame_set_config_t.max_skew_ns` 是配组阈值，默认 `10000000 ns（10ms）`，不代表曝光或相机/IMU 对齐精度。

| `reserved[]` 槽位 | 公开宏 | 含义 |
|---|---|---|
| 0 | `SC132_GROUP_RAW_LO` | 本组最早所选触发 RAW 估计的低 32 位：有界 observer 映射或 official IRQ 派生估计。 |
| 1 | `SC132_GROUP_RAW_HI` | 同一 RAW 时间的高 32 位。 |
| 2 | `SC132_GROUP_UNCERTAINTY_NS` | observer 为含 skew 的组映射不确定度，单位 ns；official 为 `UINT32_MAX`（未知），均不宣称物理精度。 |
| 3 | `SC132_GROUP_GENERATION` | 采集 generation，区分会话，禁止跨 generation 混配。 |
| 4 | `SC132_GROUP_TIMING_VALID` | observer 用 `SC132_GROUP_TIMING_MAGIC` 标记有界映射元数据；official 为 `0`，不得当作有界有效。 |
| 5..7 | — | 保留，无公开业务含义。 |

有界使用须先检查 `SC132_GROUP_TIMING_MAGIC`；official 值仅是诊断估计，不确定度未知。所选 RAW 估计按下式恢复，它不是 Unix 时间，绝不能把 official 的零 validity 提升为时间证书：

```c
uint64_t group_raw_ns =
    ((uint64_t)set->reserved[SC132_GROUP_RAW_HI] << 32) |
    (uint64_t)set->reserved[SC132_GROUP_RAW_LO];
```

#### 读取与像素有效期

读取方式见下方最小骨架：先初始化 `struct_size`，只有 `sc132_frame_get_info()` 返回 `SC132_STATUS_OK` 才使用输出。复制 `sc132_frame_info_t` 只复制元数据/指针，不复制像素，也不延长帧寿命。

callback 内同步读取无需额外 retain，也不能释放库持有的借用引用；异步使用必须在 callback 内先 `sc132_frame_retain()`，最终使用完成后 `sc132_frame_release()`。像素地址始终只读，不能自行释放；不要将它们传给 `free()`。完整停止顺序见下方生命周期和所有权说明。

#### 与 ROS2 和编码输出的区别

| 公开出口 | 结构与字段映射 |
|---|---|
| SC132 C 接口 | 上述帧组/单帧结构，保留独立 Y/UV 地址、plane size、stride/vstride 和曝光观测。 |
| ROS2 `image_raw` | `sensor_msgs/msg/Image`：`header.stamp` 为逐路交付时间（默认触发时间，测试模式为估算曝光中点），`width/height` 为有效尺寸，`encoding="nv12"`，`is_bigendian=false`，`step=stride`；`data` 是完整 Y buffer 后接完整 UV buffer 的副本。 |
| ROS2 `image_raw` 布局限制 | 消息没有独立的 vstride/plane-size 字段；不能按紧凑布局推导 UV 起点或截断数据。详见[ROS2 数据合同](data-contracts.md#ros2-topics)。 |
| ROS2 曝光 | 独立的 `/robobaton/camN/exposure` JSON，不嵌入标准 Image。 |
| ROS2 `compressed` | `sensor_msgs/msg/CompressedImage`，当前为 JPEG，不是 NV12 内存布局。 |
| PRRTSP 编码 callback | `prrtsp_encoded_frame_v2` 描述 H.264/H.265 编码访问单元；数据仅借用到 callback 返回，见本页 PRRTSP API。 |

### 配置、生命周期与集成示例

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

non-ROS 头文件：`include/icm42670_driver.h`；ROS2：`include/robobaton_4p_ros2_demo/icm42670_driver.h`。ABI `6.0`，实体 `libicm42670.so.6.0.0`，SONAME `libicm42670.so.6`，所有九个 C 导出仅使用 `ICM42670_X5_6.0`。相对 ABI5 保留原160字节 sample 前缀，但结构尺寸和 config 语义不兼容；同步头文件、库及所有重建 consumer，删除旧 major 库，不建立跨 major 链接或旧符号别名。要求匹配的内核 IIO V4 capture 模块；V2/V3 即使 host 模式也不兼容。软件 VERSION 独立。

| 导出 | 合同 |
|---|---|
| `icm42670_create` | 验证 config，创建 opaque handle |
| `icm42670_set_callback` | 启动前注册串行 sample callback 与 user_data；采集／STOP 排空至 join 完成前（包括 callback 内调用）返回 `INVALID_STATE` |
| `icm42670_start` | 必须已注册非空 callback，否则返回 `INVALID_STATE`；枚举唯一 IIO 实例，核验 scan/控制节点并启动采集 |
| `icm42670_stop` | 保持 callback 接纳，排空 STOP 集合并 join；重复调用保留终态 |
| `icm42670_is_running` | 查询 running，不替代 stop/join |
| `icm42670_get_runtime_health` | 查询终态，包括已取得的失败 stop 诊断；检查返回值与 generation |
| `icm42670_destroy` | 停止并释放 handle；不得从 callback 调用 |
| `icm42670_get_version` | 无硬件初始化的静态只读产品版本，不得修改或释放 |
| `icm42670_status_message` | 状态码对应的静态只读字符串，不得修改或释放 |

状态为 `OK=0`、`INVALID_ARGUMENT=-1`、`INVALID_STATE=-2`、`IO_ERROR=-3`、`INTERNAL_ERROR=-4`（宏前缀 `ICM42670_STATUS_`）。

`icm42670_config_t` 全为 u32：`struct_size, sample_rate_hz, fifo_watermark_samples, buffer_capacity, sample_drop_policy, timestamp_mode, fsync_diagnostics, reserved[1]`。结构为32bytes。`fsync_diagnostics`只接受0/1，默认1，0关闭独立诊断；使用 `ICM42670_CONFIG_INIT`：默认 `800Hz`、watermark `1`、buffer `4096`、`ALLOW_COUNTED`、`ICM42670_TIMESTAMP_MODE_HOST=0`；`ICM42670_TIMESTAMP_MODE_TMST=1` 选择 TMST。ODR 仅 `25/50/100/200/400/800/1600`；watermark 必须1，buffer 为256..8192的2次幂，reserved 为0。非法 mode 拒绝；创建 handle 时设置，切换需 stop/重建 handle/restart。`ALLOW_COUNTED`/`STRICT` 仅控制无效六轴 payload，不控制时间精度。两模式共用同一 IIO 读取/owner，无用户态 SPI/spidev、模块装载、DT 修改或回退。

`icm42670_sample_t` 包含 u32 `struct_size/session_generation`，u64 `sample_monotonic_ns/sample_sequence`，u32 `burst_flags/fifo_tmst`，u64 `evidence_id/burst_complete_raw_ns/observation_monotonic_ns/estimated_period_ns`，u32 `timestamp_source/packet_flags`，double `temperature_c/accel_mps2[3]/gyro_rps[3]`，16-byte `raw`（int16 温度、accel[3]、gyro[3]、reserved），原160bytes前缀尾部为 u64 `sample_raw_ns` 与 u32 `timestamp_uncertainty_ns/timestamp_mode`；再追加 u32 `fifo_header/fsync_flags`、u64 `fsync_sequence/fsync_raw_ns`、u32 `fsync_uncertainty_ns/fsync_delta_us`，共192bytes。`fifo_tmst` 是原始 u16 FIFO 值零扩展到 u32，tagged时为FSYNC delta微秒而非绝对tick。两模式均保留原始 MONOTONIC 主机估计和独立 RAW burst 完成值，禁止跨时钟直接作差。host 的 `sample_raw_ns=0`、uncertainty 为 `UINT32_MAX`。TMST 依据内核拥有的 FIFO/UI 跳变证据，由用户态解绕并作有界仿射 RAW 映射，`200µs` 为计算 admission 而非物理精度。输出适配层将所选原生 sample 时钟桥接到 realtime，分开保留 MONOTONIC/RAW 桥基点。字段、flags、schema v3 及全部 health 字段见[IMU 数据合同](data-contracts.md#imu)；独立 FSYNC 诊断随 sample 输出，无独立 callback 或触发—样本关联。

callback 的 sample 借用至返回，不抛异常、不调用 stop/destroy。异步消费须自行复制并保持 user_data 到 stop 返回；停止期间仍可能接收样本，应并行排空队列，不能先关接纳。所有覆盖 sample 交付后才 ACK 对应 record。`transport_complete` 只认证完整消费/ACK 的停止集合，不覆盖 fence 外物理尾部、不抵消 fatal。健康必须检查 stop 返回值、health 返回值、generation、错误与计数，不能只看最后一个样本。

callback 与 user_data 在一次采集生命周期内固定，避免重注册与正在交付的样本竞争。只有启动前或 stop/join 完成后才能替换或清空。内核已取得的最终 STOP／QUERY 诊断先独立保留；本地 scan／ACK 对账失败仍返回错误且 `transport_complete=0`，不会丢弃该诊断或放行未交付 record。

采集及 STOP 尾部 callback 内调用 start 或 get_runtime_health 均直接返回 `INVALID_STATE`，不等待生命周期锁；最终 health 仍须在外部 stop/join 后查询。

最小生命周期示例（业务消费和等待由调用者实现）：

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

当前库集合为 `libicm42670.so.6.0.0` / `ICM42670_X5_6.0`、`libsc132.so.3.0.0` / `LIBSC132_3.0`、`libprrtsp.so.2.0.1` / `LIBPRRTSP_2.0`。移除 ICM42670 旧 `.2`/`.3`/`.4`/`.5` 和 SC132 旧 `.2` 库，成套重建全部 consumer，不保留跨 major 别名；ROS2 不携带 PRRTSP。应用包不安装所需的匹配 IIO V4 内核模块。
