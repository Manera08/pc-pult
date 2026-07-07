import json, urllib.request, urllib.error, threading
import flet as ft

DEFAULT_WIFI_IP = "192.168.1.100"
SERVER_PORT = 8789

BG = "#0f0f23"
BG2 = "#1a1a3e"
BG3 = "#252550"
ACCENT = "#6c63ff"
SUCCESS = "#00c853"
DANGER = "#ff1744"
FG = "#ffffff"
FG2 = "#b0b0cc"
FG3 = "#6a6a8e"

CONNECTED_HOST = None


def get_config(host):
    url = f"http://{host}:{SERVER_PORT}/config"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def send_press(host, btn_id):
    url = f"http://{host}:{SERVER_PORT}/press"
    data = json.dumps({"id": btn_id}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.read().decode()
    except Exception:
        return None


def main(page: ft.Page):
    global CONNECTED_HOST
    page.title = "ПК-Пульт"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG
    page.padding = 0
    page.spacing = 0

    grid = ft.GridView(
        expand=True,
        runs_count=3,
        max_extent=120,
        child_aspect_ratio=1.0,
        spacing=12,
        run_spacing=12,
        padding=ft.Padding(left=16, top=8, right=16, bottom=16),
    )

    status_text = ft.Text("", size=12, color=FG3)
    progress = ft.ProgressBar(
        visible=False, color=ACCENT, bgcolor=BG3, height=3,
    )

    ip_input = ft.TextField(
        label="IP адрес ПК",
        value=DEFAULT_WIFI_IP,
        width=210, height=40, text_size=13,
        border_color=BG3, focused_border_color=ACCENT,
        bgcolor=BG2, color=FG, cursor_color=ACCENT,
    )

    def connect(host):
        global CONNECTED_HOST
        config = get_config(host)
        if config is None:
            status_text.value = "Ошибка подключения"
            status_text.color = DANGER
            progress.visible = False
            page.update()
            return

        CONNECTED_HOST = host
        buttons = config.get("buttons", [])
        grid.controls.clear()

        colors = [
            "#6c63ff", "#ff6b6b", "#00c853", "#ff9100",
            "#00bcd4", "#e040fb", "#ffd600", "#76ff03",
        ]

        for i, btn in enumerate(buttons):
            btn_id = btn["id"]
            label = btn.get("label", "?")
            accent = colors[i % len(colors)]

            def make_handler(bid):
                return lambda e: _on_press(host, bid)

            tile = ft.Container(
                content=ft.Column([
                    ft.Container(expand=True),
                    ft.Text(label, size=13, weight=ft.FontWeight.W_600,
                            color=FG, text_align=ft.TextAlign.CENTER,
                            no_wrap=False),
                    ft.Container(expand=True),
                ], alignment=ft.MainAxisAlignment.CENTER,
                   horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                   spacing=2),
                width=120, height=120,
                bgcolor=BG2, border_radius=16,
                border=ft.BorderSide(width=1.5, color=accent + "33"),
                ink=True, ink_color=accent + "22",
                on_click=make_handler(btn_id),
                animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            )
            grid.controls.append(tile)

        status_text.value = f"● {host}"
        status_text.color = SUCCESS
        progress.visible = False
        page.update()

    def _on_press(host, btn_id):
        result = send_press(host, btn_id)
        if result is None:
            status_text.value = "Ошибка отправки"
            status_text.color = DANGER
        else:
            status_text.value = f"● {host}"
            status_text.color = SUCCESS
        page.update()

    def try_connect(e):
        progress.visible = True
        status_text.value = "Подключение..."
        status_text.color = FG2
        page.update()
        host = ip_input.value.strip() or DEFAULT_WIFI_IP
        threading.Thread(target=connect, args=(host,), daemon=True).start()

    def try_usb(e):
        progress.visible = True
        status_text.value = "USB..."
        status_text.color = FG2
        page.update()
        threading.Thread(target=connect, args=("127.0.0.1",), daemon=True).start()

    def refresh_config(e):
        if CONNECTED_HOST:
            progress.visible = True
            status_text.value = "Обновление..."
            status_text.color = FG2
            page.update()
            threading.Thread(target=connect, args=(CONNECTED_HOST,), daemon=True).start()

    header = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text("ПК-Пульт", size=22, weight=ft.FontWeight.BOLD, color=FG),
                    ft.Text("Управление ПК", size=11, color=FG3),
                ], spacing=2),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.REFRESH, icon_size=18, icon_color=FG2,
                    bgcolor=BG2, on_click=refresh_config,
                ),
            ]),
            ft.Container(height=16),
            ft.Row([
                ip_input,
                ft.ElevatedButton(
                    "Подкл.", height=40,
                    color="white", bgcolor=ACCENT,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(10)),
                    on_click=try_connect,
                ),
            ], alignment=ft.MainAxisAlignment.START, spacing=10),
            ft.Row([
                ft.ElevatedButton(
                    "USB", height=34,
                    color=FG2, bgcolor=BG2, icon=ft.Icons.USB,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(8)),
                    on_click=try_usb,
                ),
                ft.Container(expand=True),
                status_text,
            ], alignment=ft.MainAxisAlignment.START, spacing=10),
        ], spacing=0),
        padding=ft.Padding(left=20, top=50, right=20, bottom=16),
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 0),
            colors=[BG, BG2],
        ),
    )

    page.add(header, progress, grid)


if __name__ == "__main__":
    ft.app(target=main)
