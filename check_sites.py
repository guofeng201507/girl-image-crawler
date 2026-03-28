"""
检查各网站结构
"""
import requests
from lxml import etree

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

sites = [
    ('everia.club', 'https://everia.club', '//article'),
    ('tuiimg.com', 'https://www.tuiimg.com/meinv/', '//ul[@class="img"]//li'),
    ('kanxiaojiejie.com', 'https://www.kanxiaojiejie.com', '//div[contains(@class, "post")]'),
    ('nsfwpicx', 'https://nsfwx.pics', '//div[contains(@class, "post")]'),
    ('xiurenwang', 'https://www.xiurenwang.cc/bang/page/1', '//ul[@class="list"]/li'),
    ('test', 'https://www.xiurenwang.cc/bang/page/1', '//body'),
]

for name, url, xpath in sites:
    print(f"\n{'='*60}")
    print(f"检查: {name}")
    print(f"URL: {url}")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            html = etree.HTML(resp.text)
            items = html.xpath(xpath)
            print(f"找到 {len(items)} 个元素 (xpath: {xpath})")
            
            if items:
                # 尝试提取第一个元素的链接和标题
                first = items[0]
                links = first.xpath('.//a/@href')
                titles = first.xpath('.//img/@alt') or first.xpath('.//a/@title') or first.xpath('.//h2//text()')
                print(f"  第一个元素链接: {links[:1] if links else 'None'}")
                print(f"  第一个元素标题: {titles[:1] if titles else 'None'}")
    except Exception as e:
        print(f"Error: {e}")
