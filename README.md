# 4P_doc

`4P_doc` 是 RoboBaton 4P V2 的公开在线产品文档工程，使用 Sphinx + Read the Docs 构建。文档面向拿到 V2 硬件、匹配 non-ROS demo 或 ROS2 demo 的用户，目标是完成接线、开机、路径选择、运行验证和常见问题排查。

在线文档：[中文](https://4p-docs.readthedocs.io/zh-cn/4pv2.main/) · [English](https://4p-doc-en.readthedocs.io/en/4pv2.main/)。

## 文档边界

本仓只放面向用户的公开说明：

- 产品版本与兼容性、硬件连接与安全；
- 首次上电、快速运行、non-ROS/ROS2 使用；
- 系统时间同步；
- 用户侧故障排查、进阶部署/开发/API/数据合同；
- 发布、授权和支持信息清单。

说明和使用类文档统一维护在本仓库；non-ROS 与 ROS2 代码仓的 README 仅保留仓库简介、最小运行方式和文档引用，避免重复维护。

不得写入内部测试资料、原始证据、历史调试记录、用户修改后的板卡 IP、唯一设备数据、非默认账号/凭据、内部路径或交付前检查清单。产品负责人确认的官方出厂默认 IP、账号和密码可在首次上电等公开资料中发布。

## 代码仓库

- [RoboBaton_4p_demo](https://github.com/Hessian-matrix/RoboBaton_4p_demo/tree/V2_main)：non-ROS 用户交付仓和 `/root/demo` 运行包。
- [RoboBaton_4P_ROS2_demo](https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo/tree/V2_main)：ROS2 四目 NV12/raw+compressed 图像、CameraInfo、曝光观测、IMU、温度与 timing JSON topic demo，部署目录为 `/root/ros2_demo`。
- [4P_doc](https://github.com/Hessian-matrix/4P_doc/tree/V2_main)：本公开在线文档仓。

三个公开仓库统一以 `V2_main` 作为 V2 主分支，文档中的仓库浏览、源码链接与 clone 示例显式选择该分支；不依赖远端默认分支。分支须推送后远端链接才可访问，本地创建和提交不改变 Read the Docs 的构建配置。

公开 shell 示例使用合法变量和示例值，并在相邻注释中说明需要按现场环境修改。官方出厂默认地址为 `192.168.1.12`，默认账号为 `root`。

## 文档版本政策

文档版本采用“主版本.次版本.修订号”，末位修订号用于同一版本系列内的小 bug 修复、构建脚本调整或文档内容修正，不自动改变各软件版本。`4P_doc/VERSION` 是文档修订号的唯一来源，中英文 `conf.py` 直接读取它；修改时同步两棵树的最新版本化 changelog 条目和发布说明，不联动修改主仓、non-ROS、ROS2 的 `VERSION` 或 `package.xml`。软件版本与 SO 的 SONAME/ABI 独立识别。

完整公开政策见 [中文发布说明](source/cn/release-and-support.md#文档版本政策) 和 [English release policy](source/en/release-and-support.md#documentation-version-policy)。主仓门禁命令为 `python3 -B tests/version_reporting_contract_test.py`；中英文仍须分别通过严格 HTML 构建和 linkcheck。

当前文档修订为 `2.0.85`，软件仍为 `2.0.0`；硬件标识与 SO ABI 独立识别。主板 XT30 电源输入已确认为 `9~27V DC`，中英文正文、参数表与接线图采用相同范围。当前 IMU 为内核 IIO V3／公共 ABI5，最终默认 HO（相机 observer + IMU host），其余启动组合保留比较。non-ROS 默认 Web 开、RTSP 关、IMU `800Hz`；手动曝光为显式配置，不更改默认自动曝光。当前镜像已制作并已有烧录启动设备，预装 non-ROS、ROS2 Humble/应用及系统依赖，仅 `sensor_demo` 默认自启；镜像下载：[4P_V2.0.0_image.tar.gz](https://www.hessian-matrix.com/wp-content/uploads/2026/automaticupdates/4P_V2.0.0_image.tar.gz)，发布包 SHA-256 与适用硬件须在烧录前向产品支持核对，镜像完成不等于整机验收。当前固件支持按住 SW1 上电或复位，再通过 USB3 Fastboot 使用 XBurn 烧录，无需调试串口；操作及硬件匹配、备份要求见[中文系统烧录](source/cn/ops/system-flashing.md)和[English System Flashing](source/en/ops/system-flashing.md)。ROS2 版本查询也需包内环境脚本。USB 页提供可照做的命令和交互输入，解释 Host/Device、NCM/RNDIS/ECM/UVC/ADB/MSD、状态字段与安全参数；配套新镜像候选出厂默认 CDC NCM，安装更新保留已有开机选择。较旧固件可能仍默认 RNDIS 或不支持 NCM；电脑须支持 CDC NCM，Windows 兼容性尚未认证，RNDIS/ECM 仍可手动选择而不自动回退。这不表示已发布的旧镜像下载内容发生变化。USB 页也明确 UVC 公开源码、独立构建/离线安装和相机交接：关闭电脑预览或拔线不释放相机，须停止 UVC 或切回网卡后再启动原应用；既有 RNDIS 检查不能认证 NCM 或其他模式。NTP 页说明自动授时和无 association／`stratum=16` 的未同步状态。既有整合包完成 non-ROS HO／四路30fps网页预览与姿态／bag与MP4回读／正常停止短窗验证，不自动推广到新烧录设备、ROS2 板端、其余三组合、物理精度、双机/GPU、压力、`8h` 或重启，也不构成新软件发布。见[中文能力与验证边界](source/cn/release-and-support.md#capability-verification-boundary)和[English capability and verification boundaries](source/en/release-and-support.md#capability-verification-boundary)。

配套新镜像还在无既有 `/userdata/wifi` 状态时默认初始化 `RoboBaton-4P` WPA2 热点；使用随设备提供的密码连接后，打开 `http://192.168.5.1/` 预览与录包。已有 AP/STA 和停用选择保留；Wi-Fi 与 USB DHCP 独立，`12` 小时租期可自动续租，不是连接时限。出厂与手动配置默认值、恢复方法和验收边界见[中文 Wi-Fi 配置](source/cn/getting-started/wifi-configuration.md)和[English Wi-Fi Configuration](source/en/getting-started/wifi-configuration.md)。

当前 Web 源码使用 Rust/str0m 和静态 musl mallocng，保留四路预览、IMU SSE、录制控制及 `sensor_demo` 子进程生命周期；源码编译、整包更新、内存诊断和 ICE 端点限制已同步两种语言。此源码修订不自动更新已发布镜像或已有设备，也不承诺 RSS 归零、长期无泄漏或无重连。

## 当前在线文档目录

顶层用户导航：

```text
产品介绍
产品版本与兼容性
硬件连接与安全
首次上电与开机使用
板载 Wi-Fi 配置
TF 卡（microSD）使用
时间同步（NTP / PPS / PTP）
快速开始
non-ROS Demo 使用
ROS2 Demo 使用
故障排查
进阶使用与开发
修复和升级
版本更新记录
发布、授权与支持
```

“进阶使用与开发”子页面：

```text
部署、升级与回滚
公开 Demo 源码编译
数据合同
API 参考
```

“修复和升级”子页面：

```text
V2 修复与升级边界
系统烧录
```

源码按语言分树，中英页面一一对应、口径一致；两棵树共享的图片放在 `source/image/`：

```text
source/
├── requirements.txt   # 中英共享依赖
├── image/             # 中英共享图片
├── cn/                # 中文文档（Sphinx srcdir）
│   ├── index.rst
│   ├── conf.py
│   ├── getting-started/   # 产品介绍、版本兼容、硬件安全、首次上电、Wi-Fi、TF 卡
│   ├── quick-start.md
│   ├── usage/             # non-ROS / 保存数据 / ROS2 使用
│   ├── time-sync/         # 时间同步（NTP / PPS / PTP）
│   ├── troubleshooting.md
│   ├── ops/               # 修复、升级、烧录
│   ├── development/       # 部署、源码编译、数据合同、API 参考
│   ├── changelog.md
│   └── release-and-support.md
└── en/                # 英文文档（Sphinx srcdir，与 cn/ 目录结构一一对应）
```

正文引用共享图片时，树根页用 `../image/`，子目录页用 `../../image/`。

## 本地预览与验证

在仓库根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r source/requirements.txt
make html                                  # 中文（默认 source/cn）
make html SOURCEDIR=source/en BUILDDIR=build/en   # 英文
```

严格构建和链接检查（中英两棵树都要跑）：

```bash
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
python3 -m sphinx -M html source/cn /tmp/4p-doc-html -W --keep-going
python3 -m sphinx -M linkcheck source/cn /tmp/4p-doc-linkcheck -W --keep-going
python3 -m sphinx -M html source/en /tmp/4p-doc-en-html -W --keep-going
python3 -m sphinx -M linkcheck source/en /tmp/4p-doc-en-linkcheck -W --keep-going
git diff --check
```

固定 locale 可避免 SSH 转发了目标机未安装的语言环境时出现 `locale.Error: unsupported locale setting`。

## Read the Docs 配置

Read the Docs 只认文件名 `.readthedocs.yaml`，不读取自定义文件名。中文项目读取根目录 `.readthedocs.yaml`（`source/cn/conf.py`），英文项目读取 `source/en/.readthedocs.yaml`（`source/en/conf.py`），作为独立的 Read the Docs 项目并与中文项目以翻译关系关联；英文项目需在项目设置里把「Path for .readthedocs.yaml」设为 `source/en`。两个项目共享本仓库、共享 `source/requirements.txt`。
