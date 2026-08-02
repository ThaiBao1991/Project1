const vscode = require("vscode");
const childProcess = require("child_process");
const crypto = require("crypto");
const fs = require("fs");
const os = require("os");
const path = require("path");

const REGISTRY_KEY = "codexAccountManager.accounts.v1";
let panel;
let sidebarView;
const loginTimers = new Map();
const NETWORK_KEY = "codexAccountManager.network.v1";
const PROXY_SECRET_KEY = "codexAccountManager.customProxyUrl.v1";
const PREVIOUS_VSCODE_PROXY_KEY = "codexAccountManager.previousVsCodeProxy.v1";

function networkState(context) {
  return context.globalState.get(NETWORK_KEY, { mode: "system" });
}

async function customProxy(context) {
  return networkState(context).mode === "custom"
    ? await context.secrets.get(PROXY_SECRET_KEY)
    : undefined;
}

async function configureProxy(context) {
  const selected = await vscode.window.showQuickPick(
    [
      {
        label: "$(circle-slash) Không dùng proxy",
        description: "Addon kết nối trực tiếp.",
        mode: "off",
      },
      {
        label: "$(globe) Cloudflare WARP / VPN hệ thống (free)",
        description:
          "Bật WARP trên Windows để VS Code và Codex dùng tunnel hệ thống.",
        mode: "system",
      },
      {
        label: "$(server) Custom HTTP/HTTPS/SOCKS proxy",
        description: "Chỉ áp dụng cho login và quota của addon.",
        mode: "custom",
      },
    ],
    { placeHolder: "Chọn cách Codex Account Manager kết nối mạng" },
  );
  if (!selected) return;
  if (selected.mode === "custom") {
    const value = await vscode.window.showInputBox({
      prompt: "Proxy URL",
      placeHolder: "http://host:port hoặc socks5://host:port",
      password: true,
      ignoreFocusOut: true,
    });
    if (!value) return;
    try {
      const parsed = new URL(value);
      if (!["http:", "https:", "socks:", "socks5:"].includes(parsed.protocol))
        throw new Error("protocol");
    } catch {
      vscode.window.showErrorMessage(
        "Proxy URL không hợp lệ. Dùng http://, https://, socks:// hoặc socks5://.",
      );
      return;
    }
    await context.secrets.store(PROXY_SECRET_KEY, value.trim());
  }
  await context.globalState.update(NETWORK_KEY, { mode: selected.mode });
  vscode.window.showInformationMessage(
    selected.mode === "custom"
      ? "Custom proxy đã bật cho Codex Account Manager."
      : selected.mode === "system"
        ? "Addon sẽ dùng mạng/VPN hệ thống."
        : "Custom proxy đã tắt.",
  );
  updatePanel(context);
}

async function testNetwork(context) {
  const proxy = await customProxy(context);
  const args = ["--silent", "--show-error", "--max-time", "15"];
  if (proxy) args.push("--proxy", proxy);
  args.push("https://api.ipify.org?format=json");
  const result = await new Promise((resolve) => {
    childProcess.execFile(
      "curl.exe",
      args,
      { windowsHide: true },
      (error, stdout) => resolve({ error, stdout }),
    );
  });
  if (result.error) {
    vscode.window.showErrorMessage(
      "Không thể kết nối qua cấu hình mạng hiện tại. Kiểm tra VPN/proxy rồi thử lại.",
    );
    return;
  }
  try {
    const ip = JSON.parse(result.stdout).ip;
    vscode.window.showInformationMessage(
      `Kết nối thành công. IP hiện tại: ${ip} (${proxy ? "custom proxy" : networkState(context).mode === "system" ? "mạng/VPN hệ thống" : "trực tiếp"}).`,
    );
  } catch {
    vscode.window.showErrorMessage(
      "Endpoint kiểm tra mạng trả về dữ liệu không hợp lệ.",
    );
  }
}

