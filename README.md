# 4P_doc

`4P_doc` 是 RoboBaton 4P 的公开在线产品文档工程，使用 Sphinx + Read the Docs 构建。文档面向拿到 4P 硬件、non-ROS demo 或 ROS2 demo 的用户，目标是完成接线、开机、路径选择、运行验证和常见问题排查。

## 文档边界

本仓只放面向用户的公开说明：

- 产品版本与兼容性、硬件连接与安全；
- 首次上电、快速运行、non-ROS/ROS2 使用；
- 系统时间同步；
- 用户侧故障排查、进阶部署/开发/API/数据合同；
- 发布、授权和支持信息清单。

不得写入内部测试资料、原始证据、历史调试记录、用户修改后的板卡 IP、唯一设备数据、非默认账号/凭据、内部路径或交付前检查清单。产品负责人确认的官方出厂默认 IP、账号和密码可在首次上电等公开资料中发布。

## 代码仓库

- [RoboBaton_4p_demo](https://github.com/Hessian-matrix/RoboBaton_4p_demo)：non-ROS 用户交付仓和 `/root/demo` 运行包。
- [RoboBaton_4P_ROS2_demo](https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo)：ROS2 四目 NV12/raw+compressed 图像、CameraInfo、IMU 和温度 topic demo，部署目录为 `/root/ros2_demo`。
- [4P_doc](https://github.com/Hessian-matrix/4P_doc)：本公开在线文档仓。

公开 shell 示例使用合法变量和示例值，并在相邻注释中说明需要按现场环境修改。官方出厂默认地址为 `192.168.1.12`，默认账号为 `root`。

## 当前在线文档目录

顶层用户导航：

```text
产品介绍
产品版本与兼容性
硬件连接与安全
首次上电与开机使用
板载 Wi-Fi 配置
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
X5 TF 卡无法识别的内核修复（需产品支持授权）
ISP 图像质量修复
系统烧录
```

源码按语言分树，中英页面一一对应、口径一致；两棵树共享的图片放在 `source/image/`：

```text
source/
├── requirements.txt   # 中英共享依赖
├── image/             # 中英共享图片
├── ch/                # 中文文档（Sphinx srcdir）
│   ├── index.rst
│   ├── conf.py
│   ├── getting-started/   # 产品介绍、版本兼容、硬件安全、首次上电、Wi-Fi
│   ├── quick-start.md
│   ├── usage/             # non-ROS / 保存数据 / ROS2 使用
│   ├── time-sync/         # 时间同步（NTP / PPS / PTP）
│   ├── troubleshooting.md
│   ├── ops/               # 修复、升级、烧录
│   ├── development/       # 部署、源码编译、数据合同、API 参考
│   ├── changelog.md
│   └── release-and-support.md
└── en/                # 英文文档（Sphinx srcdir，与 ch/ 目录结构一一对应）
```

正文引用共享图片时，树根页用 `../image/`，子目录页用 `../../image/`。

## 本地预览与验证

在仓库根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r source/requirements.txt
make html                                  # 中文（默认 source/ch）
make html SOURCEDIR=source/en BUILDDIR=build/en   # 英文
```

严格构建和链接检查（中英两棵树都要跑）：

```bash
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
python3 -m sphinx -M html source/ch /tmp/4p-doc-html -W --keep-going
python3 -m sphinx -M linkcheck source/ch /tmp/4p-doc-linkcheck -W --keep-going
python3 -m sphinx -M html source/en /tmp/4p-doc-en-html -W --keep-going
python3 -m sphinx -M linkcheck source/en /tmp/4p-doc-en-linkcheck -W --keep-going
git diff --check
```

固定 locale 可避免 SSH 转发了目标机未安装的语言环境时出现 `locale.Error: unsupported locale setting`。

## Read the Docs 配置

Read the Docs 会读取根目录 `.readthedocs.yaml`，使用 `source/ch/conf.py`、`source/requirements.txt` 和 `source/ch/index.rst` 构建中文在线文档。英文文档使用 `.readthedocs-en.yaml`（`source/en/conf.py`），作为独立的 Read the Docs 项目并与中文项目以翻译关系关联；两个项目共享本仓库、共享 `source/requirements.txt`。
