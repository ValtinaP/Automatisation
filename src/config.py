import os
from dataclasses import dataclass, field

import yaml
from dotenv import load_dotenv


@dataclass
class Config:
    api_id: int
    api_hash: str
    session_name: str
    openrouter_api_key: str
    openrouter_model: str
    notify_channel: str
    instruction: str
    channels: list = field(default_factory=list)
    folders: list = field(default_factory=list)
    ai_rate_limit_seconds: float = 1.0


def load_config(env_path: str = ".env", yaml_path: str = "config.yaml") -> Config:
    load_dotenv(env_path)

    with open(yaml_path, "r", encoding="utf-8") as f:
        yaml_cfg = yaml.safe_load(f) or {}

    required_env = ["TG_API_ID", "TG_API_HASH", "OPENROUTER_API_KEY", "NOTIFY_CHANNEL"]
    missing = [name for name in required_env if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing required .env variables: {', '.join(missing)}")

    if not yaml_cfg.get("instruction", "").strip():
        raise RuntimeError("config.yaml: 'instruction' must not be empty")

    return Config(
        api_id=int(os.environ["TG_API_ID"]),
        api_hash=os.environ["TG_API_HASH"],
        session_name=os.getenv("TG_SESSION_NAME", "news_parser_session"),
        openrouter_api_key=os.environ["OPENROUTER_API_KEY"],
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        notify_channel=os.environ["NOTIFY_CHANNEL"],
        instruction=yaml_cfg["instruction"].strip(),
        channels=yaml_cfg.get("channels") or [],
        folders=yaml_cfg.get("folders") or [],
        ai_rate_limit_seconds=float(yaml_cfg.get("ai_rate_limit_seconds", 1.0)),
    )
