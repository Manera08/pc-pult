import time
import pyautogui
import keyboard as kb

_held_modifiers = set()

MODIFIER_MAP = {
    "ctrl":        "ctrl",
    "control":     "ctrl",
    "alt":         "alt",
    "shift":       "shift",
    "win":         "win",
    "windows":     "win",
    "super":       "win",
}

SPECIAL_KEYS = {
    "volume_up":     (173, None),
    "volume_down":   (174, None),
    "volume_mute":   (175, None),
    "play_pause":    (179, None),
    "prev_track":    (177, None),
    "next_track":    (176, None),
    "stop":          (178, None),
    "media_stop":    (178, None),
}


def press_keys(keys):
    if not keys:
        return

    modifiers = []
    main_keys = []

    for k in keys:
        lower = k.lower()
        if lower in MODIFIER_MAP:
            modifiers.append(MODIFIER_MAP[lower])
        else:
            main_keys.append(k)

    if main_keys:
        normalized = main_keys[0].lower()
        if normalized in SPECIAL_KEYS:
            vk, _ = SPECIAL_KEYS[normalized]
            _press_media_key(vk)
            return

        hotkey = "+".join(modifiers + main_keys)
        try:
            pyautogui.hotkey(*modifiers, *main_keys, interval=0.05)
        except Exception:
            kb.send(hotkey)
    else:
        pass


def start_capture(on_keys_captured):
    recorded = []

    def on_key(event):
        nonlocal recorded
        if event.event_type == kb.KEY_DOWN:
            name = event.name
            if name == "esc" and recorded:
                return False
            if name not in recorded:
                recorded.append(name)
        if event.event_type == kb.KEY_DOWN and len(recorded) >= 10:
            return False
        return True

    kb.hook(on_key)
    return recorded


def stop_capture():
    kb.unhook_all()


def _press_media_key(vk):
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    ScanCode = 0
    Flags = 0

    inputs = (ctypes.c_ubyte * 40)()
    ctypes.memset(inputs, 0, 40)

    INPUT_KEYBOARD = 1

    def build_input(key_code, flags):
        buf = (ctypes.c_ubyte * 40)()
        ctypes.memset(buf, 0, 40)
        ctypes.c_uint16.from_buffer(buf, 0).value = INPUT_KEYBOARD
        ctypes.c_uint16.from_buffer(buf, 4).value = 0
        ctypes.c_uint16.from_buffer(buf, 8).value = vk
        ctypes.c_uint16.from_buffer(buf, 10).value = ScanCode
        ctypes.c_uint32.from_buffer(buf, 12).value = flags
        ctypes.c_uint32.from_buffer(buf, 16).value = 0
        ctypes.c_uint64.from_buffer(buf, 24).value = 0
        return buf

    try:
        press = build_input(vk, 0)
        release = build_input(vk, 2)

        combined = (ctypes.c_ubyte * 80)()
        ctypes.memcpy(combined, press, 40)
        ctypes.memcpy(ctypes.addressof(combined) + 40, release, 40)

        sent = user32.SendInput(2, ctypes.addressof(combined), 40)
        if sent != 2:
            _fallback_media_key(vk)
    except Exception:
        _fallback_media_key(vk)


def _fallback_media_key(vk):
    key_map = {
        173: "volume down",
        174: "volume up",
        175: "volume mute",
        179: "play/pause",
        177: "previous track",
        176: "next track",
        178: "stop",
    }
    name = key_map.get(vk)
    if name:
        try:
            kb.send(name)
        except Exception:
            pass
