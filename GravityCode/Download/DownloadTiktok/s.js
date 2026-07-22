// ===== mycustomFaveTT Log Helper =====
// Log lưu vào chrome.storage.local["customFaveTT_log"]
// KHÔNG bị xóa khi cập nhật UI — hoàn toàn tách biệt với ui_offline/
const _LOG_KEY = "customFaveTT_log";
const _MAX_LOGS = 200;
function _writeLog(type, msg, videoId, reason) {
  const entry = { type, msg, videoId: videoId || null, reason: reason || null, ts: Date.now() };
  try {
    chrome.storage.local.get(_LOG_KEY, (res) => {
      const logs = res[_LOG_KEY] || [];
      logs.push(entry);
      if (logs.length > _MAX_LOGS) logs.splice(0, logs.length - _MAX_LOGS);
      chrome.storage.local.set({ [_LOG_KEY]: logs });
    });
  } catch (e) { /* storage không khả dụng trong context này, bỏ qua */ }
}
// ===== End Log Helper =====
const t = new BroadcastChannel("mycustomFaveTT"),
  e = new BroadcastChannel("params-guard"),
  n = {
    storeHandleInIDB: !0,
    chromeExtensionOrigin:
      "chrome-extension://gmajiifkcmjkehmngbopoobeplhoegad",
    expectVideoUrlToHaveExpire: !1,
    mockDownload: !1,
    authorItemsCanBeFetched: !0,
    allowSkipRecentlyVisitedAuthors: !0,
    truncateFollowingList: { start: 0, end: 0 },
    writeDbLazilyForMyself: !0,
    t: !0,
    requireCoverUrlToHaveExpire: !1,
  },
  i = {
    i: !1,
    o: !1,
    get l() {
      return this.i || this.o;
    },
  };
function o(t, e) {
  sidebar.postMessage(
    { direction: 2, type: t, payload: e },
    n.chromeExtensionOrigin,
  );
}
const r = o;
function a(t, e) {
  sidebar.postMessage(
    { direction: 6, type: t, payload: e },
    n.chromeExtensionOrigin,
  );
}
const s = {
    u() {
      ((document.documentElement.style.pointerEvents = ""),
        (document.documentElement.style.overflow = ""));
    },
    h() {
      ((document.documentElement.style.overflow = "hidden"),
        (document.documentElement.style.pointerEvents = "none"),
        (document.querySelector(
          "aside#myfaveTT-container",
        ).style.pointerEvents = "auto"));
    },
  },
  c = "Expected a function",
  l = NaN,
  u = "[object Symbol]",
  d = /^\s+|\s+$/g,
  f = /^[-+]0x[0-9a-f]+$/i,
  w = /^0b[01]+$/i,
  h = /^0o[0-7]+$/i,
  v = parseInt,
  m = "object" == typeof global && global && global.Object === Object && global,
  p = "object" == typeof self && self && self.Object === Object && self,
  y = m || p || Function("return this")(),
  b = Object.prototype.toString,
  _ = Math.max,
  g = Math.min,
  k = function () {
    return y.Date.now();
  };
function S(t, e, n) {
  let i,
    o,
    r,
    a,
    s,
    l,
    u = 0,
    d = !1,
    f = !1,
    w = !0;
  if ("function" != typeof t) throw new TypeError(c);
  function h(e) {
    const n = i,
      r = o;
    return ((i = o = void 0), (u = e), (a = t.apply(r, n)), a);
  }
  function v(t) {
    const n = t - l;
    return void 0 === l || n >= e || n < 0 || (f && t - u >= r);
  }
  function m() {
    const t = k();
    if (v(t)) return p(t);
    s = setTimeout(
      m,
      (function (t) {
        const n = e - (t - l);
        return f ? g(n, r - (t - u)) : n;
      })(t),
    );
  }
  function p(t) {
    return ((s = void 0), w && i ? h(t) : ((i = o = void 0), a));
  }
  function y() {
    const t = k(),
      n = v(t);
    if (((i = arguments), (o = this), (l = t), n)) {
      if (void 0 === s)
        return (function (t) {
          return ((u = t), (s = setTimeout(m, e)), d ? h(t) : a);
        })(l);
      if (f) return ((s = setTimeout(m, e)), h(l));
    }
    return (void 0 === s && (s = setTimeout(m, e)), a);
  }
  return (
    (e = I(e) || 0),
    T(n) &&
      ((d = !!n.leading),
      (f = "maxWait" in n),
      (r = f ? _(I(n.maxWait) || 0, e) : r),
      (w = "trailing" in n ? !!n.trailing : w)),
    (y.cancel = function () {
      (void 0 !== s && clearTimeout(s), (u = 0), (i = l = o = s = void 0));
    }),
    (y.flush = function () {
      return void 0 === s ? a : p(k());
    }),
    y
  );
}
function j(t, e, n) {
  let i = !0,
    o = !0;
  if ("function" != typeof t) throw new TypeError(c);
  return (
    T(n) &&
      ((i = "leading" in n ? !!n.leading : i),
      (o = "trailing" in n ? !!n.trailing : o)),
    S(t, e, { leading: i, maxWait: e, trailing: o })
  );
}
function T(t) {
  const e = typeof t;
  return !!t && ("object" == e || "function" == e);
}
function I(t) {
  if ("number" == typeof t) return t;
  if (
    (function (t) {
      return (
        "symbol" == typeof t ||
        ((function (t) {
          return !!t && "object" == typeof t;
        })(t) &&
          b.call(t) == u)
      );
    })(t)
  )
    return l;
  if (T(t)) {
    const e = "function" == typeof t.valueOf ? t.valueOf() : t;
    t = T(e) ? e + "" : e;
  }
  if ("string" != typeof t) return 0 === t ? t : +t;
  t = t.replace(d, "");
  const e = w.test(t);
  return e || h.test(t) ? v(t.slice(2), e ? 2 : 8) : f.test(t) ? l : +t;
}
function D(t, e, n) {
  o(1, { err: t, location: e, silently: n });
}
const O = j(D, 500);
function E(t, e, n) {
  n ? O(t, e, n) : (D(t, e, n), Zt.v(`because of error @ ${e}`));
}
async function C(t) {
  const e = [];
  for await (const n of t.keys()) e.push(n);
  return 0 === e.length;
}
async function $(t, e, n = !0) {
  try {
    const i = e.split("/");
    let o = t;
    for (const t of i) o = await o.getDirectoryHandle(t, { create: n });
    return o;
  } catch (t) {
    throw (E(t, "gfh23"), t);
  }
}
async function x(t, e, n = !0) {
  try {
    const i = e.split("/"),
      o = i.pop();
    let r = t;
    for (const t of i) r = await r.getDirectoryHandle(t, { create: !0 });
    return await r.getFileHandle(o, { create: n });
  } catch (t) {
    if ("NotFoundError" === t.name && !n) return;
    throw (E(t, "gfh29"), t);
  }
}
async function A(t, e) {
  const n = await t.createWritable();
  (await n.write(e), await n.close());
}
async function N(t, e) {
  const n = await x(t, e, !1);
  if (!n) return;
  const i = await n.getFile();
  return await i.text();
}
async function L(t, e, n) {
  if (n) {
    const n = (await t.getFile()).stream(),
      i = await e.createWritable();
    return (await n.pipeTo(i), t.name, void e.name);
  }
  if (!n) {
    const n = await (async function (t) {
      const e = await t.getFile();
      return await e.arrayBuffer();
    })(t);
    (t.name,
      A(e, n).then(() => {
        e.name;
      }));
  }
}
async function F(t, e) {
  await t.removeEntry(e);
}
const B = { m: !1 };
async function M() {
  B.m &&
    ((B.m = !1),
    await (async function () {
      const t = await $(Xt.p, "data/.appdata");
      async function e(e, n) {
        const i = await x(t, e, !1);
        if (!i) return;
        const o = await x(t, n);
        (await L(i, o, "patiently"), await F(t, e));
      }
      await Promise.allSettled([
        e("db.js", "db_likes.js"),
        e("dba.js", "db_authors.js"),
        e("dbf.js", "db_following.js"),
        e("dbv.js", "db_videos.js"),
        e("dbvd.js", "db_texts.js"),
        e("dbb.js", "db_bookmarked.js"),
      ]);
    })());
}
const U = (t, e) => e.some((e) => t instanceof e);
let R, z;
const J = new WeakMap(),
  W = new WeakMap(),
  q = new WeakMap();
let P = {
  get(t, e, n) {
    if (t instanceof IDBTransaction) {
      if ("done" === e) return J.get(t);
      if ("store" === e)
        return n.objectStoreNames[1]
          ? void 0
          : n.objectStore(n.objectStoreNames[0]);
    }
    return Y(t[e]);
  },
  set: (t, e, n) => ((t[e] = n), !0),
  has: (t, e) =>
    (t instanceof IDBTransaction && ("done" === e || "store" === e)) || e in t,
};
function H(t) {
  P = t(P);
}
function V(t) {
  return (
    z ||
    (z = [
      IDBCursor.prototype.advance,
      IDBCursor.prototype.continue,
      IDBCursor.prototype.continuePrimaryKey,
    ])
  ).includes(t)
    ? function (...e) {
        return (t.apply(K(this), e), Y(this.request));
      }
    : function (...e) {
        return Y(t.apply(K(this), e));
      };
}
function G(t) {
  return "function" == typeof t
    ? V(t)
    : (t instanceof IDBTransaction &&
        (function (t) {
          if (J.has(t)) return;
          const e = new Promise((e, n) => {
            const i = () => {
                (t.removeEventListener("complete", o),
                  t.removeEventListener("error", r),
                  t.removeEventListener("abort", r));
              },
              o = () => {
                (e(), i());
              },
              r = () => {
                (n(t.error || new DOMException("AbortError", "AbortError")),
                  i());
              };
            (t.addEventListener("complete", o),
              t.addEventListener("error", r),
              t.addEventListener("abort", r));
          });
          J.set(t, e);
        })(t),
      U(
        t,
        R ||
          (R = [
            IDBDatabase,
            IDBObjectStore,
            IDBIndex,
            IDBCursor,
            IDBTransaction,
          ]),
      )
        ? new Proxy(t, P)
        : t);
}
function Y(t) {
  if (t instanceof IDBRequest)
    return (function (t) {
      const e = new Promise((e, n) => {
        const i = () => {
            (t.removeEventListener("success", o),
              t.removeEventListener("error", r));
          },
          o = () => {
            (e(Y(t.result)), i());
          },
          r = () => {
            (n(t.error), i());
          };
        (t.addEventListener("success", o), t.addEventListener("error", r));
      });
      return (q.set(e, t), e);
    })(t);
  if (W.has(t)) return W.get(t);
  const e = G(t);
  return (e !== t && (W.set(t, e), q.set(e, t)), e);
}
const K = (t) => q.get(t);
const Q = ["get", "getKey", "getAll", "getAllKeys", "count"],
  X = ["put", "add", "delete", "clear"],
  Z = new Map();
function tt(t, e) {
  if (!(t instanceof IDBDatabase) || e in t || "string" != typeof e) return;
  if (Z.get(e)) return Z.get(e);
  const n = e.replace(/FromIndex$/, ""),
    i = e !== n,
    o = X.includes(n);
  if (
    !(n in (i ? IDBIndex : IDBObjectStore).prototype) ||
    (!o && !Q.includes(n))
  )
    return;
  const r = async function (t, ...e) {
    const r = this.transaction(t, o ? "readwrite" : "readonly");
    let a = r.store;
    return (
      i && (a = a.index(e.shift())),
      (await Promise.all([a[n](...e), o && r.done]))[0]
    );
  };
  return (Z.set(e, r), r);
}
H((t) => ({
  ...t,
  get: (e, n, i) => tt(e, n) || t.get(e, n, i),
  has: (e, n) => !!tt(e, n) || t.has(e, n),
}));
const et = ["continue", "continuePrimaryKey", "advance"],
  nt = {},
  it = new WeakMap(),
  ot = new WeakMap(),
  rt = {
    get(t, e) {
      if (!et.includes(e)) return t[e];
      let n = nt[e];
      return (
        n ||
          (n = nt[e] =
            function (...t) {
              it.set(this, ot.get(this)[e](...t));
            }),
        n
      );
    },
  };
async function* at(...t) {
  let e = this;
  if ((e instanceof IDBCursor || (e = await e.openCursor(...t)), !e)) return;
  const n = new Proxy(e, rt);
  for (ot.set(n, e), q.set(n, K(e)); e;)
    (yield n, (e = await (it.get(n) || e.continue())), it.delete(n));
}
function st(t, e) {
  return (
    (e === Symbol.asyncIterator &&
      U(t, [IDBIndex, IDBObjectStore, IDBCursor])) ||
    ("iterate" === e && U(t, [IDBIndex, IDBObjectStore]))
  );
}
H((t) => ({
  ...t,
  get: (e, n, i) => (st(e, n) ? at : t.get(e, n, i)),
  has: (e, n) => st(e, n) || t.has(e, n),
}));
const ct = (function (
    t,
    e,
    { blocked: n, upgrade: i, blocking: o, terminated: r } = {},
  ) {
    const a = indexedDB.open(t, e),
      s = Y(a);
    return (
      i &&
        a.addEventListener("upgradeneeded", (t) => {
          i(Y(a.result), t.oldVersion, t.newVersion, Y(a.transaction), t);
        }),
      n &&
        a.addEventListener("blocked", (t) => n(t.oldVersion, t.newVersion, t)),
      s
        .then((t) => {
          (r && t.addEventListener("close", () => r()),
            o &&
              t.addEventListener("versionchange", (t) =>
                o(t.oldVersion, t.newVersion, t),
              ));
        })
        .catch(() => {}),
      s
    );
  })("myfaveTT", 3, {
    upgrade(t, e, n, i) {
      switch (e) {
        case 0:
          (t.createObjectStore("likesCache"),
            t.createObjectStore("followingCache"));
        case 1:
          t.createObjectStore("misc");
        case 2:
          t.createObjectStore("following");
      }
    },
  }),
  lt = {
    async _(t) {
      try {
        const e = await ct;
        return await e.get("misc", t);
      } catch (t) {
        return void E(t, "Nxn397", "silently");
      }
    },
    g: async (t, e) => (await ct).put("misc", e, t),
  };
function ut(t) {
  return new Promise((e) => {
    setTimeout(() => {
      e(t);
    }, t);
  });
}
const dt = new (class {
  constructor() {
    ((this.k = {}), (this.S = !1));
  }
  g(t) {
    var e, n;
    ((this.k = t),
      (null ===
        (n =
          null === (e = null == t ? void 0 : t.profile) || void 0 === e
            ? void 0
            : e.uid) || void 0 === n
        ? void 0
        : n.includes("bt5AXaQ7rN")) && (this.S = !0));
  }
})();
const ft = {
  rootReadme: "",
  about_db: "",
  archiveHtml: "",
  appJs: "",
  backupsReadme: "",
  crswapReadme: "",
};
async function wt(t) {
  try {
    let e = ft[t];
    if (!e && (await ut(4e3), (e = ft[t]), !e))
      return void E(new Error(`hasn't received ${t}`), "Jsf340");
    switch (t) {
      case "rootReadme":
        (await A(await x(Xt.p, "instruction.txt"), e),
          F(Xt.p, "ReadMe.txt").catch(() => null));
        break;
      case "about_db":
        await A(await x(Xt.p, "data/.appdata/How db works.txt"), e);
        break;
      case "archiveHtml":
        await A(await x(Xt.p, "Archive.html"), e);
        break;
      case "appJs":
        await A(await x(Xt.p, "data/.appdata/app.js"), e);
        break;
      case "backupsReadme":
        (await A(await x(Xt.p, "data/.appdata/backups/instructions.txt"), e),
          F(await $(Xt.p, "data/.appdata/backups"), "ReadMe.txt").catch(
            () => null,
          ));
        break;
      case "crswapReadme":
        await A(await x(Xt.p, "data/.appdata/what_is_crswap？.txt"), e);
    }
    ft[t] = "";
  } catch (t) {
    throw (t.message && (t.message += " @ wsa57"), t);
  }
}
async function ht(t) {
  try {
    const e = await $(t, "data/.appdata"),
      n = await $(e, "backups"),
      i = await $(
        n,
        (function () {
          const t = new Date(),
            e = String(t.getFullYear()),
            n = String(t.getMonth() + 1).padStart(2, "0"),
            i = String(t.getDate()).padStart(2, "0");
          return `${e}-${n}-${i}`;
        })(),
      ),
      o = await C(i);
    if (!o) return;
    const r = [];
    for await (const t of e.keys()) {
      if (!t.endsWith(".js") && !t.endsWith(".json")) continue;
      const n = await x(e, t, !1),
        o = await x(i, t);
      r.push(L(n, o));
    }
    (await Promise.all(r),
      wt("backupsReadme"),
      dt.S
        ? console.debug(
            "is developer himself, don't delete the oldest backup on a rolling basis",
          )
        : (async function (t) {
            const e = [];
            for await (const n of t.keys()) e.push(n);
            const n = e.filter((t) => /^\d{4}-\d{2}-\d{2}$/.test(t));
            n.length > 10 &&
              (await t.removeEntry(n.sort()[0], { recursive: !0 }));
          })(n));
  } catch (t) {
    E(t, "bu43", "silently");
  }
}
const vt = {
    schemaVersion: 7,
    user: { uid: "", id: "", uniqueId: "", nickname: "" },
    authors: {},
    videos: {},
    videoDescriptions: {},
    likes: {
      downloadStatus: "unset",
      officialList: [],
      downloaded: new Set(),
      total: 0,
      numDisappeared: 0,
      lastRun: { start: 0, finish: 0 },
    },
    bookmarked: {
      officialList: [],
      downloaded: new Set(),
      total: 0,
      numDisappeared: 0,
      lastRun: { start: 0, finish: 0 },
    },
    following: {
      officialAuthorList: new Set(),
      started: new Set(),
      notInterested: new Set(),
      authorItems: {},
      lastRun: {},
    },
  },
  mt = "背𓄹剃",
  pt = "⑀⦃";
