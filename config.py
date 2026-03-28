"""
爬虫项目配置模块
集中管理所有配置项，避免硬编码
"""
import os
from pathlib import Path

# ==================== 基础配置 ====================
BASE_DIR = Path(__file__).parent

# 下载根目录，可通过环境变量覆盖
DOWNLOAD_ROOT = Path(os.getenv('CRAWLER_DOWNLOAD_PATH', 'D:/crawler_downloads'))

# 默认请求头
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# 代理配置（支持环境变量）
PROXY = {
    'http': os.getenv('HTTP_PROXY', 'http://127.0.0.1:7890'),
    'https': os.getenv('HTTPS_PROXY', 'http://127.0.0.1:7890')
} if os.getenv('USE_PROXY', 'false').lower() == 'true' else None

# ==================== 下载配置 ====================
class DownloadConfig:
    """下载行为配置"""
    CHUNK_SIZE = 8192  # 下载块大小
    MAX_RETRIES = 5    # 最大重试次数
    RETRY_DELAY = 3    # 重试间隔（秒）
    TIMEOUT = 30       # 请求超时（秒）
    MIN_FILE_SIZE = 1000  # 最小有效文件大小（字节）

# ==================== 站点配置 ====================
SITE_CONFIGS = {
    'wallhaven': {
        'name': 'Wallhaven',
        'base_url': 'https://wallhaven.cc',
        'download_dir': 'wallhaven',
        'concurrent': 1,  # 单线程
    },
    'ososedki': {
        'name': 'Ososedki',
        'base_url': 'https://ososedki.com',
        'download_dir': 'ososedki',
        'concurrent': 5,  # 多线程
        'proxy': True,    # 需要代理
    },
    'xiurenwang': {
        'name': 'Xiurenwang',
        'base_url': 'https://www.xiurenwang.cc',
        'download_dir': 'xiurenwang',
        'concurrent': 3,
    },
    'everiaclub': {
        'name': 'EveriaClub',
        'base_url': 'https://everia.club',
        'download_dir': 'everiaclub',
        'concurrent': 3,
    },
    'tuiimg': {
        'name': 'Tuiimg',
        'base_url': 'https://www.tuiimg.com',
        'download_dir': 'tuiimg',
        'concurrent': 3,
    },
    'hotgirl': {
        'name': 'Hotgirl',
        'base_url': 'https://hotgirl.asia',
        'download_dir': 'hotgirl',
        'concurrent': 3,
        'proxy': True,
    },
    'kanxiaojiejie': {
        'name': 'Kanxiaojiejie',
        'base_url': 'https://www.kanxiaojiejie.com',
        'download_dir': 'kanxiaojiejie',
        'concurrent': 2,
    },
    'nsfwpicx': {
        'name': 'NSFWPicx',
        'base_url': 'https://nsfwx.pics',
        'download_dir': 'nsfwpicx',
        'concurrent': 3,
    },
    'hitxhot': {
        'name': 'Hitxhot',
        'base_url': 'https://hitxhot.com',
        'download_dir': 'hitxhot',
        'concurrent': 3,
        'proxy': True,
    },
    'asiantolick': {
        'name': 'AsianToLick',
        'base_url': 'https://asiantolick.com',
        'download_dir': 'asiantolick',
        'concurrent': 3,
        'proxy': True,
    },
    'xchina': {
        'name': 'XChina',
        'base_url': 'https://xchina.co',
        'download_dir': 'xchina',
        'concurrent': 3,
        'proxy': True,
    },
}

# ==================== 日志配置 ====================
LOG_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': BASE_DIR / 'crawler.log',
}
