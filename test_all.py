"""
测试所有爬虫
每个网站下载10张照片
"""
import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from crawlers import (
    XiurenwangCrawler, EveriaclubCrawler, TuiimgCrawler,
    KanxiaojiejieCrawler, NsfwpicxCrawler
)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 设置测试下载目录
os.environ['CRAWLER_DOWNLOAD_PATH'] = 'D:/crawler_test'
os.environ['USE_PROXY'] = 'false'  # 测试时先不使用代理


def test_crawler(name, crawler_class, **kwargs):
    """测试单个爬虫"""
    print(f"\n{'='*60}")
    print(f"测试爬虫: {name}")
    print(f"{'='*60}")
    
    try:
        with crawler_class() as crawler:
            crawler.crawl(start_page=1, max_images=10, **kwargs)
        print(f"✅ {name} 测试完成")
        return True
    except Exception as e:
        print(f"❌ {name} 测试失败: {e}")
        return False


def main():
    """主测试函数"""
    results = {}
    
    # 测试各个爬虫（不需要代理的）
    test_cases = [
        ('xiurenwang', XiurenwangCrawler),
        ('everiaclub', EveriaclubCrawler),
        ('tuiimg', TuiimgCrawler),
        ('kanxiaojiejie', KanxiaojiejieCrawler),
        ('nsfwpicx', NsfwpicxCrawler),
    ]
    
    for name, crawler_class in test_cases:
        results[name] = test_crawler(name, crawler_class)
    
    # 打印测试结果汇总
    print(f"\n{'='*60}")
    print("测试结果汇总")
    print(f"{'='*60}")
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{name:<20} {status}")
    
    print(f"\n总计: {success_count}/{total_count} 个爬虫测试通过")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
