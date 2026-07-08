# Remote Hotkeys

Программный комплекс удаленного управления ПК с мобильного устройства (Android).

## Структура проекта

```
server/          # ПК-Сервер (Python)
  main.py        # Точка входа (запуск API + GUI + ADB)
  config_manager.py  # Чтение/запись config.json
  api_server.py      # FastAPI сервер (HTTP API)
  key_handler.py     # Эмуляция нажатий клавиш
  gui_editor.py      # Flet GUI редактор конфигурации
  adb_helper.py      # ADB автопоиск и port forwarding
  config.json        # Файл конфигурации кнопок
client/          # Мобильный клиент (Python/Flet)
  main.py        # Flet приложение для Android
```

## Установка и запуск

### Сервер (ПК)

```bash
pip install -r requirements.txt
cd server
python main.py
```

> **Важно:** Для работы глобального захвата клавиш (keyboard) запускайте от имени **Администратора**.

### Клиент (Android)

```bash
cd client
flet run main.py          # для отладки на ПК
flet build apk main.py    # сборка .apk для Android
```

## API Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/config` | Получить список кнопок |
| POST | `/press` | Нажать кнопку по id |
| POST | `/buttons` | Создать новую кнопку |
| PUT | `/buttons/{id}` | Обновить кнопку |
| DELETE | `/buttons/{id}` | Удалить кнопку |

## Подключение

- **Wi-Fi:** Укажите IP компьютера в приложении
- **USB:** Подключите телефон по кабелю (режим отладки), ADB автоматически настроит порты
