import json, urllib.request, urllib.error, threading
import flet as ft

DEFAULT_WIFI_IP = "192.168.1.100"
SERVER_PORT = 8789

BG = "#0f0f23"
BG2 = "#1a1a3e"
ACCENT = "#6c63ff"
SUCCESS = "#00c853"
DANGER = "#ff1744"
FG = "#ffffff"
FG2 = "#b0b0cc"

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
    page.padding = 15
    page.spacing = 10

    ip_input = ft.TextField(
        label="IP адрес ПК", value=DEFAULT_WIFI_IP,
        width=210, height=40, text_size=13,
        border_color="#252550", focused_border_color=ACCENT,
        bgcolor=BG2, color=FG, cursor_color=ACCENT,
    )

    status_text = ft.Text("", size=12, color=FG2)

    progress = ft.ProgressBar(visible=False, color=ACCENT)

    grid = ft.GridView(
        expand=True,
        runs_count=3,
        max_extent=110,
        child_aspect_ratio=1.0,
        spacing=10,
        run_spacing=10,
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
        grid.controls.clear()
        for btn in config.get("buttons", []):
            btn_id = btn["id"]
            label = btn.get("label", "?")

            def make_handler(bid):
                return lambda e: _on_press(host, bid)

            tile = ft.Container(
                content=ft.Text(label, size=12, weight=ft.FontWeight.W_600,
                              color=FG, text_align=ft.TextAlign.CENTER),
                width=110, height=110,
                bgcolor=BG2, border_radius=12,
                ink=True, on_click=make_handler(btn_id),
            )
            grid.controls.append(tile)
        status_text.value = "● Подключено"
        status_text.color = SUCCESS
        progress.visible = False
        page.update()

    def _on_press(host, btn_id):
        result = send_press(host, btn_id)
        if result is None:
            status_text.value = "Ошибка отправки"
            status_text.color = DANGER
        else:
            status_text.value = "● Подключено"
            status_text.color = SUCCESS
        page.update()

    def try_connect(e):
        progress.visible = True
        status_text.value = "Подключение..."
        status_text.color = FG2
        page.update()
        threading.Thread(target=connect,
            args=(ip_input.value.strip() or DEFAULT_WIFI_IP,),
            daemon=True).start()

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

    page.add(
        ft.Row([
            ft.Column([
                ft.Text("ПК-Пульт", size=20, weight=ft.FontWeight.BOLD, color=FG),
                ft.Text("Управление ПК", size=10, color=FG2),
            ], spacing=1),
            ft.Container(expand=True),
            ft.IconButton(ft.Icons.REFRESH, icon_size=18,
                         icon_color=FG2, on_click=refresh_config),
        ]),
        ft.Row([ip_input,
                ft.ElevatedButton("Подкл.", height=40, color="white",
                                bgcolor=ACCENT, on_click=try_connect)]),
        ft.Row([ft.ElevatedButton("USB", height=34, color=FG2, bgcolor=BG2,
                                icon=ft.Icons.USB, on_click=try_usb),
                ft.Container(expand=True), status_text]),
        progress,
        grid,
    )


if __name__ == "__main__":
    ft.app(target=main)
