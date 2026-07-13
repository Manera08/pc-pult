# Remote Hotkeys

Управляйте компьютером с телефона Android через Wi-Fi или USB.

Сервер (Windows) эмулирует нажатия клавиш: регулировка громкости, медиа-клавиши, любые горячие сочетания. Кнопки настраиваются через встроенный GUI-редактор.

## Сборка

### Сервер (EXE)

```bash
pip install pyinstaller -r requirements.txt
cd server
pyinstaller --onefile --windowed --name "Remote-Hotkeys" ^
  --collect-all keyboard --collect-all pyautogui ^
  main.py
```

### Клиент (APK)

```bash
cd client
pip install flet==0.85.3
flet build apk --yes --verbose
```

Готовые билды можно скачать из [Releases](https://github.com/Manera08/pc-pult/releases).

## Использование

1. Запустите `Remote-Hotkeys.exe` на ПК (ПКМ → от имени администратора)
2. Откройте приложение на телефоне, введите IP компьютера, нажмите «Подкл.»
3. Для USB-подключения включите отладку по USB и нажмите «USB» в приложении

### Открыть порт 8789 в брандмауэре

Для подключения по Wi-Fi порт `8789` должен быть открыт в брандмауэре Windows:

```cmd
netsh advfirewall firewall add rule name="Remote Hotkeys" dir=in action=allow protocol=TCP localport=8789
```

Запустите эту команду от имени администратора (Win+R → `cmd` → Ctrl+Shift+Enter). Если порт уже занят, проверьте другим сервером:

```cmd
netstat -ano | findstr :8789
```

## API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/config` | Список кнопок |
| POST | `/press` | Нажать кнопку |
| POST | `/buttons` | Создать кнопку |
| PUT | `/buttons/{id}` | Обновить кнопку |
| DELETE | `/buttons/{id}` | Удалить кнопку |
