# Public Documentation Release Subrepository Rules

本子仓受主仓`/root/x5/4cam/AGENTS.md`约束。Agent从本目录启动时也必须先读取主仓规则。

## 强制规则

1. 本仓只保留面向用户的公开产品文档、Sphinx配置、公开示例和在线文档构建依赖。
2. 内部测试、fake、probe、runner、matrix、原始证据、长测日志、Agent计划和失败记录全部归主仓；本仓不得新增这些内部资产。
3. 技术事实以公开头文件、公开demo、默认配置和正式runtime manifest为依据；未确认的硬件、电气、兼容性、授权和支持信息必须明确标记待确认。
4. 不公开真实板卡IP、账号、内部临时路径、凭据、内部日志包或交付前检查清单。
5. 中英文公开内容变更时保持技术信息一致；新增页面必须同步Sphinx目录和链接检查。
6. 修改后至少运行Sphinx严格HTML构建、linkcheck和`git diff --check`，并在主仓运行`python3 tests/repository_policy_test.py`。
7. 默认不stage、不commit、不push、不tag；禁止无边界reset、clean或restore。
