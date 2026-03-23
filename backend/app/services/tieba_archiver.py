"""
贴吧数据长期存储归档服务
- 自动归档30天前的数据到压缩文件
- 保持活跃数据量可控
- 支持历史数据查询和恢复
- 不存储图片，只保留文本数据
"""

import json
import gzip
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import asyncio

from app.services.tieba_crawler import DATA_DIR, load_json_file, save_json_file, add_log

# 归档配置
ARCHIVE_DIR = Path(DATA_DIR) / "archives"
ARCHIVE_DIR.mkdir(exist_ok=True)

# 保留天数配置
ACTIVE_DAYS = 30  # 活跃数据保留30天
ARCHIVE_DAYS = 365  # 归档数据保留365天（1年）


class TiebaArchiver:
    """贴吧数据归档管理器"""
    
    def __init__(self):
        self.archive_dir = ARCHIVE_DIR
        self.archive_dir.mkdir(exist_ok=True)
        
    def get_archive_path(self, date_str: str) -> Path:
        """获取归档文件路径"""
        return self.archive_dir / f"tieba_posts_{date_str}.json.gz"
    
    def should_archive_date(self, date_str: str) -> bool:
        """判断某个日期是否应该被归档"""
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            cutoff_date = datetime.now() - timedelta(days=ACTIVE_DAYS)
            return date < cutoff_date
        except:
            return False
    
    def archive_posts_by_date(self, posts: List[Dict], date_str: str) -> bool:
        """将指定日期的帖子归档到压缩文件"""
        try:
            archive_path = self.get_archive_path(date_str)
            
            # 清理帖子数据（移除不必要字段，确保不存储图片）
            cleaned_posts = []
            for post in posts:
                cleaned_post = {
                    "tid": post.get("tid"),
                    "post_id": post.get("post_id"),
                    "title": post.get("title", ""),
                    "text": post.get("text", ""),
                    "reply_num": post.get("reply_num", 0),
                    "agree": post.get("agree", 0),
                    "like_count": post.get("like_count", 0),
                    "hot_index": post.get("hot_index", 0),
                    "url": post.get("url", ""),
                    "post_time": post.get("post_time", ""),
                    "tieba_name": post.get("tieba_name", ""),
                    "author_id": post.get("author_id", "未知")
                }
                cleaned_posts.append(cleaned_post)
            
            # 压缩存储
            json_data = json.dumps(cleaned_posts, ensure_ascii=False, indent=2)
            with gzip.open(archive_path, 'wt', encoding='utf-8') as f:
                f.write(json_data)
            
            add_log("info", f"归档完成: {date_str}，共 {len(cleaned_posts)} 条帖子")
            return True
            
        except Exception as e:
            add_log("error", f"归档失败 [{date_str}]: {e}")
            return False
    
    def load_archived_posts(self, date_str: str) -> List[Dict]:
        """从归档文件加载帖子"""
        try:
            archive_path = self.get_archive_path(date_str)
            if not archive_path.exists():
                return []
            
            with gzip.open(archive_path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            add_log("error", f"加载归档失败 [{date_str}]: {e}")
            return []
    
    async def archive_old_posts(self):
        """归档旧帖子数据"""
        add_log("info", "开始归档旧数据...")
        
        archived_count = 0
        archived_dates = []
        
        for tieba_name in self._get_monitored_tiebas():
            posts_file = Path(DATA_DIR) / f"{tieba_name}.json"
            if not posts_file.exists():
                continue
            
            posts = load_json_file(f"{tieba_name}.json")
            if not isinstance(posts, list):
                continue
            
            # 按日期分组
            posts_by_date: Dict[str, List[Dict]] = {}
            active_posts: List[Dict] = []
            
            for post in posts:
                post_time = post.get("post_time", "")
                if not post_time:
                    continue
                
                try:
                    date_str = post_time.split()[0]  # 提取日期部分
                    
                    if self.should_archive_date(date_str):
                        # 需要归档的帖子
                        if date_str not in posts_by_date:
                            posts_by_date[date_str] = []
                        posts_by_date[date_str].append(post)
                        archived_count += 1
                    else:
                        # 保留的活跃帖子
                        active_posts.append(post)
                except:
                    active_posts.append(post)
            
            # 归档各日期的帖子
            for date_str, date_posts in posts_by_date.items():
                # 加载已存在的归档数据（如果有）
                existing_archived = self.load_archived_posts(date_str)
                existing_ids = {p.get("post_id") for p in existing_archived}
                
                # 合并新归档的帖子
                for post in date_posts:
                    if post.get("post_id") not in existing_ids:
                        existing_archived.append(post)
                
                # 保存归档
                if existing_archived:
                    self.archive_posts_by_date(existing_archived, date_str)
                    archived_dates.append(date_str)
            
            # 保存活跃帖子回文件
            if len(active_posts) < len(posts):
                save_json_file(f"{tieba_name}.json", active_posts)
                add_log("info", f"[{tieba_name}] 保留 {len(active_posts)}/{len(posts)} 条活跃帖子")
        
        # 归档统计数据
        await self._archive_old_stats()
        
        # 清理过期归档
        self._cleanup_expired_archives()
        
        add_log("info", f"归档完成：共归档 {archived_count} 条帖子，{len(set(archived_dates))} 个日期")
    
    async def _archive_old_stats(self):
        """归档旧的统计数据"""
        try:
            stats = load_json_file("stats.json")
            daily_posts = stats.get("daily_posts", {})
            
            cutoff_date = (datetime.now() - timedelta(days=ACTIVE_DAYS)).strftime("%Y-%m-%d")
            
            # 分离活跃和归档数据
            active_daily = {}
            archived_daily = {}
            
            for date_str, data in daily_posts.items():
                if date_str >= cutoff_date:
                    active_daily[date_str] = data
                else:
                    archived_daily[date_str] = data
            
            # 保存归档的统计数据
            if archived_daily:
                archive_stats_path = self.archive_dir / f"stats_archive_{datetime.now().strftime('%Y%m')}.json.gz"
                
                # 加载已存在的归档统计
                existing_archived = {}
                if archive_stats_path.exists():
                    try:
                        with gzip.open(archive_stats_path, 'rt', encoding='utf-8') as f:
                            existing_archived = json.load(f)
                    except:
                        pass
                
                # 合并数据
                existing_archived.update(archived_daily)
                
                # 保存
                with gzip.open(archive_stats_path, 'wt', encoding='utf-8') as f:
                    json.dump(existing_archived, f, ensure_ascii=False, indent=2)
                
                add_log("info", f"统计数据归档完成：{len(archived_daily)} 天")
            
            # 保存活跃的统计数据
            stats["daily_posts"] = active_daily
            save_json_file("stats.json", stats)
            
        except Exception as e:
            add_log("error", f"归档统计数据失败: {e}")
    
    def _cleanup_expired_archives(self):
        """清理过期的归档文件（超过1年）"""
        try:
            cutoff_date = datetime.now() - timedelta(days=ARCHIVE_DAYS)
            
            for archive_file in self.archive_dir.glob("*.json.gz"):
                try:
                    # 从文件名提取日期
                    file_stat = archive_file.stat()
                    file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    if file_mtime < cutoff_date:
                        archive_file.unlink()
                        add_log("info", f"清理过期归档: {archive_file.name}")
                except:
                    pass
                    
        except Exception as e:
            add_log("error", f"清理过期归档失败: {e}")
    
    def _get_monitored_tiebas(self) -> List[str]:
        """获取监控的贴吧列表"""
        return [
            "鸣潮爆料", "鸣潮内鬼", "新鸣潮内鬼", "北落野", "鸣潮",
            "三度笑话", "原神内鬼", "mihoyo", "asoul",
            "崩坏星穹铁道内鬼", "星穹铁道内鬼", "原神内鬼爆料", "绝区零内鬼", "快乐雪花"
        ]
    
    def get_storage_stats(self) -> Dict:
        """获取存储统计信息"""
        stats = {
            "active_posts": 0,
            "archived_posts": 0,
            "archive_files": 0,
            "total_size_mb": 0,
            "oldest_archive": None,
            "newest_archive": None
        }
        
        try:
            # 统计活跃帖子
            for tieba_name in self._get_monitored_tiebas():
                posts = load_json_file(f"{tieba_name}.json")
                if isinstance(posts, list):
                    stats["active_posts"] += len(posts)
            
            # 统计归档文件
            archive_files = list(self.archive_dir.glob("*.json.gz"))
            stats["archive_files"] = len(archive_files)
            
            total_size = 0
            archive_dates = []
            
            for archive_file in archive_files:
                file_stat = archive_file.stat()
                total_size += file_stat.st_size
                archive_dates.append(datetime.fromtimestamp(file_stat.st_mtime))
            
            stats["total_size_mb"] = round(total_size / (1024 * 1024), 2)
            
            if archive_dates:
                stats["oldest_archive"] = min(archive_dates).strftime("%Y-%m-%d")
                stats["newest_archive"] = max(archive_dates).strftime("%Y-%m-%d")
            
        except Exception as e:
            add_log("error", f"获取存储统计失败: {e}")
        
        return stats
    
    def search_archived_posts(self, keyword: str, limit: int = 100) -> List[Dict]:
        """在归档数据中搜索帖子"""
        results = []
        
        try:
            for archive_file in sorted(self.archive_dir.glob("*.json.gz"), reverse=True):
                if len(results) >= limit:
                    break
                
                try:
                    with gzip.open(archive_file, 'rt', encoding='utf-8') as f:
                        posts = json.load(f)
                        
                    for post in posts:
                        title = post.get("title", "")
                        text = post.get("text", "")
                        
                        if keyword.lower() in title.lower() or keyword.lower() in text.lower():
                            results.append(post)
                            if len(results) >= limit:
                                break
                                
                except Exception as e:
                    continue
                    
        except Exception as e:
            add_log("error", f"搜索归档数据失败: {e}")
        
        return results


# 全局归档器实例
_archiver = TiebaArchiver()


async def run_archive_task():
    """运行归档任务"""
    await _archiver.archive_old_posts()


def get_archiver() -> TiebaArchiver:
    """获取归档器实例"""
    return _archiver


def get_archive_stats() -> Dict:
    """获取归档统计"""
    return _archiver.get_storage_stats()
