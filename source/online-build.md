# 在线文档构建

## 本地预览

在仓库根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r source/requirements.txt
make html
```

构建完成后，用浏览器打开：

```bash
build/html/index.html
```

## Read the Docs 配置

后续在 Read the Docs 导入 GitHub 仓库时，保持默认从仓库根目录读取 `.readthedocs.yaml` 即可。当前配置会使用：

- `source/conf.py` 作为 Sphinx 配置文件。
- `source/requirements.txt` 安装文档构建依赖。
- `source/index.rst` 作为文档目录入口。

新增页面后，需要把页面文件名加入 `source/index.rst` 的 `toctree`，不要带文件扩展名。例如新增 `source/quick-start.md` 后，写入：

```rst
quick-start
```
