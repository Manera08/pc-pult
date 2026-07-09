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
_EDIT_MODE = False
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


def main(page: ft.Page):
    global CONNECTED_HOST, _SETTINGS_SHOWN, _LAST_BUTTONS, _EDIT_MODE
    page.title = "Remote Hotkeys"
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

    grid = ft.Wrap(expand=True, spacing=8, run_spacing=8)

    edit_canvas = ft.Stack(expand=True)

    def _calc_grid_pos(idx):
        s = 100
        cols = 3
        gap = 8
        cell = s + gap
        return (idx % cols) * cell + 10, (idx // cols) * cell + 10

    def _rebuild_grid():
        grid.controls.clear()
        edit_canvas.controls.clear()

        for idx, btn in enumerate(_LAST_BUTTONS):
            bid = btn["id"]
            label = btn.get("label", "?")
            s = int(btn.get("size", 100))

            container = ft.Container(
                content=ft.Text(label, size=max(8, s // 9),
                              weight=ft.FontWeight.W_600,
                              color=FG, text_align=ft.TextAlign.CENTER),
                width=s, height=s,
                bgcolor=BG2, border_radius=12,
                alignment=ft.Alignment(0, 0),
                ink=not _EDIT_MODE,
                on_click=None if _EDIT_MODE else lambda e, b=bid: _on_press(CONNECTED_HOST, b),
            )

            if _EDIT_MODE:
                x = btn.get("x")
                y = btn.get("y")
                if x is None:
                    x, y = _calc_grid_pos(idx)

                body = ft.Container(
                    content=container,
                    width=s, height=s,
                    bgcolor="#2a2a5e", border_radius=12,
                    border=ft.border.all(2, ACCENT),
                )

                move = ft.GestureDetector(
                    content=body,
                    on_pan_update=lambda e, b=btn: _move_update(e, b),
                    on_pan_end=lambda e: _save_all(),
                )

                hs = max(24, min(40, s // 3))
                handle = ft.Container(
                    content=ft.Text("╱", size=hs // 2, color=ACCENT,
                                  text_align=ft.TextAlign.CENTER),
                    width=hs, height=hs,
                    bgcolor="#1a1a3e", border_radius=6,
                    border=ft.border.all(1, ACCENT),
                    alignment=ft.Alignment(1, 1),
                    right=0, bottom=0,
                )

                resize = ft.GestureDetector(
                    content=handle,
                    on_pan_update=lambda e, b=btn: _resize_update(e, b),
                    on_pan_end=lambda e: _save_all(),
                )

                edit_canvas.controls.append(
                    ft.Stack([move, resize], width=s, height=s, left=x, top=y)
                )
            else:
                grid.controls.append(container)

        page.update()

    def _move_update(e, btn):
        btn["x"] = btn.get("x", 0) + e.delta_x
        btn["y"] = btn.get("y", 0) + e.delta_y
        _rebuild_grid()

    def _resize_update(e, btn):
        old = int(btn.get("size", 100))
        btn["size"] = max(60, min(200, old + (e.delta_x + e.delta_y) / 2))
        _rebuild_grid()

    def _save_all():
        if CONNECTED_HOST:
            _http_raw("PUT", CONNECTED_HOST, SERVER_PORT,
                     "config", {"buttons": _LAST_BUTTONS})

    def _on_press(host, bid):
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

    def do_connect(host):
        progress.visible = True
        status_text.value = "Подключение..."
        status_text.color = FG2
        page.update()

        ok, val = _http_raw("GET", host, SERVER_PORT, "config")

        if ok:
            global CONNECTED_HOST, _LAST_BUTTONS
            CONNECTED_HOST = host
            _LAST_BUTTONS = val.get("buttons", [])
            _rebuild_grid()
            status_text.value = "Подключено"
            status_text.color = _SUCCESS
        else:
            status_text.value = f"Ошибка: {val}"
            status_text.color = _DANGER

        progress.visible = False
        page.update()

    def try_connect(e):
        try:
            do_connect(ip_input.value.strip() or DEFAULT_WIFI_IP)
        except Exception as ex:
            progress.visible = False
            status_text.value = f"Исключение: {type(ex).__name__}: {ex}"
            status_text.color = _DANGER
            page.update()

    def try_usb(e):
        try:
            do_connect("127.0.0.1")
        except Exception as ex:
            progress.visible = False
            status_text.value = f"Исключение: {type(ex).__name__}: {ex}"
            status_text.color = _DANGER
            page.update()

    def refresh_config(e):
        if CONNECTED_HOST:
            try_connect(e)

    def toggle_settings(e):
        global _SETTINGS_SHOWN
        _SETTINGS_SHOWN = not _SETTINGS_SHOWN
        settings_panel.visible = _SETTINGS_SHOWN
        toggle_icon.icon = ft.Icons.EXPAND_LESS if _SETTINGS_SHOWN else ft.Icons.EXPAND_MORE
        page.update()

    def toggle_edit(e):
        global _EDIT_MODE
        _EDIT_MODE = not _EDIT_MODE
        edit_icon.icon = ft.Icons.EDIT_OFF if _EDIT_MODE else ft.Icons.EDIT
        grid.visible = not _EDIT_MODE
        edit_canvas.visible = _EDIT_MODE
        _rebuild_grid()

    toggle_icon = ft.IconButton(
        ft.Icons.EXPAND_LESS, icon_size=18, icon_color=FG2,
        on_click=toggle_settings,
    )

    edit_icon = ft.IconButton(
        ft.Icons.EDIT, icon_size=18, icon_color=FG2,
        on_click=toggle_edit,
    )

    header = ft.Container(
        content=ft.Row([
            ft.Text("Remote Hotkeys", size=20, weight=ft.FontWeight.BOLD, color=FG),
            ft.Container(expand=True),
            edit_icon,
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

    edit_canvas.visible = False
    page.add(header, settings_panel, progress, grid, edit_canvas)


if __name__ == "__main__":
    ft.app(target=main)
