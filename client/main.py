import json, socket, http.client
import flet as ft

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

    try:
        saved_ip = page.client_storage.get("saved_ip") or DEFAULT_WIFI_IP
    except Exception:
        saved_ip = DEFAULT_WIFI_IP

    ip_input = ft.TextField(
        label="IP адрес ПК", value=saved_ip,
        width=200, height=38, text_size=12,
        border_color="#252550", focused_border_color=ACCENT,
        bgcolor=BG2, color=FG, cursor_color=ACCENT,
    )

    status_text = ft.Text("", size=11, color=FG2)
    progress = ft.ProgressBar(visible=False, color=ACCENT, height=2)

    grid = ft.GridView(
        expand=True, runs_count=3,
        max_extent=110, child_aspect_ratio=1.0,
        spacing=8, run_spacing=8, padding=10,
    )

    edit_stack = ft.Stack(expand=True)
    edit_wrapper = ft.Container(content=edit_stack, expand=True, visible=False)
    _edit_refs = {}

    def build_tiles():
        s = int(_TILE_SIZE)
        cols = calc_cols(s)
        gap = max(4, s // 12)
        grid.runs_count = cols
        grid.max_extent = s
        grid.spacing = gap
        grid.run_spacing = gap
        grid.controls.clear()

        for btn in _LAST_BUTTONS:
            bid = btn["id"]
            label = btn.get("label", "?")
            tile = ft.Container(
                content=ft.Text(label, size=max(8, s // 9),
                              weight=ft.FontWeight.W_600,
                              color=FG, text_align=ft.TextAlign.CENTER),
                width=s, height=s,
                bgcolor=BG2, border_radius=12,
                alignment=ft.Alignment(0, 0),
                ink=True,
                on_click=lambda e, b=bid: _on_press(CONNECTED_HOST, b),
            )
            grid.controls.append(tile)
        page.update()

    def build_edit_tiles():
        edit_stack.controls.clear()
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
            )

            move_gd = ft.GestureDetector(
                content=tile_bg,
                on_tap=lambda e, b=bid: _select_btn(b),
                on_pan_update=lambda e, b=bid: _move_btn(e, b),
            )

            if selected:
                hs = max(20, min(36, bw // 4))
                corner_gd = ft.GestureDetector(
                    content=ft.Container(
                        bgcolor=ACCENT,
                        width=hs, height=hs,
                        border_radius=hs,
                    ),
                    on_pan_update=lambda e, b=bid: _resize_btn(e, b),
                )
                btn_stack = ft.Stack([
                    move_gd,
                    ft.Container(content=corner_gd, right=0, bottom=0),
                ], width=bw, height=bh)
            else:
                btn_stack = move_gd

            wrapper = ft.Container(content=btn_stack, left=bx, top=by)
            _edit_refs[bid] = wrapper
            edit_stack.controls.append(wrapper)
        page.update()

    def _select_btn(bid):
        global _SELECTED_BTN
        _SELECTED_BTN = bid if _SELECTED_BTN != bid else None
        build_edit_tiles()

    def _move_btn(e, bid):
        w = _edit_refs.get(bid)
        if not w:
            return
        for b in _LAST_BUTTONS:
            if b["id"] == bid:
                b["x"] = b.get("x", 0) + e.delta_x
                b["y"] = b.get("y", 0) + e.delta_y
                w.left = b["x"]
                w.top = b["y"]
                break
        page.update()

    def _resize_btn(e, bid):
        w = _edit_refs.get(bid)
        if not w:
            return
        for b in _LAST_BUTTONS:
            if b["id"] == bid:
                new_w = max(60, min(300, b.get("width", 100) + e.delta_x))
                new_h = max(60, min(300, b.get("height", 100) + e.delta_y))
                b["width"] = new_w
                b["height"] = new_h
                w.width = new_w
                w.height = new_h
                stack = w.content
                stack.width = new_w
                stack.height = new_h
                for child in stack.controls:
                    if isinstance(child, ft.GestureDetector):
                        child.width = new_w
                        child.height = new_h
                        tile = child.content
                        if isinstance(tile, ft.Container):
                            tile.width = new_w
                            tile.height = new_h
                            if tile.content and isinstance(tile.content, ft.Text):
                                tile.content.size = max(8, new_w // 9)
                break
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
        try:
            do_connect(ip_input.value.strip() or DEFAULT_WIFI_IP)
        except Exception as ex:
            progress.visible = False
            status_text.value = f"Исключение: {type(ex).__name__}: {ex}"
            status_text.color = _DANGER
            page.update()

    def try_usb(e):
        if _EDIT_MODE:
            toggle_edit_mode(e)
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
            if CONNECTED_HOST:
                _save_config(CONNECTED_HOST, _LAST_BUTTONS)
            edit_wrapper.visible = False
            grid.visible = True
            build_tiles()
            edit_btn.icon = ft.Icons.EDIT
            edit_btn.icon_color = FG2
            status_text.value = "Подключено"
            status_text.color = _SUCCESS
        else:
            _EDIT_MODE = True
            _SELECTED_BTN = None
            _init_positions()
            grid.visible = False
            edit_wrapper.visible = True
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
        ], spacing=6, tight=True),
        padding=ft.Padding(left=15, right=10, top=0, bottom=5),
    )

    page.add(header, settings_panel, progress, grid, edit_wrapper)


if __name__ == "__main__":
    ft.app(target=main)
