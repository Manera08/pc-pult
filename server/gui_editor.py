import threading
import tkinter as tk
from tkinter import ttk, messagebox
from config_manager import get_buttons, add_button, update_button, delete_button
from key_handler import press_keys

_CAPTURE_ACTIVE = False
_captured_keys = []


def run_gui(api_port=8789):
    root = tk.Tk()
    root.title("ПК-Пульт — Редактор")
    root.geometry("750x550")
    root.minsize(600, 400)
    app = EditorApp(root)
    root.mainloop()


class EditorApp:
    def __init__(self, root):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._build_ui()
        self.refresh_list()

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(top, text="ПК-Пульт — Редактор конфигурации", font=("Arial", 14, "bold")).pack(side=tk.LEFT)
        ttk.Button(top, text="+ Добавить кнопку", command=self.add_new).pack(side=tk.RIGHT)

        columns = ("label", "keys", "actions")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("label", text="Название кнопки")
        self.tree.heading("keys", text="Комбинация клавиш")
        self.tree.heading("actions", text="Действия")
        self.tree.column("label", width=200)
        self.tree.column("keys", width=250)
        self.tree.column("actions", width=200)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        vsb = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.bind("<Double-1>", self.on_double_click)

        bottom = ttk.Frame(self.root, padding=8)
        bottom.pack(fill=tk.X)

        self.status_label = ttk.Label(bottom, text="Сервер: запущен", foreground="green")
        self.status_label.pack(side=tk.LEFT)

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for btn in get_buttons():
            keys_str = " + ".join(btn.get("keys", [])) if btn.get("keys") else "(нет)"
            self.tree.insert("", tk.END, iid=btn["id"], values=(btn["label"], keys_str, ""))

    def add_new(self):
        add_button()
        self.refresh_list()

    def on_double_click(self, event):
        item = self.tree.selection()
        if not item:
            return
        btn_id = item[0]
        btn = None
        for b in get_buttons():
            if b["id"] == btn_id:
                btn = b
                break
        if btn:
            EditDialog(self.root, btn, self.refresh_list)

    def on_close(self):
        self.root.destroy()


class EditDialog:
    def __init__(self, parent, btn, refresh_cb):
        self.btn = btn
        self.refresh_cb = refresh_cb
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Редактирование кнопки")
        self.dialog.geometry("450x250")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        ttk.Label(self.dialog, text="Название:").pack(padx=10, pady=(10, 0), anchor=tk.W)
        self.label_var = tk.StringVar(value=btn.get("label", ""))
        self.label_entry = ttk.Entry(self.dialog, textvariable=self.label_var, width=50)
        self.label_entry.pack(padx=10, pady=4, fill=tk.X)

        ttk.Label(self.dialog, text="Комбинация клавиш:").pack(padx=10, pady=(10, 0), anchor=tk.W)
        self.keys_var = tk.StringVar(value=" + ".join(btn.get("keys", [])) if btn.get("keys") else "")
        self.keys_entry = ttk.Entry(self.dialog, textvariable=self.keys_var, state="readonly", width=50)
        self.keys_entry.pack(padx=10, pady=4, fill=tk.X)

        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Захватить клавиши", command=self.start_capture).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Очистить", command=self.clear_keys).pack(side=tk.LEFT, padx=4)

        test_btn = ttk.Button(btn_frame, text="Тест", command=self.test_press)
        test_btn.pack(side=tk.LEFT, padx=4)

        bottom = ttk.Frame(self.dialog)
        bottom.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(bottom, text="Сохранить", command=self.save).pack(side=tk.RIGHT, padx=4)
        ttk.Button(bottom, text="Удалить", command=self.delete).pack(side=tk.RIGHT, padx=4)
        ttk.Button(bottom, text="Отмена", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=4)

        self.capture_status = ttk.Label(self.dialog, text="", foreground="blue")
        self.capture_status.pack(pady=4)

    def start_capture(self):
        global _CAPTURE_ACTIVE, _captured_keys
        if _CAPTURE_ACTIVE:
            return

        _CAPTURE_ACTIVE = True
        _captured_keys = []
        self.capture_status.config(text="Нажимайте комбинацию... ESC для завершения", foreground="orange")
        self.keys_var.set("")

        def on_key(event):
            global _CAPTURE_ACTIVE, _captured_keys
            if event.event_type == "down":
                name = event.name
                if name == "esc" and _captured_keys:
                    self.finish_capture()
                    return
                if name == "esc":
                    self.cancel_capture()
                    return
                if name not in _captured_keys:
                    _captured_keys.append(name)
                    self.keys_var.set(" + ".join(_captured_keys))

        import keyboard as kb
        kb.hook(on_key)

    def finish_capture(self):
        global _CAPTURE_ACTIVE
        _CAPTURE_ACTIVE = False
        from key_handler import stop_capture
        stop_capture()
        self.capture_status.config(text="Комбинация захвачена", foreground="green")

    def cancel_capture(self):
        global _CAPTURE_ACTIVE, _captured_keys
        _CAPTURE_ACTIVE = False
        _captured_keys = []
        from key_handler import stop_capture
        stop_capture()
        self.capture_status.config(text="Захват отменён", foreground="red")
        self.keys_var.set("")

    def clear_keys(self):
        global _captured_keys
        _captured_keys = []
        self.keys_var.set("")
        self.capture_status.config(text="")

    def test_press(self):
        press_keys(self.btn.get("keys", []))

    def save(self):
        label = self.label_var.get().strip()
        keys = list(_captured_keys) if _captured_keys else self.btn.get("keys", [])
        update_button(self.btn["id"], label=label, keys=keys)
        self.refresh_cb()
        self.dialog.destroy()

    def delete(self):
        if messagebox.askyesno("Подтверждение", "Удалить эту кнопку?"):
            delete_button(self.btn["id"])
            self.refresh_cb()
            self.dialog.destroy()
