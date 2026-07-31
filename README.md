# 4P_doc

这是 `4P_doc` 的在线文档工程，当前使用 Sphinx + Read the Docs 构建。

## 本地预览

```bash
pip install -r source/requirements.txt
make html
```

构建完成后打开 `build/html/index.html`。

## 在线发布

在 Read the Docs 导入该 GitHub 仓库后，平台会读取根目录的 `.readthedocs.yaml`，并使用 `source/conf.py` 构建文档。
