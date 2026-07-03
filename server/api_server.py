import threading
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config_manager import get_buttons, add_button, update_button, delete_button
from key_handler import press_keys

app = FastAPI(title="ПК-Пульт API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PressRequest(BaseModel):
    id: str


class ButtonCreate(BaseModel):
    label: str = "Новая кнопка"
    keys: list[str] = []


class ButtonUpdate(BaseModel):
    label: str | None = None
    keys: list[str] | None = None


@app.get("/config")
def get_config():
    return {"buttons": get_buttons()}


@app.post("/press")
def press_button(req: PressRequest):
    buttons = get_buttons()
    for btn in buttons:
        if btn["id"] == req.id:
            press_keys(btn.get("keys", []))
            return {"status": "ok", "id": req.id}
    raise HTTPException(status_code=404, detail="Button not found")


@app.post("/buttons")
def create_button(data: ButtonCreate):
    btn_id = add_button(label=data.label, keys=data.keys)
    return {"status": "created", "id": btn_id}


@app.put("/buttons/{btn_id}")
def edit_button(btn_id: str, data: ButtonUpdate):
    ok = update_button(btn_id, label=data.label, keys=data.keys)
    if not ok:
        raise HTTPException(status_code=404, detail="Button not found")
    return {"status": "updated"}


@app.delete("/buttons/{btn_id}")
def remove_button(btn_id: str):
    delete_button(btn_id)
    return {"status": "deleted"}


def run_api(host="0.0.0.0", port=8789):
    t = threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": host, "port": port, "log_level": "info"},
        daemon=True,
    )
    t.start()
    return t