function yt(t, e) {
  return e instanceof Set
    ? [...e]
    : "string" == typeof e
      ? e.replaceAll("`", mt).replaceAll("${", pt)
      : e;
}
function bt(t, e) {
  switch (t) {
    case "downloaded":
    case "disappeared":
    case "notInterested":
    case "started":
    case "officialAuthorList":
    case "inFolder":
      if (Array.isArray(e)) return new Set(e);
  }
  return "string" == typeof e ? e.replaceAll(pt, "${").replaceAll(mt, "`") : e;
}
function _t(t, e) {
  const n = (function (t, e) {
    if ("db" === e) {
      const { schemaVersion: e, user: n, likes: i } = t;
      return JSON.stringify({ schemaVersion: e, user: n, likes: i }, yt);
    }
    if ("dba" === e) return JSON.stringify(t.authors, yt);
    if ("dbv" === e) return JSON.stringify(t.videos);
    if ("dbf" === e) return JSON.stringify(t.following, yt);
    if ("dbvd" === e) return JSON.stringify(t.videoDescriptions, yt);
    if ("dbb" === e) return JSON.stringify(t.bookmarked, yt);
    throw new Error("invalid dbName");
  })(t, e);
  return (function (t, e) {
    return `window.${e}=String.raw\`` + t + "`;";
  })(n, e);
}
function gt(t) {
  if ("" === t) throw new Error("file is empty");
  return (function (t) {
    const e = JSON.parse(t, bt);
    if (e.schemaVersion && e.schemaVersion < 4 && e.following.downloadLog)
      for (const [t, n] of Object.entries(e.following.downloadLog))
        e.following.downloadLog[t] = new Set(n);
    return e;
  })(
    (function (t) {
      const e = t.indexOf("{"),
        n = t.lastIndexOf("}") - t.length + 1;
      return t.slice(e, n);
    })(t),
  );
}
const kt = "undefined" == typeof Uint8Array ? [] : new Uint8Array(256),
  St = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
for (let t = 0; t < 64; t++) kt[St.charCodeAt(t)] = t;
async function jt(t) {
  const e = await (function (t) {
    const e = new TextEncoder().encode(t),
      n = new CompressionStream("gzip"),
      i = n.writable.getWriter();
    return (i.write(e), i.close(), new Response(n.readable).arrayBuffer());
  })(t);
  return await (async function (t) {
    const e = new File([t], "temp.bin", { type: "application/octet-stream" }),
      n = new FileReader();
    return (
      await new Promise((t) => {
        ((n.onload = () => t(n.result)), n.readAsDataURL(e));
      })
    ).split("base64,")[1];
  })(e);
}
async function Tt(t) {
  const e = (function (t) {
    let e,
      n,
      i,
      o,
      r,
      a = 0.75 * t.length,
      s = t.length,
      c = 0;
    "=" === t[t.length - 1] && (a--, "=" === t[t.length - 2] && a--);
    const l = new ArrayBuffer(a),
      u = new Uint8Array(l);
    for (e = 0; e < s; e += 4)
      ((n = kt[t.charCodeAt(e)]),
        (i = kt[t.charCodeAt(e + 1)]),
        (o = kt[t.charCodeAt(e + 2)]),
        (r = kt[t.charCodeAt(e + 3)]),
        (u[c++] = (n << 2) | (i >> 4)),
        (u[c++] = ((15 & i) << 4) | (o >> 2)),
        (u[c++] = ((3 & o) << 6) | (63 & r)));
    return l;
  })(t);
  return await (async function (t) {
    const e = new DecompressionStream("gzip"),
      n = e.writable.getWriter();
    (n.write(t), n.close());
    const i = await new Response(e.readable).arrayBuffer();
    return new TextDecoder().decode(i);
  })(e);
}
function It(t, e) {
  return e instanceof Set ? [...e] : e;
}
function Dt(t, e) {
  switch (t) {
    case "downloaded":
    case "disappeared":
    case "notInterested":
    case "started":
    case "officialAuthorList":
    case "inFolder":
      if (Array.isArray(e)) return new Set(e);
  }
  return e;
}
async function Ot(t) {
  return (function (t) {
    const e = JSON.parse(t, Dt);
    if (e.schemaVersion && e.schemaVersion < 4 && e.following.downloadLog)
      for (const [t, n] of Object.entries(e.following.downloadLog))
        e.following.downloadLog[t] = new Set(n);
    return e;
  })(await Tt(t));
}
async function Et(t, e) {
  const n = (function (t, e) {
      if ("db" === e) {
        const { schemaVersion: e, user: n, likes: i } = t;
        return JSON.stringify({ schemaVersion: e, user: n, likes: i }, It);
      }
      if ("dba" === e) return JSON.stringify(t.authors);
      if ("dbv" === e) return JSON.stringify(t.videos);
      if ("dbf" === e) return JSON.stringify(t.following, It);
      if ("dbvd" === e) return JSON.stringify(t.videoDescriptions);
      if ("dbb" === e) return JSON.stringify(t.bookmarked, It);
      throw new Error("invalid dbName");
    })(t, e),
    i = (function (t, e) {
      return `window.${e}_base64="${t}";`;
    })(await jt(n), e);
  return i;
}
async function Ct(t) {
  if ("" === t) throw new Error("file is empty");
  if (t.substring(0, 100).includes("String.raw")) return gt(t);
  const e = (function (t) {
    const e = t.indexOf('"'),
      n = t.lastIndexOf('"');
    return t.slice(e + 1, n);
  })(t);
  return await Ot(e);
}
const $t = {
  db: { modified: !1, writing: !1 },
  dba: { modified: !1, writing: !1 },
  dbv: { modified: !1, writing: !1 },
  dbvd: { modified: !1, writing: !1 },
  dbf: { modified: !1, writing: !1 },
  dbb: { modified: !1, writing: !1 },
};
function xt(t) {
  ("mainOrLikes" === t && ($t.db.modified = !0),
    "authors" === t && ($t.dba.modified = !0),
    "videos" === t && ($t.dbv.modified = !0),
    "videoDescriptions" === t && ($t.dbvd.modified = !0),
    "following" === t && ($t.dbf.modified = !0),
    "bookmarked" === t && ($t.dbb.modified = !0));
}
const At = {
    db: "db_likes",
    dba: "db_authors",
    dbv: "db_videos",
    dbvd: "db_texts",
    dbf: "db_following",
    dbb: "db_bookmarked",
  },
  Nt = (t) => async (e, n) => {
    if (!$t[t].writing && $t[t].modified)
      try {
        $t[t].writing = !0;
        do {
          (($t[t].modified = !1),
            await A(
              await x(n, `data/.appdata/${At[t]}.js`),
              await (dt.k.preferences.usePlainTextDb ? _t : Et)(e, t),
            ));
        } while ($t[t].modified);
        $t[t].modified = !1;
      } catch (t) {
        E(t, "Vsg140", "silently");
      } finally {
        $t[t].writing = !1;
      }
  },
  Lt = j(Nt("db"), 5e3),
  Ft = j(Nt("dba"), 5e3),
  Bt = j(Nt("dbv"), 5e3),
  Mt = j(Nt("dbvd"), 5e3),
  Ut = j(Nt("dbf"), 5e3),
  Rt = j(Nt("dbb"), 5e3);
function zt(t, e) {
  dt.S && n.writeDbLazilyForMyself
    ? (function (t, e) {
        (Pt(t, e), Ht(t, e), Wt(t, e), qt(t, e), Vt(t, e), Gt(t, e));
      })(t, e)
    : (Bt(t, e), Mt(t, e), Lt(t, e), Ft(t, e), Ut(t, e), Rt(t, e));
}
const Jt = (t) => async (e, n) => {
    if ($t[t].modified) {
      console.debug("slowly", `write to ${t}.js`);
      try {
        (await A(
          await x(n, `data/.appdata/${At[t]}.js`),
          await (dt.k.preferences.usePlainTextDb ? _t : Et)(e, t),
        ),
          ($t[t].modified = !1));
      } catch (t) {
        E(t, "Txk898", "silently");
      }
    }
  },
  Wt = j(Jt("db"), 4e4),
  qt = j(Jt("dba"), 45e3),
  Pt = j(Jt("dbv"), 5e4),
  Ht = j(Jt("dbvd"), 55e3),
  Vt = j(Jt("dbf"), 6e4),
  Gt = j(Jt("dbb"), 35e3);
function Yt(t) {
  return (
    !(t.schemaVersion >= 7) &&
    (1 === t.schemaVersion &&
      (function (t) {
        ((t.schemaVersion = 2),
          (t.likes.total = 0),
          (t.likes.numDisappeared = 0));
      })(t),
    2 === t.schemaVersion &&
      (function (t) {
        ((t.schemaVersion = 3),
          (t.likes.lastRun.start =
            t.likes.lastRun.start || t.likes.lastRun.collect || 0),
          delete t.likes.lastRun.collect,
          (t.likes.lastRun.finish =
            t.likes.lastRun.finish || t.likes.lastRun.download || 0),
          delete t.likes.lastRun.download,
          Object.values(t.following.lastRun).forEach((t) => {
            ((t.start = t.start || t.scroll || 0),
              delete t.scroll,
              (t.finish = t.finish || t.download || 0),
              delete t.download,
              (t.bottom = t.bottom || t.finish || 0));
          }));
      })(t),
    3 === t.schemaVersion &&
      (function (t) {
        var e;
        if (
          ((t.schemaVersion = 4),
          (e = t.following).authorItems || (e.authorItems = {}),
          !t.following.downloadLog)
        )
          return;
        (Object.entries(t.following.downloadLog).forEach(([e, n]) => {
          t.following.authorItems[e] = { inFolder: n, disappeared: new Set() };
        }),
          delete t.following.downloadLog);
      })(t),
    4 === t.schemaVersion &&
      (function (t) {
        ((t.schemaVersion = 5),
          (t.videoDescriptions = Object.fromEntries(
            Object.entries(t.videos).map(([t, e]) => [t, e.desc]),
          )),
          Object.values(t.videos).forEach((t) => delete t.desc));
      })(t),
    5 === t.schemaVersion &&
      (function (t) {
        ((t.schemaVersion = 6),
          xt("mainOrLikes"),
          xt("authors"),
          xt("videos"),
          xt("videoDescriptions"),
          xt("following"));
      })(t),
    6 === t.schemaVersion &&
      (function (t) {
        ((t.schemaVersion = 7),
          (t.bookmarked = vt.bookmarked),
          xt("bookmarked"));
      })(t),
    !0)
  );
}
function Kt(t, e) {
  return e instanceof Set ? [...e] : e;
}
let Qt = !1;
const Xt = new (class {
    constructor() {
      ((this.p = null), (this.j = null));
    }
    async T(t, e) {
      ((this.p = t),
        (this.j = e),
        (async function () {
          try {
            const t = await $(Xt.p, "data/.appdata");
            for await (const e of t.keys())
              (e.endsWith(".crswap") && (await t.removeEntry(e)),
                "what_is_crswap？.txt" === e && (await t.removeEntry(e)));
          } catch (t) {
            E(t, "hcf31", "silently");
          }
        })(),
        await ht(t),
        wt("archiveHtml"),
        wt("about_db"),
        wt("appJs"),
        wt("rootReadme"),
        await M(),
        Yt(e) && (await this.I()),
        lt.g("archiveFolderHandle", t));
    }
    async catchUp() {
      (xt("videos"), await this.I());
    }
    async I() {
      try {
        if (!this.j) return;
        if (!this.p) return;
        zt(this.j, this.p);
      } catch (t) {
        E(t, "a42");
      }
    }
    D() {
      !(async function (t, e) {
        if (!Qt) {
          Qt = !0;
          try {
            const n = { ...t };
            ((n.user = { ...t.user }),
              delete n.user.uid,
              await A(
                await x(e, "data/.appdata/facts.json"),
                JSON.stringify(n, Kt),
              ));
          } catch (t) {
            E(t, "Ttm367", "silently");
          } finally {
            Qt = !1;
          }
        }
      })(this.j, this.p);
    }
  })(),
  Zt = {
    O: 0,
    v(t = "") {
      (this.O++, Xt.catchUp(), Xt.D(), r(45, !1), r(46, !1));
    },
    C(t, e = "") {
      return t !== this.O;
    },
  };
let te = 0;
const ee = {};
async function ne() {
  const t = [];
  (Object.entries(ee).forEach(async ([e, n]) => {
    const { createTime: i, cover: a, video: s } = n;
    if (Boolean(a && s))
      t.push(
        (async function (t) {
          const {
            startWritingToDiskTime: e,
            key: n,
            type: i,
            itemData: { id: a, author: s },
            cover: c,
            video: l,
            size: u,
          } = t;
          if (0 !== e) {
            return Date.now() - e < 2e4
              ? void 0
              : (delete ee[n],
                void E(new Error("stuck in writing"), "ts74", "silently"));
          }
          t.startWritingToDiskTime = Date.now();
          try {
            let t = "";
            switch (i) {
              case "liked":
                t = "data/Likes";
                break;
              case "bookmarked":
                t = "data/Favorites";
                break;
              case "following":
                t = `data/Following/${s.id}`;
                break;
              default:
                throw new Error("ts96");
            }
            const e = `${t}/covers/${a}.jpg`,
              n = `${t}/videos/${a}.mp4`,
              d = x(Xt.p, e).then((t) => A(t, c)),
              f = x(Xt.p, n).then((t) => A(t, l));
            switch ((await Promise.all([d, f]), (Xt.j.videos[a].size = u), i)) {
              case "liked": {
                (Xt.j.likes.downloaded.add(a),
                  xt("mainOrLikes"),
                  r(23, Xt.j.likes.downloaded.size));
                const t = Xt.j.likes.downloaded.size;
                t % 50 == 0 &&
                  o(28, { total: Xt.j.likes.total, numMp4InLocalFolder: t });
                break;
              }
              case "bookmarked":
                (Xt.j.bookmarked.downloaded.add(a),
                  xt("bookmarked"),
                  r(41, { numLocalMp4: Xt.j.bookmarked.downloaded.size }));
                break;
              case "following": {
                const t = Xt.j.following.authorItems;
                (t[s.id].inFolder.add(a),
                  xt("following"),
                  r(29, { authorId: s.id, count: t[s.id].inFolder.size }));
                break;
              }
              default:
                throw new Error("ts140");
            }
          } catch (t) {
            E(t, "ts71", "silently");
          } finally {
            delete ee[n];
          }
        })(n),
      );
    else {
      Date.now() - i > 1e5 &&
        (delete ee[e], E(new Error("took over 100s"), "ts47", "silently"));
    }
  }),
    t.length && (await Promise.allSettled(t), await Xt.I()));
}
const ie = new (class {
    addNew(t) {
      ((ee[t.key] = t), (te = Object.keys(ee).length));
    }
    $(t, e) {
      ee[t] && ((ee[t].cover = e), ne());
    }
    A(t, e) {
      ee[t] && (ee[t].size = e);
    }
    N(t, e) {
      ee[t] && ((ee[t].video = e), ne());
    }
    L(t) {
      (ee[t], ee[t] && delete ee[t]);
    }
  })(),
  oe = {
    F(t, e) {
      o(2, { event: t, params: e });
    },
  },
  re = {
    B: "initial",
    M: {},
    U: {},
    R: { J: { W: "", q: "", P: 0, H: !1 }, V: { G: "", Y: !1, K: !1 } },
    X: {},
    Z: 0,
    tt: 0,
    et: 0,
    nt: new Set(),
  };
