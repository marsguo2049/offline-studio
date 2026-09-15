(() => {
  const fields = ['lm-url', 'comfy-url', 'lm-model'];
  const panel = document.querySelector('.service-settings');
  const message = document.createElement('p');
  message.className = 'hint';
  message.setAttribute('role', 'status');
  message.textContent = '服务设置与文档翻译共用；修改后自动保存到本机。';
  panel.after(message);
  let queue = Promise.resolve();
  const save = document.createElement('button');
  save.className = 'secondary';
  save.textContent = '保存服务设置';
  message.after(save);
  const persist = () => {
    const settings = {
      lm_studio_url: document.getElementById('lm-url').value,
      comfyui_url: document.getElementById('comfy-url').value,
      model: document.getElementById('lm-model').value,
    };
    queue = queue.catch(() => {}).then(async () => {
      const response = await fetch('/api/studio/settings', {method:'POST',
        headers:{'Content-Type':'application/json'}, body:JSON.stringify(settings)});
      const result = await response.json();
      if (!response.ok) throw Error(result.message || '设置保存失败');
      message.textContent = '已保存，文档翻译与创作工具共用这些服务设置。';
    }).catch(error => {message.textContent = error.message;});
  };
  save.onclick = persist;
  for (const id of fields) document.getElementById(id).addEventListener('change', persist);
})();
