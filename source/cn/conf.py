# Configuration file for the Sphinx documentation builder.

import os
from pathlib import Path

project = "4P_doc"
author = "4P_doc contributors"
copyright = "2026, 4P_doc contributors"
# 文档修订号独立于软件版本；中英文构建共用本仓 VERSION。
release = (Path(__file__).resolve().parents[2] / "VERSION").read_text(encoding="utf-8").strip()

# 2026-07-31：使用 MyST 支持 Markdown，原因是后续章节更容易直接用 .md 编写。
extensions = [
    "myst_parser",
]

# 2026-07-31：同时保留 rst 和 md，原因是目录页沿用 Baton_doc 的 Sphinx/toctree 风格。
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
language = "zh_CN"

html_theme = "sphinx_book_theme"
html_title = "RoboBaton 4P 产品文档"
html_show_sourcelink = False
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_js_files = ["language-switcher.js"]

# 中英文项目共用同一套页面路径；切换按钮据此生成当前页面的对应语言链接。
html_context = {
    "rtd_version": os.environ.get("READTHEDOCS_VERSION", "latest"),
    "docs_base_url_zh": "https://4p-docs.readthedocs.io",
    "docs_base_url_en": "https://4p-doc-en.readthedocs.io",
}

html_theme_options = {
    "repository_url": "",
    "use_repository_button": False,
    "use_issues_button": False,
    "use_edit_page_button": False,
    "home_page_in_toc": True,
    "show_navbar_depth": 2,
    "navbar_persistent": ["language-switcher", "search-button-field"],
}

# 2026-07-31：为 Markdown 标题生成锚点，原因是在线文档内部跳转和外链引用更稳定。
myst_heading_anchors = 3

# GitHub 仓库可能返回 403；大型系统镜像和烧录工具下载另行核验。
linkcheck_ignore = [
    r"https://github\.com/Hessian-matrix/RoboBaton_4p_demo/?$",
    r"https://github\.com/Hessian-matrix/RoboBaton_4P_ROS2_demo/?$",
    r"https://github\.com/Hessian-matrix/4P_doc/?$",
    r"https://www\.hessian-matrix\.com/wp-content/uploads/2026/automaticupdates/product-20260918-v1\.3\.0\.tar\.gz$",
    r"https://www\.hessian-matrix\.com/wp-content/uploads/2026/automaticupdates/xburn-gui_1\.2\.1_x64-setup\.exe$",
    # 中英切换按钮与 hreflang 指向对侧语言部署域名；URL 由 RTD 部署状态决定，不参与内容链接校验。
    r"https://4p-docs\.readthedocs\.io/.*",
    r"https://4p-doc-en\.readthedocs\.io/.*",
]