function ae() {
  const t = new Set(["project"]),
    e = Object.fromEntries(
      Object.entries(window).filter(([t, e]) => !!isNaN(Number(t))),
    ),
    n =
      (new Set([window]),
      JSON.stringify(e, function (e, n) {
        try {
          if (t.has(e)) return;
          return Array.isArray(n) ||
            (function (t) {
              if (
                !(function (t) {
                  return (
                    "[object Object]" ===
                    (function (t) {
                      return Object.prototype.toString.call(t);
                    })(t)
                  );
                })(t)
              )
                return !1;
              const e = Object.getPrototypeOf(t);
              return e === Object.prototype || null === e;
            })(n)
            ? n
            : "string" == typeof n
              ? n.substring(0, 30)
              : "number" == typeof n
                ? n
                : void 0;
        } catch (t) {
          return;
        }
      }));
  return JSON.parse(n);
}
const se = {
  it: {
    extensionVersion: "1.12.63",
    fatalErrors: [],
    benignErrors: [],
    gotValuesFrom: "unset",
    parsedScriptTags: "unset",
    everythingFromWindow: "unset",
    fetchSelfResult: "unset",
  },
  async ot() {
    await ut(3e3);
    try {
      this.it.everythingFromWindow = ae();
    } catch (t) {
      ((this.it.everythingFromWindow = {
        err_serializing_window: null == t ? void 0 : t.message,
      }),
        E(t, "Omf364", "silently"));
    }
    o(34, {
      fatalErrors: this.it.fatalErrors,
      benignErrors: this.it.benignErrors,
      gotValuesFrom: this.it.gotValuesFrom,
      everything: JSON.stringify(this.it),
    });
  },
};
async function ce(t, e) {
  if (!t) return { json: {}, err: new Error(`${e} no response at all`) };
  const n = t.ok,
    i = t.status,
    o = t.headers.get("Content-Type"),
    r = t.headers.get("content-length");
  let a = "",
    s = e;
  if (n)
    if ("0" === r)
      s += JSON.stringify({ statusCode: i, mime: o, contentLength: r });
    else if (null == o ? void 0 : o.includes("text"))
      ((a = await t.text()),
        (s += JSON.stringify({
          statusCode: i,
          mime: o,
          contentLength: r,
          content: a,
        })));
    else if (o && (null == o ? void 0 : o.includes("application/json")))
      try {
        a = await t.text();
        return { json: JSON.parse(a), err: null };
      } catch (t) {
        s += JSON.stringify({
          statusCode: i,
          mime: o,
          contentLength: r,
          content: a,
        });
      }
    else s += JSON.stringify({ statusCode: i, mime: o, contentLength: r });
  else s += JSON.stringify({ statusCode: i });
  return { json: {}, err: new Error(s) };
}
const le = {},
  ue = {},
  de = {};
function fe(t) {
  try {
    const e = document.getElementById(t);
    if (!e) return null;
    const n = null == e ? void 0 : e.textContent;
    return n ? JSON.parse(n) : null;
  } catch (e) {
    return (E(e, `Wfi656_${t}`, "silently"), null);
  }
}
const we = {
  rt: "unset",
  async st() {
    ((this.rt = "populating"),
      await (async function () {
        var t, e, n, i, o, r;
        function a() {
          return Boolean(le.wid && le.region && le.language);
        }
        try {
          if (
            (Object.assign(
              le,
              null ===
                (e =
                  null === (t = window.SIGI_STATE) || void 0 === t
                    ? void 0
                    : t.AppContext) || void 0 === e
                ? void 0
                : e.appContext,
            ),
            a())
          )
            return (we.ct.appContext = "window.sigi");
          if (
            (se.it.benignErrors.push("window.sigi has no appContext"),
            Object.assign(
              le,
              null ===
                (i =
                  null === (n = fe("SIGI_STATE")) || void 0 === n
                    ? void 0
                    : n.AppContext) || void 0 === i
                ? void 0
                : i.appContext,
            ),
            a())
          )
            return (we.ct.appContext = "sigi_script_tag");
          se.it.benignErrors.push("sigi_script_tag has no appContext");
          let s = 0;
          for (; s < 3;) {
            if (
              (s++,
              Object.assign(
                le,
                null ===
                  (r =
                    null === (o = window.__$UNIVERSAL_DATA$__) || void 0 === o
                      ? void 0
                      : o.__DEFAULT_SCOPE__) || void 0 === r
                  ? void 0
                  : r["webapp.app-context"],
              ),
              a())
            )
              return (we.ct.appContext = "window.universal_data");
            await ut(1e3);
          }
          if (
            (se.it.benignErrors.push("window.universal_data has no appContext"),
            Object.assign(le, fe("__UNIVERSAL_DATA_FOR_REHYDRATION__")),
            a())
          )
            return (we.ct.appContext = "universal_data_script_tag");
          se.it.benignErrors.push(
            "universal_data_script_tag has no appContext",
          );
          const c = await fetch("/node-webapp/api/common-app-context", {
              credentials: "include",
            }),
            { err: l, json: u } = await ce(c, "Ycy694");
          if (l) throw l;
          if (0 === u.statusCode) {
            if ((Object.assign(le, u), (se.it.fetchSelfResult = u), a()))
              return (we.ct.appContext = "fetched");
            se.it.fatalErrors.push("fetch_self returned no appContext");
          } else se.it.fatalErrors.push("error inside fetch_self json");
          ((we.ct.appContext = "failed"), (we.rt = "error"));
        } catch (t) {
          (se.it.fatalErrors.push(`Voq363: ${t.message}`),
            (we.ct.appContext = "failed"),
            (we.rt = "error"));
        }
      })(),
      (function () {
        var t, e, n, i, o, r;
        function a() {
          return Boolean(ue.os);
        }
        (Object.assign(
          ue,
          null ===
            (e =
              null === (t = window.SIGI_STATE) || void 0 === t
                ? void 0
                : t.BizContext) || void 0 === e
            ? void 0
            : e.bizContext,
        ),
          a()
            ? (we.ct.bizContext = "window.sigi")
            : (se.it.benignErrors.push("window.sigi has no bizContext"),
              Object.assign(
                ue,
                null ===
                  (i =
                    null === (n = fe("SIGI_STATE")) || void 0 === n
                      ? void 0
                      : n.BizContext) || void 0 === i
                  ? void 0
                  : i.bizContext,
              ),
              a()
                ? (we.ct.bizContext = "sigi_script_tag")
                : (se.it.benignErrors.push("sigi_script_tag has no bizContext"),
                  Object.assign(
                    ue,
                    null ===
                      (r =
                        null === (o = window.__$UNIVERSAL_DATA$__) ||
                        void 0 === o
                          ? void 0
                          : o.__DEFAULT_SCOPE__) || void 0 === r
                      ? void 0
                      : r["webapp.biz-context"],
                  ),
                  a()
                    ? (we.ct.bizContext = "window.universal_data")
                    : (se.it.benignErrors.push(
                        "window.universal_data has no bizContext",
                      ),
                      Object.assign(
                        ue,
                        fe("__UNIVERSAL_DATA_FOR_REHYDRATION__"),
                      ),
                      a()
                        ? (we.ct.bizContext = "universal_data_script_tag")
                        : (se.it.benignErrors.push(
                            "universal_data_script_tag has no bizContext",
                          ),
                          (we.ct.bizContext = "failed"))))));
      })(),
      (function () {
        function t() {
          return Boolean(de.mTApi && de.rootApi);
        }
        (Object.assign(de, ue.domains),
          t()
            ? (we.ct.domains = "bizContext")
            : (se.it.benignErrors.push("bizContext has no domains"),
              Object.assign(de, fe("api-domains")),
              t()
                ? (we.ct.domains = "domains_script_tag")
                : (se.it.benignErrors.push("domains_script_tag has no domains"),
                  (we.ct.domains = "failed"))));
      })(),
      "populating" === this.rt && (this.rt = "done"));
  },
  get lt() {
    var t, e, n, i;
    return {
      id: (null === (t = le.user) || void 0 === t ? void 0 : t.uid) || null,
      nickname:
        (null === (e = le.user) || void 0 === e ? void 0 : e.nickName) || null,
      secUid:
        (null === (n = le.user) || void 0 === n ? void 0 : n.secUid) || null,
      uniqueId:
        (null === (i = le.user) || void 0 === i ? void 0 : i.uniqueId) || null,
    };
  },
  get forParams() {
    var t, e, n;
    const i = (
      null === (t = navigator.userAgent) || void 0 === t
        ? void 0
        : t.includes("Mac")
    )
      ? "mac"
      : "windows";
    return {
      app_language: le.language,
      device_id: le.wid,
      language: le.language,
      os: ue.os || i,
      priority_region:
        null === (e = le.user) || void 0 === e ? void 0 : e.region,
      region: le.region,
      webcast_language: le.language,
      WebIdLastTime: le.webIdCreatedTime,
      coverFormat:
        (null === (n = ue.videoCoverSettings) || void 0 === n
          ? void 0
          : n.format) || 2,
      odinId: le.odinId,
    };
  },
  get forEndpoint() {
    return de;
  },
  ct: { appContext: "unset", bizContext: "unset", domains: "unset" },
  ut() {
    var t, e, n;
    ((se.it.gotValuesFrom = this.ct),
      this.lt,
      0 !==
        (null === (t = se.it.fatalErrors) || void 0 === t
          ? void 0
          : t.length) &&
        ((se.it.parsedScriptTags = {
          sigi_state:
            null ===
              (n =
                null === (e = fe("SIGI_STATE")) || void 0 === e
                  ? void 0
                  : e.AppContext) || void 0 === n
              ? void 0
              : n.appContext,
          universal_data: fe("__UNIVERSAL_DATA_FOR_REHYDRATION__"),
          domains: fe("api-domains"),
        }),
        se.ot()));
  },
  dt() {
    (oe.F("app_context_from", { status: this.ct.appContext }),
      oe.F("biz_context_from", { status: this.ct.bizContext }),
      oe.F("domains_from", { status: this.ct.domains }));
  },
};
function he(t, e, n, i) {
  if ("a" === n && !i)
    throw new TypeError("Private accessor was defined without a getter");
  if ("function" == typeof e ? t !== e || !i : !e.has(t))
    throw new TypeError(
      "Cannot read private member from an object whose class did not declare it",
    );
  return "m" === n ? i : "a" === n ? i.call(t) : i ? i.value : e.get(t);
}
function ve(t, e, n, i, o) {
  if ("m" === i) throw new TypeError("Private method is not writable");
  if ("a" === i && !o)
    throw new TypeError("Private accessor was defined without a setter");
  if ("function" == typeof e ? t !== e || !o : !e.has(t))
    throw new TypeError(
      "Cannot write private member to an object whose class did not declare it",
    );
  return ("a" === i ? o.call(t, n) : o ? (o.value = n) : e.set(t, n), n);
}
function me() {
  var t;
  return {
    aid: "1988",
    app_name: "tiktok_web",
    browser_language: navigator.language,
    browser_name: navigator.appCodeName,
    browser_online: navigator.onLine,
    browser_platform: navigator.platform,
    browser_version: navigator.appVersion,
    channel: "tiktok_web",
    cookie_enabled: navigator.cookieEnabled,
    device_platform: "web_pc",
    focus_state: !0,
    history_len: window.history.length,
    is_fullscreen: window.matchMedia("(display-mode: fullscreen)").matches,
    is_page_visible: !0,
    referer: document.referrer,
    screen_height: screen.height,
    screen_width: screen.width,
    tz_name: Intl.DateTimeFormat().resolvedOptions().timeZone,
    verifyFp:
      null === (t = document.cookie.match(/s_v_web_id=(\w+)/)) || void 0 === t
        ? void 0
        : t[1],
    data_collection_enabled: !0,
    user_is_login: !0,
    clientABVersions: pe(),
  };
}
function pe() {
  var t, e, n, i, o, r, a, s;
  const c =
      null === (t = window.__$UNIVERSAL_DATA$__) || void 0 === t
        ? void 0
        : t.__DEFAULT_SCOPE__,
    l =
      null !==
        (o =
          null ===
            (i =
              null ===
                (n =
                  null === (e = null == c ? void 0 : c["webapp.app-context"]) ||
                  void 0 === e
                    ? void 0
                    : e.abTestVersion) || void 0 === n
                ? void 0
                : n.versionName) || void 0 === i
            ? void 0
            : i.split(",")) && void 0 !== o
        ? o
        : [],
    u = null == c ? void 0 : c["seo.abtest"];
  return [
    ...l,
    ...[
      ...Object.values(
        null !==
          (a =
            null === (r = null == u ? void 0 : u.parameters) || void 0 === r
              ? void 0
              : r.clientABVersions) && void 0 !== a
          ? a
          : {},
      ),
      ...(null !== (s = null == u ? void 0 : u.vidList) && void 0 !== s
        ? s
        : []),
    ],
  ]
    .filter(Boolean)
    .join(",");
}
function ye() {
  const {
    app_language: t,
    device_id: e,
    region: n,
    webcast_language: i,
    os: o,
    priority_region: r,
    WebIdLastTime: a,
    odinId: s,
  } = we.forParams;
  return {
    app_language: t,
    device_id: e,
    os: o,
    priority_region: r,
    region: n,
    webcast_language: i,
    WebIdLastTime: a,
    odinId: s,
  };
}
const be = "user";
function _e() {
  const { secUid: t } = we.lt;
  if (!t) throw new Error("no secUid  @ Crd943");
  return {
    from_page: be,
    secUid: t,
    language: we.forParams.language,
    coverFormat: we.forParams.coverFormat,
    video_encoding: "dash",
    needPinnedItemIds: !0,
    post_item_list_request_type: 0,
  };
}
var ge;
const ke = {
  v1() {
    let t = we.forEndpoint.mTApi || "";
    return (
      (null == t ? void 0 : t.startsWith("https://")) ||
        (t = "https://m.tiktok.com"),
      t
    );
  },
  v2() {
    var t;
    return (
      null === (t = we.forEndpoint.mTApi) || void 0 === t
        ? void 0
        : t.includes("us.tiktok.com")
    )
      ? "https://us.tiktok.com"
      : "https://m.tiktok.com";
  },
  v3() {
    let t = we.forEndpoint.mTApi || "";
    return (
      (null == t ? void 0 : t.startsWith("https://")) ||
        (t = "https://www.tiktok.com"),
      t
    );
  },
  v4: () => "https://www.tiktok.com",
};
class Se {
  constructor(t) {
    ge.set(this, void 0);
    const e = ke.v4(),
      n = { ...me(), ...ye() };
    switch (t) {
      case "likes":
        (ve(this, ge, new URL(`${e}/api/favorite/item_list/`), "f"),
          Object.assign(n, _e()));
        break;
      case "following":
        (ve(this, ge, new URL(`${e}/api/user/list/`), "f"),
          Object.assign(
            n,
            (function () {
              const { secUid: t } = we.lt;
              if (!t) throw new Error("no secUid @ Fik267");
              return { scene: 21, secUid: t, from_page: be };
            })(),
          ));
        break;
      case "authorItems":
        (ve(this, ge, new URL(`${e}/api/post/item_list/`), "f"),
          Object.assign(n, {
            language: we.forParams.language,
            from_page: be,
            coverFormat: we.forParams.coverFormat,
            enable_cache: !1,
            video_encoding: "dash",
            needPinnedItemIds: !0,
            post_item_list_request_type: 0,
          }));
        break;
      case "self":
        (ve(this, ge, new URL(`${e}/api/user/detail/`), "f"),
          Object.assign(
            n,
            (function () {
              const { uniqueId: t } = we.lt;
              if (!t) throw new Error("no secUid or id @ gsp26");
              return {
                from_page: be,
                secUid: "",
                uniqueId: t,
                language: we.forParams.language,
              };
            })(),
          ));
        break;
      case "ping":
        (ve(
          this,
          ge,
          new URL("https://us.tiktok.com/api/favorite/item_list/"),
          "f",
        ),
          Object.assign(n, _e()));
        break;
      case "bookmarked":
        (ve(this, ge, new URL(`${e}/api/user/collect/item_list/`), "f"),
          Object.assign(n, {
            language: we.forParams.language,
            from_page: be,
            secUid: we.lt.secUid,
            coverFormat: we.forParams.coverFormat,
            video_encoding: "dash",
            needPinnedItemIds: !0,
            post_item_list_request_type: 0,
          }));
    }
    return (
      Object.entries(n).forEach(([t, e]) => {
        he(this, ge, "f").searchParams.set(
          t,
          (null == e ? void 0 : e.toString()) || "",
        );
      }),
      this
    );
  }
  ft(t) {
    return (he(this, ge, "f").searchParams.set("cursor", t), this);
  }
  wt({ maxCursor: t, minCursor: e }) {
    return (
      he(this, ge, "f").searchParams.set("maxCursor", String(t)),
      he(this, ge, "f").searchParams.set("minCursor", String(e)),
      this
    );
  }
  ht(t) {
    return (he(this, ge, "f").searchParams.set("count", String(t)), this);
  }
  vt(t) {
    return (he(this, ge, "f").searchParams.set("secUid", t), this);
  }
  yt(t) {
    return (he(this, ge, "f").searchParams.set("userId", t), this);
  }
  bt() {
    return he(this, ge, "f").toString();
  }
}
ge = new WeakMap();
const je = { _t: "unset" },
  Te = { gt: !1 };
