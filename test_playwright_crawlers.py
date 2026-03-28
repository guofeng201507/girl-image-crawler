"""
测试所有 Playwright 爬虫
验证迁移是否成功
"""
import logging
import sys
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入所有爬虫
from crawlers import (
    XiurenwangCrawler,
    HotgirlCrawler,
)

# 测试配置
TEST_MAX_IMAGES = 3  # 每个网站测试下载 3 张图片


def test_crawler(crawler_class, name: str) -> dict:
    """测试单个爬虫"""
    result = {
        'name': name,
        'success': False,
        'downloaded': 0,
        'error': None,
    }
    
    logger.info(f"\n{'='*60}")
    logger.info(f"测试爬虫: {name}")
    logger.info('='*60)
    
    try:
        with crawler_class() as crawler:
            crawler.crawl(start_page=1, max_images=TEST_MAX_IMAGES)
            result['downloaded'] = crawler.stats['success']
            result['success'] = crawler.stats['success'] > 0
            
    except Exception as e:
        logger.error(f"爬虫 {name} 测试失败: {e}")
        result['error'] = str(e)
    
    return result


def main():
    """主测试函数"""
    logger.info("开始 Playwright 爬虫测试")
    logger.info(f"每个网站测试下载 {TEST_MAX_IMAGES} 张图片")
    
    # 爬虫列表（排除 WallhavenCrawler 需要 ID 文件）
    crawlers = [
        (XiurenwangCrawler, "秀人网"),
        (HotgirlCrawler, "HotGirl"),
    ]
    
    results = []
    for crawler_class, name in crawlers:
        result = test_crawler(crawler_class, name)
        results.append(result)
    
    # 打印测试结果汇总
    logger.info("\n" + "="*60)
    logger.info("测试结果汇总")
    logger.info("="*60)
    
    total_success = 0
    total_downloaded = 0
    
    for r in results:
        status = "✓ 成功" if r['success'] else "✗ 失败"
        logger.info(f"{status} | {r['name']:15} | 下载: {r['downloaded']}张")
        if r['error']:
            logger.info(f"      错误: {r['error']}")
        if r['success']:
            total_success += 1
        total_downloaded += r['downloaded']
    
    logger.info("-"*60)
    logger.info(f"总计: {total_success}/{len(results)} 个爬虫成功")
    logger.info(f"总共下载: {total_downloaded} 张图片")
    logger.info("="*60)
    
    return total_success == len(results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
