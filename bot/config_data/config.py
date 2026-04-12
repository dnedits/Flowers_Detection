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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(current_dir, '..', '..', '.env')

    env.read_env(path)
    return Config(tg_bot=TgBot(token=env('BOT_TOKEN')))