# Configuration file for the Sphinx documentation builder.

project = "4P_doc"
author = "4P_doc contributors"
copyright = "2026, 4P_doc contributors"
# 正式产品/文档版本尚待确认，避免把浮动的 latest 显示成兼容性依据。
release = "draft"

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

# 2026-08-01：保留用户可点击的公开仓链接，原因是 GitHub 自动检查可能返回 403/断连，不应阻塞内部链接检查。
linkcheck_ignore = [
    r"https://github\.com/Hessian-matrix/RoboBaton_4p_demo/?$",
    r"https://github\.com/Hessian-matrix/RoboBaton_4P_ROS2_demo/?$",
]