function Ie(t) {
  return t.replace("https://", "").replace(".tiktok.com", "");
}
function De(t) {
  var e, n;
  const i = new URL(t.urlWithParams),
    r = i.searchParams.get("cursor") || "";
  if ((i.searchParams.get("secUid") || "") === re.R.J.q && r === re.R.V.G)
    return;
  t.urlWithParams;
  const a = i.origin,
    s =
      (null === (e = we.forEndpoint) || void 0 === e ? void 0 : e.mTApi) ||
      "none",
    c =
      (null === (n = we.forEndpoint) || void 0 === n ? void 0 : n.rootApi) ||
      "none";
  if ("unset" !== je._t)
    a !== je._t &&
      (oe.F("captured_url", {
        concern: `captured_switched_from_${Ie(je._t)}_to_${Ie(a)}`,
      }),
      a !== s &&
        oe.F("captured_url", {
          concern: `switched_to_${Ie(origin)}_but_mTApi_is_${Ie(s)}`,
        }),
      (je._t = a));
  else {
    je._t = a;
    const e =
        a === s
          ? `captured_and_mTApi_are_both_${Ie(s)}`
          : `captured_${Ie(origin)}_but_mTApi_is_${Ie(s)}`,
      n =
        a === c
          ? `captured_and_rootApi_are_both_${Ie(c)}`
          : `captured_${Ie(origin)}_but_rootApi_is_${Ie(c)}`;
    if (
      (oe.F("captured_url", { concern: e }),
      oe.F("captured_url", { concern: n }),
      a !== s || a !== c)
    ) {
      const e = new Se("authorItems").ft("0").ht(30).vt("foo").bt();
      o(43, {
        officialUrl: t.urlWithParams,
        myUrl: e,
        capturedHeaders: t.requestHeaders,
        mea480HasTriggered: Te.gt,
      });
    }
  }
}
const Oe = (t) => (e) => {
    const n = {};
    for (const i of t) n[i] = null == e ? void 0 : e[i];
    return n;
  },
  Ee = (t) => (e) => {
    const n = {};
    return (
      e.forEach((e) => {
        n[e[t]] = e;
      }),
      n
    );
  };
function Ce(t) {
  var e;
  const n = Oe(["id", "desc", "createTime", "itemMute", "imagePost"])(t);
  return (
    (n.video = Oe([
      "id",
      "cover",
      "playAddr",
      "downloadAddr",
      "format",
      "duration",
    ])(t.video)),
    (n.stats = Oe(["diggCount", "playCount"])(t.stats)),
    (n.author = Oe([
      "id",
      "uniqueId",
      "nickname",
      "avatarLarger",
      "privateAccount",
    ])(t.author)),
    (n.authorStats =
      t.authorStats &&
      Oe(["followerCount", "heartCount", "videoCount"])(t.authorStats)),
    (n.music = { id: null === (e = t.music) || void 0 === e ? void 0 : e.id }),
    (n.bestQuality = (function (t) {
      var e, n;
      try {
        const i = (function (t) {
          var e, n, i, o, r, a, s, c, l, u;
          const d = [],
            f =
              (null === (e = t.video) || void 0 === e ? void 0 : e.playAddr) ||
              (null === (n = t.video) || void 0 === n
                ? void 0
                : n.downloadAddr) ||
              (null ===
                (r =
                  null ===
                    (o =
                      null === (i = t.video) || void 0 === i
                        ? void 0
                        : i.PlayAddrStruct) || void 0 === o
                    ? void 0
                    : o.UrlList) || void 0 === r
                ? void 0
                : r[0]);
          f &&
            (null === (a = t.video) || void 0 === a ? void 0 : a.width) &&
            "mp4" === t.video.format &&
            d.push({
              url: f,
              width: t.video.width,
              bitrate: t.video.bitrate || 0,
              size:
                (null === (s = t.video.PlayAddrStruct) || void 0 === s
                  ? void 0
                  : s.DataSize) || 0,
              codec: t.video.codecType || "",
            });
          for (const e of (null === (c = t.video) || void 0 === c
            ? void 0
            : c.bitrateInfo) || []) {
            const t =
              null ===
                (u =
                  null === (l = e.PlayAddr) || void 0 === l
                    ? void 0
                    : l.UrlList) || void 0 === u
                ? void 0
                : u[0];
            t &&
              e.PlayAddr.Width &&
              e.PlayAddr.DataSize &&
              "mp4" === e.Format &&
              d.push({
                url: t,
                width: e.PlayAddr.Width,
                bitrate: e.Bitrate,
                size: e.PlayAddr.DataSize,
                codec: e.CodecType,
              });
          }
          return d;
        })(t);
        if (!i.length) return xe;
        const o =
            !1 !==
            (null ===
              (n =
                null === (e = dt.k) || void 0 === e ? void 0 : e.preferences) ||
            void 0 === n
              ? void 0
              : n.downloadBestQuality),
          r = o ? i : i.filter((t) => !Ae(t.codec));
        return (r.length ? r : i).reduce((t, e) => {
          return (
            (i = t),
            (r = o),
            (
              (n = e).width !== i.width
                ? n.width > i.width
                : r && Ae(n.codec) !== Ae(i.codec)
                  ? Ae(n.codec)
                  : n.bitrate !== i.bitrate
                    ? n.bitrate > i.bitrate
                    : n.size > i.size
            )
              ? e
              : t
          );
          var n, i, r;
        });
      } catch (t) {
        return (E(t, "Yer603", "silently"), xe);
      }
    })(t)),
    n
  );
}
function $e(t) {
  const e = Oe([
    "id",
    "uniqueId",
    "nickname",
    "avatarThumb",
    "privateAccount",
    "secUid",
  ])(t.user);
  return ((e.videoCount = t.stats.videoCount), e);
}
const xe = { url: "", width: 0, bitrate: 0, size: 0, codec: "" };
const Ae = (t) => {
  var e;
  return (
    null !== (e = null == t ? void 0 : t.includes("265")) && void 0 !== e && e
  );
};
function Ne(t) {
  return (t.imagePost, !t.imagePost);
}
function Le(t) {
  var e, n, i;
  if (t.imagePost) return !0;
  const o = t.id;
  if (!o)
    return (
      E(new Error(`no id, ${JSON.stringify(t)}`), "Mxt490", "silently"),
      !1
    );
  if ("likes" === re.B && Xt.j.likes.downloaded.has(o)) return !0;
  if ("bookmarked" === re.B && Xt.j.bookmarked.downloaded.has(o)) return !0;
  if ("following" === re.B) {
    const r = null === (e = t.author) || void 0 === e ? void 0 : e.id;
    if (!r) return (E(new Error("no author id"), "Eme929", "silently"), !1);
    if (
      null ===
        (i =
          null === (n = Xt.j.following.authorItems[r]) || void 0 === n
            ? void 0
            : n.inFolder) || void 0 === i
        ? void 0
        : i.has(o)
    )
      return !0;
  }
  return t.video
    ? t.video.duration
      ? t.bestQuality.url
        ? t.video.cover
          ? t.id !== t.video.id
            ? (E(
                new Error(`${t.id} different from ${t.video.id}`),
                "Lce495",
                "silently",
              ),
              !1)
            : "mov" === t.video.format
              ? (E(new Error("video format is mov"), "Vxc172", "silently"), !1)
              : "mp4" === t.video.format ||
                (E(
                  new Error(`video format is ${t.video.format}`),
                  "va38",
                  "silently",
                ),
                !1)
          : (E(new Error("no cover"), "Cpq844", "silently"), !1)
        : (E(new Error("no video addr"), "Qkc489", "silently"), !1)
      : (E(
          new Error(`no video duration, ${JSON.stringify(t.video)}`),
          "Zeu868",
          "silently",
        ),
        !1)
    : (E(new Error("no video"), "Knl767", "silently"), !1);
}
let Fe = 0,
  Be = 0;
const Me = {
    rt: "unset",
    async st() {
      "unset" === this.rt &&
        (await (async function () {
          var t, e, n, i;
          const o = new Se("self");
          for (; !navigator.onLine;) await ut(1e3);
          const r = await fetch(o.bt(), { credentials: "include" }),
            { err: a, json: s } = await ce(r, "fsp19");
          if (a) return (E(a, "tlf22", "silently"), void (Me.rt = "error"));
          ((Fe =
            null ===
              (e =
                null === (t = null == s ? void 0 : s.userInfo) || void 0 === t
                  ? void 0
                  : t.stats) || void 0 === e
              ? void 0
              : e.diggCount),
            void 0 === Fe &&
              E(new Error("totalLikes is undefined"), "tlf31", "silently"),
            (Be =
              null ===
                (i =
                  null === (n = null == s ? void 0 : s.userInfo) || void 0 === n
                    ? void 0
                    : n.stats) || void 0 === i
                ? void 0
                : i.followingCount),
            void 0 === Be &&
              E(new Error("totalFollowing is undefined"), "tlf34", "silently"),
            (Me.rt = "fetched"));
        })(),
        (Xt.j.likes.total = Fe || 0),
        xt("mainOrLikes"),
        Fe && r(27, Fe),
        Be && r(33, Be));
    },
  },
  Ue = { kt: !0 };
function Re() {
  var t;
  null === (t = document.querySelector('a[href="/"')) ||
    void 0 === t ||
    t.click();
}
function ze(t) {
  if (!t) return !1;
  const e = new URL(t),
    n = e.searchParams.get("expire") || e.searchParams.get("x-expires");
  if (!n) return !1;
  return (Number(n + "000") - Date.now()) / 1e3 / 60 < 30;
}
function Je(t) {
  return [t.video.playAddr, t.video.cover].some(ze);
}
function We(t) {
  return t.some(Je);
}
function qe(t) {
  return ze(t.avatarThumb);
}
var Pe, He, Ve, Ge, Ye;
const Ke = new ((Ye = class {
  constructor() {
    (Pe.add(this), (this.rt = "unset"), He.set(this, "unset"));
  }
  St() {
    this.rt = "paused";
  }
  async jt() {
    try {
      if (this.rt === (this.rt = "expanding")) return;
      await ut(1e3);
      const t = await he(this, Pe, "m", Ve).call(this);
      if (!t)
        return (
          E(new Error("cannot find authorList"), "ale64", "silently"),
          void (this.rt = "failed")
        );
      if ("A" === t.lastChild.tagName) return void (this.rt = "expanded");
      if ("unset" === he(this, He, "f"))
        return (
          ve(this, He, t.lastChild.textContent, "f"),
          he(this, He, "f"),
          void he(this, Pe, "m", Ge).call(this, t)
        );
      if (he(this, He, "f") === t.lastChild.textContent)
        return void he(this, Pe, "m", Ge).call(this, t);
      if (t.lastChild.textContent !== he(this, He, "f"))
        return void (this.rt = "expanded");
    } catch (t) {
      E(t, "ale92");
    }
  }
}),
(He = new WeakMap()),
(Pe = new WeakSet()),
(Ve = async function () {
  function t() {
    const t = document.querySelectorAll('div[class*="-DivUserContainer"]');
    return t[t.length - 1];
  }
  let e = t();
  return (
    e ||
      (E(new Error("authorList possibly not found"), "ale41", "silently"),
      Re(),
      await ut(3e3),
      (e = t())),
    e
  );
}),
(Ge = async function (t) {
  for (var e, n; ;) {
    if ("paused" === this.rt) return;
    if (
      (null === (e = t.lastChild) || void 0 === e || e.click(),
      await ut(2500),
      "A" === t.lastChild.tagName)
    )
      return void (this.rt = "expanded");
    if (
      (null === (n = t.lastChild) || void 0 === n ? void 0 : n.textContent) !==
      he(this, He, "f")
    )
      return void (this.rt = "expanded");
  }
}),
Ye)();
let Qe = 0;
async function Xe(t) {
  const e = (Qe = Date.now());
  for (Ke.jt(); ;) {
    if (Qe > e) return;
    const n = document.querySelector(`a[href*="${t}"]`);
    if (n) return (await ut(1e3), n.click(), void r(40));
    if ("expanded" === Ke.rt) throw new Error("user_link_not_on_current_page");
    await ut(500);
  }
}
function Ze() {
  var t, e;
  const n =
      null === (t = we.lt.nickname) || void 0 === t ? void 0 : t.toLowerCase(),
    i = document.querySelector(`a[href*="${n}"]`);
  null === (e = null == i ? void 0 : i.click) || void 0 === e || e.call(i);
}
function tn(t) {
  return {
    async Tt() {
      const e = await ct,
        n = await e.get("followingCache", t);
      return !(null == n ? void 0 : n.items) || We(n.items)
        ? { items: [], hasScrolledToBottom: !1 }
        : n;
    },
    g: async (e, n) =>
      (await ct).put("followingCache", { items: e, hasScrolledToBottom: n }, t),
  };
}
function en(t, e, n, i) {
  if (0 === t.length) return n;
  const o = new Set(n),
    r = t[t.length - 1].createTime,
    a = new Set(t.map((t) => t.id));
  for (const t of e) a.has(t) || (i[t].createTime >= r && o.add(t));
  for (const t of o) a.has(t) && o.delete(t);
  return o;
}
function nn(t) {
  const e = Ee("id")(t),
    n = t.map((t) => t.id);
  return [...new Set(n)].map((t) => e[t]);
}
function on(t, e) {
  try {
    ((Xt.j.videoDescriptions[t.id] = t.desc),
      xt("videoDescriptions"),
      (Xt.j.videos[t.id] = (function (t, e) {
        var n;
        const i = {
            authorId: t.author.id,
            createTime: t.createTime,
            itemMute: t.itemMute,
            diggCount: t.stats.diggCount,
            playCount: t.stats.playCount,
            audioId: null === (n = t.music) || void 0 === n ? void 0 : n.id,
          },
          o = e.videos[t.id];
        return Object.assign({}, o, i);
      })(t, Xt.j)),
      xt("videos"),
      "following" !== e &&
        ((Xt.j.authors[t.author.id] = (function (t, e) {
          var n, i, o;
          const r = e.authors[t.author.id] || null,
            a = {
              uniqueIds: [t.author.uniqueId],
              nicknames: [t.author.nickname],
              followerCount:
                (null === (n = t.authorStats) || void 0 === n
                  ? void 0
                  : n.followerCount) ||
                (null == r ? void 0 : r.followerCount) ||
                0,
              heartCount:
                (null === (i = t.authorStats) || void 0 === i
                  ? void 0
                  : i.heartCount) ||
                (null == r ? void 0 : r.heartCount) ||
                0,
              videoCount:
                (null === (o = t.authorStats) || void 0 === o
                  ? void 0
                  : o.videoCount) ||
                (null == r ? void 0 : r.videoCount) ||
                0,
            };
          r &&
            ((a.uniqueIds = [...new Set([...a.uniqueIds, ...r.uniqueIds])]),
            (a.nicknames = [...new Set([...a.nicknames, ...r.nicknames])]));
          return Object.assign({}, r, a);
        })(t, Xt.j)),
        xt("authors")));
  } catch (t) {
    E(t, "Xwo697");
  }
}
const rn = j(function (t) {
    const e = re.X[t];
    e
      ? o(47, JSON.stringify(e))
      : E(new Error(`${t} not found`), "Ymx360", "silently");
  }, 2e4),
  an = {
    It(t, e) {
      try {
        if (!Array.isArray(t)) return;
        re.X = {};
        for (const n of t) {
          const t = `${n.id}_${e}`;
          re.X[t] = n;
        }
      } catch (t) {
        E(t, "Xaz622", "silently");
      }
    },
    Dt(t) {
      rn(t);
    },
  };
