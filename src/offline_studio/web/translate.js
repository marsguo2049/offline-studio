(() => {
  const el = id => document.getElementById(id);
  const labels = {ready:'待开始',running:'运行中',completed:'操作完成',failed:'需要处理',interrupted:'已中断'};
  let selected = new URLSearchParams(location.search).get('id');
  let pending = false;
  let lastError = '';
  async function api(path, options) {
    const response = await fetch(path, options);
    const body = await response.json();
    if (!response.ok) throw Error(body.message || '请求失败');
    return body;
  }
  function render(job) {
    el('job-title').textContent = job.name;
    el('job-state').textContent = labels[job.status] || job.status;
    el('message').textContent = lastError || job.message;
    el('log').textContent = job.log || '暂无日志。';
    el('downloads').replaceChildren();
    for (const name of job.artifacts) {
      const link = document.createElement('a');
      link.href = `/translation-download?id=${encodeURIComponent(job.id)}&name=${encodeURIComponent(name)}`;
      link.download = name;
      link.textContent = name.endsWith('_zh.docx') ? '下载中文译文' : '下载中英对照';
      el('downloads').append(link);
    }
  }
  async function refresh() {
    const result = await api('/api/translation/jobs');
    el('jobs').replaceChildren();
    if (!result.available) el('upload-message').textContent = '尚未安装翻译工具，请运行安装脚本。';
    if (!result.jobs.length) el('jobs').textContent = '尚无任务，选择一份文档开始。';
    for (const job of result.jobs) {
      const button = document.createElement('button');
      button.className = 'secondary';
      button.textContent = `${job.name} · ${labels[job.status] || job.status}`;
      button.onclick = () => {selected = job.id; lastError = ''; history.replaceState(null,'',`?id=${selected}`); refresh().catch(showError);};
      el('jobs').append(button);
    }
    const job = result.jobs.find(item => item.id === selected);
    if (job) render(job);
    for (const button of document.querySelectorAll('[data-action]')) {
      button.disabled = pending || !job || !result.available || result.jobs.some(item => item.status === 'running');
    }
  }
  function showError(error) {lastError = error.message; el('message').textContent = lastError;}
  el('upload').onclick = async () => {
    const file = el('document').files[0];
    if (!file) {el('upload-message').textContent = '请先选择 DOCX 文件。'; return;}
    el('upload').disabled = true;
    try {
      const job = await api(`/api/translation/upload?filename=${encodeURIComponent(file.name)}`, {method:'POST',body:file});
      selected = job.id;
      lastError = '';
      history.replaceState(null,'',`?id=${selected}`);
      el('upload-message').textContent = '文档已保存到本机。';
      await refresh();
    } catch(error) {el('upload-message').textContent = error.message;}
    finally {el('upload').disabled = false;}
  };
  for (const button of document.querySelectorAll('[data-action]')) button.onclick = async () => {
    lastError = '';
    pending = true;
    document.querySelectorAll('[data-action]').forEach(node => {node.disabled = true;});
    try {
      await api('/api/translation/start', {method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({id:selected,action:button.dataset.action})});
    } catch(error) {showError(error);}
    finally {pending = false;}
    // Preserve any actionable error until the next user action or poll.
    setTimeout(() => refresh().catch(showError), 3000);
  };
  el('refresh').onclick = () => refresh().catch(showError);
  api('/api/studio/settings').then(settings => {
    el('model').textContent = settings.model ? `本地模型：${settings.model}` : '尚未选择模型，请到服务设置中选择并保存。';
  }).catch(showError);
  refresh().catch(showError);
  setInterval(() => {if (!pending) refresh().catch(showError);}, 3000);
})();
