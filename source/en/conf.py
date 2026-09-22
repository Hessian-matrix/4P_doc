# Configuration file for the Sphinx documentation builder.

import os

project = "4P_doc"
author = "4P_doc contributors"
copyright = "2026, 4P_doc contributors"
# release must stay in sync with the VERSION file shared across the four repositories.
release = "1.3.1"

# MyST is enabled so chapters can be authored directly in Markdown.
extensions = [
    "myst_parser",
]

# Both rst and md are kept: the index pages follow the Sphinx toctree style.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
language = "en"

html_theme = "sphinx_book_theme"
html_title = "RoboBaton 4P Product Documentation"
html_show_sourcelink = False
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_js_files = ["language-switcher.js"]

# The Chinese and English projects share the same page paths; the switcher builds the matching
# cross-language link from the current page.
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

# Generate stable anchors for Markdown headings so in-page and cross-page links stay valid.
myst_heading_anchors = 3

# Keep user-facing public repositories and large toolchain links clickable; GitHub may return
# 403 and the toolchain direct links must not be downloaded or block the release linkcheck.
linkcheck_ignore = [
    r"https://github\.com/Hessian-matrix/RoboBaton_4p_demo/?$",
    r"https://github\.com/Hessian-matrix/RoboBaton_4P_ROS2_demo/?$",
    r"https://github\.com/Hessian-matrix/4P_doc/?$",
    r"https://www\.hessian-matrix\.com/wp-content/uploads/2026/automaticupdates/x5_4cam_cross_toolchain_20260708\.tar\.gz$",
    r"https://www\.hessian-matrix\.com/wp-content/uploads/2026/automaticupdates/product-20260918-v1\.3\.0\.tar\.gz$",
    r"https://www\.hessian-matrix\.com/wp-content/uploads/2026/automaticupdates/xburn-gui_1\.2\.1_x64-setup\.exe$",
    # The switcher and hreflang links point at the opposite language's deployment domain; those
    # URLs depend on Read the Docs deployment state, not on content correctness.
    r"https://4p-docs\.readthedocs\.io/.*",
    r"https://4p-doc-en\.readthedocs\.io/.*",
]
