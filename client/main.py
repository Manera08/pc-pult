import json, socket
import flet as ft

DEFAULT_WIFI_IP = "192.168.1.100"
SERVER_PORT = 8789
TIMEOUT = 5

BG = "#0f0f23"
BG2 = "#1a1a3e"
ACCENT = "#6c63ff"
SUCCESS = "#00c853"
DANGER = "#ff1744"
FG = "#ffffff"
FG2 = "#b0b0cc"

CONNECTED_HOST = None
_LAST_BUTTONS = []
_SETTINGS_SHOWN = True
_TILE_SIZE = 100.0
_DRAGGING = False


def _http_request(method, host, port, path, data=None):
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((host, port))
        body = json.dumps(data).encode() if data else b""
        req = f"{method} /{path} HTTP/1.1\r\nHost: {host}:{port}\r\n"
        if body:
            req += f"Content-Length: {len(body)}\r\n"
        req += "Connection: close\r\n\r\n"
        sock.sendall(req.encode() + body)

        resp = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            resp += chunk
        header_end = resp.find(b"\r\n\r\n")
        if header_end == -1:
            return None
        body_start = header_end + 4
        status_line = resp[: resp.find(b"\r\n")].decode()
        if "200" not in status_line:
            return None
        return json.loads(resp[body_start:].decode())
    except Exception:
        return None
    finally:
        if sock:
            sock.close()


def get_config(host):
    return _http_request("GET", host, SERVER_PORT, "config")


def send_press(host, btn_id):
    return _http_request("POST", host, SERVER_PORT, "press", {"id": btn_id})


def calc_cols(size):
    if size >= 150: return 2
    if size >= 100: return 3
    return 4


def main(page: ft.Page):
    global CONNECTED_HOST, _SETTINGS_SHOWN, _TILE_SIZE, _LAST_BUTTONS, _DRAGGING
    page.title = "pk-pult"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 0
    page.spacing = 0

    ip_input = ft.TextField(
        label="IP адрес ПК", value=DEFAULT_WIFI_IP,
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

    size_text = ft.Text("100", size=11, color=FG2)

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

            def make_handler(bid_arg, host=CONNECTED_HOST):
                return lambda e: _on_press(host, bid_arg)

            def start_drag(e):
                global _DRAGGING
                _DRAGGING = True
            def end_drag(e):
                global _DRAGGING
                _DRAGGING = False

            handle = ft.GestureDetector(
                content=ft.Container(
                    content=ft.Text("╱", size=s // 6, color=ACCENT,
                                  opacity=0.4),
                    width=30, height=30,
                    alignment=ft.alignment.bottom_right,
                ),
                on_pan_start=start_drag,
                on_pan_update=on_resize_update,
                on_pan_end=end_drag,
            )

            tile_bg = ft.Container(
                content=ft.Text(label, size=max(8, s // 9),
                              weight=ft.FontWeight.W_600,
                              color=FG, text_align=ft.TextAlign.CENTER),
                width=s, height=s,
                bgcolor=BG2, border_radius=12,
                alignment=ft.alignment.center,
                ink=True,
                on_click=make_handler(bid),
            )

            stack = ft.Stack([tile_bg, handle], width=s, height=s)
            grid.controls.append(stack)

        size_text.value = str(s)
        page.update()

    def on_resize_update(e):
        global _TILE_SIZE, _DRAGGING
        if not _DRAGGING:
            return
        _TILE_SIZE = max(50, min(200, _TILE_SIZE + (e.delta_x + e.delta_y) / 4))
        s = int(_TILE_SIZE)
        cols = calc_cols(s)
        gap = max(4, s // 12)
        grid.runs_count = cols
        grid.max_extent = s
        grid.spacing = gap
        grid.run_spacing = gap

        for control in grid.controls:
            if isinstance(control, ft.Stack):
                control.width = s
                control.height = s
                for child in control.controls:
                    child.width = s
                    child.height = s
                    if hasattr(child, 'content') and isinstance(child.content, ft.Text):
                        child.content.size = max(8, s // 9)

        size_text.value = str(s)
        page.update()

    def _set_status(text, color=FG2, show_progress=False):
        status_text.value = text
        status_text.color = color
        progress.visible = show_progress
        page.update()

    def connect(host):
        _set_status("Подключение...", show_progress=True)
        config = get_config(host)
        if config is None:
            _set_status("Ошибка подключения", DANGER)
            return
        global CONNECTED_HOST, _LAST_BUTTONS
        CONNECTED_HOST = host
        _LAST_BUTTONS = config.get("buttons", [])
        build_tiles()
        _set_status("Подключено", SUCCESS)

    def _on_press(host, bid):
        result = send_press(host, bid)
        if result is None:
            _set_status("Ошибка отправки", DANGER)
        else:
            _set_status("Подключено", SUCCESS)

    def try_connect(e):
        page.run_thread(connect, ip_input.value.strip() or DEFAULT_WIFI_IP)

    def try_usb(e):
        page.run_thread(connect, "127.0.0.1")

    def refresh_config(e):
        if CONNECTED_HOST:
            page.run_thread(connect, CONNECTED_HOST)

    def toggle_settings(e):
        global _SETTINGS_SHOWN
        _SETTINGS_SHOWN = not _SETTINGS_SHOWN
        settings_panel.visible = _SETTINGS_SHOWN
        toggle_icon.icon = ft.Icons.EXPAND_LESS if _SETTINGS_SHOWN else ft.Icons.EXPAND_MORE
        page.update()

    header = ft.Container(
        content=ft.Row([
            ft.Text("pk-pult", size=20, weight=ft.FontWeight.BOLD, color=FG),
            ft.Container(expand=True),
            ft.IconButton(ft.Icons.REFRESH, icon_size=18,
                         icon_color=FG2, on_click=refresh_config),
        ]),
        padding=ft.Padding(left=15, top=45, right=5, bottom=5),
    )

    toggle_icon = ft.IconButton(
        ft.Icons.EXPAND_LESS, icon_size=20, icon_color=FG2,
        on_click=toggle_settings,
    )

    settings_panel = ft.Container(
        content=ft.Column([
            ft.Row([
                ip_input,
                ft.ElevatedButton("Подкл.", height=38, color="white",
                                bgcolor=ACCENT, on_click=try_connect),
                toggle_icon,
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

    page.add(header, settings_panel, progress, grid)


if __name__ == "__main__":
    ft.app(target=main)
