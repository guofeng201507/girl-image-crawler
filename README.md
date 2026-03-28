# 图片爬虫项目 (Image Crawler)

一个模块化、可扩展的图片爬虫框架，支持多个图片网站的批量下载。

## 功能特性

- **模块化架构**：核心组件分离，易于维护和扩展
- **统一接口**：所有爬虫继承基类，实现方式一致
- **自动重试**：下载失败自动重试，支持指数退避
- **断点续传**：支持从指定位置继续下载
- **并发控制**：可配置并发数，避免请求过快
- **代理支持**：通过环境变量配置代理
- **日志记录**：完整的日志系统，便于调试

## 支持的网站

| 网站 | 状态 | 需要代理 | 说明 |
|------|------|----------|------|
| EveriaClub | ✅ 可用 | 否 | 亚洲套图，质量高 |
| Xiurenwang | ⚠️ 需调整 | 否 | 秀人网 |
| Tuiimg | ⚠️ 需调整 | 否 | 推图网 |
| Kanxiaojiejie | ⚠️ 需调整 | 否 | 看小姐姐 |
| NSFWPicx | ⚠️ 需调整 | 否 | 每日更新 |
| Wallhaven | ✅ 可用 | 否 | 壁纸网站，需ID文件 |
| Hotgirl | ⚠️ 需代理 | 是 | 亚洲套图 |
| Hitxhot | ⚠️ 需代理 | 是 | 热门图片 |
| AsianToLick | ⚠️ 需代理 | 是 | 国产图 |

## 快速开始

### 安装依赖（使用 uv - 推荐）

**安装 uv**

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**创建环境并安装**

```bash
# 创建虚拟环境（自动下载 Python）
uv venv

# 安装项目依赖
uv pip install -e .

# 安装开发依赖
uv pip install -e ".[dev]"
```

**或者使用传统 pip**

```bash
pip install -e .
```

### 基本使用

```bash
# 查看可用站点
python main.py --list

# 爬取 EveriaClub（无需代理）
python main.py everiaclub --start-page 1

# 爬取指定页码范围
python main.py xiurenwang --start-page 1 --end-page 5

# Wallhaven 需要ID文件
python main.py wallhaven --id-file ids.txt
```

### 环境变量配置

```bash
# 设置下载目录（默认: D:/crawler_downloads）
set CRAWLER_DOWNLOAD_PATH=D:/downloads

# 启用代理
set USE_PROXY=true
set HTTP_PROXY=http://127.0.0.1:7890
set HTTPS_PROXY=http://127.0.0.1:7890

# 设置日志级别
set LOG_LEVEL=INFO
```

## 项目结构

```
.
├── config.py              # 全局配置
├── downloader.py          # 通用下载器
├── base_crawler.py        # 爬虫基类
├── main.py                # 命令行入口
├── crawlers/              # 爬虫集合
│   ├── __init__.py
│   ├── wallhaven.py       # Wallhaven爬虫
│   ├── xiurenwang.py      # 秀人网爬虫
│   ├── everiaclub.py      # EveriaClub爬虫
│   ├── tuiimg.py          # 推图网爬虫
│   ├── hotgirl.py         # Hotgirl爬虫
│   ├── kanxiaojiejie.py   # 看小姐姐爬虫
│   ├── nsfwpicx.py        # NSFWPicx爬虫
│   ├── hitxhot.py         # Hitxhot爬虫
│   └── asiantolick.py     # AsianToLick爬虫
├── test_all.py            # 测试脚本
├── check_sites.py         # 站点检查工具
└── README.md              # 本文档
```

## 开发指南

### 添加新爬虫

1. 在 `crawlers/` 目录下创建新文件，如 `mycrawler.py`：

```python
from base_crawler import BaseCrawler, ImageItem, GalleryItem
from typing import Iterator

class MyCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('site_key')  # 对应 config.py 中的配置
        self.list_url_template = f"{self.base_url}/page/{{page}}/"
    
    def get_galleries(self, page: int = 1) -> Iterator[GalleryItem]:
        """获取图集列表"""
        html = self.get_html(self.list_url_template.format(page=page))
        # 解析HTML，生成 GalleryItem
        pass
    
    def get_images(self, gallery: GalleryItem) -> Iterator[ImageItem]:
        """获取图集中的图片"""
        html = self.get_html(gallery.url)
        # 解析HTML，生成 ImageItem
        pass
```

2. 在 `config.py` 的 `SITE_CONFIGS` 中添加配置：

```python
'my_site': {
    'name': 'MySite',
    'base_url': 'https://example.com',
    'download_dir': 'mysite',
    'concurrent': 3,
    'proxy': False,
},
```

3. 在 `crawlers/__init__.py` 中导出：

```python
from .mycrawler import MyCrawler
__all__ = [..., 'MyCrawler']
```

4. 在 `main.py` 的 `crawler_map` 中注册：

```python
'my_site': MyCrawler,
```

### 测试爬虫

```python
from crawlers import MyCrawler
import logging

logging.basicConfig(level=logging.INFO)

with MyCrawler() as crawler:
    crawler.crawl(start_page=1, max_images=10)
```

## 配置说明

### 下载配置 (DownloadConfig)

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| CHUNK_SIZE | 8192 | 下载块大小（字节） |
| MAX_RETRIES | 5 | 最大重试次数 |
| RETRY_DELAY | 3 | 重试间隔（秒） |
| TIMEOUT | 30 | 请求超时（秒） |
| MIN_FILE_SIZE | 1000 | 最小有效文件大小（字节） |

### 站点配置 (SITE_CONFIGS)

| 配置项 | 说明 |
|--------|------|
| name | 站点显示名称 |
| base_url | 站点基础URL |
| download_dir | 下载文件夹名 |
| concurrent | 并发数 |
| proxy | 是否需要代理 |

## 注意事项

1. **遵守法律法规**：请确保使用本工具符合当地法律法规
2. **尊重网站规则**：请勿过度频繁请求，避免对目标网站造成压力
3. **版权问题**：下载的图片仅供个人学习研究，请勿用于商业用途
4. **代理设置**：部分网站需要科学上网才能访问

## 依赖管理

本项目使用 `uv` 进行依赖管理，同时兼容标准 `pyproject.toml`。

### uv 常用命令

```bash
# 创建虚拟环境（自动下载 Python）
uv venv

# 激活环境
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 安装依赖
uv pip install -e .

# 安装开发依赖
uv pip install -e ".[dev]"

# 同步依赖（根据 pyproject.toml）
uv pip sync

# 生成锁定文件
uv pip compile pyproject.toml -o uv.lock
```

### 代码格式化

```bash
# 使用 black 格式化代码
black .

# 使用 ruff 检查代码
ruff check .
ruff check . --fix
```

## 许可证

MIT License

## 更新日志

### 2024-03-28
- 重构项目架构，实现模块化设计
- 添加 9 个网站的爬虫实现
- 统一命令行入口
- 添加日志和统计功能
