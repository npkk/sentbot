import json
import os
import logging

STATE_FILE = "data/channel_state.json"
logger = logging.getLogger(__name__)

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"all_enabled": False, "channels": {}}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"状態ファイルの読み込みに失敗しました: {e}")
        return {"all_enabled": False, "channels": {}}

def save_state(state):
    os.makedirs("data", exist_ok=True)
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"状態ファイルの保存に失敗しました: {e}")
