import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import subprocess
import threading
import re
import os
import json
from pathlib import Path


CONFIG_FILE = Path(__file__).parent / "config.json"

COMMON_ADB_PATHS = [
    r"C:\Users\{user}\AppData\Local\Android\Sdk\platform-tools\adb.exe",
    r"C:\Android\platform-tools\adb.exe",
    r"C:\Program Files\Android\platform-tools\adb.exe",
    r"C:\Program Files (x86)\Android\platform-tools\adb.exe",
]


def find_adb_auto() -> str:
    """PATH에서 adb를 찾고, 없으면 일반적인 설치 경로를 탐색."""
    # 1. PATH에 있는 경우
    for path_dir in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(path_dir) / "adb.exe"
        if candidate.exists():
            return str(candidate)

    # 2. 일반 설치 경로 탐색
    user = os.environ.get("USERNAME", "")
    for template in COMMON_ADB_PATHS:
        candidate = Path(template.format(user=user))
        if candidate.exists():
            return str(candidate)

    return ""


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_config(data: dict):
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class AdbConnectorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("ADB 무선 디버깅 연결")
        self.root.resizable(False, False)

        cfg = load_config()
        saved_adb = cfg.get("adb_path", "")
        if saved_adb and Path(saved_adb).exists():
            initial_adb = saved_adb
        else:
            initial_adb = find_adb_auto()

        self.adb_path = tk.StringVar(value=initial_adb)
        self._build_ui()

        if initial_adb:
            self._log(f"ADB 경로: {initial_adb}", "ok")
            self._refresh_devices()
        else:
            self._log("ADB를 찾을 수 없습니다. 아래에서 직접 경로를 지정하세요.", "err")

    # ── adb 실행 ──────────────────────────────────────────────

    def _adb_cmd(self) -> str:
        return self.adb_path.get().strip() or "adb"

    def run_adb(self, args: list[str]) -> tuple[str, str, int]:
        cmd = self._adb_cmd()
        try:
            result = subprocess.run(
                [cmd] + args,
                capture_output=True,
                text=True,
                timeout=15,
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except FileNotFoundError:
            return "", f"ADB 실행 파일을 찾을 수 없습니다:\n{cmd}", 1
        except subprocess.TimeoutExpired:
            return "", "시간 초과 (15초)", 1

    # ── UI 구성 ───────────────────────────────────────────────

    def _build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # --- ADB 경로 ---
        adb_frame = ttk.LabelFrame(self.root, text="ADB 경로 설정", padding=10)
        adb_frame.grid(row=0, column=0, sticky="ew", **pad)

        self.adb_entry = ttk.Entry(adb_frame, textvariable=self.adb_path, width=42)
        self.adb_entry.grid(row=0, column=0, padx=(0, 6))

        ttk.Button(adb_frame, text="찾아보기", command=self._browse_adb, width=9).grid(row=0, column=1)
        ttk.Button(adb_frame, text="저장", command=self._save_adb_path, width=6).grid(row=0, column=2, padx=(4, 0))
        ttk.Button(adb_frame, text="자동 탐색", command=self._auto_find_adb, width=9).grid(row=1, column=0, pady=(6, 0), sticky="w")

        # --- 연결 프레임 ---
        conn_frame = ttk.LabelFrame(self.root, text="기기 연결", padding=10)
        conn_frame.grid(row=1, column=0, sticky="ew", **pad)

        ttk.Label(conn_frame, text="IP 주소:").grid(row=0, column=0, sticky="w")
        self.ip_var = tk.StringVar(value="192.168.")
        ip_entry = ttk.Entry(conn_frame, textvariable=self.ip_var, width=20)
        ip_entry.grid(row=0, column=1, padx=(6, 12))
        ip_entry.bind("<Return>", lambda e: self._connect())

        ttk.Label(conn_frame, text="포트:").grid(row=0, column=2, sticky="w")
        self.port_var = tk.StringVar(value="5555")
        port_entry = ttk.Entry(conn_frame, textvariable=self.port_var, width=8)
        port_entry.grid(row=0, column=3, padx=(6, 0))
        port_entry.bind("<Return>", lambda e: self._connect())

        self.connect_btn = ttk.Button(conn_frame, text="연결", command=self._connect, width=10)
        self.connect_btn.grid(row=1, column=0, columnspan=2, pady=(8, 0), sticky="w")

        self.disconnect_btn = ttk.Button(conn_frame, text="연결 해제", command=self._disconnect, width=10)
        self.disconnect_btn.grid(row=1, column=2, columnspan=2, pady=(8, 0), sticky="w")

        # --- 페어링 프레임 (Android 11+) ---
        pair_frame = ttk.LabelFrame(self.root, text="페어링 (Android 11+)", padding=10)
        pair_frame.grid(row=2, column=0, sticky="ew", **pad)

        ttk.Label(pair_frame, text="IP 주소:").grid(row=0, column=0, sticky="w")
        self.pair_ip_var = tk.StringVar(value="192.168.")
        ttk.Entry(pair_frame, textvariable=self.pair_ip_var, width=20).grid(row=0, column=1, padx=(6, 12))

        ttk.Label(pair_frame, text="페어링 포트:").grid(row=0, column=2, sticky="w")
        self.pair_port_var = tk.StringVar()
        ttk.Entry(pair_frame, textvariable=self.pair_port_var, width=8).grid(row=0, column=3, padx=(6, 0))

        ttk.Label(pair_frame, text="페어링 코드:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.pair_code_var = tk.StringVar()
        ttk.Entry(pair_frame, textvariable=self.pair_code_var, width=12).grid(row=1, column=1, padx=(6, 0), pady=(6, 0), sticky="w")

        ttk.Button(pair_frame, text="페어링", command=self._pair, width=10).grid(row=1, column=2, columnspan=2, pady=(6, 0), sticky="w")

        # --- 기기 목록 ---
        devices_frame = ttk.LabelFrame(self.root, text="연결된 기기", padding=10)
        devices_frame.grid(row=3, column=0, sticky="ew", **pad)

        self.devices_list = tk.Listbox(devices_frame, height=4, width=52)
        self.devices_list.grid(row=0, column=0, sticky="ew")
        ttk.Button(devices_frame, text="새로 고침", command=self._refresh_devices).grid(row=1, column=0, pady=(6, 0), sticky="w")

        # --- 로그 ---
        log_frame = ttk.LabelFrame(self.root, text="로그", padding=10)
        log_frame.grid(row=4, column=0, sticky="ew", **pad)

        self.log_box = scrolledtext.ScrolledText(log_frame, height=8, width=54, state="disabled", font=("Consolas", 9))
        self.log_box.grid(row=0, column=0)
        ttk.Button(log_frame, text="로그 지우기", command=self._clear_log).grid(row=1, column=0, pady=(6, 0), sticky="w")

    # ── helpers ──────────────────────────────────────────────

    def _log(self, msg: str, tag: str = ""):
        self.log_box.config(state="normal")
        if tag == "ok":
            self.log_box.insert("end", f"✔ {msg}\n", "ok")
            self.log_box.tag_config("ok", foreground="#2a9d2a")
        elif tag == "err":
            self.log_box.insert("end", f"✘ {msg}\n", "err")
            self.log_box.tag_config("err", foreground="#c0392b")
        else:
            self.log_box.insert("end", f"  {msg}\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")

    def _set_buttons(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.connect_btn.config(state=state)
        self.disconnect_btn.config(state=state)

    def _validate_ip(self, ip: str) -> bool:
        return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip))

    # ── ADB 경로 관련 ─────────────────────────────────────────

    def _browse_adb(self):
        path = filedialog.askopenfilename(
            title="adb.exe 선택",
            filetypes=[("ADB 실행 파일", "adb.exe"), ("모든 파일", "*.*")],
        )
        if path:
            self.adb_path.set(path)
            self._save_adb_path()

    def _save_adb_path(self):
        path = self.adb_path.get().strip()
        if not path:
            return
        if not Path(path).exists():
            self._log(f"경로를 찾을 수 없습니다: {path}", "err")
            return
        cfg = load_config()
        cfg["adb_path"] = path
        save_config(cfg)
        self._log(f"ADB 경로 저장됨: {path}", "ok")
        self._refresh_devices()

    def _auto_find_adb(self):
        found = find_adb_auto()
        if found:
            self.adb_path.set(found)
            self._log(f"ADB 자동 발견: {found}", "ok")
            self._save_adb_path()
        else:
            self._log("ADB를 자동으로 찾지 못했습니다. '찾아보기'로 직접 지정하세요.", "err")

    # ── actions ──────────────────────────────────────────────

    def _connect(self):
        ip = self.ip_var.get().strip()
        port = self.port_var.get().strip()
        if not self._validate_ip(ip):
            self._log("올바른 IP 주소를 입력하세요.", "err")
            return
        if not port.isdigit():
            self._log("올바른 포트 번호를 입력하세요.", "err")
            return

        self._set_buttons(False)
        self._log(f"연결 중... {ip}:{port}")

        def task():
            stdout, stderr, code = self.run_adb(["connect", f"{ip}:{port}"])
            output = stdout or stderr
            tag = "ok" if code == 0 and "connected" in output.lower() else "err"
            self.root.after(0, lambda: self._log(output, tag))
            self.root.after(0, lambda: self._set_buttons(True))
            self.root.after(0, self._refresh_devices)

        threading.Thread(target=task, daemon=True).start()

    def _disconnect(self):
        ip = self.ip_var.get().strip()
        port = self.port_var.get().strip()
        if not self._validate_ip(ip):
            self._log("올바른 IP 주소를 입력하세요.", "err")
            return

        self._set_buttons(False)
        self._log(f"연결 해제 중... {ip}:{port}")

        def task():
            stdout, stderr, code = self.run_adb(["disconnect", f"{ip}:{port}"])
            output = stdout or stderr
            self.root.after(0, lambda: self._log(output, "ok" if code == 0 else "err"))
            self.root.after(0, lambda: self._set_buttons(True))
            self.root.after(0, self._refresh_devices)

        threading.Thread(target=task, daemon=True).start()

    def _pair(self):
        ip = self.pair_ip_var.get().strip()
        port = self.pair_port_var.get().strip()
        code = self.pair_code_var.get().strip()

        if not self._validate_ip(ip):
            self._log("올바른 페어링 IP 주소를 입력하세요.", "err")
            return
        if not port.isdigit():
            self._log("페어링 포트를 입력하세요.", "err")
            return
        if not code:
            self._log("페어링 코드를 입력하세요.", "err")
            return

        self._log(f"페어링 중... {ip}:{port}")

        def task():
            cmd = self._adb_cmd()
            try:
                proc = subprocess.Popen(
                    [cmd, "pair", f"{ip}:{port}"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = proc.communicate(input=code + "\n", timeout=15)
                output = stdout.strip() or stderr.strip()
                tag = "ok" if "successfully" in output.lower() else "err"
                self.root.after(0, lambda: self._log(output, tag))
            except Exception as e:
                self.root.after(0, lambda: self._log(str(e), "err"))

        threading.Thread(target=task, daemon=True).start()

    def _refresh_devices(self):
        def task():
            stdout, stderr, _ = self.run_adb(["devices"])
            lines = stdout.splitlines()
            devices = [l for l in lines[1:] if l.strip() and "offline" not in l]
            self.root.after(0, lambda: self._update_devices(devices))

        threading.Thread(target=task, daemon=True).start()

    def _update_devices(self, devices: list[str]):
        self.devices_list.delete(0, "end")
        if devices:
            for d in devices:
                self.devices_list.insert("end", d)
        else:
            self.devices_list.insert("end", "연결된 기기 없음")


def main():
    root = tk.Tk()
    AdbConnectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
