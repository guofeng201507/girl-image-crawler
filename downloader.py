"""
通用下载器模块
提供统一的文件下载功能，支持重试、断点续传、进度显示
"""
import os
import time
import logging
from pathlib import Path
from typing import Optional, Callable
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import DownloadConfig, DEFAULT_HEADERS, PROXY

logger = logging.getLogger(__name__)


class Downloader:
    """通用文件下载器"""
    
    def __init__(self, headers: Optional[dict] = None, proxy: Optional[dict] = None):
        self.headers = headers or DEFAULT_HEADERS.copy()
        self.proxy = proxy or PROXY
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建配置好的session"""
        session = requests.Session()
        session.headers.update(self.headers)
        
        # 配置重试策略
        retry_strategy = Retry(
            total=DownloadConfig.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def download(
        self, 
        url: str, 
        filepath: Path, 
        overwrite: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        下载文件
        
        Args:
            url: 下载链接
            filepath: 保存路径
            overwrite: 是否覆盖已存在文件
            progress_callback: 进度回调函数(已下载, 总大小)
        
        Returns:
            bool: 下载是否成功
        """
        filepath = Path(filepath)
        
        # 检查文件是否已存在
        if filepath.exists() and not overwrite:
            logger.debug(f"文件已存在，跳过: {filepath}")
            return True
        
        # 确保目录存在
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # 临时文件路径
        temp_path = filepath.with_suffix(filepath.suffix + '.tmp')
        
        for attempt in range(DownloadConfig.MAX_RETRIES):
            try:
                response = self.session.get(
                    url, 
                    stream=True, 
                    timeout=DownloadConfig.TIMEOUT,
                    proxies=self.proxy
                )
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=DownloadConfig.CHUNK_SIZE):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback:
                                progress_callback(downloaded, total_size)
                
                # 检查文件大小
                if temp_path.stat().st_size < DownloadConfig.MIN_FILE_SIZE:
                    logger.warning(f"文件过小，可能下载失败: {url}")
                    temp_path.unlink(missing_ok=True)
                    return False
                
                # 移动到最终位置
                temp_path.rename(filepath)
                logger.debug(f"下载成功: {filepath.name}")
                return True
                
            except Exception as e:
                logger.warning(f"下载失败 (尝试 {attempt + 1}/{DownloadConfig.MAX_RETRIES}): {url} - {e}")
                if temp_path.exists():
                    temp_path.unlink(missing_ok=True)
                if attempt < DownloadConfig.MAX_RETRIES - 1:
                    time.sleep(DownloadConfig.RETRY_DELAY * (attempt + 1))
        
        logger.error(f"下载最终失败: {url}")
        return False
    
    def download_image(self, url: str, folder: Path, filename: Optional[str] = None) -> Optional[Path]:
        """
        下载图片（自动处理扩展名）
        
        Args:
            url: 图片URL
            folder: 保存文件夹
            filename: 指定文件名，None则使用URL中的文件名
        
        Returns:
            Path: 下载后的文件路径，失败返回None
        """
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        
        if filename is None:
            filename = os.path.basename(url.split('?')[0])
        
        filepath = folder / filename
        
        # 尝试下载
        if self.download(url, filepath):
            return filepath
        
        # 如果失败，尝试其他扩展名
        if filepath.suffix.lower() == '.jpg':
            alt_filepath = filepath.with_suffix('.png')
        else:
            alt_filepath = filepath.with_suffix('.jpg')
        
        alt_url = url.replace(filepath.suffix, alt_filepath.suffix)
        if self.download(alt_url, alt_filepath):
            return alt_filepath
        
        return None
    
    def close(self):
        """关闭session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
