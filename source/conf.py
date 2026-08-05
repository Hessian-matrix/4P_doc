# Configuration file for the Sphinx documentation builder.

project = "4P_doc"
author = "4P_doc contributors"
copyright = "2026, 4P_doc contributors"
# 2026-08-04 修改原因：仓库根 VERSION 已固定为 1.0.0，Sphinx release 与公开 v1.0.0 发布版本保持一致。
release = "1.0.0"

# 2026-07-31：使用 MyST 支持 Markdown，原因是后续章节更容易直接用 .md 编写。
extensions = [
    "myst_parser",
    "sphinx_rtd_theme",
]

# 2026-07-31：同时保留 rst 和 md，原因是目录页沿用 Baton_doc 的 Sphinx/toctree 风格。
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
language = "zh_CN"

html_theme = "sphinx_rtd_theme"
html_show_sourcelink = False
html_static_path = ["_static"]

# 2026-07-31：为 Markdown 标题生成锚点，原因是在线文档内部跳转和外链引用更稳定。
myst_heading_anchors = 3

# 2026-08-04 修改原因：保留用户可点击的公开仓和大体积工具链链接；GitHub 可能返回 403，工具链直链不应在 linkcheck 中下载或阻塞发布门禁。
linkcheck_ignore = [
    r"https://github\.com/Hessian-matrix/RoboBaton_4p_demo/?$",
    r"https://github\.com/Hessian-matrix/RoboBaton_4P_ROS2_demo/?$",
    r"https://github\.com/Hessian-matrix/4P_doc/?$",
    r"https://www\.hessian-matrix\.com/wp-content/uploads/2026/automaticupdates/x5_4cam_cross_toolchain_20260708\.tar\.gz$",
]
