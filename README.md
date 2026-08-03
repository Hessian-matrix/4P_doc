# 4P_doc

`4P_doc` 是 RoboBaton 4P 的公开在线产品文档工程，使用 Sphinx + Read the Docs 构建。文档面向拿到 4P 硬件、non-ROS demo 或 ROS2 demo 的用户，目标是让用户完成兼容性确认、硬件安全检查、部署升级、运行验证、数据/API 理解和常见问题排查。

## 文档边界

本仓只放面向用户的公开说明：

- 产品版本与兼容性、硬件连接与安全边界；
- non-ROS 运行包部署、升级、回滚和最小验证；
- 四目 RTSP、IMU、UART 的公开参数和数据合同；
- `libsc132.so`、`libicm42688.so`、`libprrtsp.so` 的公开 C ABI/API；
- ROS2 demo 构建、部署、运行、topics 和数据语义；
- 用户侧故障排查、发布授权和支持信息清单。

不得写入公开文档的内容：内部测试资料、原始证据、历史调试记录、未公开板端路径和维护记录不属于本仓公开内容。

## 代码仓库

- [RoboBaton_4p_demo](https://github.com/Hessian-matrix/RoboBaton_4p_demo)：non-ROS 用户交付仓和 `/root/demo` 运行包。
- [RoboBaton_4P_ROS2_demo](https://github.com/Hessian-matrix/RoboBaton_4P_ROS2_demo)：ROS2 四目 NV12/raw+compressed 图像与 IMU 发布 demo，部署目录为 `/root/ros2_demo`。
- [4P_doc](https://github.com/Hessian-matrix/4P_doc)：本公开在线文档仓。

三个公开仓规划使用 `main` 作为 V1 发布线。正式 V1 发布时，由顶层 `4cam` 主仓通过 gitlink 固定明确提交；当前工作区状态、正式 tag 和产品兼容组成仍以发布记录为准。未进入正式组成的 `feature/dev/rc` 候选不代表公开支持能力。

本公开文档只描述用户可见的仓库、commit/tag、运行包manifest和兼容关系，不公开内部clone路径、候选目录或Git操作授权流程。

文档中的 `<non-ros-demo-root>` 和 `<x5-ip>` 是占位符，不表示本仓内的子目录或真实板卡地址。

## 当前在线文档目录

Read the Docs 侧边栏使用真实页面表达层级，不使用 `toctree` 的 `:caption:` 充当不可点击分组。

```text
产品版本与兼容性
硬件连接与安全
快速开始
部署、升级与回滚
数据合同
示例代码与接口
├── 公开 Demo 源码编译
├── non-ROS Demo 使用
├── API 参考
└── ROS2 Demo 使用
故障排查
发布、授权与支持
```

源码文件保持扁平，便于维护：

```text
source/
├── index.rst
├── product-and-compatibility.md
├── hardware-and-safety.md
├── quick-start.md
├── deployment-and-upgrade.md
├── data-contracts.md
├── code-and-interfaces.rst
├── open-source-build.md
├── non-ros-demo.md
├── api-reference.md
├── ros2-demo.md
├── troubleshooting.md
└── release-and-support.md
```

## 维护流程

更新文档时：

- 只写当前公开 demo 仓、公开头文件、默认配置和运行包 manifest 可以证明的事实。
- 未确认的硬件、电气、系统版本、授权、支持渠道和性能门限写“待产品确认”。
- non-ROS 部署命令必须先上传到 `/root/demo.new` 并校验 `manifest.sha256`，再备份旧 `/root/demo` 后切换。
- ROS2 部署命令必须先上传 `/root/ros2_demo.new` archive 并校验 archive checksum，解包后再校验 runtime ABI 子集 `abi_manifest.sha256`，再备份旧 `/root/ros2_demo` 后切换。
- 不建议停止 `cam-service`；切换相机应用时只要求退出旧相机应用。
- 新增页面后同步更新 `source/index.rst`；新增“示例代码与接口”子页面后同步更新 `source/code-and-interfaces.rst`。

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

构建完成后，用浏览器打开：

```bash
build/html/index.html
```

## Read the Docs 配置

Read the Docs 会读取根目录 `.readthedocs.yaml`，使用 `source/conf.py`、`source/requirements.txt` 和 `source/index.rst` 构建公开在线文档。
