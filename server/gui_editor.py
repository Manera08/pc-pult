import threading, tkinter as tk
from tkinter import ttk, messagebox
from config_manager import get_buttons, add_button, update_button, delete_button
from key_handler import press_keys

_CAPTURE_ACTIVE = False
_captured_keys = []

BG = "#1a1a2e"
BG2 = "#16213e"
BG3 = "#0f3460"
FG = "#e0e0e0"
FG_DIM = "#7a7a9e"
ACCENT = "#e94560"
ACCENT2 = "#0f3460"
HOVER = "#533483"
ENTRY_BG = "#16213e"
ENTRY_FG = "#e0e0e0"
BORDER = "#2a2a4a"
SUCCESS = "#00b894"
DANGER = "#e94560"


def run_gui(api_port=8789):
    root = tk.Tk()
    root.title("ПК-Пульт — Редактор")
    root.geometry("800x600")
    root.minsize(650, 450)
    root.configure(bg=BG)
    try:
        root.state("zoomed")
    except Exception:
        pass
    EditorApp(root)
    root.mainloop()


class EditorApp:
    def __init__(self, root):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._build_ui()
        self.refresh_list()

    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG2, height=60)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)

        tk.Label(
            header, text="ПК-Пульт", font=("Segoe UI", 16, "bold"),
            bg=BG2, fg=FG
        ).pack(side=tk.LEFT, padx=20, pady=15)

        tk.Label(
            header, text="Редактор конфигурации",
            font=("Segoe UI", 10), bg=BG2, fg=FG_DIM
        ).pack(side=tk.LEFT, padx=(0, 20), pady=18)

        self.status_label = tk.Label(
            header, text="● API-сервер запущен",
            font=("Segoe UI", 9), bg=BG2, fg=SUCCESS
        )
        self.status_label.pack(side=tk.RIGHT, padx=20)

        toolbar = tk.Frame(self.root, bg=BG, height=50)
        toolbar.pack(fill=tk.X, padx=20, pady=(15, 0))

        self.add_btn = tk.Button(
            toolbar, text="+ Добавить кнопку",
            font=("Segoe UI", 10, "bold"), bg=ACCENT, fg="white",
            activebackground=HOVER, activeforeground="white",
            relief=tk.FLAT, padx=20, pady=8, cursor="hand2",
            command=self.add_new
        )
        self.add_btn.pack(side=tk.LEFT)

        tk.Button(
            toolbar, text="⟳ Обновить",
            font=("Segoe UI", 10), bg=BG3, fg=FG,
            activebackground=HOVER, activeforeground="white",
            relief=tk.FLAT, padx=15, pady=8, cursor="hand2",
            command=self.refresh_list
        ).pack(side=tk.LEFT, padx=(10, 0))

        list_frame = tk.Frame(self.root, bg=BG)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        columns_frame = tk.Frame(list_frame, bg=BG3, height=40)
        columns_frame.pack(fill=tk.X)
        columns_frame.pack_propagate(False)

        tk.Label(columns_frame, text="Название", font=("Segoe UI", 9, "bold"),
                 bg=BG3, fg=FG_DIM, width=25, anchor=tk.W).pack(side=tk.LEFT, padx=20, pady=10)
        tk.Label(columns_frame, text="Комбинация клавиш", font=("Segoe UI", 9, "bold"),
                 bg=BG3, fg=FG_DIM, width=25, anchor=tk.W).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Label(columns_frame, text="Действия", font=("Segoe UI", 9, "bold"),
                 bg=BG3, fg=FG_DIM, anchor=tk.W).pack(side=tk.LEFT, padx=10, pady=10)

        canvas_frame = tk.Frame(list_frame, bg=BG)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.inner_frame = tk.Frame(self.canvas, bg=BG)

        self.inner_frame.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor=tk.NW)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.bind_all("<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        footer = tk.Frame(self.root, bg=BG2, height=35)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        tk.Label(
            footer, text="ПК-Пульт v1.0.0  |  Порт: 8789  |  IP: 192.168.88.130",
            font=("Segoe UI", 8), bg=BG2, fg=FG_DIM
        ).pack(side=tk.LEFT, padx=15, pady=8)

    def refresh_list(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        buttons = get_buttons()
        if not buttons:
            tk.Label(
                self.inner_frame, text="Нет кнопок. Нажмите '+ Добавить кнопку'",
                font=("Segoe UI", 11), bg=BG, fg=FG_DIM
            ).pack(pady=40)
            return

        for btn in buttons:
            self._create_button_row(btn)

    def _create_button_row(self, btn):
        row = tk.Frame(self.inner_frame, bg=BG2, bd=1, relief=tk.FLAT)
        row.pack(fill=tk.X, pady=3, padx=2)

        hover_enter = lambda e, w=row: w.configure(bg=BG3)
        hover_leave = lambda e, w=row: w.configure(bg=BG2)
        row.bind("<Enter>", hover_enter)
        row.bind("<Leave>", hover_leave)

        label_var = tk.StringVar(value=btn.get("label", "?"))
        entry = tk.Entry(
            row, textvariable=label_var, font=("Segoe UI", 11),
            bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=FG,
            relief=tk.FLAT, bd=0, width=22
        )
        entry.pack(side=tk.LEFT, padx=20, pady=10)
        entry.bind("<FocusOut>", lambda e, bid=btn["id"], v=label_var:
                   update_button(bid, label=v.get()))

        keys = btn.get("keys", [])
        keys_str = " + ".join(keys) if keys else "(нет клавиш)"
        keys_fg = FG if keys else FG_DIM

        tk.Label(
            row, text=keys_str, font=("Segoe UI", 10),
            bg=BG2, fg=keys_fg, width=25, anchor=tk.W
        ).pack(side=tk.LEFT, padx=10, pady=10)

        btn_frame = tk.Frame(row, bg=BG2)
        btn_frame.pack(side=tk.LEFT, padx=10, pady=5)

        self._icon_button(btn_frame, "⌨", "Захватить", BG3,
                         lambda e, b=btn: self.start_capture(b))
        self._icon_button(btn_frame, "▶", "Тест", BG3,
                         lambda e, k=btn.get("keys", []): press_keys(k))
        self._icon_button(btn_frame, "✕", "Удалить", DANGER,
                         lambda e, b=btn: self.confirm_delete(b))

    def _icon_button(self, parent, text, tooltip, color, command):
        btn = tk.Label(
            parent, text=text, font=("Segoe UI", 12),
            bg=color, fg=FG, padx=10, pady=5, cursor="hand2"
        )
        btn.pack(side=tk.LEFT, padx=3)

        def on_enter(e): btn.configure(bg=HOVER)
        def on_leave(e): btn.configure(bg=color)
        def on_click(e): command(e)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", on_click)

    def add_new(self):
        add_button()
        self.refresh_list()

    def confirm_delete(self, btn):
        if messagebox.askyesno("Удаление", f"Удалить кнопку '{btn.get('label', '')}'?"):
            delete_button(btn["id"])
            self.refresh_list()

    def start_capture(self, btn):
        global _CAPTURE_ACTIVE, _captured_keys
        if _CAPTURE_ACTIVE:
            return

        _CAPTURE_ACTIVE = True
        _captured_keys = []

        dlg = tk.Toplevel(self.root)
        dlg.title("Захват клавиш")
        dlg.geometry("400x220")
        dlg.configure(bg=BG)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.attributes("-topmost", True)

        tk.Label(
            dlg, text="Нажмите комбинацию клавиш",
            font=("Segoe UI", 12, "bold"), bg=BG, fg=FG
        ).pack(pady=(20, 5))

        tk.Label(
            dlg, text="ESC — отмена",
            font=("Segoe UI", 9), bg=BG, fg=FG_DIM
        ).pack()

        keys_var = tk.StringVar(value="")
        keys_label = tk.Label(
            dlg, textvariable=keys_var, font=("Segoe UI", 14, "bold"),
            bg=BG, fg=ACCENT, pady=15
        )
        keys_label.pack()

        status_var = tk.StringVar(value="Ожидание нажатий...")
        status_label = tk.Label(
            dlg, textvariable=status_var, font=("Segoe UI", 9),
            bg=BG, fg=FG_DIM
        )
        status_label.pack()

        def on_key(event):
            if not _CAPTURE_ACTIVE:
                return
            if event.event_type == "down":
                name = event.name
                if name == "esc":
                    if _captured_keys:
                        finish()
                    else:
                        cancel()
                    return
                if name not in _captured_keys:
                    _captured_keys.append(name)
                    keys_var.set(" + ".join(_captured_keys))
                    status_var.set(f"{len(_captured_keys)} клавиш")

        def finish():
            global _CAPTURE_ACTIVE
            _CAPTURE_ACTIVE = False
            from key_handler import stop_capture
            stop_capture()
            if _captured_keys:
                update_button(btn["id"], keys=list(_captured_keys))
            self.refresh_list()
            dlg.destroy()

        def cancel():
            global _CAPTURE_ACTIVE, _captured_keys
            _CAPTURE_ACTIVE = False
            _captured_keys = []
            from key_handler import stop_capture
            stop_capture()
            dlg.destroy()

        def on_close_dlg():
            cancel()

        dlg.protocol("WM_DELETE_WINDOW", on_close_dlg)

        import keyboard as kb
        kb.hook(on_key)

    def on_close(self):
        self.root.destroy()
