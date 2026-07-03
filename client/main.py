import json, urllib.request, urllib.error, threading
import flet as ft

DEFAULT_WIFI_IP = "192.168.1.100"
SERVER_PORT = 8789
CONFIG_CACHE = None


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
    page.title = "ПК-Пульт"
    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    ip_input = ft.TextField(
        label="IP адрес ПК",
        value=DEFAULT_WIFI_IP,
        width=250,
        dense=True,
    )

    status_text = ft.Text("Подключение...", size=14, color=ft.Colors.GREY_400)

    grid = ft.GridView(
        expand=True,
        runs_count=3,
        max_extent=120,
        child_aspect_ratio=1.2,
        spacing=10,
        run_spacing=10,
        padding=ft.Padding(left=12, top=12, right=12, bottom=12),
    )

    progress = ft.ProgressBar(visible=False)

    def connect(host):
        config = get_config(host)
        if config is None:
            status_text.value = "Ошибка подключения"
            status_text.color = ft.Colors.RED_400
            progress.visible = False
            page.update()
            return

        buttons = config.get("buttons", [])
        grid.controls.clear()

        for btn in buttons:
            btn_id = btn["id"]
            label = btn.get("label", "?")

            def make_handler(bid):
                return lambda e: _on_press(host, bid)

            tile = ft.Container(
                content=ft.Column([
                    ft.Container(expand=True),
                    ft.Text(label, size=13, weight=ft.FontWeight.W_600, text_align=ft.TextAlign.CENTER),
                    ft.Container(expand=True),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=120,
                height=100,
                bgcolor=ft.Colors.GREY_800,
                border_radius=12,
                border=ft.Border.all(width=1, color=ft.Colors.GREY_600),
                ink=True,
                on_click=make_handler(btn_id),
                animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            )
            grid.controls.append(tile)

        status_text.value = f"Подключено: {host}"
        status_text.color = ft.Colors.GREEN_400
        progress.visible = False
        page.update()

    def _on_press(host, btn_id):
        result = send_press(host, btn_id)
        if result is None:
            status_text.value = "Ошибка отправки"
            status_text.color = ft.Colors.RED_400
            page.update()

    def try_connect(e):
        progress.visible = True
        status_text.value = "Подключение..."
        status_text.color = ft.Colors.GREY_400
        page.update()

        host = ip_input.value.strip() or DEFAULT_WIFI_IP
        threading.Thread(target=connect, args=(host,), daemon=True).start()

    connect_btn = ft.ElevatedButton(
        "Подключиться",
        icon=ft.Icons.WIFI,
        on_click=try_connect,
    )

    def try_usb(e):
        progress.visible = True
        status_text.value = "USB-подключение..."
        status_text.color = ft.Colors.GREY_400
        page.update()
        threading.Thread(target=connect, args=("127.0.0.1",), daemon=True).start()

    usb_btn = ft.ElevatedButton(
        "USB (127.0.0.1)",
        icon=ft.Icons.USB,
        on_click=try_usb,
    )

    def refresh_config(e):
        host = ip_input.value.strip() or DEFAULT_WIFI_IP
        progress.visible = True
        status_text.value = "Обновление..."
        page.update()
        threading.Thread(target=connect, args=(host,), daemon=True).start()

    refresh_btn = ft.IconButton(
        icon=ft.Icons.REFRESH,
        tooltip="Обновить конфигурацию",
        on_click=refresh_config,
    )

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("ПК-Пульт", size=22, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    refresh_btn,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ip_input,
                    connect_btn,
                    usb_btn,
                ], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
                progress,
                status_text,
                ft.Divider(height=4),
            ], spacing=8),
            padding=ft.Padding(left=12, top=12, right=12, bottom=12),
        ),
        grid,
    )

    threading.Thread(target=connect, args=(DEFAULT_WIFI_IP,), daemon=True).start()


if __name__ == "__main__":
    ft.app(target=main)
