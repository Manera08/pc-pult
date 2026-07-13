import json, socket, http.client, os, tempfile
import flet as ft

_PRESETS_FILE = os.path.join(tempfile.gettempdir(), "rh_presets.json")

DEFAULT_WIFI_IP = "192.168.1.100"
SERVER_PORT = 8789
TIMEOUT = 5

BG = "#0f0f23"
BG2 = "#1a1a3e"
ACCENT = "#6c63ff"
FG = "#ffffff"
FG2 = "#b0b0cc"

CONNECTED_HOST = None
_LAST_BUTTONS = []
_SETTINGS_SHOWN = True
_TILE_SIZE = 100.0
_EDIT_MODE = False
_SELECTED_BTN = None
_SUCCESS = "#00c853"
_DANGER = "#ff1744"


def _http_raw(method, host, port, path, data=None):
    conn = None
    try:
        conn = http.client.HTTPConnection(host, port, timeout=TIMEOUT)
        body = json.dumps(data).encode() if data else None
        conn.request(method, f"/{path}", body=body,
                     headers={"Content-Type": "application/json",
                              "Connection": "close"})
        resp = conn.getresponse()
        if resp.status != 200:
            return (False, f"Код: {resp.status}")
        return (True, json.loads(resp.read()))
    except socket.timeout:
        return (False, "Таймаут 5с")
    except ConnectionRefusedError:
        return (False, "Сервер не отвечает")
    except socket.gaierror:
        return (False, "Неверный IP")
    except Exception as e:
        return (False, f"{type(e).__name__}")
    finally:
        if conn:
            conn.close()


def calc_cols(size):
    if size >= 150: return 2
    if size >= 100: return 3
    return 4


def _save_config(host, buttons):
    _http_raw("PUT", host, SERVER_PORT, "config", {"buttons": buttons})


