import threading
import flet as ft
from config_manager import get_buttons, add_button, update_button, delete_button
from key_handler import start_capture, stop_capture, press_keys

_CAPTURE_ACTIVE = False
_captured_keys = []
_capture_target = None


def run_gui(api_port=8789):
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8580)


def main(page: ft.Page):
    page.title = "ПК-Пульт — Редактор"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 800
    page.window.height = 700
    page.window.min_width = 600
    page.window.min_height = 500

    btn_list = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO)

    status_bar = ft.Text("Сервер: запущен", size=12, color=ft.Colors.GREEN_400)

    def refresh_list():
        btn_list.controls.clear()
        for btn in get_buttons():
            btn_list.controls.append(_build_button_row(page, btn, refresh_list))
        page.update()

    page.add(
        ft.Row([
            ft.Text("ПК-Пульт — Редактор конфигурации", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            ft.ElevatedButton("+ Добавить кнопку", icon=ft.Icons.ADD, on_click=lambda e: _add_new(page, refresh_list)),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        ft.Container(
            content=btn_list,
            expand=True,
        ),
        ft.Divider(),
        status_bar,
    )

    refresh_list()


def _build_button_row(page, btn, refresh_cb):
    btn_id = btn["id"]
    label = btn.get("label", "?")
    keys = btn.get("keys", [])

    label_field = ft.TextField(
        value=label,
        dense=True,
        width=200,
        on_change=lambda e, bid=btn_id: update_button(bid, label=e.control.value),
    )

    keys_display = ft.Text(
        value=" + ".join(keys) if keys else "(нет клавиш)",
        size=13,
        italic=not keys,
        width=180,
        no_wrap=False,
    )

    capture_btn = ft.IconButton(
        icon=ft.Icons.KEYBOARD,
        tooltip="Захватить комбинацию",
        on_click=lambda e, bid=btn_id: _start_capture(page, bid, refresh_cb),
    )

    test_btn = ft.IconButton(
        icon=ft.Icons.PLAY_ARROW,
        tooltip="Тест нажатия",
        on_click=lambda e, k=keys: press_keys(k),
    )

    delete_btn = ft.IconButton(
        icon=ft.Icons.DELETE_OUTLINE,
        icon_color=ft.Colors.RED_400,
        tooltip="Удалить кнопку",
        on_click=lambda e, bid=btn_id: (_confirm_delete(page, bid, refresh_cb)),
    )

    return ft.Container(
        content=ft.Row([
            label_field,
            keys_display,
            capture_btn,
            test_btn,
            delete_btn,
        ], alignment=ft.MainAxisAlignment.START, spacing=8),
        padding=ft.Padding(left=8, top=4, right=8, bottom=4),
        border=ft.Border.all(width=0.5, color=ft.Colors.GREY_700),
        border_radius=6,
    )


def _add_new(page, refresh_cb):
    add_button()
    refresh_cb()


def _confirm_delete(page, btn_id, refresh_cb):
    dlg = ft.AlertDialog(
        title=ft.Text("Подтверждение"),
        content=ft.Text("Удалить эту кнопку?"),
        actions=[
            ft.TextButton("Отмена", on_click=lambda e: _close_dialog(page)),
            ft.TextButton("Удалить", on_click=lambda e: (_close_dialog(page), delete_button(btn_id), refresh_cb())),
        ],
    )
    page.dialog = dlg
    dlg.open = True
    page.update()


def _close_dialog(page):
    if page.dialog:
        page.dialog.open = False
        page.update()


def _start_capture(page, btn_id, refresh_cb):
    global _CAPTURE_ACTIVE, _captured_keys, _capture_target
    if _CAPTURE_ACTIVE:
        return

    _CAPTURE_ACTIVE = True
    _captured_keys = []
    _capture_target = btn_id

    captured_text = ft.Text("Захвачено: ", size=16, weight=ft.FontWeight.BOLD)
    status_text = ft.Text("Ожидание нажатий...", size=14)

    dlg = ft.AlertDialog(
        title=ft.Text("Захват клавиш"),
        content=ft.Column([
            ft.Text("Нажмите нужную комбинацию (до 10 клавиш).\nESC — завершить захват.", size=14),
            captured_text,
            status_text,
        ], tight=True, spacing=10),
        actions=[
            ft.TextButton("Готово", on_click=lambda e: _finish_capture(page, btn_id, refresh_cb)),
            ft.TextButton("Отмена", on_click=lambda e: _cancel_capture(page)),
        ],
        modal=True,
    )

    page.dialog = dlg
    dlg.open = True
    page.update()

    def on_key(event):
        nonlocal captured_text, status_text
        if event.event_type == "down":
            name = event.name
            if name == "esc" and _captured_keys:
                _finish_capture(page, btn_id, refresh_cb)
                return
            if name == "esc":
                _cancel_capture(page)
                return
            if name not in _captured_keys:
                _captured_keys.append(name)
                captured_text.value = "Захвачено: " + " + ".join(_captured_keys)
                status_text.value = f"({len(_captured_keys)} клавиш)"
                try:
                    page.update()
                except Exception:
                    pass

    import keyboard as kb
    kb.hook(on_key)


def _finish_capture(page, btn_id, refresh_cb):
    global _CAPTURE_ACTIVE
    _CAPTURE_ACTIVE = False
    stop_capture()

    if _captured_keys and btn_id:
        update_button(btn_id, keys=list(_captured_keys))

    _captured_keys.clear()
    _close_dialog(page)
    refresh_cb()


def _cancel_capture(page):
    global _CAPTURE_ACTIVE
    _CAPTURE_ACTIVE = False
    stop_capture()
    _captured_keys.clear()
    _close_dialog(page)