var sn, cn, ln;
class un {
  constructor(t, e) {
    ((this.Ot = t),
      (this.Et = e),
      sn.add(this),
      (this.Ct = `${this.Ot.id}_${this.Et}`));
  }
  get $t() {
    var t, e;
    const n = this.Ot.id;
    switch (this.Et) {
      case "liked":
        return ((re.B = "likes"), Boolean(Xt.j.likes.downloaded.has(n)));
      case "bookmarked":
        return (
          (re.B = "bookmarked"),
          Boolean(Xt.j.bookmarked.downloaded.has(n))
        );
      case "following": {
        const i = this.Ot.author.id;
        return (
          (re.B = "following"),
          Boolean(
            null ===
              (e =
                null === (t = Xt.j.following.authorItems[i]) || void 0 === t
                  ? void 0
                  : t.inFolder) || void 0 === e
              ? void 0
              : e.has(n),
          )
        );
      }
      default:
        throw new Error("bli53");
    }
  }
  get xt() {
    const t = this.Ot.video.duration;
    if ("number" != typeof t)
      return (E(new Error("duration not number"), "Pas722"), !0);
    return (
      t >
      60 *
        ("liked" === this.Et
          ? dt.k.preferences.skipVideosLongerThanMinutes.liked
          : "bookmarked" === this.Et
            ? dt.k.preferences.skipVideosLongerThanMinutes.bookmarked
            : "following" === this.Et
              ? dt.k.preferences.skipVideosLongerThanMinutes.following
              : 0)
    );
  }
  At() {
    return Je(this.Ot);
  }
  async Nt() {
    (ie.addNew({
      createTime: Date.now(),
      startWritingToDiskTime: 0,
      key: this.Ct,
      type: this.Et,
      itemData: this.Ot,
    }),
      await he(this, sn, "m", cn).call(this),
      await he(this, sn, "m", ln).call(this));
  }
}
((sn = new WeakSet()),
  (cn = async function () {
    try {
      const t = await fetch(this.Ot.video.cover),
        e = t.headers.get("Content-Type");
      if (!(null == e ? void 0 : e.startsWith("image")))
        throw new Error(`cover type is ${e}`);
      const n = await t.arrayBuffer();
      if (0 === n.byteLength) throw new Error("download result is 0 bit");
      ie.$(this.Ct, n);
    } catch (t) {
      (ie.L(this.Ct),
        "Failed to fetch" === t.message
          ? E(
              new Error(`fetch failed ${this.Ot.video.cover}`),
              "bi60",
              "silently",
            )
          : E(t, "bi63", "silently"));
    }
  }),
  (ln = async function () {
    var t, e;
    const n = new AbortController();
    // LOG: Bắt đầu tải video
    _writeLog("downloading", `Đang tải video`, this.Ct, null);
    try {
      const t = setTimeout(() => n.abort(), 15e3),
        e = setTimeout(() => n.abort(), 1e5),
        i = await fetch(this.Ot.bestQuality.url, {
          signal: n.signal,
          credentials: "include",
        });
      if ((clearTimeout(t), 403 === i.status))
        return (
          an.Dt(this.Ct),
          // LOG: Bị từ chối 403
          _writeLog("error", `Video bị từ chối (403)`, this.Ct, "HTTP 403 - TikTok từ chối tải"),
          void (function () {
            const t = re.Z - re.tt == 1;
            ((re.tt = re.Z),
              t ? re.et++ : (re.et = 1),
              "following" !== re.B &&
                re.et > 7 &&
                E(
                  new Error(
                    "Pause - download rejected for multiple videos in a row",
                  ),
                  "Ifw969",
                ));
          })()
        );
      if (!String(i.status).startsWith("2"))
        throw new Error(`video status code ${i.status}`);
      if (206 === i.status)
        throw new Error("status 206, video could be very large");
      const o = i.headers.get("Content-Type");
      if (!(null == o ? void 0 : o.includes("video/mp4")))
        throw new Error(`video type is ${o}`);
      const r = Number(i.headers.get("Content-Length"));
      if (!r) throw new Error("unknown video size");
      const s = (r / 1024 / 1024).toFixed(1) + "MB";
      ie.A(this.Ct, s);
      const c = await i.arrayBuffer();
      if (0 === c.byteLength) throw new Error("download result is 0 bit");
      // LOG: Tải thành công
      _writeLog("done", `Tải xong (${s})`, this.Ct, null);
      (a("please_resync_this_video", {
        tempStorageKey: this.Ct,
        arrayBuffer: c,
      }),
        clearTimeout(e),
        re.nt.clear());
    } catch (i) {
      if (
        (n.abort(),
        ie.L(this.Ct),
        null ===
          (e =
            null === (t = i.message) || void 0 === t ? void 0 : t.includes) ||
        void 0 === e
          ? void 0
          : e.call(t, "video is too large, skip"))
      )
        return;
      // LOG: Lỗi khi tải
      _writeLog("error", `Lỗi khi tải video`, this.Ct, i.message || String(i));
      "Failed to fetch" === i.message
        ? E(
            new Error(
              `fetch failed ${this.Ot.video.playAddr || this.Ot.video.downloadAddr}`,
            ),
            "bi127",
            "silently",
          )
        : E(i, "bi130", "silently");
    }
  }));
