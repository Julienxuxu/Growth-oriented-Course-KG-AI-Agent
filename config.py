import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Qwen API配置 (兼容OpenAI接口)
OPEN_API_KEY = os.getenv("QWEN_API_KEY")
OPEN_API_BASE = os.getenv("QWEN_API_BASE")
QWEN_MODEL = "qwen-turbo"
#KIMI_MODEL = "kimi-k2-thinking"
#KIMI_MODEL = "kimi-k2-turbo-preview"
OPEN_API_MODEL = QWEN_MODEL

# 文件路径配置
REPORTS_DIR = "./reports"
LOGS_DIR = "./logs"
UPLOADS_DIR = "./uploads"
DATA_DIR = "./data"  # 用于存储用户和会话数据

# 确保目录存在
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

