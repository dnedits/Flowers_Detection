import re
import os
from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str


@dataclass
class Config:
    tg_bot: TgBot


def load_config(path: str | None = None) -> Config:
    env = Env()

    if path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, '..', '..', '.env')

    env.read_env(path)

    raw_token = env('BOT_TOKEN')

    clean_token = re.sub(r'[^a-zA-Z0-9:-]', '', raw_token)

    return Config(tg_bot=TgBot(token=clean_token))