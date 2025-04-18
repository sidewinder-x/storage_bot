from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN: str
    ADMIN_ID: int

config = Config(
    BOT_TOKEN=os.getenv("BOT_TOKEN"),
    ADMIN_ID=int(os.getenv("ADMIN_ID"))
)