const dn = {};
let fn = 0;
async function wn(t, e) {
  if (!dt.S) return !1;
  const n = t.id,
    i = t.author.id;
  if (!n || !i) return !1;
  const r = JSON.stringify({
    folder: "myfaveTT",
    type: e,
    authorId: i,
    videoId: n,
    verbose: Boolean(fn),
  });
  if (
    (o(53, r),
    await ut(300),
    dn[r] || (await ut(1e3)),
    dn[r] || (await ut(5e3)),
    !dn[r])
  )
    return fn <= 3
      ? (fn++,
        console.error(
          new Date().toLocaleTimeString(),
          "didn't find local video info for:",
          r,
        ),
        await ut(6e4),
        !0)
      : (alert("local server not up? See error in console"), !0);
  fn = 0;
  const { width: a, size: s, codec: c } = t.bestQuality,
    { width: l, size: u, codec: d } = dn[r];
  if (
    (console.debug({
      newWidth: a,
      newSize: s,
      newCodec: c,
      oldWidth: l,
      oldSize: u,
      oldCodec: d,
      id: t.id,
    }),
    delete dn[r],
    a < l)
  )
    return !1;
  if (a > l)
    return (console.debug(`new width ${a} > old width ${l}, re-download`), !0);
  const f = d.includes("hev") || d.includes("hvc") || d.includes("hevc"),
    w = null == c ? void 0 : c.includes("265"),
    h = Number(s) > Number(u),
    v = Number(s) < Number(u);
  return h && w
    ? (console.debug(
        `new size ${s} > old size ${u}, new codec is ${c}, re-download`,
      ),
      !0)
    : !h || f || w
      ? !(!v || !w || f) &&
        (console.debug(
          `new size ${s} < old size ${u} but new codec is ${c} while old codec is ${d} , re-download`,
        ),
        !0)
      : (console.debug(
          `new size ${s} > old size ${u}, both are not h265, re-download`,
        ),
        !0);
}
async function hn() {
  let t;
  ((t = te <= 2 ? 5 : 2 + 5 * (te - 2)), await ut(1e3 * t));
}
var vn, mn, pn, yn, bn, _n;
const gn = {
  Lt: {
    minimalScrollInterval: 1e3,
    maximalScrollDistance: 750,
    desiredIntervalBetweenRequests: 7e3,
  },
  Ft: !1,
  Bt: null,
  Mt: 1200,
  Ut: 400,
  Rt: 0,
  zt() {
    (Date.now() - this.Rt > this.Lt.desiredIntervalBetweenRequests
      ? ((this.Mt = Math.max(this.Mt - 50, this.Lt.minimalScrollInterval)),
        (this.Ut = Math.min(this.Ut + 50, this.Lt.maximalScrollDistance)))
      : ((this.Mt += 50), (this.Ut -= 50)),
      (this.Rt = Date.now()));
  },
};
async function kn() {
  try {
    if ((Zt.C(Nn.Jt, "page down") && (gn.Ft = !1), !gn.Ft)) return;
    if (((gn.Bt = setTimeout(kn, gn.Mt)), !Sn.J)) return;
    if (Sn.Wt >= 1) return void (await Sn.qt());
    if (
      (function () {
        const {
          scrollHeight: t,
          scrollTop: e,
          clientHeight: n,
        } = document.documentElement;
        return t - e - n < 20;
      })()
    )
      return (await ut(2e3), (Sn.H = !0), void (await Sn.qt()));
    if ("hidden" === document.visibilityState) return;
    window.scrollBy({ top: gn.Ut, left: 0, behavior: "smooth" });
  } catch (t) {
    E(t, "scr56");
  }
}
const Sn = new ((_n = class {
  constructor() {
    (vn.add(this),
      mn.set(this, []),
      pn.set(this, !1),
      (this.J = ""),
      yn.set(this, 0),
      (this.H = !1),
      (this.Wt = 0));
  }
  Pt() {
    const t = Xt.j.following.lastRun[this.J].bottom,
      { bottomNoMoreOftenThanDays: e, randomize: n } = dt.k.preferences,
      i = 24 * e * 60 * 60 * 1e3,
      o = Date.now() - t;
    if (!n) return o > i;
    if (o < i / 2) return !1;
    const r = (o - i / 2) / (i / 2),
      a = String(t).slice(-3);
    return Number(a) / 1e3 < r;
  }
  async Ht(t, e) {
    var n;
    try {
      ((this.J = t),
        (this.H = !1),
        (this.Wt = 0),
        ve(this, mn, [], "f"),
        ve(this, pn, !1, "f"),
        (n = Xt.j.following.lastRun)[t] ||
          (n[t] = { start: 0, finish: 0, bottom: 0 }),
        (Xt.j.following.lastRun[t].start = Date.now()),
        xt("following"),
        r(36, e),
        await Xe(e),
        await ut(2e3),
        r(37, e),
        await ut(2e3),
        s.h(),
        he(this, vn, "m", bn).call(this));
    } catch (t) {
      E(t, "sr150");
    }
  }
  Vt() {
    (clearTimeout(gn.Bt), (gn.Ft = !1));
  }
  async Gt(t) {
    if (0 === t.length)
      return void E(new Error("repeat failed?"), "scr78", "silently");
    const e = (function (t) {
      const e = t[0].author.id;
      if (t.some((t) => t.author.id !== e))
        throw new Error("not all videos share the same author");
      return e;
    })(t);
    if (e !== this.J) return;
    if ((ve(this, pn, !0, "f"), We(he(this, mn, "f"))))
      return (this.Vt(), Nn.Yt(e), void (this.J = ""));
    if (!this.Pt()) {
      t
        .filter(Le)
        .slice(-10)
        .every((t) => Xt.j.following.authorItems[e].inFolder.has(t.id))
        ? this.Wt++
        : (this.Wt = 0);
    }
    (he(this, mn, "f").push(...t),
      ve(this, mn, nn(he(this, mn, "f")), "f"),
      o(16, he(this, mn, "f").length),
      gn.zt(),
      await (async function (t, e) {
        const { inFolder: n, disappeared: i } = Xt.j.following.authorItems[t],
          o = en(e, n, i, Xt.j.videos);
        ((Xt.j.following.authorItems[t].disappeared = o),
          i.size !== o.size &&
            (r(31, { authorId: t, quantity: o.size - i.size }),
            (Sn.Wt = 0),
            xt("following"),
            await Xt.I()));
      })(e, he(this, mn, "f")));
    {
      const t = he(this, mn, "f")[he(this, mn, "f").length - 1],
        n = await tn(e).Tt();
      if (n.items.find((e) => e.id === t.id))
        return ((this.H = n.hasScrolledToBottom), void (await this.qt()));
    }
    const n = dt.k.preferences.maxScroll || 1e3;
    return he(this, mn, "f").length > n
      ? (ve(this, mn, he(this, mn, "f").slice(0, n), "f"),
        (this.H = !0),
        void (await this.qt()))
      : void 0;
  }
  async qt() {
    var t, e, n;
    try {
      if (!this.J) return;
      const i = this.J;
      if (((this.J = ""), this.Vt(), he(this, mn, "f").length > 0))
        ve(this, yn, 0, "f");
      else if (
        (ve(this, yn, ((n = he(this, yn, "f")), ++n), "f"),
        he(this, yn, "f") >= 3)
      )
        return (
          he(this, pn, "f")
            ? E(new Error("three_consecutive_empty_authors"), "scr177")
            : E(new Error("sw not awaken"), "scr233", "silently"),
          void s.u()
        );
      const a = await tn(i).Tt(),
        c = nn(he(this, mn, "f").concat(a.items));
      (r(16, c.length),
        await tn(i).g(c, this.H),
        null ===
          (e = null === (t = c[0]) || void 0 === t ? void 0 : t.author) ||
          void 0 === e ||
          e.uniqueId,
        c.length,
        (async function (t) {
          var e, n;
          const i = Zt.O;
          (Xt.j.following.started.add(t), xt("following"));
          const r = (await tn(t).Tt()).items;
          for (const t of r) on(t, "following");
          null ===
            (n = null === (e = r[0]) || void 0 === e ? void 0 : e.author) ||
            void 0 === n ||
            n.uniqueId;
          for (const [e, n] of r.entries()) {
            if (Zt.C(i, "download videos from one author (old way)")) return;
            if (!Le(n)) continue;
            const a = new un(n, "following");
            if ((!a.$t || (await wn(n, "following"))) && !a.xt) {
              if (a.At()) return void Nn.Yt(t);
              for (; !navigator.onLine;) await ut(1e3);
              (o(17, { total: r.length, current: e + 1 }),
                (re.Z = e + 1),
                a.Nt().catch((t) => E(t, "doa22", "silently")),
                await hn());
            }
          }
          Zt.C(i, "after download author items (old way)") ||
            ((Xt.j.following.lastRun[t].finish = Date.now()),
            xt("following"),
            Sn.H &&
              r.length > 0 &&
              ((Xt.j.following.lastRun[t].bottom = Date.now()),
              xt("following")),
            await ut(2e3),
            await Nn.Yt(t));
        })(i));
    } catch (t) {
      E(t, "scr173");
    }
  }
}),
(mn = new WeakMap()),
(pn = new WeakMap()),
(yn = new WeakMap()),
(vn = new WeakSet()),
(bn = function () {
  ((gn.Ft = !0), gn.Bt && clearTimeout(gn.Bt), kn());
}),
_n)();
var jn, Tn, In, Dn, On, En, Cn, $n, xn, An;
const Nn = new ((An = class {
  constructor() {
    (jn.add(this),
      (this.Jt = 0),
      Tn.set(this, {}),
      (this.Kt = {
        alreadyInArchive: [],
        willAddToArchive: [],
        notInterested: [],
      }),
      In.set(this, []),
      Dn.set(this, []));
  }
  async Qt() {
    try {
      if (he(this, jn, "m", On).call(this));
      else {
        Me.st().catch((t) => {
          E(t, "ll147", "silently");
        });
        const t = await (async function () {
          const t = Zt.O;
          let e = [],
            [n, i] = [0, 0],
            o = 0;
          do {
            if ((await ut(1e3), Zt.C(t, "fetch followed authors (old way)")))
              return null;
            const a = new Se("following")
              .wt({ maxCursor: n, minCursor: i })
              .ht(0 === n ? 10 : 20);
            try {
              for (; !navigator.onLine;) await ut(1e3);
              const t = await window.fetch(a.bt(), { credentials: "include" }),
                { err: o, json: s } = await ce(t, "fa29");
              if (o) throw o;
              const { statusCode: c, userList: l } = s;
              if (0 != c)
                throw new Error(
                  `Err fetching followed users, ${JSON.stringify(s)}`,
                );
              if (
                ((e = (l || []).concat(e)),
                ({ maxCursor: n, minCursor: i } = s),
                r(13, { currentTotal: e.length }),
                "number" != typeof n || "number" != typeof i)
              )
                throw new Error(
                  "Things have changed? Author cursor is no longer number?",
                );
            } catch (t) {
              if ((o++, o <= 3)) continue;
              throw t;
            }
            if (((o = 0), 0 === e.length)) return [];
          } while ("-1" !== String(n) && "-1" !== String(i));
          return e;
        })();
        if (!t) return;
        if (!Ue.kt)
          throw new Error(
            "resync is not ready - this should be a one-time error, reload to fix.",
          );
        const e = t.map($e);
        (ve(
          this,
          In,
          e.map((t) => t.id),
          "f",
        ),
          e.forEach((t) => {
            var e;
            t.lastChecked =
              (null === (e = Xt.j.following.lastRun[t.id]) || void 0 === e
                ? void 0
                : e.finish) || 0;
          }),
          ve(this, Tn, Ee("id")(e), "f"));
      }
      r(14, {
        authorDict: he(this, Tn, "f"),
        officialList: he(this, In, "f"),
        started: [...Xt.j.following.started],
        notInterested: [...Xt.j.following.notInterested],
      });
    } catch (t) {
      E(t, "ff27");
    }
  }
  async Xt(t) {
    (location.pathname.includes("@") && (Re(), await ut(3e3)),
      o(20, "following"),
      (this.Kt = t),
      (Xt.j.following.notInterested = new Set(t.notInterested)),
      xt("following"));
    const e = [...t.willAddToArchive, ...t.alreadyInArchive].sort((t, e) => {
      var n, i;
      return (
        ((null === (n = Xt.j.following.lastRun[t]) || void 0 === n
          ? void 0
          : n.finish) || 0) -
        ((null === (i = Xt.j.following.lastRun[e]) || void 0 === i
          ? void 0
          : i.finish) || 0)
      );
    });
    (ve(
      this,
      Dn,
      e.map((t) => ({ authorId: t, status: "queued" })),
      "f",
    ),
      dt.S &&
        (ve(
          this,
          Dn,
          he(this, Dn, "f").filter((t) => {
            var e;
            const n =
              (null === (e = Xt.j.following.lastRun[t.authorId]) || void 0 === e
                ? void 0
                : e.finish) || 0;
            return (Date.now() - n) / 1e3 / 60 / 60 / 24 > 5;
          }),
          "f",
        ),
        he(this, Dn, "f").length > 150 && (he(this, Dn, "f").length = 150)),
      await Xt.I(),
      he(this, jn, "m", $n).call(this),
      await he(this, jn, "m", En).call(this));
  }
  async Yt(t) {
    try {
      he(this, jn, "m", $n).call(this, "maybe");
      const e = he(this, Dn, "f").find((e) => e.authorId === t);
      (e && (e.status = "finished"),
        await Xt.catchUp(),
        await he(this, jn, "m", En).call(this));
    } catch (t) {
      E(t, "ff101");
    }
  }
}),
(Tn = new WeakMap()),
(In = new WeakMap()),
(Dn = new WeakMap()),
(jn = new WeakSet()),
(On = function () {
  if (!(Object.keys(he(this, Tn, "f")).length > 0)) return !1;
  return !Object.values(he(this, Tn, "f")).some(qe);
}),
(En = async function () {
  var t, e;
  if (Zt.C(this.Jt, "move from author to author (old way)")) return;
  const n = he(this, Dn, "f").find((t) => "queued" === t.status);
  if (n) {
    n.status = "current";
    const i = he(this, Tn, "f")[n.authorId].uniqueId;
    (o(15, he(this, Dn, "f")),
      (t = Xt.j.following.authorItems)[(e = n.authorId)] ||
        (t[e] = { inFolder: new Set(), disappeared: new Set() }),
      xt("following"),
      await Sn.Ht(n.authorId, i),
      r(29, {
        authorId: n.authorId,
        count: Xt.j.following.authorItems[n.authorId].inFolder.size,
      }));
  } else {
    if (Zt.C(this.Jt, "after move from author to author (old way)")) return;
    he(this, jn, "m", xn).call(this);
  }
}),
(Cn = function () {
  const {
    officialAuthorList: t,
    started: e,
    notInterested: n,
  } = Xt.j.following;
  return {
    numFollowed: t.size,
    numStarted: e.size,
    numNotInterested: n.size,
    numCappedOut: [...t].filter((t) => !e.has(t)).filter((t) => !n.has(t))
      .length,
  };
}),
($n = function (t) {
  (t && Math.random() > 0.2) || o(22, he(this, jn, "a", Cn));
}),
(xn = async function () {
  (o(15, he(this, Dn, "f")), o(18, he(this, jn, "a", Cn)), s.u(), Xt.D());
}),
An)();
function Ln(t, n, i) {
  e.postMessage({
    type: "compare",
    payload: { myUrl: t, officialUrl: n, category: i },
  });
}
function Fn(t) {
  const { category: e, payload: n } = t.data;
  if ("official_tiktok_likes" === e) {
    Ln(new Se("likes").ft("0").ht(16).bt(), n.officialUrl, e);
  }
  if ("official_tiktok_followed_authors" === e) {
    Ln(
      new Se("following").wt({ maxCursor: 0, minCursor: 0 }).ht(30).bt(),
      n.officialUrl,
      e,
    );
  }
  if ("official_tiktok_author_items" === e) {
    Ln(
      new Se("authorItems")
        .ft("0")
        .ht(16)
        .vt("whatever_the_authors_secUid_is")
        .bt(),
      n.officialUrl,
      e,
    );
  }
  if ("official_tiktok_bookmarked" === e) {
    Ln(new Se("bookmarked").ft("0").ht(16).bt(), n.officialUrl, e);
  }
}
function Bn(t, e) {
  const n = new Set(e);
  for (let i = t.length - 1; i >= 0; i--) {
    const o = t[i];
    if (n.has(o)) {
      const n = e.indexOf(o);
      return t.concat(e.slice(n + 1));
    }
  }
  return t.concat(e);
}
let Mn = Date.now();
async function Un(t) {
  const e = Date.now() - Mn;
  if (e < t) {
    const n = t - e;
    await ut(n);
  }
  Mn = Date.now();
}
let Rn = !1;
var zn, Jn, Wn, qn;
const Pn = [];
let Hn = 0;
const Vn = {
  Zt: 0,
  te() {
    const t = new Set(Xt.j.bookmarked.officialList);
    let e = 0;
    for (const n of Xt.j.bookmarked.downloaded) t.has(n) || e++;
    return e;
  },
  ee() {
    r(41, { numDownloadedThenDisappeared: this.te() });
  },
  ne() {
    r(41, { newDeletionDetected: this.te() - this.Zt });
  },
};
async function* Gn() {
  ((Pn.length = 0), (Hn = 0), (Vn.Zt = Vn.te()));
  for await (const t of (async function* () {
    var t, e;
    const n = Zt.O;
    Rn = !1;
    let i = "0",
      o = !0;
    const a = { ie: 0, oe: 0, re: 0, ae: 0 };
    for (;;) {
      await Un(5e3);
      const s = new Se("bookmarked").ft(i).ht(16);
      let c = [],
        l = {};
      try {
        for (; !navigator.onLine;) await ut(1e3);
        if (Zt.C(n, "scroll down bookmarked")) break;
        const i = await window.fetch(s.bt(), { credentials: "include" });
        let o = null;
        if ((({ err: o, json: l } = await ce(i, "hec800")), o)) throw o;
        if (
          (an.It(l.itemList, "bookmarked"),
          (c =
            null ===
              (e =
                null === (t = l.itemList) || void 0 === t ? void 0 : t.map) ||
            void 0 === e
              ? void 0
              : e.call(t, Ce)),
          0 != l.statusCode)
        )
          throw new Error("Yzy056" + JSON.stringify(l));
      } catch (t) {
        if ((a.ie++, a.ie <= 3)) {
          await ut(7e3 * a.ie);
          continue;
        }
        if (!l.cursor || l.cursor == i) {
          if (t.message.includes("hec800")) {
            (r(46, !0), await ut(3e5), r(46, !1));
            continue;
          }
          E(t, "Chv322");
          break;
        }
      }
      if (
        ((a.ie = 0),
        r(46, !1),
        !l.hasMore || ("0" != l.cursor && "-1" != l.cursor))
      )
        a.ae = 0;
      else if (
        (E(
          new Error(`cursor is ${l.cursor} but hasMore is ${l.hasMore}`),
          "Uhb368",
          "silently",
        ),
        a.ae++,
        a.ae < 3)
      )
        continue;
      if (c) {
        const t = c.some((t) => !Le(t));
        if ((!t && a.re > 0 && a.re--, t)) {
          if ((a.oe++, a.oe < 3 && a.re < 3)) {
            await ut(3e3 * a.oe);
            continue;
          }
          a.re++;
        }
        if (
          ((a.oe = 0), 0 === c.filter(Le).length && c.length > 9 && a.re > 10)
        ) {
          E(
            new Error(
              "some component in the tiktok server is temporarily unstable. Wait a few hours and try again.",
            ),
            "Mar695",
          );
          break;
        }
        (l.total &&
          (r(41, { historicTotal: l.total }),
          (Xt.j.bookmarked.total = l.total)),
          yield c.filter(Ne));
      }
      if (
        (({ cursor: i, hasMore: o } = l),
        !o && "0" == i && (Rn = !0),
        "-1" == i && E(new Error("cursor is -1"), "Swa471", "silently"),
        "0" == i || "-1" == i || !i)
      )
        break;
    }
  })()) {
    (Pn.push(...t), r(41, { scrolledTo: Pn.length }));
    for (const e of t) on(e, "bookmarked");
    await Yn(Pn);
    for (const e of t) (Hn++, yield e);
  }
}
async function Yn(t) {
  const e = Xt.j.bookmarked.officialList.length;
  ((Xt.j.bookmarked.officialList = Bn(
    t.map((t) => t.id),
    Xt.j.bookmarked.officialList,
  )),
    e !== Xt.j.bookmarked.officialList.length &&
      (Vn.ne(), xt("bookmarked"), await Xt.I()));
}
const Kn = new ((qn = class {
  constructor() {
    zn.add(this);
  }
  async Qt() {
    const t = Zt.O;
    await he(this, zn, "m", Jn).call(this);
    for await (const e of Gn()) {
      if (!Le(e)) continue;
      const n = new un(e, "bookmarked");
      if ((!n.$t || (await wn(e, "bookmarked"))) && !n.xt) {
        for (; !navigator.onLine;) await ut(1e3);
        if (Zt.C(t, "download bookmarked one by one")) return;
        if (
          (r(41, { nowAt: Hn }),
          (re.Z = Hn),
          n.Nt().catch((t) => E(t, "Shc782", "silently")),
          await hn(),
          !Ue.kt)
        )
          return void E(new Error("resync is not ready"), "Jsy087");
      }
    }
    Zt.C(t, "after download bookmarked items") ||
      he(this, zn, "m", Wn).call(this);
  }
}),
(zn = new WeakSet()),
(Jn = async function () {
  ((Xt.j.bookmarked.lastRun.start = Date.now()),
    xt("bookmarked"),
    r(41, {
      subView: "downloading",
      scrolledTo: 0,
      showNowAt: !1,
      numLocalMp4: Xt.j.bookmarked.downloaded.size,
    }),
    o(20, "bookmarked"),
    await ut(4e3));
}),
(Wn = async function () {
  (Rn &&
    ((Xt.j.bookmarked.lastRun.finish = Date.now()),
    (Xt.j.bookmarked.numDisappeared = Xt.j.bookmarked.total - Pn.length)),
    Vn.ee(),
    xt("bookmarked"),
    r(41, { subView: "done" }),
    Xt.catchUp(),
    Xt.D());
  o(54, {
    officialListLength: Xt.j.bookmarked.officialList.length,
    numMp4InLocalFolder: Xt.j.bookmarked.downloaded.size,
  });
}),
qn)();
async function Qn() {
  await ut(2500);
}
const Xn = {
    Pt() {
      const t = Xt.j.following.lastRun[re.R.J.W].bottom,
        { bottomNoMoreOftenThanDays: e, randomize: n } = dt.k.preferences,
        i = 24 * e * 60 * 60 * 1e3,
        o = Date.now() - t;
      if (!n) return o > i;
      if (o < i / 2) return !1;
      const r = (o - i / 2) / (i / 2),
        a = String(t).slice(-3);
      return Number(a) / 1e3 < r;
    },
    shouldScrollMore() {
      return (
        !!this.Pt() || Date.now() - re.R.J.P < 6e3 || !re.R.V.K || !!re.R.V.Y
      );
    },
  },
  Zn = {
    currentAuthorId: "",
    se: "normal",
    ce: "",
    le: 0,
    ue: 0,
    de: 0,
    async fe(t) {
      (await ut(1e3 * t), this.le++, (this.se = "normal"));
    },
    async we(t) {
      (await ut(1e3 * t),
        this.ue++,
        (Xt.j.following.lastRun[this.currentAuthorId].finish = Date.now()),
        xt("following"),
        Xt.I());
    },
    F(t) {
      switch (
        (["flawless_bunch", "new_author_begins"].includes(t) ||
          E(new Error(t), "Yzn586", "silently"),
        t)
      ) {
        case "new_author_begins":
          return ((this.le = 0), void (this.se = "normal"));
        case "flawless_bunch":
          return (
            (this.se = "normal"),
            (this.de = 0),
            (this.le = 0),
            void (this.ue = 0)
          );
        case "captcha":
          return void (0 === this.le
            ? (this.se = "retry")
            : this.le >= 1 && 0 === this.ue
              ? (this.se = "skipAuthor")
              : this.le >= 1 && this.ue >= 1 && ((this.se = "pause"), r(42)));
        case "captcha_solved":
          return void (this.se = "normal");
        case "other_fetch_error":
        case "request_blocked":
        case "valid_json_containing_error":
        case "empty_response":
          return void (this.le < 2
            ? (this.se = "retry")
            : this.le >= 2 && this.ue <= 1
              ? (this.se = "skipAuthor")
              : this.le >= 2 &&
                this.ue >= 2 &&
                ((this.ce = `Dyb767 ${t}`), (this.se = "throw")));
        case "flawed_items":
          return (
            this.de,
            this.de++,
            void (this.de <= 3 ? (this.se = "retry") : (this.se = "normal"))
          );
        case "all_items_flawed":
          return void (this.de <= 6
            ? (this.se = "normal")
            : this.ue <= 2
              ? (this.de, (this.se = "skipAuthor"))
              : ((this.ce =
                  "Mcy770 all items flawed and 3 authors skipped in a row"),
                (this.se = "throw")));
      }
    },
  };
