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

文档中的 `<x5-ip>`、`<non-ros-demo-root>` 和 `<ros2-demo-root>` 是占位符，不表示用户现场板卡地址或仓内目录。公开文档可以写明官方出厂默认地址 `192.168.1.12` 和默认账号 `root`；用户修改后的 IP、唯一设备数据和非默认凭据不得发布。

## 当前在线文档目录

顶层用户导航：

```text
产品介绍
产品版本与兼容性
硬件连接与安全
首次上电与开机使用
板载 Wi-Fi 配置
系统时间同步
快速开始
non-ROS Demo 使用
ROS2 Demo 使用
故障排查
进阶使用与开发
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

源码文件保持扁平，便于维护：

```text
source/
├── index.rst
├── Product_Introduction.md
├── product-and-compatibility.md
├── hardware-and-safety.md
├── first-boot.md
├── wifi-configuration.md
├── system-time-sync.md
├── quick-start.md
├── non-ros-demo.md
├── ros2-demo.md
├── troubleshooting.md
├── code-and-interfaces.rst
├── deployment-and-upgrade.md
├── open-source-build.md
├── data-contracts.md
├── api-reference.md
├── changelog.md
└── release-and-support.md
```

## 维护流程

更新文档时：

- 只写当前公开 demo 仓、公开头文件、默认配置、`VERSION` 和运行包 manifest 可以证明的事实。
- 未确认的硬件、电气、系统版本、授权、支持渠道和性能门限集中标记，不在每个表格字段重复占位。
- 新增顶层页面后同步 `source/index.rst`；新增进阶页面后同步 `source/code-and-interfaces.rst`。
- 不建议停止 `cam-service`；切换相机应用时只要求退出旧相机应用。
- 中英文公开内容变更时保持技术信息一致。

首次上电图片维护计划只在这里记录，公开页面不放编辑任务表：

- 板卡接口总览；
- 首次上电流程；
- Camera 映射；
- UART 接线；
- 网络拓扑。

## 本地预览与验证

在仓库根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r source/requirements.txt
make html
```

严格构建和链接检查：

```bash
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
python3 -m sphinx -M html source /tmp/4p-doc-html -W --keep-going
python3 -m sphinx -M linkcheck source /tmp/4p-doc-linkcheck -W --keep-going
git diff --check
```

固定 locale 可避免 SSH 转发了目标机未安装的语言环境时出现 `locale.Error: unsupported locale setting`。

## Read the Docs 配置

Read the Docs 会读取根目录 `.readthedocs.yaml`，使用 `source/conf.py`、`source/requirements.txt` 和 `source/index.rst` 构建公开在线文档。

维护策略：在线文档当前会根据用户反馈和文档/代码更新继续滚动发布；此阶段不定义固定的 Read the Docs 文档版本，也不配置或承诺 `stable` alias。除非产品负责人变更该策略，不要对外承诺稳定快照。
