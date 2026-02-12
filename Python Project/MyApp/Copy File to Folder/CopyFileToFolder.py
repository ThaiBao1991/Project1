
import os, time, json, threading, queue, shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "Copy thư mục (gia tăng + multi-thread)"
LOG_FILE_NAME = "copy_log.txt"
STATE_FILE_NAME = "copy_state.json"

def ensure_dir(p: Path): p.mkdir(parents=True, exist_ok=True)
def rel_of(root: Path, p: Path) -> str: return p.relative_to(root).as_posix()
def file_stat_tuple(p: Path): st = p.stat(); return int(st.st_size), int(st.st_mtime_ns)

def load_log_set(log_path: Path) -> set:
    s=set()
    if log_path.exists():
        with log_path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parts=line.strip().split("\t",2)
                if len(parts)>=2: s.add("\t".join(parts[:2]))
    return s

def append_log_line(log_path: Path, kind: str, rel: str, lock: threading.Lock):
    with lock:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"{kind}\t{rel}\t{time.strftime('%Y-%m-%d %H:%M:%S')}\n")

def load_state(state_path: Path) -> dict:
    if state_path.exists():
        try: return json.loads(state_path.read_text(encoding="utf-8"))
        except: return {}
    return {}

def save_state(state_path: Path, state: dict, lock: threading.Lock):
    with lock:
        tmp=state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        tmp.replace(state_path)

class CopyMode:
    ONLY_NEW_BY_LOG = "Chỉ file mới (theo log)"
    NEW_OR_CHANGED_BY_STAT = "Chỉ file mới/đổi (theo size/mtime)"
    FORCE_ALL = "Bắt buộc (copy tất cả)"

