# 技术设计文档

## 1. 架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        应用层 (main.py)                      │
│                    命令行接口 / 统一入口                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      爬虫实现层 (crawlers/)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Wallhaven │ │Xiurenwang│ │Everiaclub│ │   ...    │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      核心抽象层 (base_crawler.py)            │
│              BaseCrawler (抽象基类)                          │
│         ┌────────────────┬────────────────┐                 │
│         │   get_html()   │ get_galleries() │                 │
│         │ download_image()│ get_images()   │                 │
│         └────────────────┴────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│   下载器 (downloader.py) │     │   配置 (config.py)       │
│      Downloader         │     │  SITE_CONFIGS           │
│  ┌───────────────────┐  │     │  DownloadConfig         │
│  │   download()      │  │     │  DEFAULT_HEADERS        │
│  │ download_image()  │  │     │  PROXY                  │
│  └───────────────────┘  │     └─────────────────────────┘
└─────────────────────────┘
```

### 1.2 设计模式

- **模板方法模式**：`BaseCrawler` 定义算法骨架，子类实现具体步骤
- **工厂模式**：`main.py` 中的 `crawler_map` 根据 key 创建对应爬虫实例
- **策略模式**：不同的爬虫实现相同的接口，可互换使用

## 2. 核心模块设计

### 2.1 配置模块 (config.py)

**职责**：集中管理所有配置项

**关键设计**：
- 使用环境变量支持运行时配置
- 配置项分类：基础配置、下载配置、站点配置、日志配置
- 站点配置使用字典结构，便于扩展

```python
# 配置层级
BASE_DIR                    # 项目根目录
├── DOWNLOAD_ROOT           # 下载根目录（可配置）
├── DEFAULT_HEADERS         # 默认请求头
├── PROXY                   # 代理配置
├── DownloadConfig          # 下载行为配置（类）
├── SITE_CONFIGS            # 各站点配置（字典）
└── LOG_CONFIG              # 日志配置
```

### 2.2 下载器模块 (downloader.py)

**职责**：提供统一的文件下载功能

**关键设计**：
- 使用 `requests.Session` 保持连接池
- 集成 `urllib3` 重试机制
- 临时文件 + 原子操作，避免下载中断产生脏文件
- 流式下载，支持大文件

**下载流程**：
```
检查文件是否存在 ──否──> 创建临时文件 ──> 流式下载 ──> 检查文件大小
      │                                                    │
      是                                                  合格
      │                                                    │
   跳过返回                                               重命名
```

**异常处理策略**：
- 网络异常：指数退避重试
- 文件过小：视为失败，删除临时文件
- 其他异常：记录日志，返回失败

### 2.3 爬虫基类 (base_crawler.py)

**职责**：定义爬虫的标准接口和公共功能

**核心抽象**：

```python
class BaseCrawler(ABC):
    # 子类必须实现
    @abstractmethod
    def get_galleries(self, page: int) -> Iterator[GalleryItem]
    
    @abstractmethod  
    def get_images(self, gallery: GalleryItem) -> Iterator[ImageItem]
    
    # 基类提供默认实现
    def download_image(self, image: ImageItem) -> bool
    def crawl(self, start_page: int, end_page: int)
```

**数据模型**：

```python
@dataclass
class GalleryItem:
    url: str           # 图集详情页URL
    title: str         # 图集标题
    image_count: int   # 图片数量（预估）
    category: str      # 分类
    meta: Dict         # 扩展元数据

@dataclass
class ImageItem:
    url: str           # 图片URL
    title: str         # 图片标题
    folder_name: str   # 保存文件夹
    filename: str      # 保存文件名
    meta: Dict         # 扩展元数据
```

## 3. 爬虫实现设计

### 3.1 通用实现模式

所有爬虫遵循相同的实现模式：

```python
class XxxCrawler(BaseCrawler):
    def __init__(self):
        super().__init__('site_key')
        # 初始化站点特定配置
    
    def get_galleries(self, page: int):
        # 1. 构造列表页URL
        # 2. 请求并解析HTML
        # 3. 提取图集信息
        # 4. yield GalleryItem
    
    def get_images(self, gallery: GalleryItem):
        # 1. 请求详情页
        # 2. 解析HTML提取图片URL
        # 3. yield ImageItem
    
    def crawl(self, ...):
        # 可选：重写以实现特殊逻辑（如限制下载数量）
