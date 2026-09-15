
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import ttk, messagebox, filedialog, simpledialog

APP_NAME = "COLIZEUM PC Manager"
VERSION = "1.4"

def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

APP_DIR = app_dir()
CONFIG_PATH = APP_DIR / "config.json"
LOGS_DIR = APP_DIR / "Logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG = {
    "drive": "D:\\",
    "log_days": 30,

    "root_keep_dirs": [
        "$RECYCLE.BIN", "Батники", "Games", "Programs", "Recovery",
        "RentalGames", "System Volume Information", "UpdateCheck3",
        "Игры без аккаунта"
    ],
    "root_keep_files": ["desktop.ini"],

    "games_keep_dirs": [
        "Battle.net", "BsgLauncher", "CS 1.6 Small Crosshair", "EA Games",
        "Electronic Arts", "Epic Games", "Game Centre", "iccupLauncher",
        "iccup_war3_ru", "Innova", "Lesta", "packages", "Portable", "RAGEMP",
        "Riot Games", "Rockstar Games", "Steam", "Tanki",
        "Ubisoft Game Launcher"
    ],
    "games_keep_files": ["is550iy5yp.dat"],

    "steam_common_keep_dirs": [
        "Apex Legends", "Arc Raiders", "Call of Duty HQ",
        "Counter-Strike Global Offensive", "Deadlock", "dota 2 beta",
        "Grand Theft Auto V", "Left 4 Dead 2", "OBS Studio",
        "Phasmophobia", "PUBG", "Rust", "Steam Controller Configs",
        "Steamworks Shared"
    ],

    "cache_paths": [
        {"enabled": True, "path": r"D:\Games\Steam\steam\cached"},
        {"enabled": True, "path": r"D:\Games\Steam\userdata"},
        {"enabled": True, "path": r"D:\Games\Steam\steamapps\shadercache"},
        {"enabled": True, "path": r"D:\Games\Steam\steamapps\temp"},
        {"enabled": True, "path": r"D:\Games\Steam\steamapps\workshop\content"},
        {"enabled": True, "path": r"D:\Games\Steam\steamapps\workshop\temp"},
        {"enabled": True, "path": r"D:\Games\Steam\steamapps\common\Counter-Strike Global Offensive\csgo\maps\workshop"},
        {"enabled": True, "path": r"D:\Games\Steam\steamapps\downloading"},
        {"enabled": True, "path": r"D:\Games\Steam\package"},
        {"enabled": True, "path": r"D:\Games\Steam\config"},
        {"enabled": True, "path": r"D:\Games\Steam\logs"},
        {"enabled": True, "path": r"D:\Games\Steam\appcache"},
        {"enabled": True, "path": r"D:\Games\Ubisoft Game Launcher\logs"}
    ],

    "cache_start_updater": True,
    "cache_start_rentalgames": True,
    "cache_reboot": False,

    "launchers": [
        {"enabled": True, "name": "RentalGames updater", "path": r"D:\RentalGames\updater.exe", "wait": 120},
        {"enabled": True, "name": "Epic Games", "path": r"D:\Games\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe", "wait": 60},
        {"enabled": True, "name": "Lesta Game Center", "path": r"D:\Games\Lesta\GameCenter\lgc.exe", "wait": 60},
        {"enabled": True, "name": "GameCenter", "path": r"C:\Users\Colizeum\AppData\Local\GameCenter\GameCenter.exe", "wait": 60},
        {"enabled": True, "name": "Discord", "path": r"C:\Users\Colizeum\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Discord Inc\Discord.lnk", "wait": 60},
        {"enabled": True, "name": "Riot Client", "path": r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Riot Games\Riot Client.lnk", "wait": 60},
        {"enabled": True, "name": "VALORANT", "path": r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Riot Games\VALORANT.lnk", "wait": 300},
        {"enabled": True, "name": "League of Legends", "path": r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Riot Games\League of Legends.lnk", "wait": 300},
        {"enabled": True, "name": "FACEIT", "path": r"C:\Users\Colizeum\AppData\Local\FACEIT\FACEIT.exe", "wait": 60},
        {"enabled": True, "name": "FACEIT AC", "path": r"C:\Program Files\FACEIT AC\faceitclient.exe", "wait": 60},
        {"enabled": True, "name": "Rockstar Launcher", "path": r"D:\Games\Rockstar Games\Launcher\LauncherPatcher.exe", "wait": 60},
        {"enabled": True, "name": "iCCup Launcher", "path": r"D:\Games\iccupLauncher\Launcher.exe", "wait": 60},
        {"enabled": True, "name": "Update Check 3", "path": r"D:\UpdateCheck3\Update_check3.exe", "wait": 0}
    ]
}

def deep_copy_default():
    return json.loads(json.dumps(DEFAULT_CONFIG, ensure_ascii=False))

def save_config(cfg):
    CONFIG_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def load_config():
    if not CONFIG_PATH.exists():
        cfg = deep_copy_default()
        save_config(cfg)
        return cfg

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cfg = deep_copy_default()
        cfg.update(data)
        return cfg
    except Exception:
        return deep_copy_default()

def same_name(a, b):
    return str(a).casefold() == str(b).casefold()

def is_kept(name, keep_list):
    return any(same_name(name, x) for x in keep_list)

def launch_path(path):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    os.startfile(str(p))

def remove_path(path):
    p = Path(path)
    if not p.exists():
        return False
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink()
    return True

def purge_old_logs(days):
    try:
        days = max(1, int(days))
    except Exception:
        days = 30

    cutoff = datetime.now() - timedelta(days=days)
    for f in LOGS_DIR.rglob("*.log"):
        try:
            if datetime.fromtimestamp(f.stat().st_mtime) < cutoff:
                f.unlink()
        except Exception:
            pass

    for d in sorted([x for x in LOGS_DIR.iterdir() if x.is_dir()], reverse=True):
        try:
            if not any(d.iterdir()):
                d.rmdir()
        except Exception:
            pass


# -------------------- Windows automation / credentials --------------------
if os.name == "nt":
    user32 = ctypes.windll.user32
    advapi32 = ctypes.windll.advapi32
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    VK_MAP = {
        "ENTER":0x0D,"TAB":0x09,"ESC":0x1B,"SPACE":0x20,"BACKSPACE":0x08,"DELETE":0x2E,
        "F1":0x70,"F2":0x71,"F3":0x72,"F4":0x73,"F5":0x74,"F6":0x75,
        "F7":0x76,"F8":0x77,"F9":0x78,"F10":0x79,"F11":0x7A,"F12":0x7B
    }

    class CREDENTIALW(ctypes.Structure):
        _fields_ = [
            ("Flags",wintypes.DWORD),("Type",wintypes.DWORD),("TargetName",wintypes.LPWSTR),
            ("Comment",wintypes.LPWSTR),("LastWritten",wintypes.FILETIME),
            ("CredentialBlobSize",wintypes.DWORD),("CredentialBlob",ctypes.POINTER(ctypes.c_ubyte)),
            ("Persist",wintypes.DWORD),("AttributeCount",wintypes.DWORD),
            ("Attributes",ctypes.c_void_p),("TargetAlias",wintypes.LPWSTR),("UserName",wintypes.LPWSTR)
        ]
    PCREDENTIALW = ctypes.POINTER(CREDENTIALW)
    advapi32.CredWriteW.argtypes=[ctypes.POINTER(CREDENTIALW),wintypes.DWORD]
    advapi32.CredReadW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.POINTER(PCREDENTIALW)]
    advapi32.CredFree.argtypes=[ctypes.c_void_p]

def cred_target(profile):
    return "COLIZEUM_PC_Manager:" + profile

def save_credential(profile, username, password):
    if os.name != "nt": raise OSError("Windows only")
    blob=password.encode("utf-16-le")
    buf=(ctypes.c_ubyte*len(blob)).from_buffer_copy(blob)
    c=CREDENTIALW(); c.Type=1; c.TargetName=cred_target(profile); c.Comment="COLIZEUM PC Manager"
    c.CredentialBlobSize=len(blob); c.CredentialBlob=ctypes.cast(buf,ctypes.POINTER(ctypes.c_ubyte))
    c.Persist=2; c.UserName=username
    if not advapi32.CredWriteW(ctypes.byref(c),0): raise ctypes.WinError()

def read_credential(profile):
    if os.name != "nt": raise OSError("Windows only")
    p=PCREDENTIALW()
    if not advapi32.CredReadW(cred_target(profile),1,0,ctypes.byref(p)):
        raise FileNotFoundError("Профиль аккаунта не найден: "+profile)
    try:
        c=p.contents
        raw=ctypes.string_at(c.CredentialBlob,c.CredentialBlobSize)
        return c.UserName or "", raw.decode("utf-16-le")
    finally:
        advapi32.CredFree(p)

def mouse_click(x,y,double=False):
    user32.SetCursorPos(int(x),int(y))
    for _ in range(2 if double else 1):
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN,0,0,0,0)
        user32.mouse_event(MOUSEEVENTF_LEFTUP,0,0,0,0)
        if double: time.sleep(.08)