class Copier:
    def __init__(self, src: Path, dst: Path, mode: str, workers: int,
                 msg_queue: queue.Queue, progress_cb=None, stop_event=None):
        self.src, self.dst, self.mode = src, dst, mode
        self.workers = max(1, int(workers))
        self.msg_queue = msg_queue
        self.progress_cb = progress_cb or (lambda a,b: None)
        self.stop_event = stop_event or threading.Event()
        self.log_path = dst/LOG_FILE_NAME
        self.state_path = dst/STATE_FILE_NAME
        self.total_files=self.total_dirs=self.total_items=0
        self.copied=self.skipped=self.errors=0
        self.log_lock=threading.Lock()
        self.state_lock=threading.Lock()
        self.progress_lock=threading.Lock()
        self.log_set=set(); self.state={}

    def log(self, m:str): self.msg_queue.put(m)

    def scan(self):
        self.log_set = load_log_set(self.log_path)
        self.state = load_state(self.state_path) if self.mode==CopyMode.NEW_OR_CHANGED_BY_STAT else {}
        for dp,dns,fns in os.walk(self.src):
            self.total_dirs+=len(dns); self.total_files+=len(fns)
        self.total_items=self.total_dirs+self.total_files

    def should_copy(self, src_file: Path)->bool:
        if self.mode==CopyMode.FORCE_ALL: return True
        rel = rel_of(self.src, src_file); key=f"F\t{rel}"
        if self.mode==CopyMode.ONLY_NEW_BY_LOG: return key not in self.log_set
        if self.mode==CopyMode.NEW_OR_CHANGED_BY_STAT:
            size,mt=file_stat_tuple(src_file); entry=self.state.get(rel)
            if entry is None: return True
            old_size,old_mt=entry; return not (int(old_size)==size and int(old_mt)==mt)
        return True

    def copy_one(self, src_file: Path):
        if self.stop_event.is_set(): return False
        rel = rel_of(self.src, src_file); dst_file=self.dst/rel
        try:
            ensure_dir(dst_file.parent)
            shutil.copy2(src_file, dst_file)
            size,mt=file_stat_tuple(src_file)
            append_log_line(self.log_path, "F", rel, self.log_lock)
            if self.mode in (CopyMode.NEW_OR_CHANGED_BY_STAT, CopyMode.FORCE_ALL):
                with self.state_lock: self.state[rel]=[int(size), int(mt)]
            self.log(f"✅ Copied: {rel}"); return True
        except Exception as e:
            self.log(f"❌ Lỗi copy {rel}: {e}")
            with self.progress_lock: self.errors+=1
            return False

    def run(self):
        if not self.src.exists() or not self.src.is_dir():
            self.log("❌ Thư mục nguồn không hợp lệ."); return
        ensure_dir(self.dst); self.scan()
        if self.total_items==0: self.log("⚠️ Thư mục nguồn trống."); return

        # tạo thư mục đích và log thư mục
        for dp,dns,_ in os.walk(self.src):
            if self.stop_event.is_set(): return
            dp=Path(dp)
            for d in dns:
                src_dir=dp/d; dst_dir=self.dst/rel_of(self.src, src_dir)
                ensure_dir(dst_dir)
                rel_d=rel_of(self.src, src_dir); key_d=f"D\t{rel_d}"
                if key_d not in self.log_set:
                    append_log_line(self.log_path,"D",rel_d,self.log_lock); self.log_set.add(key_d)

        # danh sách file cần copy
        files=[]
        for dp,_,fns in os.walk(self.src):
            if self.stop_event.is_set(): break
            dp=Path(dp)
            for fn in fns:
                f=dp/fn
                if self.should_copy(f): files.append(f)
                else: self.skipped+=1

        if not files:
            self.log("ℹ️ Không có file cần copy (theo chế độ đã chọn).")
            self.progress_cb(1,1); return

        self.log(f"🚀 Copy {len(files)} file với {self.workers} luồng...")
        done=0
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs=[ex.submit(self.copy_one,f) for f in files]
            for fu in as_completed(futs):
                ok=fu.result()
                with self.progress_lock:
                    done+=1
                    if ok: self.copied+=1
                    self.progress_cb(done, len(files))
                if self.stop_event.is_set(): break

        if self.mode in (CopyMode.NEW_OR_CHANGED_BY_STAT, CopyMode.FORCE_ALL):
            save_state(self.state_path, self.state, self.state_lock)

        self.log("—"*60)
        self.log(f"🎯 Hoàn tất | Copied: {self.copied} | Bỏ qua: {self.skipped} | Lỗi: {self.errors}")
        self.log(f"📝 Log: {self.log_path}")
        if self.mode in (CopyMode.NEW_OR_CHANGED_BY_STAT, CopyMode.FORCE_ALL):
            self.log(f"🧠 State: {self.state_path}")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE); self.geometry("860x600"); self.resizable(False, False)
        self.src_var=tk.StringVar(); self.dst_var=tk.StringVar()
        self.mode_var=tk.StringVar(value=CopyMode.NEW_OR_CHANGED_BY_STAT)
        self.workers_var=tk.IntVar(value=min(8, (os.cpu_count() or 4)*2))
        self.status_var=tk.StringVar(value="Sẵn sàng.")
        self.msg_queue=queue.Queue(); self.stop_event=threading.Event()
        self.copier=None; self.worker=None
        self._build_ui(); self.after(80, self._drain)

    def _build_ui(self):
        pad=8; frm=ttk.Frame(self, padding=pad); frm.pack(fill="both", expand=True)
        r1=ttk.Frame(frm); r1.pack(fill="x", pady=(0,pad))
        ttk.Label(r1, text="Thư mục nguồn:").pack(side="left")
        ttk.Entry(r1, textvariable=self.src_var, width=85).pack(side="left", padx=(pad,pad))
        ttk.Button(r1, text="Chọn...", command=self._pick_src).pack(side="left")

        r2=ttk.Frame(frm); r2.pack(fill="x", pady=(0,pad))
        ttk.Label(r2, text="Thư mục đích:").pack(side="left")
        ttk.Entry(r2, textvariable=self.dst_var, width=85).pack(side="left", padx=(pad,pad))
        ttk.Button(r2, text="Chọn...", command=self._pick_dst).pack(side="left")

        r3=ttk.Frame(frm); r3.pack(fill="x", pady=(0,pad))
        ttk.Label(r3, text="Chế độ copy:").pack(side="left")
        cb=ttk.Combobox(r3, textvariable=self.mode_var, width=36, state="readonly",
                        values=[CopyMode.NEW_OR_CHANGED_BY_STAT, CopyMode.ONLY_NEW_BY_LOG, CopyMode.FORCE_ALL])
        cb.pack(side="left", padx=(pad,3))
        ttk.Label(r3, text="Số luồng:").pack(side="left", padx=(pad,0))
        sp=ttk.Spinbox(r3, from_=1, to=64, textvariable=self.workers_var, width=5); sp.pack(side="left")

        r4=ttk.Frame(frm); r4.pack(fill="x", pady=(0,pad))
        self.btn_start=ttk.Button(r4, text="Start", command=self._on_start); self.btn_start.pack(side="left")
        self.btn_stop=ttk.Button(r4, text="Stop", command=self._on_stop, state="disabled"); self.btn_stop.pack(side="left", padx=(pad,0))

        r5=ttk.Frame(frm); r5.pack(fill="x", pady=(0,pad))
        self.pb=ttk.Progressbar(r5, mode="determinate", maximum=100); self.pb.pack(fill="x", expand=True, side="left")
        ttk.Label(r5, textvariable=self.status_var, width=28, anchor="e").pack(side="left", padx=(pad,0))

        self.txt=tk.Text(frm, height=24, wrap="word"); self.txt.pack(fill="both", expand=True)
        self._set_text("", replace=True)

    def _pick_src(self):
        d=filedialog.askdirectory(title="Chọn thư mục nguồn")
        if d: self.src_var.set(d)

    def _pick_dst(self):
        d=filedialog.askdirectory(title="Chọn thư mục đích")
        if d: self.dst_var.set(d)

    def _set_text(self, s, replace=False):
        self.txt.configure(state="normal")
        if replace: self.txt.delete("1.0","end")
        self.txt.insert("end", s); self.txt.see("end"); self.txt.configure(state="disabled")

    def _drain(self):
        try:
            while True: self._set_text(self.msg_queue.get_nowait()+"\n")
        except queue.Empty: pass
        self.after(80, self._drain)

    def _progress(self, done, total):
        self.pb["maximum"]=max(1,total); self.pb["value"]=min(done,total)
        self.status_var.set(f"{done}/{total}")

    def _on_start(self):
        src=Path(self.src_var.get().strip()); dst=Path(self.dst_var.get().strip())
        if not src.exists() or not src.is_dir():
            messagebox.showerror("Lỗi","Thư mục nguồn không hợp lệ."); return
        try: ensure_dir(dst)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tạo được thư mục đích:\n{e}"); return
        try:
            if str(dst.resolve()).startswith(str(src.resolve())):
                messagebox.showerror("Lỗi","Thư mục đích không được nằm trong thư mục nguồn."); return
        except: pass
        self.stop_event.clear(); self.btn_start.configure(state="disabled"); self.btn_stop.configure(state="normal")
        self.pb["value"]=0; self.status_var.set("Đang chuẩn bị..."); self._set_text("", replace=True)
        self.copier=Copier(src, dst, self.mode_var.get(), self.workers_var.get(),
                           self.msg_queue, self._progress, self.stop_event)
        self.worker=threading.Thread(target=self.copier.run, daemon=True); self.worker.start()
        self.after(250, self._check_done)

    def _on_stop(self):
        if messagebox.askyesno("Xác nhận","Dừng phiên copy hiện tại?"): self.stop_event.set()

    def _check_done(self):
        if self.worker and self.worker.is_alive(): self.after(250, self._check_done)
        else:
            self.btn_start.configure(state="normal"); self.btn_stop.configure(state="disabled")
            self.status_var.set("Xong." if self.pb["value"]>=self.pb["maximum"] else "Đã dừng.")

if __name__ == "__main__":
    app = App()
    app.mainloop()
