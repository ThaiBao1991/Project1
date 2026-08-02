const vscode = require('vscode');
const fs = require('fs/promises');
const path = require('path');
const os = require('os');

const DATA_FILE = 'codex_quota_data.dat';

function dataDirectory() {
  const configured = vscode.workspace.getConfiguration('codexQuotaTracker').get('dataDirectory', '').trim();
  return configured || path.join(os.homedir(), '.quota-tracker');
}

function codexHome() {
  return process.env.CODEX_HOME || path.join(os.homedir(), '.codex');
}

async function walkJsonl(directory) {
  const result = [];
  try {
    for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
      const fullPath = path.join(directory, entry.name);
      if (entry.isDirectory()) result.push(...await walkJsonl(fullPath));
      else if (entry.isFile() && entry.name.endsWith('.jsonl')) result.push(fullPath);
    }
  } catch (_) { /* Codex has not created sessions on this machine yet. */ }
  return result;
}

async function latestRateLimits() {
  const files = await walkJsonl(path.join(codexHome(), 'sessions'));
  const ordered = await Promise.all(files.map(async file => ({ file, stat: await fs.stat(file) })));
  ordered.sort((a, b) => b.stat.mtimeMs - a.stat.mtimeMs);
  for (const { file } of ordered) {
    const lines = (await fs.readFile(file, 'utf8')).split(/\r?\n/);
    for (let index = lines.length - 1; index >= 0; index -= 1) {
      try {
        const limits = JSON.parse(lines[index]).payload?.rate_limits;
        if (limits) return { limits, file };
      } catch (_) { /* Skip incomplete or unrelated JSONL events. */ }
    }
  }
  return null;
}

function windowSnapshot(window) {
  if (!window) return null;
  const used = window.used_percent;
  return {
    usedPercent: used,
    remainingPercent: typeof used === 'number' ? Math.max(0, 100 - used) : null,
    windowMinutes: window.window_minutes ?? null,
    resetsAt: window.resets_at ?? null
  };
}

async function writeSnapshot() {
  const result = await latestRateLimits();
  if (!result) throw new Error('Chưa có quota Codex local. Hãy gửi ít nhất một yêu cầu trong Codex trên máy này.');
  const { limits, file } = result;
  const plan = limits.plan_type || 'unknown';
  const configuredLabel = vscode.workspace.getConfiguration('codexQuotaTracker').get('accountLabel', '').trim();
  const label = configuredLabel || `Codex (${plan})`;
  const snapshot = {
    schemaVersion: 1,
    provider: 'codex',
    sourceMachine: os.hostname(),
    sourceFile: path.basename(file),
    updatedAt: new Date().toISOString(),
    accounts: {
      [label]: {
        label,
        planType: plan,
        primary: windowSnapshot(limits.primary),
        secondary: windowSnapshot(limits.secondary),
        rateLimitReached: limits.rate_limit_reached_type ?? null,
        updatedAt: new Date().toISOString()
      }
    }
  };
  await fs.mkdir(dataDirectory(), { recursive: true });
  await fs.writeFile(path.join(dataDirectory(), DATA_FILE), Buffer.from(JSON.stringify(snapshot), 'utf8').toString('base64'), 'utf8');
  return snapshot;
}

function resetText(epochSeconds) {
  if (!epochSeconds) return '—';
  const seconds = Math.max(0, epochSeconds - Date.now() / 1000);
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return hours >= 24 ? `↻ ${Math.floor(hours / 24)}d ${hours % 24}h` : `↻ ${hours}h ${minutes}m`;
}