async function applyVsCodeProxy(context) {
  const state = networkState(context);
  const http = vscode.workspace.getConfiguration("http");
  const previous = context.globalState.get(PREVIOUS_VSCODE_PROXY_KEY);
  if (state.mode === "custom") {
    const proxy = await customProxy(context);
    if (!proxy) {
      vscode.window.showErrorMessage("Chưa có Custom Proxy để áp dụng.");
      return;
    }
    const parsed = new URL(proxy);
    if (!["http:", "https:"].includes(parsed.protocol)) {
      vscode.window.showWarningMessage(
        "VS Code http.proxy chỉ dùng HTTP/HTTPS. SOCKS vẫn chỉ áp dụng cho Codex Account Manager.",
      );
      return;
    }
    if (previous === undefined) {
      await context.globalState.update(PREVIOUS_VSCODE_PROXY_KEY, {
        proxy: http.inspect("proxy")?.globalValue,
        proxySupport: http.inspect("proxySupport")?.globalValue,
      });
    }
    if (
      (parsed.username || parsed.password) &&
      (await vscode.window.showWarningMessage(
        "VS Code sẽ lưu URL proxy (có thể gồm username/password) trong settings.json dạng đọc được. Tiếp tục?",
        { modal: true },
        "Áp dụng",
      )) !== "Áp dụng"
    )
      return;
    await http.update("proxy", proxy, vscode.ConfigurationTarget.Global);
    await http.update("proxySupport", "on", vscode.ConfigurationTarget.Global);
    vscode.window.showInformationMessage(
      "Đã áp dụng HTTP(S) proxy cho VS Code. Reload Window để extension khác nhận cấu hình mới.",
    );
    return;
  }
  if (previous) {
    await http.update(
      "proxy",
      previous.proxy,
      vscode.ConfigurationTarget.Global,
    );
    await http.update(
      "proxySupport",
      previous.proxySupport,
      vscode.ConfigurationTarget.Global,
    );
    await context.globalState.update(PREVIOUS_VSCODE_PROXY_KEY, undefined);
  } else {
    await http.update("proxy", undefined, vscode.ConfigurationTarget.Global);
  }
  vscode.window.showInformationMessage(
    state.mode === "system"
      ? "Đã xóa http.proxy của VS Code. Bật Cloudflare WARP/VPN Windows để toàn bộ VS Code đi qua VPN."
      : "Đã gỡ http.proxy của VS Code.",
  );
}

function codexExecutable() {
  const explicit = process.env.CODEX_ACCOUNT_MANAGER_BINARY;
  if (explicit && fs.existsSync(explicit)) return explicit;
  if (process.platform === "win32") {
    const extensionRoot = path.join(os.homedir(), ".vscode", "extensions");
    try {
      const installs = fs
        .readdirSync(extensionRoot)
        .filter((name) => name.startsWith("openai.chatgpt-"))
        .map((name) =>
          path.join(extensionRoot, name, "bin", "windows-x86_64", "codex.exe"),
        )
        .filter((candidate) => fs.existsSync(candidate))
        .sort(
          (left, right) =>
            fs.statSync(right).mtimeMs - fs.statSync(left).mtimeMs,
        );
      if (installs.length) return installs[0];
    } catch {
      /* Fall back to a globally installed Codex CLI. */
    }
  }
  return "codex";
}

function profileRoot(context, account) {
  return path.join(context.globalStorageUri.fsPath, "profiles", account.id);
}

function snapshotPath() {
  const configured = vscode.workspace
    .getConfiguration("codexAccountManager")
    .get("snapshotDirectory", "")
    .trim();
  return path.join(
    configured || path.join(os.homedir(), ".quota-tracker"),
    "codex_quota_data.dat",
  );
}

function loadAccounts(context) {
  return context.globalState.get(REGISTRY_KEY, []);
}

async function saveAccounts(context, accounts) {
  await context.globalState.update(REGISTRY_KEY, accounts);
}

