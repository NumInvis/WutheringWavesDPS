#!/usr/bin/env python3
"""
测试贴吧爬虫功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.tieba_crawler import crawl_all_tiebas

async def main():
    print("开始测试贴吧爬虫...")
    try:
        results = await crawl_all_tiebas()
        print(f"爬取完成，共爬取 {len(results)} 个贴吧")
        
        total_posts = 0
        for result in results:
            if not result.get("error"):
                post_count = result.get("post_count", 0)
                total_posts += post_count
                print(f"{result['tieba_name']}: {post_count} 帖")
            else:
                print(f"{result['tieba_name']}: 错误 - {result['error']}")
        
        print(f"总计: {total_posts} 帖")
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
