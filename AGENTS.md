# Public Documentation Release Subrepository Rules

本子仓受当前工作区主仓统一 Agent 规则约束。Agent 从本目录启动时也必须先读取主仓规则。


## 目录结构

在线文档按语言分树，中文与英文都是可直接编辑的一等文档；两棵树共享的资产（如图片）放在 `source/` 顶层：

```text
source/
├── requirements.txt   # 中英共享的 Sphinx/MyST 依赖
├── image/             # 中英共享的图片资产
├── cn/                # 中文文档（Sphinx srcdir，conf.py language = "zh_CN"）
└── en/                # 英文文档（Sphinx srcdir，conf.py language = "en"）
```

每棵树内按功能分级存放，中英目录结构一一对应（`getting-started/`、`usage/`、`time-sync/`、`ops/`、`development/`），树根只保留 `index.rst`、`conf.py`、`_static/`、`_templates/` 和四个独立入口页（`quick-start.md`、`troubleshooting.md`、`changelog.md`、`release-and-support.md`）：

```text
cn/ 与 en/ 各自：
├── index.rst
├── conf.py
├── getting-started/   # Product_Introduction、版本兼容、硬件安全、首次上电、Wi-Fi
├── quick-start.md     # 快速开始（toctree 指向 usage/）
├── usage/             # non-ros-demo、save-data-guide、ros2-demo
├── time-sync/         # system-time-sync、ntp-sync、pps-sync、ptp-sync
├── troubleshooting.md
├── ops/               # fix-and-upgrade、tf-card-field-fix、isp-image-quality-fix、system-flashing
├── development/       # code-and-interfaces、deployment-and-upgrade、open-source-build、data-contracts、api-reference
├── changelog.md
└── release-and-support.md
```

两棵树必须同步维护：技术口径一致、页面一一对应；正文引用共享图片时，树根页写 `../image/<file>`，子目录页写 `../../image/<file>`，只有语言专属资产才放进各自树内。


## 强制规则

1. 本仓只保留面向用户的公开产品文档、Sphinx配置、公开示例和在线文档构建依赖。
2. 内部测试、fake、probe、runner、matrix、原始证据、长测日志、Agent计划和失败记录全部归主仓；本仓不得新增这些内部资产。
3. 技术事实以公开头文件、公开demo、默认配置和正式runtime manifest为依据；未确认的硬件、电气、兼容性、授权和支持信息必须明确标记待确认。
4. 不公开用户修改后的板卡 IP、唯一设备数据、非默认账号/凭据、内部临时路径、内部日志包或交付前检查清单；产品负责人确认的官方出厂默认 IP、账号和密码可作为公开开机资料发布。
5. cn/（中文）与 en/（英文）公开内容变更时必须保持技术信息一致、页面一一对应；新增页面必须同时更新两棵树的 Sphinx 目录和链接检查。
6. 修改后至少对 cn/ 与 en/ 两棵树运行 Sphinx 严格 HTML 构建和 linkcheck，并运行 `git diff --check`；在主仓运行 `python3 tests/repository_policy_test.py`。
7. 默认不stage、不commit、不push、不tag；禁止无边界reset、clean或restore。
8. 已发布的版本化下载 URL 及其工件内容不可变；更新工件必须使用新的版本化文件名和新 URL，禁止原地替换已发布 URL 对应的文件。
9. 在线文档当前跟随用户反馈和文档/代码更新持续发布；在产品负责人变更策略前，不定义或承诺固定的 Read the Docs 文档版本或 `stable` 别名。