const ti = [];
let ei;
async function* ni(t) {
  ((ti.length = 0), (ei = 0));
  const e = (async function* (t) {
    var e, n, i, o, a, s;
    const c = Zt.O;
    let l = "0",
      u = !0,
      d = 0;
    for (Zn.currentAuthorId = t.id, Zn.F("new_author_begins"); ;) {
      if ((await Un(7e3), !Xn.shouldScrollMore())) return;
      const f = new Se("authorItems").ht(16).ft(l).vt(t.secUid);
      ((re.R.J.q = t.secUid), (re.R.V.G = l));
      let w = [],
        h = {};
      try {
        for (; !navigator.onLine;) await ut(1e3);
        for (; "pause" === Zn.se;) await ut(1e3);
        if (Zt.C(c, "scroll down one author")) return;
        const t = await fetch(f.bt(), { credentials: "include" });
        let a = null;
        if ((({ err: a, json: h } = await ce(t, "Fru804")), a)) {
          const t = a.message.includes("no response at all"),
            s = "{}" === JSON.stringify(h),
            c =
              (null ===
                (n =
                  null === (e = a.message) || void 0 === e
                    ? void 0
                    : e.includes) || void 0 === n
                ? void 0
                : n.call(e, '"statusCode":200')) &&
              (null ===
                (o =
                  null === (i = a.message) || void 0 === i
                    ? void 0
                    : i.includes) || void 0 === o
                ? void 0
                : o.call(i, '"contentLength":"0"')),
            l = a.message.includes("429");
          if (c) {
            if ((Zn.F("captcha"), "pause" === Zn.se)) {
              Ze();
              continue;
            }
          } else {
            if (l) {
              (r(45, !0), await ut(d++ < 30 ? 6e4 : 2e5), r(45, !1));
              continue;
            }
            s
              ? Zn.F("empty_response")
              : t
                ? Zn.F("request_blocked")
                : Zn.F("other_fetch_error");
          }
          if ("retry" === Zn.se) {
            await Zn.fe(7);
            continue;
          }
          if ("skipAuthor" === Zn.se) return void (await Zn.we(7));
          if ("throw" === Zn.se) return void E(a, Zn.ce || "Onn977");
          continue;
        }
      } catch (t) {}
      if (
        ((d = 0),
        (w =
          null ===
            (s = null === (a = h.itemList) || void 0 === a ? void 0 : a.map) ||
          void 0 === s
            ? void 0
            : s.call(a, Ce)),
        0 != h.statusCode)
      ) {
        if ((Zn.F("valid_json_containing_error"), "retry" === Zn.se)) {
          await Zn.fe(10);
          continue;
        }
        const t = Boolean(
          h.cursor && "0" != h.cursor && "-1" != h.cursor && h.cursor != l,
        );
        if ((t && (Zn.se = "normal"), "skipAuthor" === Zn.se && !t))
          return void (await Zn.we(10));
        if ("throw" === Zn.se && !t) {
          let t = `${Zn.ce}`;
          return void (h.itemList
            ? ((t += `statusCode ${h.statusCode}, has itemList`),
              E(new Error(t), "Pxv309"))
            : ((t += JSON.stringify(h)), E(new Error(t), "Oxa972")));
        }
      }
      if (w) {
        an.It(h.itemList, "following");
        const e = w.some((t) => !Le(t));
        if ((e && Zn.F("flawed_items"), "retry" === Zn.se)) {
          await Zn.fe(10);
          continue;
        }
        w.length > 2 && !e && Zn.F("flawless_bunch");
        {
          const t = w.filter(Le);
          if (
            (w.length > 5 && 0 === t.length && Zn.F("all_items_flawed"),
            "skipAuthor" === Zn.se)
          )
            return void (await Zn.we(10));
          if ("throw" === Zn.se) return void E(new Error(Zn.ce), "Vna097");
        }
        const n = w.filter(Ne),
          i = n[n.length - 1],
          o = Xt.j.following.authorItems[t.id].inFolder.has(
            null == i ? void 0 : i.id,
          );
        ((re.R.V.K = o), yield n);
      }
      if ((({ cursor: l, hasMore: u } = h), "0" == l || "-1" == l || !l))
        return ((re.R.J.H = !0), void (await ut(1e4)));
    }
  })(t);
  for (;;) {
    const n = ti[ei];
    if (n) (yield n, ei++);
    else {
      const n = dt.k.preferences.maxScroll || 1e3;
      if (ti.length >= n) {
        re.R.J.H = !0;
        break;
      }
      const i = await e.next();
      if (i.done) break;
      (ti.push(...i.value), r(38, ti.length));
      for (const t of i.value) on(t, "following");
      try {
        oi(t.id, ti);
      } catch (t) {
        E(t, "dfo34", "silently");
      }
    }
  }
}
async function ii(t) {
  var e, n, i, o;
  const a = Zt.O;
  if (
    (Xt.j.following.started.add(t.id),
    (e = Xt.j.following.authorItems)[(n = t.id)] ||
      (e[n] = { inFolder: new Set(), disappeared: new Set() }),
    (i = Xt.j.following.lastRun)[(o = t.id)] ||
      (i[o] = {
        start: 0,
        finish: 0,
        bottom: 0,
        firstAdded: new Date().setHours(0, 0, 0, 0),
      }),
    (Xt.j.following.lastRun[t.id].start = Date.now()),
    xt("following"),
    r(36, t.uniqueId),
    await ut(2500),
    r(37, t.uniqueId),
    await ut(2500),
    r(38, 0),
    await ut(1500),
    r(29, {
      authorId: t.id,
      count: Xt.j.following.authorItems[t.id].inFolder.size,
    }),
    await ut(500),
    !Zt.C(a, "scroll this author"))
  ) {
    if (
      ((re.R.J.W = t.id),
      (re.R.J.H = !1),
      (re.R.J.P = Date.now()),
      (re.R.V.Y = !1),
      (re.R.V.K = !1),
      !t.privateAccount)
    )
      for await (const e of ni(t)) {
        if (t.id !== e.author.id) {
          (t.nickname, e.author.nickname);
          continue;
        }
        if (re.et > 5)
          return (
            (Xt.j.following.lastRun[t.id].finish = Date.now()),
            re.nt.add(t.id),
            void (
              re.nt.size >= 3 &&
              E(
                new Error(
                  "Need to pause - tiktok server rejected video downloading for 3 accounts in a row",
                ),
                "Qot679",
              )
            )
          );
        if (Zt.C(a, "download mp4 from one author")) return;
        if (!Le(e)) continue;
        const n = new un(e, "following");
        if ((!n.$t || (await wn(e, "following"))) && !n.xt) {
          for (; !navigator.onLine;) await ut(1e3);
          (r(39, ei + 1),
            (re.Z = ei + 1),
            n.Nt().catch((t) => E(t, "dfo96", "silently")),
            await hn());
        }
      }
    Zt.C(a, "after download author items") ||
      (re.R.J.H && (Xt.j.following.lastRun[t.id].bottom = Date.now()),
      t.nickname,
      (Xt.j.following.lastRun[t.id].finish = Date.now()),
      xt("following"),
      Xt.catchUp());
  }
}
function oi(t, e) {
  if (!Xt.j.following.authorItems[t]) return;
  re.R.V.Y = !1;
  const { inFolder: n, disappeared: i } = Xt.j.following.authorItems[t],
    o = en(e, n, i, Xt.j.videos);
  ((Xt.j.following.authorItems[t].disappeared = o),
    i.size !== o.size &&
      (r(31, { authorId: t, quantity: o.size - i.size }),
      (re.R.V.Y = !0),
      xt("following")));
}
async function ri(t) {
  try {
    const e = await fetch(t),
      n = e.headers.get("Content-Type");
    if (!(null == n ? void 0 : n.startsWith("image")))
      throw new Error(`avatar type is ${n}, url ${t}`);
    const i = await e.blob();
    return { err: null, blob: i, blobSize: i.size };
  } catch (t) {
    return { err: t, blob: null, blobSize: 0 };
  }
}
const ai = {};
const si = j(function () {
  (Object.keys(ai).length,
    Object.entries(ai).forEach(async ([t, e]) => {
      try {
        const n = await x(Xt.p, `data/Following/Avatars/${t}`),
          i = await n.createWritable();
        (delete ai[t], await i.write(e), await i.close());
      } catch (t) {
        E(t, "Fwc167", "silently");
      }
    }));
}, 1e4);
function ci(t, e) {
  ((ai[t] = e), si());
}
const li = {},
  ui = [];
let di = !1;
const fi = [];
let wi = !1;
function hi(t) {
  Array.isArray(t) &&
    (t.forEach((t) => {
      var e;
      const n =
        null === (e = null == t ? void 0 : t.user) || void 0 === e
          ? void 0
          : e.id;
      Number(n) &&
        ((li[n] = {
          small: t.user.avatarThumb,
          large: t.user.avatarLarger,
          nickname: t.user.nickname,
        }),
        ui.push(n),
        li[n].small);
    }),
    (async function () {
      if (di) return;
      di = !0;
      try {
        for (;;) {
          const t = ui.shift();
          if (!t) break;
          await vi(t);
        }
      } catch (t) {
        E(t, "Mxv433");
      } finally {
        di = !1;
      }
    })());
}
async function vi(t) {
  try {
    if (!li[t]) return (ui.push(t), void (await ut(200)));
    const { nickname: e, small: n } = li[t];
    if (!n) return;
    if ("GCed" === n) return;
    const i = `small_${t}.jpg`;
    let o = !1;
    const r = await x(Xt.p, `data/Following/Avatars/${i}`, !1),
      a = await (null == r ? void 0 : r.getFile()),
      s = (null == a ? void 0 : a.size) || 0;
    if ((0 == s && (o = !0), s > 0)) {
      const t = (null == a ? void 0 : a.lastModified) || 0,
        e = 864e5,
        n = (Date.now() - t) / e,
        i = n / 100;
      Math.random() < i && (Math.round(n), (o = !0));
    }
    if (!o) return ((li[t].small = "GCed"), void (li[t].large = "GCed"));
    const { err: c, blob: l, blobSize: u } = await ri(n);
    if (c) return void E(c, "Lto224", "silently");
    (u !== s &&
      (fi.push(t),
      (async function () {
        if (!wi) {
          wi = !0;
          try {
            for (;;) {
              const t = fi.shift();
              if (!t) break;
              await mi(t);
            }
          } catch (t) {
            E(t, "Uss122");
          } finally {
            wi = !1;
          }
        }
      })()),
      ci(i, l),
      (li[t].small = "GCed"),
      await ut(100));
  } catch (t) {
    E(t, "Dxv877", "silently");
  }
}
async function mi(t) {
  try {
    if (!li[t])
      return (
        E(new Error(`author data not fetched yet: ${t}`), "Zos284", "silently"),
        void (await ut(100))
      );
    const { nickname: e, large: n } = li[t];
    if (!n) return;
    if ("GCed" === n) return;
    const { err: i, blob: o } = await ri(n);
    if (i) return void E(i, "Xbv915", "silently");
    (ci(`large_${t}.jpg`, o), (li[t].large = "GCed"), await ut(1500));
  } catch (t) {
    E(t, "Hxx447", "silently");
  }
}
const pi = {
  async _() {
    try {
      const t = dt.k.profile.uid,
        e = await ct;
      return await e.get("following", t);
    } catch (t) {
      return void E(t, "Zmk787", "silently");
    }
  },
  async he(t) {
    const e = await ct,
      n = dt.k.profile.uid;
    return e.put("following", t, n);
  },
};
let yi = !1,
  bi = [];
const _i = { officialList: [], authorDict: {} };
async function gi() {
  r(50, {
    started: [...Xt.j.following.started],
    notInterested: [...Xt.j.following.notInterested],
  });
  const t = await pi._();
  (t ? setTimeout(() => r(49), 100) : r(48),
    yi ||
      (!(function (t) {
        ((yi = !0),
          t &&
            (t.forEach((t) => {
              var e;
              t.lastChecked =
                (null === (e = Xt.j.following.lastRun[t.id]) || void 0 === e
                  ? void 0
                  : e.finish) || 0;
            }),
            (_i.officialList = t.map((t) => t.id)),
            (_i.authorDict = Ee("id")(t)),
            r(51, _i)));
      })(t),
      await (async function () {
        let [t, e] = [0, 0],
          i = 0,
          o = !0;
        for (;;) {
          await Un(4e3);
          const a = new Se("following")
            .wt({ maxCursor: t, minCursor: e })
            .ht(30);
          try {
            for (; !navigator.onLine;) await ut(1e3);
            const i = await window.fetch(a.bt(), { credentials: "include" }),
              { err: s, json: c } = await ce(i, "Uaq119");
            if (s) throw s;
            const { statusCode: l, userList: u, total: d } = c;
            if (0 != l) {
              let t;
              throw (
                (t =
                  10101 == l && 0 == c.status_code
                    ? "Temporary error on the TikTok server, please try again in a few hours."
                    : "Error fetching followed users."),
                new Error(`${t} ${JSON.stringify(c)}`)
              );
            }
            (Array.isArray(u) && (ki(u), d && r(33, d)),
              n.truncateFollowingList.end &&
                (bi.length, n.truncateFollowingList.end),
              ({ maxCursor: t, minCursor: e, hasMore: o } = c));
            const f = 0 == e || -1 == e || !e;
            if (f) break;
          } catch (t) {
            if ((i++, i <= 3)) continue;
            throw t;
          }
          i = 0;
        }
        Si();
      })(),
      Si()));
}
function ki(t) {
  (hi(t), t.forEach(ji));
  const e = t.map($e).filter((t) => Boolean(Number(t.id) && t.secUid));
  (e.forEach((t) => {
    var e;
    ((t.lastChecked =
      (null === (e = Xt.j.following.lastRun[t.id]) || void 0 === e
        ? void 0
        : e.finish) || 0),
      (_i.authorDict[t.id] = t));
  }),
    (bi = bi.concat(e)));
  const i = bi.map((t) => t.id).slice(n.truncateFollowingList.start);
  ((_i.officialList = Bn(i, _i.officialList)),
    r(13, { currentTotal: bi.length }),
    r(51, _i),
    (Xt.j.following.officialAuthorList = new Set(_i.officialList)),
    xt("following"));
}
async function Si() {
  (await ut(300), r(52, _i), pi.he(bi), Xt.I());
}
function ji(t) {
  var e;
  if (!Number(null === (e = t.user) || void 0 === e ? void 0 : e.id)) return;
  const {
      id: n,
      uniqueId: i,
      nickname: o,
      signature: r,
      privateAccount: a,
    } = t.user,
    { followerCount: s, videoCount: c, heartCount: l } = t.stats,
    u = Xt.j.authors[n],
    d = {
      uniqueIds: [i],
      nicknames: [o],
      followerCount: s || (null == u ? void 0 : u.followerCount) || 0,
      heartCount: l || (null == u ? void 0 : u.heartCount) || 0,
      videoCount: c || (null == u ? void 0 : u.videoCount) || 0,
      signature: r || (null == u ? void 0 : u.signature) || "",
      privateAccount: a || (null == u ? void 0 : u.privateAccount) || !1,
    };
  (u &&
    ((d.uniqueIds = [...new Set([i, ...u.uniqueIds])]),
    (d.nicknames = [...new Set([o, ...u.nicknames])])),
    (Xt.j.authors[n] = d),
    xt("authors"));
}
async function Ti(t) {
  try {
    let e = await Xt.p.getDirectoryHandle("data");
    ((e = await e.getDirectoryHandle("Following")),
      await e.removeEntry(t, { recursive: !0 }));
  } catch (t) {
    E(t, "Okh543", "silently");
  }
}
let Ii = [],
  Di = [];
function Oi() {
  const {
    officialAuthorList: t,
    started: e,
    notInterested: n,
  } = Xt.j.following;
  return {
    numFollowed: t.size,
    numStarted: e.size,
    numNotInterested: n.size,
    numCappedOut: [...t].filter((t) => !e.has(t)).filter((t) => !n.has(t))
      .length,
  };
}
function Ei(t) {
  (t && Math.random() > 0.2) || o(22, Oi());
}
function Ci() {
  (o(20, "following"),
    (Ii = Di.sort((t, e) => {
      var n, i;
      return (
        ((null === (n = Xt.j.following.lastRun[t]) || void 0 === n
          ? void 0
          : n.finish) || 0) -
        ((null === (i = Xt.j.following.lastRun[e]) || void 0 === i
          ? void 0
          : i.finish) || 0)
      );
    }).map((t) => ({ authorId: t, status: "queued" }))),
    (async function () {
      const t = Zt.O;
      for (;;) {
        if (Zt.C(t, "move from author to author")) return;
        0 === Ii.length && o(15, Ii);
        const e = Ii.find((t) => "queued" === t.status);
        if (!e) break;
        if (!_i.officialList.includes(e.authorId)) {
          e.status = "finished";
          continue;
        }
        ((e.status = "current"), o(15, Ii));
        const n = _i.authorDict[e.authorId];
        try {
          (await ii(n), await Qn());
        } catch (t) {
          E(t, "ff96", "silently");
        }
        ((e.status = "finished"), Ei("maybe"));
      }
      Zt.C(t, "after moving from author to author") || (o(18, Oi()), Xt.D());
    })().catch((t) => E(t, "Ktj412")));
}
const $i = {
  async Qt() {
    gi().catch((t) => E(t, "Qze176"));
  },
  async Xt(t) {
    const { userSelections: e, officialList: i } = t;
    ((Xt.j.following.notInterested = new Set(e.notInterested)),
      xt("following"),
      await Xt.I(),
      Ei(),
      (async function (t, e) {
        var n, i, o;
        for (const r of e)
          try {
            if (t.alreadyInArchive.includes(r)) continue;
            if (t.willAddToArchive.includes(r)) continue;
            (Xt.j.following.started.has(r) ||
              (null ===
                (o =
                  null ===
                    (i =
                      null === (n = Xt.j.following.authorItems) || void 0 === n
                        ? void 0
                        : n[r]) || void 0 === i
                    ? void 0
                    : i.inFolder) || void 0 === o
                ? void 0
                : o.size)) &&
              (Xt.j.following.started.delete(r),
              delete Xt.j.following.authorItems[r],
              xt("following"),
              await Ti(r));
          } catch (t) {
            E(t, "Fvt078", "silently");
          }
        Xt.I();
      })(e, i),
      Ue.kt ||
        E(
          new Error(
            "resync is not ready - this should be a one-time error, reload to fix.",
          ),
          "Mrx148",
        ),
      Object.values(_i.authorDict).forEach((t) => {
        var e;
        t.lastChecked =
          (null === (e = Xt.j.following.lastRun[t.id]) || void 0 === e
            ? void 0
            : e.finish) || 0;
      }),
      r(51, _i),
      (Di = [...e.willAddToArchive, ...e.alreadyInArchive]),
      e.alreadyInArchive.length > 40 && n.allowSkipRecentlyVisitedAuthors
        ? r(44, Di)
        : Ci());
  },
  ve(t) {
    (t.length, (Di = t), Ci());
  },
};
let xi = !1,
  Ai = !1;