def type_unicode(value):
    for ch in str(value):
        code=ord(ch)
        user32.keybd_event(0,code,KEYEVENTF_UNICODE,0)
        user32.keybd_event(0,code,KEYEVENTF_UNICODE|KEYEVENTF_KEYUP,0)

def press_key(name):
    name=str(name).upper()
    vk=VK_MAP.get(name)
    if vk is None and len(name)==1: vk=user32.VkKeyScanW(ord(name)) & 0xff
    if vk is None: raise ValueError("Неизвестная клавиша: "+name)
    user32.keybd_event(vk,0,0,0); user32.keybd_event(vk,0,KEYEVENTF_KEYUP,0)

def mouse_pos():
    pt=wintypes.POINT(); user32.GetCursorPos(ctypes.byref(pt)); return pt.x,pt.y


class LogWriter:
    def __init__(self, operation):
        day_dir = LOGS_DIR / datetime.now().strftime("%Y-%m-%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%H-%M-%S")
        self.path = day_dir / f"{stamp}_{operation}.log"
        self.started = time.time()

        self.write(f"{APP_NAME} v{VERSION}")
        self.write(f"Компьютер: {socket.gethostname()}")
        self.write(f"Операция: {operation}")

    def write(self, text):
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {text}"
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def finish(self, text):
        self.write(text)
        self.write(f"Время работы: {round(time.time() - self.started, 1)} сек.")

class PCManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        purge_old_logs(self.cfg.get("log_days", 30))

        self.title(f"{APP_NAME} v{VERSION}")
        self.geometry("1180x780")
        self.minsize(1000, 650)

        self.update_running = False
        self.cleanup_running = False
        self.status_var = tk.StringVar(value="Готово")

        self.build_ui()

    def build_ui(self):
        header = ttk.Frame(self, padding=10)
        header.pack(fill="x")
        ttk.Label(
            header,
            text="COLIZEUM PC Manager",
            font=("Segoe UI", 17, "bold")
        ).pack(side="left")
        ttk.Label(header, textvariable=self.status_var).pack(side="right")
        self.progress = ttk.Progressbar(header, mode="indeterminate", length=180)
        self.progress.pack(side="right", padx=(0, 12))

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.disk_tab = ttk.Frame(self.tabs, padding=10)
        self.cache_tab = ttk.Frame(self.tabs, padding=10)
        self.update_tab = ttk.Frame(self.tabs, padding=10)
        self.logs_tab = ttk.Frame(self.tabs, padding=10)
        self.settings_tab = ttk.Frame(self.tabs, padding=10)

        self.tabs.add(self.disk_tab, text="Очистка диска")
        self.tabs.add(self.cache_tab, text="Очистка кэша")
        self.tabs.add(self.update_tab, text="Обновление игр и приложений")
        self.tabs.add(self.logs_tab, text="Логи")
        self.tabs.add(self.settings_tab, text="Настройки")

        self.build_disk_tab()
        self.build_cache_tab()
        self.build_update_tab()
        self.build_logs_tab()
        self.build_settings_tab()

    def make_tree(self, parent, columns):
        names = [name for name, _ in columns]
        tree = ttk.Treeview(parent, columns=names, show="headings")
        for name, width in columns:
            tree.heading(name, text=name)
            tree.column(name, width=width)
        tree.pack(fill="both", expand=True, pady=8)
        return tree

    def clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    # -------------------- Очистка диска --------------------

    def build_disk_tab(self):
        bar = ttk.Frame(self.disk_tab)
        bar.pack(fill="x")

        ttk.Button(
            bar,
            text="Проверить без удаления",
            command=self.disk_scan
        ).pack(side="left")

        ttk.Button(
            bar,
            text="Очистить диск",
            command=self.disk_clean
        ).pack(side="left", padx=8)

        ttk.Button(
            bar,
            text="Исключения",
            command=self.open_exclusions
        ).pack(side="left")

        self.disk_tree = self.make_tree(
            self.disk_tab,
            [("Статус", 160), ("Путь", 760), ("Комментарий", 180)]
        )

    def auto_protected_root(self, drive):
        try:
            rel = APP_DIR.resolve().relative_to(drive.resolve())
            if rel.parts:
                return rel.parts[0]
        except Exception:
            pass
        return None

    def disk_items(self):
        drive = Path(self.cfg["drive"])
        if not drive.exists():
            raise FileNotFoundError(f"Диск не найден: {drive}")

        auto_root = self.auto_protected_root(drive)
        items = []

        for p in drive.iterdir():
            if p.is_dir():
                keep = is_kept(p.name, self.cfg["root_keep_dirs"])
                note = ""
                if auto_root and same_name(p.name, auto_root):
                    keep = True
                    note = "автозащита программы"
            else:
                keep = is_kept(p.name, self.cfg["root_keep_files"])
                note = ""
            items.append((p, keep, note))

        games = drive / "Games"
        if games.exists():
            for p in games.iterdir():
                if p.is_dir():
                    keep = is_kept(p.name, self.cfg["games_keep_dirs"])
                else:
                    keep = is_kept(p.name, self.cfg["games_keep_files"])
                items.append((p, keep, ""))

        common = drive / "Games" / "Steam" / "steamapps" / "common"
        if common.exists():
            for p in common.iterdir():
                if p.is_dir():
                    keep = is_kept(p.name, self.cfg["steam_common_keep_dirs"])
                    items.append((p, keep, ""))
                else:
                    items.append((p, True, "служебный файл Steam"))

        return items

    def disk_scan(self):
        try:
            items = self.disk_items()
            self.clear_tree(self.disk_tree)

            delete_count = 0
            for path, keep, note in items:
                status = "СОХРАНИТЬ" if keep else "БУДЕТ УДАЛЕНО"
                if not keep:
                    delete_count += 1
                self.disk_tree.insert("", "end", values=(status, str(path), note))

            self.status_var.set(
                f"Проверено: {len(items)} | К удалению: {delete_count}"
            )
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def disk_clean(self):
        if self.cleanup_running:
            messagebox.showinfo("Очистка", "Очистка уже выполняется.")
            return

        try:
            items = self.disk_items()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return

        to_delete = [(p, n) for p, keep, n in items if not keep]
        if not to_delete:
            messagebox.showinfo("Очистка", "Лишних объектов не найдено.")
            return

        if not messagebox.askyesno(
            "Подтверждение",
            f"Будет удалено объектов: {len(to_delete)}.\n\nПродолжить?"
        ):
            return

        self.cleanup_running = True
        self.progress.start(12)
        self.status_var.set("Очистка диска выполняется...")
        threading.Thread(
            target=self.disk_clean_worker,
            args=(items, to_delete),
            daemon=True
        ).start()

    def disk_clean_worker(self, items, to_delete):
        log = LogWriter("DiskCleanup")
        rows = []
        deleted = 0
        errors = 0

        for path, keep, note in items:
            if keep:
                rows.append(("СОХРАНЕНО", str(path), note))
                log.write(f"СОХРАНЕНО: {path}")

        for index, (path, note) in enumerate(to_delete, start=1):
            self.after(
                0,
                lambda i=index, total=len(to_delete), p=str(path):
                    self.status_var.set(f"Очистка диска {i}/{total}: {p}")
            )
            try:
                remove_path(path)
                deleted += 1
                rows.append(("УДАЛЕНО", str(path), note))
                log.write(f"УДАЛЕНО: {path}")
            except Exception as e:
                errors += 1
                rows.append(("ОШИБКА", str(path), str(e)))
                log.write(f"ОШИБКА: {path} | {e}")

        log.finish(f"ИТОГ: удалено={deleted}, ошибок={errors}")

        def done():
            self.clear_tree(self.disk_tree)
            for row in rows:
                self.disk_tree.insert("", "end", values=row)
            self.refresh_logs()
            self.cleanup_running = False
            self.progress.stop()
            self.status_var.set(
                f"Очистка завершена | Удалено: {deleted} | Ошибок: {errors}"
            )
            messagebox.showinfo(
                "Очистка завершена",
                f"Удалено: {deleted}\nОшибок: {errors}"
            )

        self.after(0, done)

    def open_exclusions(self):
        w = tk.Toplevel(self)
        w.title("Исключения")
        w.geometry("720x540")

        key_var = tk.StringVar(value="root_keep_dirs")

        radio_frame = ttk.Frame(w)
        radio_frame.pack(fill="x", padx=10, pady=10)

        listbox = tk.Listbox(w)
        listbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        def refresh():
            listbox.delete(0, "end")
            for item in self.cfg[key_var.get()]:
                listbox.insert("end", item)

        for label, key in [
            ("Корень D:\\", "root_keep_dirs"),
            ("D:\\Games", "games_keep_dirs"),
            ("Steam common", "steam_common_keep_dirs")
        ]:
            ttk.Radiobutton(
                radio_frame,
                text=label,
                variable=key_var,
                value=key,
                command=refresh
            ).pack(side="left", padx=5)

        def add_item():
            q = tk.Toplevel(w)
            q.title("Добавить")
            q.geometry("450x140")
            var = tk.StringVar()
            ttk.Label(q, text="Название папки:").pack(
                anchor="w", padx=10, pady=(10, 4)
            )
            entry = ttk.Entry(q, textvariable=var)
            entry.pack(fill="x", padx=10)
            entry.focus_set()

            def save():
                name = var.get().strip()
                if name and not is_kept(name, self.cfg[key_var.get()]):
                    self.cfg[key_var.get()].append(name)
                    self.cfg[key_var.get()].sort(key=str.casefold)
                    save_config(self.cfg)
                    refresh()
                q.destroy()

            ttk.Button(q, text="Добавить", command=save).pack(pady=10)

        def remove_item():
            sel = listbox.curselection()
            if not sel:
                return
            item = listbox.get(sel[0])
            if messagebox.askyesno(
                "Подтверждение",
                f"Удалить из исключений?\n\n{item}"
            ):
                self.cfg[key_var.get()].pop(sel[0])
                save_config(self.cfg)
                refresh()

        buttons = ttk.Frame(w)
        buttons.pack(pady=8)
        ttk.Button(buttons, text="Добавить", command=add_item).pack(
            side="left", padx=5
        )
        ttk.Button(buttons, text="Удалить", command=remove_item).pack(
            side="left", padx=5
        )

        refresh()

    # -------------------- Очистка кэша --------------------

    def build_cache_tab(self):
        bar = ttk.Frame(self.cache_tab)
        bar.pack(fill="x")

        ttk.Button(
            bar,
            text="Очистить выбранное",
            command=self.cache_clean
        ).pack(side="left")

        ttk.Button(
            bar,
            text="Добавить путь",
            command=self.cache_add
        ).pack(side="left", padx=8)

        ttk.Button(
            bar,
            text="Удалить путь",
            command=self.cache_remove
        ).pack(side="left")

        ttk.Label(
            bar,
            text="Двойной клик по строке = включить / выключить"
        ).pack(side="right")

        self.cache_tree = self.make_tree(
            self.cache_tab,
            [("Вкл", 60), ("Путь", 920)]
        )
        self.cache_tree.bind("<Double-1>", self.cache_toggle)

        opts = ttk.Frame(self.cache_tab)
        opts.pack(fill="x", pady=(4, 0))

        self.cache_updater_var = tk.BooleanVar(
            value=self.cfg.get("cache_start_updater", True)
        )
        self.cache_rental_var = tk.BooleanVar(
            value=self.cfg.get("cache_start_rentalgames", True)
        )
        self.cache_reboot_var = tk.BooleanVar(
            value=self.cfg.get("cache_reboot", False)
        )

        ttk.Checkbutton(
            opts,
            text="Запустить updater перед очисткой",
            variable=self.cache_updater_var
        ).pack(side="left", padx=5)

        ttk.Checkbutton(
            opts,
            text="Запустить RentalGames после",
            variable=self.cache_rental_var
        ).pack(side="left", padx=5)

        ttk.Checkbutton(
            opts,
            text="Перезагрузить ПК после",
            variable=self.cache_reboot_var
        ).pack(side="left", padx=5)

        self.refresh_cache()

    def refresh_cache(self):
        self.clear_tree(self.cache_tree)
        for item in self.cfg["cache_paths"]:
            self.cache_tree.insert(
                "", "end",
                values=("✓" if item["enabled"] else "", item["path"])
            )

    def cache_toggle(self, event=None):
        sel = self.cache_tree.selection()
        if not sel:
            return
        index = self.cache_tree.index(sel[0])
        self.cfg["cache_paths"][index]["enabled"] = (
            not self.cfg["cache_paths"][index]["enabled"]
        )
        save_config(self.cfg)
        self.refresh_cache()

    def cache_add(self):
        path = filedialog.askdirectory(
            title="Выбери папку, которую нужно очищать"
        )
        if not path:
            return
        self.cfg["cache_paths"].append({
            "enabled": True,
            "path": path
        })
        save_config(self.cfg)
        self.refresh_cache()

    def cache_remove(self):
        sel = self.cache_tree.selection()
        if not sel:
            return
        index = self.cache_tree.index(sel[0])
        path = self.cfg["cache_paths"][index]["path"]

        if messagebox.askyesno(
            "Подтверждение",
            f"Удалить путь из списка очистки?\n\n{path}"
        ):
            self.cfg["cache_paths"].pop(index)
            save_config(self.cfg)
            self.refresh_cache()

    def cache_clean(self):
        if self.cleanup_running:
            messagebox.showinfo("Очистка", "Очистка уже выполняется.")
            return

        selected = [
            x for x in self.cfg["cache_paths"]
            if x.get("enabled", True)
        ]

        if not selected:
            messagebox.showinfo("Очистка кэша", "Нет выбранных путей.")
            return

        if not messagebox.askyesno(
            "Очистка кэша",
            f"Будет обработано путей: {len(selected)}.\n\nПродолжить?"
        ):
            return

        self.cfg["cache_start_updater"] = self.cache_updater_var.get()
        self.cfg["cache_start_rentalgames"] = self.cache_rental_var.get()
        self.cfg["cache_reboot"] = self.cache_reboot_var.get()
        save_config(self.cfg)

        options = {
            "start_updater": self.cache_updater_var.get(),
            "start_rentalgames": self.cache_rental_var.get(),
            "reboot": self.cache_reboot_var.get()
        }

        self.cleanup_running = True
        self.progress.start(12)
        self.status_var.set("Очистка кэша выполняется...")
        threading.Thread(
            target=self.cache_clean_worker,
            args=(selected, options),
            daemon=True
        ).start()

    def cache_clean_worker(self, selected, options):
        log = LogWriter("CacheCleanup")

        if options["start_updater"]:
            try:
                launch_path(r"D:\RentalGames\updater.exe")
                log.write("ЗАПУЩЕН: D:\\RentalGames\\updater.exe")
            except Exception as e:
                log.write(f"ОШИБКА updater: {e}")

        deleted = 0
        missing = 0
        errors = 0

        for index, item in enumerate(selected, start=1):
            path = Path(item["path"])
            self.after(
                0,
                lambda i=index, total=len(selected), p=str(path):
                    self.status_var.set(f"Очистка кэша {i}/{total}: {p}")
            )
            try:
                if path.exists():
                    remove_path(path)
                    deleted += 1
                    log.write(f"УДАЛЕНО: {path}")
                else:
                    missing += 1
                    log.write(f"НЕ НАЙДЕНО: {path}")
            except Exception as e:
                errors += 1
                log.write(f"ОШИБКА: {path} | {e}")

        if options["start_rentalgames"]:
            try:
                launch_path(r"D:\RentalGames\RentalGames.exe")
                log.write("ЗАПУЩЕН: D:\\RentalGames\\RentalGames.exe")
            except Exception as e:
                log.write(f"ОШИБКА RentalGames: {e}")

        log.finish(
            f"ИТОГ: удалено={deleted}, не найдено={missing}, ошибок={errors}"
        )

        def done():
            self.refresh_logs()
            self.cleanup_running = False
            self.progress.stop()
            self.status_var.set(
                f"Очистка кэша завершена | Удалено: {deleted} | Ошибок: {errors}"
            )
            messagebox.showinfo(
                "Очистка кэша завершена",
                f"Удалено: {deleted}\nНе найдено: {missing}\nОшибок: {errors}"
            )

            if options["reboot"]:
                if messagebox.askyesno(
                    "Перезагрузка",
                    "Перезагрузить компьютер сейчас?"
                ):
                    subprocess.Popen(["shutdown", "-r", "-t", "1"])

        self.after(0, done)

    # -------------------- Обновление игр и приложений --------------------

    def build_update_tab(self):
        pane = ttk.Panedwindow(self.update_tab, orient="vertical")
        pane.pack(fill="both", expand=True)

        top = ttk.Frame(pane, padding=5)
        bottom = ttk.Frame(pane, padding=5)
        pane.add(top, weight=2)
        pane.add(bottom, weight=2)

        bar = ttk.Frame(top)
        bar.pack(fill="x")
        ttk.Button(bar, text="▶ Обновить всё", command=self.start_updates).pack(side="left")
        ttk.Button(bar, text="+ Программа", command=self.launcher_add).pack(side="left", padx=5)
        ttk.Button(bar, text="Удалить", command=self.launcher_remove).pack(side="left")
        ttk.Button(bar, text="↑ Выше", command=lambda:self.move_launcher(-1)).pack(side="left", padx=(10,2))
        ttk.Button(bar, text="↓ Ниже", command=lambda:self.move_launcher(1)).pack(side="left", padx=2)
        ttk.Button(bar, text="Изменить ожидание", command=self.launcher_edit_wait).pack(side="left", padx=8)
        ttk.Label(bar, text="Двойной клик = включить / выключить").pack(side="right")

        self.update_tree = self.make_tree(
            top,
            [("Вкл",55),("Программа",190),("Путь",550),("Ожидание",90),("Автоматизация",160)]
        )
        self.update_tree.bind("<Double-1>", self.launcher_toggle)
        self.update_tree.bind("<<TreeviewSelect>>", lambda e:self.refresh_launcher_steps())

        head = ttk.Frame(bottom)
        head.pack(fill="x")
        ttk.Label(head, text="Автоматизация выбранной программы", font=("Segoe UI",11,"bold")).pack(side="left")
        self.auto_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            head, text="Включить автоматизацию",
            variable=self.auto_enabled_var, command=self.toggle_launcher_automation
        ).pack(side="left", padx=15)
        ttk.Button(head, text="▶ Проверить только автоматизацию", command=self.test_selected_automation).pack(side="right")

        self.steps_tree = self.make_tree(
            bottom,
            [("№",45),("Действие",145),("Параметры",620)]
        )

        bb = ttk.Frame(bottom)
        bb.pack(fill="x")
        actions = [
            ("+ Ожидание", self.step_wait),
            ("+ Клик", lambda:self.capture_click_step(False)),
            ("+ Двойной клик", lambda:self.capture_click_step(True)),
            ("+ Клавиша", self.step_key),
            ("+ Текст", self.step_text),
            ("+ Логин", lambda:self.step_cred("username")),
            ("+ Пароль", lambda:self.step_cred("password")),
            ("+ Запуск", self.step_launch),
            ("↑ Шаг", lambda:self.move_step(-1)),
            ("↓ Шаг", lambda:self.move_step(1)),
            ("Редактировать", self.edit_step),
            ("Удалить шаг", self.step_remove),
            ("Аккаунты", self.accounts_window),
        ]
        for label, cmd in actions:
            ttk.Button(bb, text=label, command=cmd).pack(side="left", padx=2, pady=5)

        self.refresh_launchers()

    def selected_launcher_index(self):
        sel = self.update_tree.selection()
        return self.update_tree.index(sel[0]) if sel else None

    def normalize_launcher(self, item):
        item.setdefault("enabled", True)
        item.setdefault("wait", 0)
        item.setdefault("automation_enabled", False)
        item.setdefault("steps", [])
        return item

    def refresh_launchers(self, select_index=None):
        self.clear_tree(self.update_tree)
        for item in self.cfg["launchers"]:
            self.normalize_launcher(item)
            auto = "ВКЛ" if item.get("automation_enabled") and item.get("steps") else "—"
            self.update_tree.insert(
                "", "end",
                values=("✓" if item["enabled"] else "", item["name"], item["path"], item["wait"], auto)
            )
        if self.update_tree.get_children():
            if select_index is None:
                select_index = 0
            select_index = max(0, min(select_index, len(self.update_tree.get_children())-1))
            iid = self.update_tree.get_children()[select_index]
            self.update_tree.selection_set(iid)
            self.update_tree.focus(iid)
        self.refresh_launcher_steps()

    def launcher_toggle(self, event=None):
        idx = self.selected_launcher_index()
        if idx is None: return
        self.cfg["launchers"][idx]["enabled"] = not self.cfg["launchers"][idx].get("enabled", True)
        save_config(self.cfg)
        self.refresh_launchers(idx)

    def move_launcher(self, direction):
        idx = self.selected_launcher_index()
        if idx is None: return
        new = idx + direction
        if new < 0 or new >= len(self.cfg["launchers"]): return
        self.cfg["launchers"][idx], self.cfg["launchers"][new] = self.cfg["launchers"][new], self.cfg["launchers"][idx]
        save_config(self.cfg)
        self.refresh_launchers(new)

    def launcher_add(self):
        path = filedialog.askopenfilename(
            title="Выбери EXE / LNK / BAT",
            filetypes=[("Программы","*.exe *.lnk *.bat"),("Все файлы","*.*")]
        )
        if not path: return
        self.cfg["launchers"].append({
            "enabled": True, "name": Path(path).stem, "path": path, "wait": 60,
            "automation_enabled": False, "steps": []
        })
        save_config(self.cfg)
        self.refresh_launchers(len(self.cfg["launchers"])-1)

    def launcher_remove(self):
        idx = self.selected_launcher_index()
        if idx is None: return
        name = self.cfg["launchers"][idx]["name"]
        if messagebox.askyesno("Подтверждение", f"Удалить из списка?\n\n{name}"):
            self.cfg["launchers"].pop(idx)
            save_config(self.cfg)
            self.refresh_launchers(max(0, idx-1))

    def launcher_edit_wait(self):
        idx = self.selected_launcher_index()
        if idx is None: return
        item = self.cfg["launchers"][idx]
        sec = simpledialog.askinteger(
            "Ожидание",
            f"{item['name']}\n\nСколько секунд ждать после запуска?",
            initialvalue=int(item.get("wait",0)), minvalue=0, maxvalue=3600
        )
        if sec is not None:
            item["wait"] = sec
            save_config(self.cfg)
            self.refresh_launchers(idx)

    def refresh_launcher_steps(self):
        if not hasattr(self, "steps_tree"): return
        self.clear_tree(self.steps_tree)
        idx = self.selected_launcher_index()
        if idx is None:
            self.auto_enabled_var.set(False)
            return
        item = self.normalize_launcher(self.cfg["launchers"][idx])
        self.auto_enabled_var.set(bool(item.get("automation_enabled", False)))
        for i, s in enumerate(item.get("steps", []), 1):
            t = s.get("type","")
            if t == "wait": par = f'{s.get("seconds",0)} сек.'
            elif t in ("click","double_click"): par = f'x={s.get("x")} y={s.get("y")}'
            elif t == "key": par = s.get("key","")
            elif t == "text": par = s.get("text","")
            elif t in ("username","password"): par = "профиль: " + s.get("profile","")
            elif t == "launch": par = s.get("path","")
            else: par = ""
            self.steps_tree.insert("", "end", values=(i,t,par))

    def toggle_launcher_automation(self):
        idx = self.selected_launcher_index()
        if idx is None: return
        self.cfg["launchers"][idx]["automation_enabled"] = self.auto_enabled_var.get()
        save_config(self.cfg)
        self.refresh_launchers(idx)

    def append_step(self, step):
        idx = self.selected_launcher_index()
        if idx is None:
            messagebox.showinfo("Автоматизация","Сначала выбери программу.")
            return
        self.normalize_launcher(self.cfg["launchers"][idx])
        self.cfg["launchers"][idx]["steps"].append(step)
        save_config(self.cfg)
        self.refresh_launchers(idx)

    def selected_step_index(self):
        sel = self.steps_tree.selection()
        return self.steps_tree.index(sel[0]) if sel else None

    def move_step(self, direction):
        idx = self.selected_launcher_index()
        sidx = self.selected_step_index()
        if idx is None or sidx is None: return
        steps = self.cfg["launchers"][idx].setdefault("steps",[])
        new = sidx + direction
        if new < 0 or new >= len(steps): return
        steps[sidx], steps[new] = steps[new], steps[sidx]
        save_config(self.cfg)
        self.refresh_launcher_steps()
        iid = self.steps_tree.get_children()[new]
        self.steps_tree.selection_set(iid)
        self.steps_tree.focus(iid)

    def edit_step(self):
        idx = self.selected_launcher_index()
        sidx = self.selected_step_index()
        if idx is None or sidx is None:
            messagebox.showinfo("Редактирование","Выбери шаг.")
            return
        s = self.cfg["launchers"][idx]["steps"][sidx]
        t = s.get("type")
        if t == "wait":
            v = simpledialog.askinteger("Ожидание","Секунд:",initialvalue=int(s.get("seconds",0)),minvalue=0,maxvalue=3600)
            if v is not None: s["seconds"] = v
        elif t in ("click","double_click"):
            if messagebox.askyesno("Координата","Перезаписать точку новым нажатием мыши?"):
                self.capture_click_step(t=="double_click", replace_index=sidx)
                return
        elif t == "key":
            v = simpledialog.askstring("Клавиша","Клавиша:",initialvalue=s.get("key",""))
            if v: s["key"] = v.upper().strip()
        elif t == "text":
            v = simpledialog.askstring("Текст","Текст:",initialvalue=s.get("text",""))
            if v is not None: s["text"] = v
        elif t in ("username","password"):
            v = simpledialog.askstring("Профиль","Имя профиля:",initialvalue=s.get("profile",""))
            if v: s["profile"] = v.strip()
        elif t == "launch":
            v = filedialog.askopenfilename(title="Выбери EXE / LNK / BAT")
            if v: s["path"] = v
        save_config(self.cfg)
        self.refresh_launcher_steps()

    def step_wait(self):
        n = simpledialog.askinteger("Ожидание","Секунд:",minvalue=0,maxvalue=3600)
        if n is not None: self.append_step({"type":"wait","seconds":n})

    def capture_click_step(self, double=False, replace_index=None):
        idx = self.selected_launcher_index()
        if idx is None:
            messagebox.showinfo("Автоматизация","Сначала выбери программу.")
            return
        action = "двойного клика" if double else "клика"
        if not messagebox.askokcancel(
            "Выбрать точку мышью",
            f"После OK окно COLIZEUM PC Manager спрячется.\n\n"
            f"Один раз нажми мышью на нужное место для {action}.\n"
            f"X/Y запишутся автоматически.\n\nESC — отмена."
        ): return

        self.status_var.set("Жду нажатие мышью по нужному месту...")
        self.withdraw()

        def worker():
            while user32.GetAsyncKeyState(0x01) & 0x8000: time.sleep(.03)
            time.sleep(.2)
            while True:
                if user32.GetAsyncKeyState(0x1B) & 0x8000:
                    self.after(0,self.deiconify)
                    self.after(0,lambda:self.status_var.set("Выбор точки отменён"))
                    return
                if user32.GetAsyncKeyState(0x01) & 0x8000:
                    x,y = mouse_pos()
                    while user32.GetAsyncKeyState(0x01) & 0x8000: time.sleep(.01)
                    step={"type":"double_click" if double else "click","x":int(x),"y":int(y)}
                    def finish():
                        self.deiconify(); self.lift(); self.focus_force()
                        current = self.selected_launcher_index()
                        if current is None: return
                        if replace_index is None:
                            self.cfg["launchers"][current].setdefault("steps",[]).append(step)
                        else:
                            self.cfg["launchers"][current]["steps"][replace_index] = step
                        save_config(self.cfg)
                        self.refresh_launcher_steps()
                        self.status_var.set(f"Точка сохранена: x={x}, y={y}")
                    self.after(0,finish)
                    return
                time.sleep(.02)
        threading.Thread(target=worker,daemon=True).start()

    def step_key(self):
        k=simpledialog.askstring("Клавиша","ENTER, TAB, ESC, F1-F12 или буква:")
        if k:self.append_step({"type":"key","key":k.upper().strip()})

    def step_text(self):
        v=simpledialog.askstring("Текст","Что ввести:")
        if v is not None:self.append_step({"type":"text","text":v})

    def step_cred(self,kind):
        p=simpledialog.askstring("Аккаунт","Имя профиля из раздела «Аккаунты»:")
        if p:self.append_step({"type":kind,"profile":p.strip()})

    def step_launch(self):
        p=filedialog.askopenfilename(title="EXE / LNK / BAT",filetypes=[("Программы","*.exe *.lnk *.bat"),("Все","*.*")])
        if p:self.append_step({"type":"launch","path":p})

    def step_remove(self):
        idx=self.selected_launcher_index(); sidx=self.selected_step_index()
        if idx is None or sidx is None:return
        self.cfg["launchers"][idx]["steps"].pop(sidx)
        save_config(self.cfg); self.refresh_launcher_steps()

    def accounts_window(self):
        w=tk.Toplevel(self); w.title("Аккаунты"); w.geometry("520x285")
        ttk.Label(w,text="Пароль хранится в Windows Credential Manager,\nа не в config.json.",justify="left").pack(anchor="w",padx=12,pady=10)
        pv,uv,pwv=tk.StringVar(),tk.StringVar(),tk.StringVar()
        f=ttk.Frame(w); f.pack(fill="x",padx=12)
        for r,(lab,var,show) in enumerate([("Профиль:",pv,""),("Логин:",uv,""),("Пароль:",pwv,"*")]):
            ttk.Label(f,text=lab).grid(row=r,column=0,sticky="w",pady=5)
            ttk.Entry(f,textvariable=var,show=show,width=45).grid(row=r,column=1,pady=5)
        def save():
            if not pv.get().strip():messagebox.showerror("Ошибка","Укажи профиль.");return
            try:
                save_credential(pv.get().strip(),uv.get(),pwv.get()); pwv.set("")
                messagebox.showinfo("Аккаунты","Сохранено в Windows Credential Manager.")
            except Exception as e:messagebox.showerror("Ошибка",str(e))
        ttk.Button(w,text="Сохранить / обновить",command=save).pack(pady=12)

    def execute_steps(self, item, log):
        steps = item.get("steps", [])
        for i,s in enumerate(steps,1):
            t=s.get("type")
            self.after(0,lambda i=i,n=t,total=len(steps),name=item["name"]:
                       self.status_var.set(f"{name}: автоматизация {i}/{total} — {n}"))
            if t=="wait":
                sec=max(0,int(s.get("seconds",0))); time.sleep(sec); log.write(f"{item['name']} | ОЖИДАНИЕ: {sec} сек.")
            elif t=="click":
                mouse_click(s["x"],s["y"]); log.write(f"{item['name']} | КЛИК: x={s['x']} y={s['y']}")
            elif t=="double_click":
                mouse_click(s["x"],s["y"],True); log.write(f"{item['name']} | ДВОЙНОЙ КЛИК: x={s['x']} y={s['y']}")
            elif t=="key":
                press_key(s["key"]); log.write(f"{item['name']} | КЛАВИША: {s['key']}")
            elif t=="text":
                type_unicode(s.get("text","")); log.write(f"{item['name']} | ВВЕДЁН ТЕКСТ")
            elif t in ("username","password"):
                u,p=read_credential(s["profile"]); type_unicode(u if t=="username" else p)
                log.write(f"{item['name']} | " + ("ВВЕДЁН ЛОГИН" if t=="username" else "ВВЕДЁН ПАРОЛЬ"))
            elif t=="launch":
                launch_path(s["path"]); log.write(f"{item['name']} | ЗАПУЩЕНО: {s['path']}")
            time.sleep(.15)

    def test_selected_automation(self):
        idx=self.selected_launcher_index()
        if idx is None:return
        item=json.loads(json.dumps(self.cfg["launchers"][idx],ensure_ascii=False))
        if not item.get("steps"):
            messagebox.showinfo("Автоматизация","У этой программы пока нет шагов."); return
        if not messagebox.askyesno("Тест",f"Выполнить только автоматизацию для «{item['name']}»?\n\nСама программа автоматически запускаться не будет."):
            return
        threading.Thread(target=self.automation_test_worker,args=(item,),daemon=True).start()

    def automation_test_worker(self,item):
        log=LogWriter("AutomationTest")
        try:
            self.execute_steps(item,log); log.finish("ТЕСТ ЗАВЕРШЁН: ошибок=0")
            self.after(0,lambda:messagebox.showinfo("Тест","Автоматизация выполнена."))
        except Exception as e:
            log.write(f"ОШИБКА: {e}"); log.finish("ТЕСТ ОСТАНОВЛЕН")
            self.after(0,lambda e=e:messagebox.showerror("Ошибка",str(e)))
        self.after(0,self.refresh_logs)

    def start_updates(self):
        if self.update_running:
            messagebox.showinfo("Обновление","Обновление уже выполняется."); return
        selected=[json.loads(json.dumps(self.normalize_launcher(x),ensure_ascii=False)) for x in self.cfg["launchers"] if x.get("enabled",True)]
        if not selected:
            messagebox.showinfo("Обновление","Нет включённых программ."); return
        if not messagebox.askyesno("Обновление игр и приложений",f"Последовательно обработать программ: {len(selected)}?"):
            return
        self.update_running=True
        self.progress.start(12)
        threading.Thread(target=self.update_worker,args=(selected,),daemon=True).start()

    def update_worker(self, selected):
        log=LogWriter("GameUpdate"); ok=0; errors=0
        for i,item in enumerate(selected,1):
            name=item["name"]
            self.after(0,lambda n=name,i=i,t=len(selected):self.status_var.set(f"Обновление {i}/{t}: {n}"))
            try:
                launch_path(item["path"]); ok+=1; log.write(f"ЗАПУЩЕН: {name} | {item['path']}")
                wait=max(0,int(item.get("wait",0)))
                if wait:
                    log.write(f"{name} | ОЖИДАНИЕ ПОСЛЕ ЗАПУСКА: {wait} сек."); time.sleep(wait)
                if item.get("automation_enabled") and item.get("steps"):
                    log.write(f"{name} | СТАРТ АВТОМАТИЗАЦИИ")
                    self.execute_steps(item,log)
                    log.write(f"{name} | АВТОМАТИЗАЦИЯ ЗАВЕРШЕНА")
            except Exception as e:
                errors+=1; log.write(f"ОШИБКА: {name} | {e}")
        log.finish(f"ИТОГ: запущено={ok}, ошибок={errors}")
        self.update_running=False
        def done():
            self.progress.stop(); self.refresh_logs()
            self.status_var.set(f"Обновление завершено | Запущено: {ok} | Ошибок: {errors}")
            messagebox.showinfo("Обновление завершено",f"Запущено: {ok}\nОшибок: {errors}")
        self.after(0,done)

    # -------------------- Логи --------------------

    def build_logs_tab(self):
        bar = ttk.Frame(self.logs_tab)
        bar.pack(fill="x")

        ttk.Button(
            bar,
            text="Обновить",
            command=self.refresh_logs
        ).pack(side="left")

        ttk.Button(
            bar,
            text="Открыть папку Logs",
            command=lambda: os.startfile(LOGS_DIR)
        ).pack(side="left", padx=8)

        ttk.Button(
            bar,
            text="Открыть выбранный лог",
            command=self.open_selected_log
        ).pack(side="left")

        self.logs_tree = self.make_tree(
            self.logs_tab,
            [("Дата", 180), ("Файл", 650), ("Размер", 120)]
        )

        self.refresh_logs()

    def refresh_logs(self):
        if not hasattr(self, "logs_tree"):
            return

        self.clear_tree(self.logs_tree)

        files = sorted(
            LOGS_DIR.rglob("*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for p in files:
            stamp = datetime.fromtimestamp(
                p.stat().st_mtime
            ).strftime("%d.%m.%Y %H:%M:%S")

            rel = str(p.relative_to(LOGS_DIR))
            size = f"{p.stat().st_size / 1024:.1f} KB"

            self.logs_tree.insert(
                "", "end",
                values=(stamp, rel, size)
            )

    def open_selected_log(self):
        sel = self.logs_tree.selection()
        if not sel:
            return

        rel = self.logs_tree.item(
            sel[0],
            "values"
        )[1]

        os.startfile(str(LOGS_DIR / rel))

    # -------------------- Настройки --------------------

    def build_settings_tab(self):
        frame = ttk.Frame(self.settings_tab)
        frame.pack(anchor="nw", fill="x")

        ttk.Label(
            frame,
            text="Диск для очистки:"
        ).grid(row=0, column=0, sticky="w", pady=8)

        self.drive_var = tk.StringVar(
            value=self.cfg["drive"]
        )
        ttk.Entry(
            frame,
            textvariable=self.drive_var,
            width=20
        ).grid(row=0, column=1, sticky="w")

        ttk.Label(
            frame,
            text="Хранить логи, дней:"
        ).grid(row=1, column=0, sticky="w", pady=8)

        self.log_days_var = tk.IntVar(
            value=int(self.cfg.get("log_days", 30))
        )
        ttk.Spinbox(
            frame,
            from_=1,
            to=365,
            textvariable=self.log_days_var,
            width=8
        ).grid(row=1, column=1, sticky="w")

        ttk.Button(
            frame,
            text="Сохранить настройки",
            command=self.save_settings
        ).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
            pady=15
        )


    def save_settings(self):
        drive = self.drive_var.get().strip()
        if not drive.endswith("\\"):
            drive += "\\"

        self.cfg["drive"] = drive
        self.cfg["log_days"] = int(
            self.log_days_var.get()
        )

        save_config(self.cfg)
        purge_old_logs(self.cfg["log_days"])

        messagebox.showinfo(
            "Настройки",
            "Настройки сохранены."
        )

if __name__ == "__main__":
    PCManager().mainloop()