def main(page: ft.Page):
    global CONNECTED_HOST, _SETTINGS_SHOWN, _TILE_SIZE, _LAST_BUTTONS, _EDIT_MODE, _SELECTED_BTN
    page.title = "Remote Hotkeys"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 0
    page.spacing = 0

    _presets = []

    try:
        saved_ip = page.client_storage.get("saved_ip") or DEFAULT_WIFI_IP
    except Exception:
        saved_ip = DEFAULT_WIFI_IP

    def _load_presets():
        _presets.clear()
        try:
            with open(_PRESETS_FILE, "r") as f:
                _presets.extend(json.load(f))
        except Exception:
            pass

    def _save_presets():
        try:
            with open(_PRESETS_FILE, "w") as f:
                json.dump(_presets, f)
        except Exception:
            pass

    _load_presets()

    def _rebuild_presets():
        preset_row.controls.clear()
        for i, p in enumerate(_presets):
            btn = ft.ElevatedButton(
                p["name"], height=28, color=FG2, bgcolor=BG2,
                data=p["ip"],
                on_click=lambda e: _use_preset(e.control.data),
            )
            del_btn = ft.IconButton(
                ft.Icons.CLOSE, icon_size=12, icon_color=_DANGER,
                height=20, width=20,
                data=i,
                on_click=lambda e: _del_preset(e.control.data),
            )
            preset_row.controls.append(
                ft.Row([btn, del_btn], spacing=2)
            )
        page.update()

    def _use_preset(ip):
        ip_input.value = ip
        try:
            page.client_storage.set("saved_ip", ip)
        except Exception:
            pass
        try_connect(None)

    def _save_preset(e):
        ip = ip_input.value.strip()
        if not ip:
            return
        name = preset_name_input.value.strip() or ip
        for p in _presets:
            if p["ip"] == ip:
                p["name"] = name
                _save_presets()
                _rebuild_presets()
                return
        _presets.append({"name": name, "ip": ip})
        _save_presets()
        preset_name_input.value = ""
        _rebuild_presets()

    def _del_preset(idx):
        if 0 <= idx < len(_presets):
            _presets.pop(idx)
            _save_presets()
            _rebuild_presets()

    ip_input = ft.TextField(
        label="IP адрес ПК", value=saved_ip,
        width=200, height=38, text_size=12,
        border_color="#252550", focused_border_color=ACCENT,
        bgcolor=BG2, color=FG, cursor_color=ACCENT,
    )

    status_text = ft.Text("", size=11, color=FG2)
    progress = ft.ProgressBar(visible=False, color=ACCENT, height=2)

    preset_name_input = ft.TextField(
        hint_text="Имя пресета", width=100, height=32, text_size=11,
        border_color="#252550", focused_border_color=ACCENT,
        bgcolor=BG2, color=FG, cursor_color=ACCENT,
    )
    preset_row = ft.Row(spacing=4, wrap=True, width=340)

    main_stack = ft.Stack(expand=True)
    _edit_refs = {}

    sx = ft.Slider(min=0, max=800, value=0, divisions=80, width=180, height=24,
                   active_color=ACCENT, inactive_color=BG2, thumb_color=ACCENT,
                   on_change=lambda e: _slider_update())
    sy = ft.Slider(min=0, max=800, value=0, divisions=80, width=180, height=24,
                   active_color=ACCENT, inactive_color=BG2, thumb_color=ACCENT,
                   on_change=lambda e: _slider_update())
    sw = ft.Slider(min=60, max=300, value=100, divisions=24, width=180, height=24,
                   active_color=ACCENT, inactive_color=BG2, thumb_color=ACCENT,
                   on_change=lambda e: _slider_update())
    sh = ft.Slider(min=60, max=300, value=100, divisions=24, width=180, height=24,
                   active_color=ACCENT, inactive_color=BG2, thumb_color=ACCENT,
                   on_change=lambda e: _slider_update())
    sx_label = ft.Text("0", size=10, color=FG2)
    sy_label = ft.Text("0", size=10, color=FG2)
    sw_label = ft.Text("100", size=10, color=FG2)
    sh_label = ft.Text("100", size=10, color=FG2)

    slider_panel = ft.Container(
        content=ft.Column([
            ft.Row([ft.Text("X:", size=10, color=FG2, width=16), sx, sx_label]),
            ft.Row([ft.Text("Y:", size=10, color=FG2, width=16), sy, sy_label]),
            ft.Row([ft.Text("W:", size=10, color=FG2, width=16), sw, sw_label]),
            ft.Row([ft.Text("H:", size=10, color=FG2, width=16), sh, sh_label]),
        ], spacing=2, tight=True),
        padding=ft.Padding(left=15, right=10, top=4, bottom=4),
        bgcolor="#151530",
        border_radius=8,
        visible=False,
    )

    def _slider_update():
        bid = _SELECTED_BTN
        if not bid:
            return
        for b in _LAST_BUTTONS:
            if b["id"] == bid:
                b["x"] = int(sx.value)
                b["y"] = int(sy.value)
                b["width"] = int(sw.value)
                b["height"] = int(sh.value)
                _update_btn_pos(bid)
                break

    def _update_btn_pos(bid):
        w = _edit_refs.get(bid)
        if not w:
            return
        for b in _LAST_BUTTONS:
            if b["id"] == bid:
                w.left = b["x"]
                w.top = b["y"]
                w.width = b["width"]
                w.height = b["height"]
                tile = w.content
                if isinstance(tile, ft.Container):
                    tile.width = b["width"]
                    tile.height = b["height"]
                    if tile.content and isinstance(tile.content, ft.Text):
                        tile.content.size = max(8, b["width"] // 9)
                break
        page.update()

    def build_tiles():
        main_stack.controls.clear()
        for btn in _LAST_BUTTONS:
            bid = btn["id"]
            label = btn.get("label", "?")
            bw = btn.get("width", 100)
            bh = btn.get("height", 100)
            bx = btn.get("x", 0)
            by = btn.get("y", 0)

            tile = ft.Container(
                content=ft.Text(label, size=max(8, bw // 9),
                              weight=ft.FontWeight.W_600,
                              color=FG, text_align=ft.TextAlign.CENTER),
                width=bw, height=bh,
                bgcolor=BG2, border_radius=12,
                alignment=ft.Alignment(0, 0),
                ink=True,
                on_click=lambda e, b=bid: _on_press(CONNECTED_HOST, b),
            )

            wrapper = ft.Container(content=tile, left=bx, top=by, width=bw, height=bh)
            main_stack.controls.append(wrapper)
        page.update()

    def build_edit_tiles():
        main_stack.controls.clear()
        _edit_refs.clear()
        for btn in _LAST_BUTTONS:
            bid = btn["id"]
            label = btn.get("label", "?")
            bw = btn.get("width", 100)
            bh = btn.get("height", 100)
            bx = btn.get("x", 0)
            by = btn.get("y", 0)
            selected = (_SELECTED_BTN == bid)

            border = None
            if selected:
                border = ft.Border(
                    left=ft.BorderSide(2, ACCENT),
                    top=ft.BorderSide(2, ACCENT),
                    right=ft.BorderSide(2, ACCENT),
                    bottom=ft.BorderSide(2, ACCENT),
                )

            tile_bg = ft.Container(
                content=ft.Text(label, size=max(8, bw // 9),
                              weight=ft.FontWeight.W_600,
                              color=FG, text_align=ft.TextAlign.CENTER),
                width=bw, height=bh,
                bgcolor=BG2, border_radius=12,
                border=border,
                alignment=ft.Alignment(0, 0),
                on_click=lambda e, b=bid: _select_btn(b),
            )

            wrapper = ft.Container(content=tile_bg, left=bx, top=by, width=bw, height=bh)
            _edit_refs[bid] = wrapper
            main_stack.controls.append(wrapper)
        page.update()

    def _select_btn(bid):
        global _SELECTED_BTN
        _SELECTED_BTN = bid if _SELECTED_BTN != bid else None
        build_edit_tiles()
        if _SELECTED_BTN:
            for b in _LAST_BUTTONS:
                if b["id"] == _SELECTED_BTN:
                    sx.value = b.get("x", 0)
                    sy.value = b.get("y", 0)
                    sw.value = b.get("width", 100)
                    sh.value = b.get("height", 100)
                    sx_label.value = str(int(sx.value))
                    sy_label.value = str(int(sy.value))
                    sw_label.value = str(int(sw.value))
                    sh_label.value = str(int(sh.value))
                    break
            slider_panel.visible = True
        else:
            slider_panel.visible = False
        page.update()

    def _on_press(host, bid):
        if _EDIT_MODE:
            _select_btn(bid)
            return
        if not host:
            return
        ok, val = _http_raw("POST", host, SERVER_PORT, "press", {"id": bid})
        if not ok:
            status_text.value = f"Ошибка: {val}"
            status_text.color = _DANGER
        else:
            status_text.value = "Подключено"
            status_text.color = _SUCCESS
        page.update()

    def _init_positions():
        s = int(_TILE_SIZE)
        cols = calc_cols(s)
        gap = max(4, s // 12)
        pad = 10
        for i, btn in enumerate(_LAST_BUTTONS):
            if "x" not in btn:
                btn["x"] = (i % cols) * (s + gap) + pad
            if "y" not in btn:
                btn["y"] = (i // cols) * (s + gap) + pad
            if "width" not in btn:
                btn["width"] = s
            if "height" not in btn:
                btn["height"] = s

    def do_connect(host):
        progress.visible = True
        status_text.value = "Подключение..."
        status_text.color = FG2
        page.update()

        ok, val = _http_raw("GET", host, SERVER_PORT, "config")

        if ok:
            global CONNECTED_HOST, _LAST_BUTTONS
            CONNECTED_HOST = host
            try:
                page.client_storage.set("saved_ip", host)
            except Exception:
                pass
            _LAST_BUTTONS = val.get("buttons", [])
            _init_positions()
            build_tiles()
            status_text.value = "Подключено"
            status_text.color = _SUCCESS
        else:
            status_text.value = f"Ошибка: {val}"
            status_text.color = _DANGER

        progress.visible = False
        page.update()

    def try_connect(e):
        if _EDIT_MODE:
            toggle_edit_mode(e)
        ip = ip_input.value.strip() or DEFAULT_WIFI_IP
        try:
            page.client_storage.set("saved_ip", ip)
        except Exception:
            pass
        try:
            do_connect(ip)
        except Exception as ex:
            progress.visible = False
            status_text.value = f"Исключение: {type(ex).__name__}: {ex}"
            status_text.color = _DANGER
            page.update()

    def try_usb(e):
        if _EDIT_MODE:
            toggle_edit_mode(e)
        try:
            page.client_storage.set("saved_ip", "127.0.0.1")
        except Exception:
            pass
        try:
            do_connect("127.0.0.1")
        except Exception as ex:
            progress.visible = False
            status_text.value = f"Исключение: {type(ex).__name__}: {ex}"
            status_text.color = _DANGER
            page.update()

    def refresh_config(e):
        if CONNECTED_HOST:
            if _EDIT_MODE:
                toggle_edit_mode(e)
            try_connect(e)

    def toggle_edit_mode(e):
        global _EDIT_MODE, _SELECTED_BTN

        if _EDIT_MODE:
            _EDIT_MODE = False
            _SELECTED_BTN = None
            slider_panel.visible = False
            if CONNECTED_HOST:
                _save_config(CONNECTED_HOST, _LAST_BUTTONS)
            build_tiles()
            edit_btn.icon = ft.Icons.EDIT
            edit_btn.icon_color = FG2
            status_text.value = "Подключено"
            status_text.color = _SUCCESS
        else:
            _EDIT_MODE = True
            _SELECTED_BTN = None
            _init_positions()
            build_edit_tiles()
            edit_btn.icon = ft.Icons.EDIT_OFF
            edit_btn.icon_color = ACCENT
            status_text.value = "Режим редактирования"
            status_text.color = ACCENT
        page.update()

    def toggle_settings(e):
        global _SETTINGS_SHOWN
        _SETTINGS_SHOWN = not _SETTINGS_SHOWN
        settings_panel.visible = _SETTINGS_SHOWN
        toggle_icon.icon = ft.Icons.EXPAND_LESS if _SETTINGS_SHOWN else ft.Icons.EXPAND_MORE
        page.update()

    toggle_icon = ft.IconButton(
        ft.Icons.EXPAND_LESS, icon_size=18, icon_color=FG2,
        on_click=toggle_settings,
    )



    edit_btn = ft.IconButton(
        ft.Icons.EDIT, icon_size=18, icon_color=FG2,
        on_click=toggle_edit_mode,
    )

    header = ft.Container(
        content=ft.Row([
            ft.Text("Remote Hotkeys", size=20, weight=ft.FontWeight.BOLD, color=FG),
            ft.Container(expand=True),
            edit_btn,
            toggle_icon,
            ft.IconButton(ft.Icons.REFRESH, icon_size=18,
                         icon_color=FG2, on_click=refresh_config),
        ]),
        padding=ft.Padding(left=15, top=45, right=5, bottom=5),
    )

    settings_panel = ft.Container(
        content=ft.Column([
            ft.Row([
                ip_input,
                ft.ElevatedButton("Подкл.", height=38, color="white",
                                bgcolor=ACCENT, on_click=try_connect),
            ]),
            ft.Row([
                ft.ElevatedButton("USB", height=32, color=FG2, bgcolor=BG2,
                                icon=ft.Icons.USB, on_click=try_usb),
                ft.Container(expand=True),
                status_text,
            ]),
            ft.Row([
                ft.Text("Пресеты:", size=10, color=FG2),
                preset_name_input,
                ft.ElevatedButton("+", height=28, width=28, color=FG2,
                                bgcolor=BG2, on_click=_save_preset),
            ]),
            preset_row,
        ], spacing=6, tight=True),
        padding=ft.Padding(left=15, right=10, top=0, bottom=5),
    )

    page.add(header, settings_panel, progress, slider_panel, main_stack)
    _rebuild_presets()


if __name__ == "__main__":
    ft.app(target=main)