function rpcAccountState(codexHome, proxy) {
  return new Promise((resolve) => {
    const proc = childProcess.spawn(
      codexExecutable(),
      ["app-server", "--stdio"],
      {
        env: {
          ...process.env,
          CODEX_HOME: codexHome,
          ...(proxy
            ? { HTTP_PROXY: proxy, HTTPS_PROXY: proxy, ALL_PROXY: proxy }
            : {}),
        },
        windowsHide: true,
        stdio: ["pipe", "pipe", "pipe"],
      },
    );
    let buffer = "";
    let done = false;
    let accountInfo = null;
    const finish = (value) => {
      if (!done) {
        done = true;
        clearTimeout(timeout);
        proc.kill();
        resolve(value);
      }
    };
    const timeout = setTimeout(
      () => finish({ error: "Codex App Server quá thời gian phản hồi." }),
      15000,
    );
    proc.on("error", (error) =>
      finish({ error: `Không chạy được Codex: ${error.message}` }),
    );
    proc.stderr.on("data", () => {});
    proc.stdout.on("data", (chunk) => {
      buffer += chunk.toString("utf8");
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const message = JSON.parse(line);
          if (message.id === 1) {
            proc.stdin.write(
              JSON.stringify({
                jsonrpc: "2.0",
                id: 2,
                method: "account/read",
                params: {},
              }) + "\n",
            );
          } else if (message.id === 2) {
            accountInfo = message.result && message.result.account;
            if (!accountInfo || !accountInfo.email) {
              finish({ error: "Profile này chưa hoàn tất đăng nhập Codex." });
              continue;
            }
            proc.stdin.write(
              JSON.stringify({
                jsonrpc: "2.0",
                id: 3,
                method: "account/rateLimits/read",
                params: {},
              }) + "\n",
            );
          } else if (message.id === 3) {
            const limits = message.result && message.result.rateLimits;
            finish(
              limits
                ? { account: accountInfo, limits }
                : { error: "Codex không trả dữ liệu quota cho profile này." },
            );
          }
        } catch {
          /* Notifications or incomplete lines are ignored. */
        }
      }
    });
    proc.stdin.write(
      JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "initialize",
        params: {
          clientInfo: { name: "codex-account-manager", version: "1.0.0" },
          capabilities: {},
        },
      }) + "\n",
    );
  });
}

function makeWindow(window) {
  if (!window) return null;
  const used = window.usedPercent;
  return {
    usedPercent: used,
    remainingPercent: typeof used === "number" ? Math.max(0, 100 - used) : null,
    windowMinutes: window.windowDurationMins,
    resetsAt: window.resetsAt,
  };
}

function writeSnapshot(accounts) {
  const result = {
    schemaVersion: 1,
    provider: "codex",
    updatedAt: Date.now(),
    sourceMachine: os.hostname(),
    accounts: {},
  };
  for (const account of accounts) {
    if (!account.lastQuota) continue;
    result.accounts[account.label] = {
      label: account.label,
      email: account.email,
      planType: account.lastQuota.planType,
      primary: account.lastQuota.primary,
      secondary: account.lastQuota.secondary,
      rateLimitReached: account.lastQuota.rateLimitReached,
      updatedAt: account.lastChecked,
      resetDetectedAt: account.resetDetectedAt || null,
      lastError: account.lastError || null,
    };
  }
  const target = snapshotPath();
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(
    target,
    Buffer.from(JSON.stringify(result), "utf8").toString("base64"),
    "utf8",
  );
}

async function refreshAccount(context, id) {
  const accounts = loadAccounts(context);
  const account = accounts.find((item) => item.id === id);
  if (!account) return { error: "Không tìm thấy account." };
  const response = await rpcAccountState(
    profileRoot(context, account),
    await customProxy(context),
  );
  account.lastChecked = Date.now();
  if (response.error) {
    account.lastError = response.error;
  } else {
    account.email = response.account.email;
    account.label = response.account.email;
    account.planType =
      response.account.planType || response.limits.planType || "unknown";
    account.loginPending = false;
    const previous = account.lastQuota && account.lastQuota.primary;
    const primary = makeWindow(response.limits.primary);
    account.lastQuota = {
      planType: response.limits.planType || "unknown",
      primary,
      secondary: makeWindow(response.limits.secondary),
      rateLimitReached: response.limits.rateLimitReachedType || null,
    };
    if (
      previous &&
      primary &&
      typeof previous.remainingPercent === "number" &&
      primary.remainingPercent > previous.remainingPercent &&
      primary.resetsAt !== previous.resetsAt
    ) {
      account.resetDetectedAt = Date.now();
    }
    if (
      primary &&
      primary.remainingPercent === 100 &&
      account.resetDetectedAt
    ) {
      account.resetDetectedAt = null;
    }
    account.lastError = null;
  }
  await saveAccounts(context, accounts);
  writeSnapshot(accounts);
  return response;
}

async function refreshAll(context) {
  for (const account of loadAccounts(context))
    await refreshAccount(context, account.id);
  updatePanel(context);
}

