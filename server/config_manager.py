import json, os, uuid

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "buttons": [
        {"id": "btn_vol_up",   "label": "🔊 Громкость +", "keys": ["volume_up"]},
        {"id": "btn_vol_down", "label": "🔉 Громкость -", "keys": ["volume_down"]},
        {"id": "btn_mute",     "label": "🔇 Выкл. звук",  "keys": ["volume_mute"]},
        {"id": "btn_play",     "label": "⏯️ Play/Pause",  "keys": ["play_pause"]},
        {"id": "btn_prev",     "label": "⏮️ Пред. трек",  "keys": ["prev_track"]},
        {"id": "btn_next",     "label": "⏭️ След. трек",  "keys": ["next_track"]},
    ]
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_buttons():
    return load_config().get("buttons", [])


def add_button(label="Новая кнопка", keys=None):
    config = load_config()
    btn_id = f"btn_{uuid.uuid4().hex[:8]}"
    config["buttons"].append({
        "id": btn_id,
        "label": label,
        "keys": keys or []
    })
    save_config(config)
    return btn_id


def update_button(btn_id, label=None, keys=None):
    config = load_config()
    for btn in config["buttons"]:
        if btn["id"] == btn_id:
            if label is not None:
                btn["label"] = label
            if keys is not None:
                btn["keys"] = keys
            save_config(config)
            return True
    return False


def delete_button(btn_id):
    config = load_config()
    config["buttons"] = [b for b in config["buttons"] if b["id"] != btn_id]
    save_config(config)