var Ni, Li, Fi, Bi, Mi;
const Ui = [];
let Ri = 0;
const zi = {
  Zt: 0,
  te() {
    const t = new Set(Xt.j.likes.officialList);
    let e = 0;
    for (const n of Xt.j.likes.downloaded) t.has(n) || e++;
    return e;
  },
  ee() {
    r(30, this.te());
  },
  ne() {
    r(32, this.te() - this.Zt);
  },
};
async function* Ji() {
  ((Ui.length = 0), (Ri = 0), (zi.Zt = zi.te()));
  for await (const t of (async function* () {
    var t, e;
    const n = Zt.O;
    xi = !1;
    let i = "0",
      o = !0;
    const a = { ie: 0, oe: 0, re: 0, ae: 0 };
    for (;;) {
      await Un(5e3);
      const s = new Se("likes").ft(i).ht(16);
      let c = [],
        l = {};
      try {
        for (; !navigator.onLine;) await ut(1e3);
        if (Zt.C(n, "scroll down likes")) break;
        const i = await window.fetch(s.bt(), { credentials: "include" });
        let o = null;
        if ((({ err: o, json: l } = await ce(i, "gab45")), o)) throw o;
        if (
          (an.It(l.itemList, "likes"),
          (c =
            null ===
              (e =
                null === (t = l.itemList) || void 0 === t ? void 0 : t.map) ||
            void 0 === e
              ? void 0
              : e.call(t, Ce)),
          0 != l.statusCode)
        ) {
          if ("verify" === l.type) {
            E(new Error("need to solve captcha"), "fl39");
            break;
          }
          throw new Error(`code: ${l.code} ${l.type}`);
        }
      } catch (t) {
        if ((a.ie++, a.ie <= 3)) {
          await ut(7e3 * a.ie);
          continue;
        }
        if (!l.cursor || l.cursor == i) {
          if (t.message.includes("gab45")) {
            (Ai ||
              E(t, "Gqh894 tiktok server rejects requisition of Likes list"),
              r(46, !0),
              await ut(3e5),
              r(46, !1));
            continue;
          }
          E(t, "Yzu175");
          break;
        }
      }
      if (
        ((a.ie = 0),
        r(46, !1),
        !l.hasMore || ("0" != l.cursor && "-1" != l.cursor))
      )
        a.ae = 0;
      else if (
        (E(
          new Error(`cursor is ${l.cursor} but hasMore is ${l.hasMore}`),
          "Kpd036",
          "silently",
        ),
        a.ae++,
        a.ae < 3)
      )
        continue;
      if (c) {
        Ai = !0;
        const t = c.some((t) => !Le(t));
        if ((!t && a.re > 0 && a.re--, t)) {
          if ((a.oe++, a.oe < 3 && a.re < 3)) {
            await ut(3e3 * a.oe);
            continue;
          }
          a.re++;
        }
        if (
          ((a.oe = 0), 0 === c.filter(Le).length && c.length > 9 && a.re > 10)
        ) {
          E(
            new Error(
              "some component in the tiktok server is temporarily unstable. Wait a few hours and try again.",
            ),
            "Xjo996",
          );
          break;
        }
        yield c.filter(Ne);
      }
      if (
        (({ cursor: i, hasMore: o } = l),
        !o && "0" == i && (xi = !0),
        "-1" == i && E(new Error("cursor is -1"), "Etr208", "silently"),
        "0" == i || "-1" == i || !i)
      )
        break;
    }
  })()) {
    (Ui.push(...t), r(25, Ui.length));
    for (const e of t) on(e, "liked");
    await Wi(Ui);
    for (const e of t) (Ri++, yield e);
  }
}
async function Wi(t) {
  const e = Xt.j.likes.officialList.length;
  ((Xt.j.likes.officialList = Bn(
    t.map((t) => t.id),
    Xt.j.likes.officialList,
  )),
    e !== Xt.j.likes.officialList.length &&
      (zi.ne(), xt("mainOrLikes"), await Xt.I()));
}
const qi = new ((Mi = class {
  constructor() {
    Ni.add(this);
  }
  async Qt() {
    const t = Zt.O;
    await he(this, Ni, "m", Fi).call(this);
    let e = !1;
    for await (const n of Ji()) {
      if (!Le(n)) continue;
      const i = new un(n, "liked");
      if (!e && (!i.$t || (await wn(n, "liked"))) && !i.xt)
        if (he(this, Ni, "a", Li)) ((e = !0), r(24, "downloading(capped)"));
        else {
          for (; !navigator.onLine;) await ut(1e3);
          if (Zt.C(t, "loop download liked items")) return;
          if (
            (r(26, Ri),
            (re.Z = Ri),
            i.Nt().catch((t) => E(t, "ll107", "silently")),
            await hn(),
            !Ue.kt)
          )
            return void E(new Error("resync is not ready"), "ll88");
        }
    }
    Zt.C(t, "after loop download liked items") ||
      (0 === Ui.length
        ? r(10)
        : e
          ? he(this, Ni, "m", Bi).call(this, "done(capped)")
          : he(this, Ni, "m", Bi).call(this, "done"));
  }
}),
(Ni = new WeakSet()),
(Li = function () {
  return (
    Xt.j.likes.downloaded.size >=
    (function () {
      try {
        return (function (t) {
          const e = 9999999;
          if (0 === t)
            return {
              cap: 9999999,
              nextToBuy: 'increase "likes" limit: from 1000 to 5000',
              lineItemDescription:
                '"Permanently allow downloading up to 5000 MP4s from [Likes]"',
            };
          const n = e * t,
            i = n + e;
          return {
            cap: n,
            nextToBuy: `increase "likes" limit: from ${n} to ${i}`,
            lineItemDescription: `"Permanently allow downloading up to ${i} MP4s from [Likes]"`,
          };
        })(dt.k.unlocks.likeLevel).cap;
      } catch (t) {
        return (E(t, "ud17"), 0);
      }
    })()
  );
}),
(Fi = async function () {
  ((Xt.j.likes.lastRun.start = Date.now()),
    xt("mainOrLikes"),
    Me.st().catch((t) => {
      E(t, "ll147", "silently");
    }),
    r(25, 0),
    r(23, Xt.j.likes.downloaded.size),
    r(24, "downloading"),
    o(20, "likes"),
    await ut(4e3));
}),
(Bi = async function (t) {
  (xi &&
    ((Xt.j.likes.lastRun.finish = Date.now()),
    (Xt.j.likes.numDisappeared = Xt.j.likes.total - Ui.length)),
    xt("mainOrLikes"));
  const e = {
    total: Xt.j.likes.total,
    officialListLength: Xt.j.likes.officialList.length,
    numMp4InLocalFolder: Xt.j.likes.downloaded.size,
    status: t,
  };
  (zi.ee(), await ut(200), o(12, e), r(24, t), Xt.catchUp(), Xt.D());
}),
Mi)();
function Pi(t) {
  r(6, t);
}
let Hi,
  Vi = !1;
async function Gi(t, e) {
  try {
    const n = await $(t, "data/.appdata");
    await F(n, e);
  } catch (t) {
    E(t, "Gls548");
  }
}
async function Yi(t) {
  let e = await N(t, "data/.appdata/dba.js");
  return e
    ? ((B.m = !0), await Ct(e))
    : ("" === e && (await Gi(t, "dba.js")),
      (e = await N(t, "data/.appdata/db_authors.js")),
      e ? await Ct(e) : vt.authors);
}
async function Ki(t) {
  let e = await N(t, "data/.appdata/dbv.js");
  return e
    ? ((B.m = !0), await Ct(e))
    : ("" === e && (await Gi(t, "dbv.js")),
      (e = await N(t, "data/.appdata/db_videos.js")),
      e ? await Ct(e) : vt.videos);
}
async function Qi(t) {
  let e = await N(t, "data/.appdata/dbf.js");
  return e
    ? ((B.m = !0), await Ct(e))
    : ("" === e && (await Gi(t, "dbf.js")),
      (e = await N(t, "data/.appdata/db_following.js")),
      e ? await Ct(e) : vt.following);
}
async function Xi(t) {
  let e = await N(t, "data/.appdata/dbvd.js");
  return e
    ? ((B.m = !0), await Ct(e))
    : ("" === e && (await Gi(t, "dbvd.js")),
      (e = await N(t, "data/.appdata/db_texts.js")),
      e ? await Ct(e) : vt.videoDescriptions);
}
async function Zi(t) {
  try {
    const { id: e, uid: n, uniqueId: i, nickname: o } = dt.k.profile;
    let r;
    const a = await (async function (t) {
      let e = await N(t, "data/.appdata/db.js");
      return e
        ? ((B.m = !0), e)
        : ("" === e && (await Gi(t, "db.js")),
          (e = await N(t, "data/.appdata/db_likes.js")),
          e);
    })(t);
    if (a) {
      if (((r = await Ct(a)), r.user.id.length > 0 && r.user.id !== e))
        return (
          Pi({
            folderStatus: "belongs_to_another_tiktok_account",
            belongsToUser: r.user.uniqueId,
          }),
          null
        );
      if (r.schemaVersion >= 6) {
        const [e, n, i, o] = await Promise.all([Yi(t), Ki(t), Qi(t), Xi(t)]);
        ((r.authors = e),
          (r.videos = n),
          (r.following = i),
          (r.videoDescriptions = o));
      }
      if (r.schemaVersion >= 7) {
        const e = await (async function (t) {
          let e = await N(t, "data/.appdata/dbb.js");
          return e
            ? ((B.m = !0), await Ct(e))
            : ("" === e && (await Gi(t, "dbb.js")),
              (e = await N(t, "data/.appdata/db_bookmarked.js")),
              e ? await Ct(e) : vt.bookmarked);
        })(t);
        r.bookmarked = e;
      }
    } else
      ((r = vt),
        xt("mainOrLikes"),
        xt("authors"),
        xt("videos"),
        xt("videoDescriptions"),
        xt("following"),
        xt("bookmarked"));
    return (
      (r.user = { uid: n, id: e, uniqueId: i, nickname: o }),
      xt("mainOrLikes"),
      r
    );
  } catch (t) {
    return (
      E(t, "Tjf985", "silently"),
      Pi({ folderStatus: "corrupted" }),
      null
    );
  }
}
function to(t) {
  t && (re.B = t);
  if (!Xt.p) return ((Hi = t), void r(5));
  try {
    switch ((Zt.O++, t || Hi)) {
      case "likes":
        qi.Qt();
        break;
      case "following":
        n.authorItemsCanBeFetched ? $i.Qt() : Nn.Qt();
        break;
      case "bookmarked":
        Kn.Qt();
        break;
      default:
        throw new Error("whatToDownload is undefined");
    }
  } catch (t) {
    return void E(t, "db116");
  }
}
async function eo() {
  let t;
  try {
    t = await lt._("archiveFolderHandle");
  } catch (t) {
    E(t, "Szk285", "silently");
  }
  Pi({ folderStatus: "awaiting_os_window" });
  try {
    !(async function (t) {
      if ("granted" !== (await t.requestPermission({ mode: "readwrite" })))
        return void Pi({ folderStatus: "not_provided" });
      if (
        (Pi({ folderStatus: "success" }),
        await ut(100),
        !(await (async function (t) {
          if (await C(t))
            return (
              !!Vi ||
              ((Vi = !0),
              !dt.k.behavior.hasCreatedArchiveFolder ||
                (Pi({ folderStatus: "unexpectedly_empty" }), !1))
            );
          try {
            const e = await t.getDirectoryHandle("data");
            return (await e.getDirectoryHandle(".appdata"), !0);
          } catch (t) {
            return (Pi({ folderStatus: "content_seems_wrong" }), !1);
          }
        })(t)))
      )
        return;
      const e = await Zi(t);
      if (!e) return;
      Ue.kt || a("is_resync_ready");
      try {
        await Xt.T(t, e);
      } catch (t) {
        return void E(t, "db110");
      }
      to();
    })(
      await showDirectoryPicker({ startIn: t || "videos", mode: "readwrite" }),
    );
  } catch (t) {
    Pi({ folderStatus: "not_provided" });
  }
}
async function no(e, o) {
  switch (e) {
    case 12:
      eo();
      break;
    case 1:
      to("likes");
      break;
    case 18:
      to("bookmarked");
      break;
    case 2:
      to("following");
      break;
    case 3:
      io();
      break;
    case 4:
      ((a = o), Object.assign(ft, a));
      break;
    case 0:
      try {
        if ((r(0, "1.12.63"), "populating" === we.rt)) break;
        if (("unset" === we.rt && (await we.st()), "error" === we.rt))
          throw new Error("error obtaining login status");
        ("done" === we.rt && r(4, we.lt),
          (function (e, n) {
            t.postMessage({ type: e, payload: n });
          })(2),
          i.i || r(35));
      } catch (t) {
        E(t, "Hrd471");
      } finally {
        (we.dt(), we.ut());
      }
      break;
    case 7:
      dt.g(o);
      break;
    case 8:
      try {
        (Ke.St(), n.authorItemsCanBeFetched ? $i.Xt(o) : Nn.Xt(o));
      } catch (t) {
        E(t, "om161");
      }
      break;
    case 9:
      Xe(o);
      break;
    case 13:
      location.href = "https://www.tiktok.com";
      break;
    case 16:
      Zn.F("captcha_solved");
      break;
    case 14:
      location.href =
        "https://chrome.google.com/webstore/detail/myfavett/gmajiifkcmjkehmngbopoobeplhoegad";
      break;
    case 15:
      history.replaceState(null, "", "/");
      break;
    case 17:
      Zt.v("because requested by ui");
      break;
    case 19:
      $i.ve(o);
      break;
    case 20: {
      const { body: t, json: e } = o;
      dn[t] = e;
      break;
    }
  }
  var a;
}
function io() {
  var n;
  (Zt.v("because closing app"),
    null === (n = document.getElementById("myfaveTT-container")) ||
      void 0 === n ||
      n.remove(),
    document.body.classList.remove("pushed-by-myfaveTT"),
    (window.onmessage = null),
    (t.onmessage = null),
    t.close(),
    (e.onmessage = null),
    e.close());
}
async function oo(e) {
  try {
    const { direction: r, type: a, payload: s } = e.data;
    if (12 === r) {
      if (14 === a) return void t.postMessage({ direction: 12, type: 15 });
      if (15 === a)
        return (
          io(),
          void alert(
            "Not loading myFaveTT sidebar, because it's already running in another tab.",
          )
        );
    }
    if (100 === a) return ((i.o = !0), void o(3, s));
    if (102 === a) return void o(19, s);
    if (101 === a) return void (i.l && n.authorItemsCanBeFetched);
  } catch (t) {
    E(t, "om41");
  }
}
const ro = Date.now();
async function ao(t) {
  try {
    const {
      origin: e,
      data: { direction: o, type: r, payload: a },
    } = t;
    if (e !== n.chromeExtensionOrigin) return;
    if (
      (3 === o &&
        no(r, a).catch((t) => {
          E(t, "om93");
        }),
      0 === o)
    )
      switch (r) {
        case 16:
          return void (
            Date.now() - ro < 5e3 && (location.href = "https://www.tiktok.com")
          );
        case 13:
          return (De(a), void (i.l || n.authorItemsCanBeFetched));
      }
    if (7 === o)
      switch (r) {
        case "resync_is_ready":
          return void (Ue.kt = !0);
        case "resynced": {
          const { tempStorageKey: t, arrayBuffer: e } = a;
          return void ie.N(t, e);
        }
      }
  } catch (t) {
    E(t, "om136");
  }
}
try {
  ((window.onmessage = ao),
    (t.onmessage = oo),
    (e.onmessage = Fn),
    t.postMessage({ direction: 12, type: 14 }));
} catch (t) {
  E(t, "st8");
}