function serialize(context) {
  return loadAccounts(context).map((account) => ({
    ...account,
    profileReady: fs.existsSync(
      path.join(profileRoot(context, account), "auth.json"),
    ),
  }));
}

function updatePanel(context) {
  if (panel)
    panel.webview.postMessage({
      type: "accounts",
      accounts: serialize(context),
    });
  if (sidebarView)
    sidebarView.webview.postMessage({
      type: "accounts",
      accounts: serialize(context),
    });
}

async function addAccount(context) {
  const id = crypto.randomBytes(8).toString("hex");
  const account = {
    id,
    email: "",
    label: "Đang chờ đăng nhập…",
    createdAt: Date.now(),
    lastChecked: null,
    lastQuota: null,
    lastError: null,
    loginPending: true,
  };
  const accounts = loadAccounts(context);
  accounts.push(account);
  await saveAccounts(context, accounts);
  fs.mkdirSync(profileRoot(context, account), { recursive: true });
  updatePanel(context);
  await loginAccount(context, id);
}

async function loginAccount(context, id) {
  const accounts = loadAccounts(context);
  const account = accounts.find((item) => item.id === id);
  if (!account) return;
  const root = profileRoot(context, account).replace(/'/g, "''");
  const executable = codexExecutable().replace(/'/g, "''");
  const proxy = await customProxy(context);
  const terminal = vscode.window.createTerminal({
    name: `Codex login: ${account.label}`,
    hideFromUser: false,
  });
  terminal.show(true);
  const proxyCommand = proxy
    ? `$env:HTTP_PROXY='${proxy.replace(/'/g, "''")}'; $env:HTTPS_PROXY=$env:HTTP_PROXY; $env:ALL_PROXY=$env:HTTP_PROXY; `
    : "";
  terminal.sendText(
    `$env:CODEX_HOME='${root}'; ${proxyCommand}& '${executable}' login --device-auth`,
    true,
  );
  account.loginPending = true;
  await saveAccounts(context, accounts);
  updatePanel(context);
  vscode.window.showInformationMessage(
    "Hoàn tất đăng nhập trong Terminal. Addon sẽ tự nhận email và quota.",
  );
  watchLogin(context, id);
}

function watchLogin(context, id, attempt = 0) {
  if (loginTimers.has(id)) clearTimeout(loginTimers.get(id));
  const timer = setTimeout(
    async () => {
      const account = loadAccounts(context).find((item) => item.id === id);
      if (!account || !account.loginPending || attempt >= 150) {
        loginTimers.delete(id);
        return;
      }
      const response = await refreshAccount(context, id);
      if (!response.error) {
        loginTimers.delete(id);
        updatePanel(context);
        vscode.window.showInformationMessage(
          `Đã thêm ${response.account.email} và lấy quota thành công.`,
        );
        return;
      }
      updatePanel(context);
      watchLogin(context, id, attempt + 1);
    },
    attempt ? 3000 : 1500,
  );
  loginTimers.set(id, timer);
}

async function removeAccount(context, id) {
  const accounts = loadAccounts(context);
  const account = accounts.find((item) => item.id === id);
  if (
    !account ||
    !(await vscode.window.showWarningMessage(
      `Xóa ${account.label} khỏi danh sách? Profile đăng nhập cục bộ sẽ được giữ lại.`,
      { modal: true },
      "Xóa",
    ))
  )
    return;
  await saveAccounts(
    context,
    accounts.filter((item) => item.id !== id),
  );
  writeSnapshot(loadAccounts(context));
  updatePanel(context);
}

function html(webview) {
  const nonce = crypto.randomBytes(16).toString("hex");
  return `<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';"><style>
body{font:13px var(--vscode-font-family);color:var(--vscode-foreground);padding:8px}.bar{display:flex;gap:6px;margin-bottom:10px}button{border:0;border-radius:4px;padding:6px 8px;background:var(--vscode-button-background);color:var(--vscode-button-foreground);cursor:pointer}button.alt{background:var(--vscode-button-secondaryBackground)}.row{border-top:1px solid var(--vscode-panel-border);padding:10px 2px}.title{font-weight:600}.meta{color:var(--vscode-descriptionForeground);margin-top:3px}.ok{color:#54c69c}.bad{color:#f48771}.reset{color:#cca700}.actions{display:flex;gap:5px;margin-top:7px}.actions button{font-size:11px;padding:3px 6px}#empty{color:var(--vscode-descriptionForeground);padding:22px 0}</style></head><body><div class="bar"><button onclick="post('add')">+ Thêm account</button><button class="alt" onclick="post('refreshAll')">↻ Refresh tất cả</button></div><div id="list"></div><script nonce="${nonce}">const vscode=acquireVsCodeApi();const post=(action,id)=>vscode.postMessage({action,id});const ago=(t)=>t?new Date(t).toLocaleString():'chưa check';const reset=(s)=>{if(!s)return 'chưa có reset';const d=s*1000-Date.now();if(d<=0)return 'đang chờ refresh';const h=Math.floor(d/3600000),m=Math.floor((d%3600000)/60000);return 'reset sau '+(h? h+'h ':'')+m+'m'};function render(accounts){const root=document.getElementById('list');if(!accounts.length){root.innerHTML='<div id="empty">Chưa có account. Bấm “Thêm account” để mở đăng nhập Codex chính chủ.</div>';return}root.innerHTML=accounts.map(a=>{const q=a.lastQuota&&a.lastQuota.primary;const remaining=q&&q.remainingPercent;const status=a.lastError?'<span class="bad">'+a.lastError+'</span>':q?'<span class="ok">Còn '+remaining+'%</span>':'<span class="reset">Chưa có quota — đăng nhập rồi Refresh</span>';return '<div class="row"><div class="title">'+esc(a.label)+'</div><div class="meta">'+esc(a.email)+' · '+status+'</div><div class="meta">'+(q?reset(q.resetsAt):'')+' · Check: '+ago(a.lastChecked)+(a.resetDetectedAt?' · <span class="ok">đã reset sớm</span>':'')+'</div><div class="actions"><button onclick="post(\'login\',\''+a.id+'\')">Login</button><button class="alt" onclick="post(\'refresh\',\''+a.id+'\')">Refresh</button><button class="alt" onclick="post(\'remove\',\''+a.id+'\')">Xóa khỏi danh sách</button></div></div>'}).join('')}function esc(v){return String(v||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}window.addEventListener('message',e=>{if(e.data.type==='accounts')render(e.data.accounts)});post('ready');</script></body></html>`;
}

function htmlV2(webview) {
  const nonce = crypto.randomBytes(16).toString("hex");
  return `<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';"><style>
body{font:13px var(--vscode-font-family);color:var(--vscode-foreground);padding:8px}.bar,.actions{display:flex;gap:6px}.bar{margin-bottom:10px}button{border:0;border-radius:4px;padding:6px 8px;background:var(--vscode-button-background);color:var(--vscode-button-foreground);cursor:pointer}button.alt{background:var(--vscode-button-secondaryBackground)}.row{border-top:1px solid var(--vscode-panel-border);padding:10px 2px}.title{font-weight:600}.meta{color:var(--vscode-descriptionForeground);margin-top:3px}.ok{color:#54c69c}.bad{color:#f48771}.reset{color:#cca700}.actions{margin-top:7px}.actions button{font-size:11px;padding:3px 6px}#empty{color:var(--vscode-descriptionForeground);padding:22px 0}</style></head><body><div class="bar"><button data-action="add">+ Thêm account</button><button class="alt" data-action="refreshAll">↻ Refresh tất cả</button></div><div id="list"></div><script nonce="${nonce}">
const vscode=acquireVsCodeApi();
const post=(action,id)=>vscode.postMessage({action,id});
const esc=(v)=>String(v||'').replace(/[&<>"']/g,(c)=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ago=(t)=>t?new Date(t).toLocaleString():'chưa check';
const reset=(s)=>{if(!s)return 'chưa có reset';const d=s*1000-Date.now();if(d<=0)return 'đang chờ refresh';const h=Math.floor(d/3600000),m=Math.floor((d%3600000)/60000);return 'reset sau '+(h?h+'h ':'')+m+'m'};
document.addEventListener('click',(event)=>{const button=event.target.closest('button[data-action]');if(button)post(button.dataset.action,button.dataset.id)});
function render(accounts){const root=document.getElementById('list');if(!accounts.length){root.innerHTML='<div id="empty">Chưa có account. Bấm “Thêm account” để mở đăng nhập Codex chính chủ.</div>';return}root.innerHTML=accounts.map((a)=>{const q=a.lastQuota&&a.lastQuota.primary;const remaining=q&&q.remainingPercent;const status=a.lastError?'<span class="bad">'+esc(a.lastError)+'</span>':q?'<span class="ok">Còn '+remaining+'%</span>':'<span class="reset">Chưa có quota — đăng nhập rồi Refresh</span>';const id=esc(a.id);return '<div class="row"><div class="title">'+esc(a.label)+'</div><div class="meta">'+esc(a.email)+' · '+status+'</div><div class="meta">'+(q?reset(q.resetsAt):'')+' · Check: '+ago(a.lastChecked)+(a.resetDetectedAt?' · <span class="ok">đã reset sớm</span>':'')+'</div><div class="actions"><button data-action="login" data-id="'+id+'">Login</button><button class="alt" data-action="refresh" data-id="'+id+'">Refresh</button><button class="alt" data-action="remove" data-id="'+id+'">Xóa khỏi danh sách</button></div></div>'}).join('')}
window.addEventListener('message',(event)=>{if(event.data.type==='accounts')render(event.data.accounts)});post('ready');
</script></body></html>`;
}

function htmlV3(webview) {
  return htmlV2(webview).replace(
    /<div class="bar">[\s\S]*?<\/div><div id="list">/,
    '<div class="bar"><button data-action="add">+ Thêm account</button><button class="alt" data-action="refreshAll">↻ Refresh</button><button class="alt" data-action="configureProxy">Mạng / Proxy</button><button class="alt" data-action="testNetwork">Test IP</button><button class="alt" data-action="applyVsCodeProxy">Áp dụng VS Code</button></div><div id="list">',
  );
}

function bindWebview(webview, context) {
  webview.onDidReceiveMessage(async ({ action, id }) => {
    if (action === "ready") updatePanel(context);
    if (action === "add") await addAccount(context);
    if (action === "login") await loginAccount(context, id);
    if (action === "refresh") {
      await refreshAccount(context, id);
      updatePanel(context);
    }
    if (action === "refreshAll") await refreshAll(context);
    if (action === "configureProxy") await configureProxy(context);
    if (action === "testNetwork") await testNetwork(context);
    if (action === "applyVsCodeProxy") await applyVsCodeProxy(context);
    if (action === "remove") await removeAccount(context, id);
  });
}

function open(context) {
  if (panel) {
    panel.reveal();
    updatePanel(context);
    return;
  }
  panel = vscode.window.createWebviewPanel(
    "codexAccountManager",
    "Codex Accounts",
    vscode.ViewColumn.One,
    { enableScripts: true },
  );
  panel.webview.html = htmlV3(panel.webview);
  panel.onDidDispose(() => {
    panel = undefined;
  });
  bindWebview(panel.webview, context);
}

function activate(context) {
  context.subscriptions.push(
    vscode.commands.registerCommand("codexAccountManager.open", () =>
      open(context),
    ),
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("codexAccountManager.add", () =>
      addAccount(context),
    ),
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("codexAccountManager.refreshAll", () =>
      refreshAll(context),
    ),
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("codexAccountManager.configureProxy", () =>
      configureProxy(context),
    ),
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("codexAccountManager.testNetwork", () =>
      testNetwork(context),
    ),
  );
  context.subscriptions.push(
    vscode.commands.registerCommand(
      "codexAccountManager.applyVsCodeProxy",
      () => applyVsCodeProxy(context),
    ),
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("codexAccountManager.openDataFolder", () =>
      vscode.commands.executeCommand(
        "revealFileInOS",
        vscode.Uri.file(snapshotPath()),
      ),
    ),
  );
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("codexAccountManager.dashboard", {
      resolveWebviewView(view) {
        sidebarView = view;
        view.webview.options = { enableScripts: true };
        view.webview.html = htmlV3(view.webview);
        bindWebview(view.webview, context);
        view.onDidDispose(() => {
          sidebarView = undefined;
        });
      },
    }),
  );
  const minutes = vscode.workspace
    .getConfiguration("codexAccountManager")
    .get("autoRefreshMinutes", 10);
  const timer = setInterval(
    () => refreshAll(context),
    Math.max(1, minutes) * 60000,
  );
  context.subscriptions.push(new vscode.Disposable(() => clearInterval(timer)));
}

function deactivate() {}
module.exports = { activate, deactivate };
