# Offline Studio

**统一使用本地 AI 的工作台，支持文档翻译、图像处理、漫画与视频创作。**

[English](README.md) · [架构说明](docs/design.md)

工作台提供统一入口、共用服务设置和翻译任务管理。ComfyUI 执行、文档翻译、
优化研究和学习笔记继续在各自仓库维护，通过适配器连接。

## 本机启动

首次使用：安装 Python 3.10+，联网运行 `install.bat`。安装器按
`integrations.lock.json` 下载固定版本的工具，依赖安装到独立 `.venv`。
LM Studio、ComfyUI、模型权重和自定义节点需要提前准备。

之后双击 **`start-studio.bat`**，默认打开 **http://127.0.0.1:7870/#batch**。
日常启动不会自动下载模型，也不调用云端推理。教程与研究是明确标注的在线链接。

当前这台机器已有同级工具目录，可以使用：

```powershell
python scripts/install.py --local
```

本地接入模式直接使用现有版本，不强制它们与锁定版本一致。
安装时可用 `--minimal` 跳过可选 PDF 与 OCR 依赖。
PyAV 是后端启动必需的媒体依赖，最小安装也会保留。

## 第一版功能

- **批量工具**：复用现有 Qwen Image Edit 批量图片处理。
- **故事漫画 / 故事视频**：复用分镜审阅、生成与导出流程。
- **文档翻译**：上传 DOCX、检查文档、提取/审校术语、翻译/继续、导出中文与中英对照 Word。
- **服务设置**：LM Studio、ComfyUI 地址和选定模型保存到本机，供工具共用。
- **学习与研究**：访问大模型笔记、工作流优化研究仓库。

先在“服务设置”选择本地模型并保存，再到“文档翻译”创建任务。
翻译支持断点继续；每个文档拥有独立的术语表与进度。
当前翻译引擎的提示词针对艺术史等学术文献的英译中，其他领域请先检查术语。
第一版网页未覆盖旧工具的逐词选择性重译命令。

一次运行一个翻译操作。第一版尚未统一调度各工具的 GPU 任务，显存有限时请先
结束图像/视频生成，再开始翻译。关闭网页不会停止后台；退出服务会中断翻译，
重新启动后可继续已有进度。

## 仓库分工

| 仓库 | 定位 |
| --- | --- |
| offline-studio | 统一工作台、服务配置、应用适配 |
| [comfyui-py-workflow](https://github.com/marsguo2049/comfyui-py-workflow) | ComfyUI 工作流与执行能力 |
| [local-llm-word-translator](https://github.com/marsguo2049/local-llm-word-translator) | 文档翻译、术语与 Word 导出 |
| [multi-model-workflow-optimization](https://github.com/marsguo2049/multi-model-workflow-optimization) | 模型选择、调度与优化研究 |
| [my-llm](https://github.com/marsguo2049/my-llm) | 部署教程与使用笔记 |

第一版通过适配器沿用现有界面，没有复制一整套 ComfyUI 源码。
[原有在线预览](https://marsguo2049.github.io/comfyui-py-workflow/#batch)继续展示创作页面，
不执行真实任务，也尚未展示新翻译页。

## 数据与验证

新任务保存在忽略的 `data/`：创作记录在 `data/creative/`，翻译记录在
`data/translation/`，共用设置在 `data/settings.json`。
旧工具的历史记录保持原位，第一版不自动导入。模型、虚拟环境、私人文档、译文、
日志与下载的工具代码均不提交到 GitHub。

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m offline_studio.server --no-browser
```

测试使用合成文档，不需要调用模型。可通过 `--port`、`--data-dir` 和
`--translator` 指定端口、数据目录和翻译脚本。

原始代码采用 [PolyForm Noncommercial 1.0.0](LICENSE)。
第三方工具和模型保持各自许可，详见 [第三方说明](THIRD_PARTY_NOTICES.md)。