function renderHtml(snapshot, error = '') {
  const account = snapshot && Object.values(snapshot.accounts)[0];
  const card = account ? `
    <section class="card"><h2>${account.label}</h2><p>Máy: ${snapshot.sourceMachine}</p>
    <div class="metrics"><div><b>${account.primary?.remainingPercent ?? '—'}%</b><span>Còn lại</span></div><div><b>${account.primary?.usedPercent ?? '—'}%</b><span>Đã dùng</span></div><div><b>${resetText(account.primary?.resetsAt)}</b><span>Reset</span></div></div>
    <p>Chu kỳ: ${account.primary?.windowMinutes ?? '—'} phút · Cập nhật: ${new Date(account.updatedAt).toLocaleString()}</p></section>` : '<section class="card"><h2>Chưa có dữ liệu</h2><p>Nhấn Refresh sau khi dùng Codex trên máy này.</p></section>';
  return `<!doctype html><html><head><meta charset="utf-8"><style>body{font-family:var(--vscode-font-family);color:var(--vscode-foreground);padding:12px}.toolbar{display:flex;gap:8px;margin-bottom:12px}button{padding:7px 10px;border:0;border-radius:4px;background:var(--vscode-button-background);color:var(--vscode-button-foreground);cursor:pointer}.card{background:var(--vscode-editorWidget-background);border:1px solid var(--vscode-widget-border);border-radius:8px;padding:14px}.card h2{margin-top:0}.metrics{display:flex;gap:18px}.metrics div{display:flex;flex-direction:column}.metrics b{font-size:22px;color:#10a37f}.metrics span,p{opacity:.8}.error{color:var(--vscode-errorForeground)}</style></head><body><div class="toolbar"><button onclick="vscode.postMessage({command:'refresh'})">↻ Refresh</button><button onclick="vscode.postMessage({command:'openDataFolder'})">Mở data folder</button></div>${error ? `<p class="error">${error}</p>` : ''}${card}<script>const vscode=acquireVsCodeApi();</script></body></html>`;
}

function activate(context) {
  let view;
  let lastSnapshot;
  const status = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 50);
  status.command = 'codexQuotaTracker.open';
  status.show();
  context.subscriptions.push(status);

  const refresh = async (showError = false) => {
    try {
      lastSnapshot = await writeSnapshot();
      const account = Object.values(lastSnapshot.accounts)[0];
      status.text = `$(pulse) Codex ${account.primary?.remainingPercent ?? '—'}% · ${resetText(account.primary?.resetsAt)}`;
      status.tooltip = 'Codex Quota Tracker — click to open dashboard';
      if (view) view.webview.html = renderHtml(lastSnapshot);
    } catch (error) {
      status.text = '$(warning) Codex quota: chưa có data';
      if (view) view.webview.html = renderHtml(null, error.message);
      if (showError) vscode.window.showWarningMessage(error.message);
    }
  };

  context.subscriptions.push(vscode.window.registerWebviewViewProvider('codexQuotaTracker.dashboard', {
    resolveWebviewView(webviewView) {
      view = webviewView;
      webviewView.webview.options = { enableScripts: true };
      webviewView.webview.onDidReceiveMessage(async message => {
        if (message.command === 'refresh') await refresh(true);
        if (message.command === 'openDataFolder') await vscode.commands.executeCommand('codexQuotaTracker.openDataFolder');
      });
      refresh(false);
    }
  }));
  context.subscriptions.push(vscode.commands.registerCommand('codexQuotaTracker.open', async () => {
    await vscode.commands.executeCommand('workbench.view.extension.codex-quota-tracker');
    await vscode.commands.executeCommand('codexQuotaTracker.dashboard.focus');
  }));
  context.subscriptions.push(vscode.commands.registerCommand('codexQuotaTracker.refresh', () => refresh(true)));
  context.subscriptions.push(vscode.commands.registerCommand('codexQuotaTracker.openDataFolder', () => vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(dataDirectory()))));
  refresh(false);
  const seconds = Math.max(30, Number(vscode.workspace.getConfiguration('codexQuotaTracker').get('refreshIntervalSeconds', 60)) || 60);
  const timer = setInterval(() => refresh(false), seconds * 1000);
  context.subscriptions.push({ dispose: () => clearInterval(timer) });
}

function deactivate() {}
module.exports = { activate, deactivate };
