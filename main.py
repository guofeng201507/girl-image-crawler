"""
爬虫统一入口
提供命令行界面管理所有爬虫
"""
import sys
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import SITE_CONFIGS, LOG_CONFIG, DOWNLOAD_ROOT
from crawlers import XiurenwangCrawler, HotgirlCrawler


def setup_logging(level: str = 'INFO'):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=LOG_CONFIG['format'],
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_CONFIG['file'], encoding='utf-8'),
        ]
    )


def list_sites():
    """列出所有可用站点"""
    print("\n可用站点列表:")
    print("-" * 50)
    print(f"{'站点Key':<15} {'站点名称':<20} {'需要代理':<10}")
    print("-" * 50)
    for key, config in SITE_CONFIGS.items():
        proxy = "是" if config.get('proxy') else "否"
        print(f"{key:<15} {config['name']:<20} {proxy:<10}")
    print("-" * 50)


def crawl_site(site: str, start_page: int = 1, end_page: int = None, max_images: int = None):
    """运行指定站点的爬虫"""
    if site not in SITE_CONFIGS:
        print(f"错误: 未知站点 '{site}'")
        print(f"可用站点: {', '.join(SITE_CONFIGS.keys())}")
        return

    config = SITE_CONFIGS[site]
    print(f"\n开始爬取: {config['name']}")
    print(f"下载目录: {DOWNLOAD_ROOT / config['download_dir']}")
    print(f"页码范围: {start_page} - {end_page or '不限'}")
    print("-" * 50)

    crawler_map = {
        'xiurenwang': XiurenwangCrawler,
        'hotgirl': HotgirlCrawler,
    }

    if site not in crawler_map:
        print(f"错误: 站点 '{site}' 的爬虫尚未实现")
        return

    with crawler_map[site]() as crawler:
        crawler.crawl(start_page=start_page, end_page=end_page, max_images=max_images)

    print(f"\n爬取完成: {config['name']}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='图片爬虫工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 列出所有可用站点
  python main.py --list

  # 爬取秀人网第1-5页
  python main.py xiurenwang --start-page 1 --end-page 5

  # 爬取HotGirl，最多下载20张
  python main.py hotgirl --max-images 20

  # 设置下载目录（环境变量）
  set CRAWLER_DOWNLOAD_PATH=D:/downloads
  set USE_PROXY=true
        """
    )

    parser.add_argument('site', nargs='?', help='要爬取的站点key')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有可用站点')
    parser.add_argument('--start-page', '-s', type=int, default=1, help='起始页码 (默认: 1)')
    parser.add_argument('--end-page', '-e', type=int, help='结束页码')
    parser.add_argument('--max-images', '-n', type=int, help='最多下载图片数量')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='日志级别 (默认: INFO)')

    args = parser.parse_args()
    setup_logging(args.log_level)

    if args.list:
        list_sites()
        return

    if not args.site:
        parser.print_help()
        print("\n错误: 请指定站点或使用 --list 查看可用站点")
        return

    crawl_site(
        site=args.site,
        start_page=args.start_page,
        end_page=args.end_page,
        max_images=args.max_images,
    )


if __name__ == '__main__':
    main()
