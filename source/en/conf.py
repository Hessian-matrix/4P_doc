# Configuration file for the Sphinx documentation builder.

project = "4P_doc"
author = "4P_doc contributors"
copyright = "2026, 4P_doc contributors"
# release must stay in sync with the VERSION file shared across the four repositories.
release = "1.3.1"

# MyST is enabled so chapters can be authored directly in Markdown.
extensions = [
    "myst_parser",
    "sphinx_rtd_theme",
]

# Both rst and md are kept: the index pages follow the Sphinx toctree style.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
language = "en"

html_theme = "sphinx_rtd_theme"
html_show_sourcelink = False
html_static_path = ["_static"]

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
]