```

### 3.2 特殊处理

**Wallhaven**：
- 数据来源为文本文件而非网页
- 每个ID对应一张图片
- 支持 jpg/png 格式自动切换

**分页处理**：
- 大部分网站使用 URL 参数分页：`/page/{page}/`
- 部分网站使用路径分页：`/list_1_{page}.html`

## 4. 扩展性设计

### 4.1 添加新爬虫

只需实现三个步骤：

1. **创建实现类**：继承 `BaseCrawler`，实现 `get_galleries()` 和 `get_images()`
2. **添加配置**：在 `SITE_CONFIGS` 中注册站点信息
3. **注册到入口**：在 `crawler_map` 中建立映射

### 4.2 自定义下载行为

可通过以下方式扩展：

- 继承 `Downloader` 类，重写 `download()` 方法
- 在爬虫中自定义 `download_image()` 方法
- 通过 `config.DownloadConfig` 调整下载参数

### 4.3 中间件机制（预留）

未来可扩展的中间件点：

```python
# 请求前处理
def before_request(self, url: str) -> str:
    """可修改URL或添加签名"""
    return url

# 响应后处理
def after_response(self, html: str) -> str:
    """可解密或清理HTML"""
    return html

# 下载前处理
def before_download(self, image: ImageItem) -> ImageItem:
    """可修改下载参数"""
    return image
```

## 5. 错误处理策略

### 5.1 分层处理

| 层级 | 处理方式 | 示例 |
|------|----------|------|
| 网络层 | 自动重试 | 连接超时、DNS失败 |
| HTTP层 | 状态码检查 | 404、500、503 |
| 解析层 | 异常捕获 | XPath不存在、属性缺失 |
| 下载层 | 重试+跳过 | 文件损坏、大小异常 |

### 5.2 重试策略

```python
# 指数退避
retry_delay = RETRY_DELAY * (attempt + 1)

# 最大重试次数
MAX_RETRIES = 5

# 需要重试的状态码
status_forcelist = [429, 500, 502, 503, 504]
```

## 6. 性能优化

### 6.1 已实现的优化

- **连接池复用**：使用 `requests.Session`
- **流式下载**：避免大文件占用内存
- **临时文件**：原子操作避免脏数据
- **智能跳过**：文件已存在则跳过

### 6.2 可扩展的优化

- **异步下载**：使用 `aiohttp` 替代 `requests`
- **多线程/多进程**：按图集并行下载
- **缓存机制**：缓存页面HTML避免重复请求
- **增量更新**：记录已下载的图集ID

## 7. 安全考虑

### 7.1 请求安全

- User-Agent 伪装
- 请求头模拟真实浏览器
- 代理支持（HTTP/HTTPS/SOCKS）

### 7.2 数据安全

- 文件名校验（移除非法字符）
- 路径遍历防护（使用 `Path` 类）
- 临时文件机制

## 8. 监控与调试

### 8.1 日志系统

```python
# 日志级别
DEBUG   - 详细调试信息
INFO    - 正常流程信息
WARNING - 可恢复的异常
ERROR   - 严重错误

# 日志内容
- 请求URL和状态
- 下载进度
- 错误详情
- 统计信息
```

### 8.2 统计信息

```python
stats = {
    'total': 0,      # 总任务数
    'success': 0,    # 成功数
    'failed': 0,     # 失败数
    'skipped': 0,    # 跳过数（已存在）
}
```

## 9. 技术栈

| 组件 | 用途 | 版本要求 |
|------|------|----------|
| Python | 运行环境 | >= 3.8 |
| requests | HTTP请求 | >= 2.25 |
| lxml | HTML解析 | >= 4.6 |
| urllib3 | 底层HTTP | >= 1.26 |

## 10. 未来规划

### 10.1 短期优化

- [ ] 修复各网站的 XPath 选择器
- [ ] 添加更多网站的爬虫实现
- [ ] 完善异常处理和错误恢复

### 10.2 中期规划

- [ ] 异步下载支持（asyncio + aiohttp）
- [ ] 数据库支持（记录下载历史）
- [ ] Web 管理界面
- [ ] 定时任务调度

### 10.3 长期愿景

- [ ] 分布式爬虫架构
- [ ] 智能去重和增量更新
- [ ] 图片分类和标签系统
- [ ] 机器学习辅助内容识别
