"""Aggregate UI ownership; only the batch fragment comes from ComfyUI."""
import html
from pathlib import Path

ASSETS = Path(__file__).with_name('web')
NAVIGATION = '''<a class="nav-item studio-link" href="/translate">▧ 文档翻译</a>
<p class="nav-caption">学习与研究 · 在线链接</p>
<a class="nav-item studio-link" href="https://github.com/marsguo2049/my-llm" target="_blank" rel="noopener">↗ 大模型笔记</a>
<a class="nav-item studio-link" href="https://github.com/marsguo2049/multi-model-workflow-optimization" target="_blank" rel="noopener">↗ 工作流优化研究</a>'''


def render_workbench(settings: dict, comfy_web: Path) -> str:
    source = (ASSETS / 'creative.html').read_text(encoding='utf-8')
    fragment = (comfy_web / 'batch.html').read_text(encoding='utf-8')
    if source.count('<!-- COMFYUI_BATCH -->') != 1:
        raise RuntimeError('Aggregate page must contain exactly one batch slot')
    source = source.replace('<!-- COMFYUI_BATCH -->', fragment)
    source = source.replace('</nav>', NAVIGATION + '</nav>', 1)
    source = source.replace('本地创作工作台', '本地 AI 工作台').replace('<small>ComfyUI Py Workflow</small>', '<small>Offline Studio · 0.2</small>')
    source = source.replace('</head>', '<link rel="stylesheet" href="/studio-assets/studio.css"></head>')
    source = source.replace('value="http://127.0.0.1:1234/v1"', f'value="{html.escape(settings["lm_studio_url"], quote=True)}"')
    source = source.replace('value="http://127.0.0.1:8188"', f'value="{html.escape(settings["comfyui_url"], quote=True)}"')
    if settings['model']:
        model = html.escape(settings['model'], quote=True)
        source = source.replace('<option value="">等待检测</option>', f'<option value="{model}">{model}</option>')
    return source.replace('<script src="/static/app.js"></script>', '<script src="/studio-assets/settings.js"></script>\n<script src="/static/app.js"></script>')
