#!/bin/bash
# 数据备份脚本
# 备份数据库、上传文件、畅销榜数据
# 总大小限制50MB

BACKUP_DIR="/root/ai/WutheringWavesDPS/backups"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/root/ai/WutheringWavesDPS"
MAX_SIZE_MB=50

mkdir -p "$BACKUP_DIR"

echo "开始备份... $DATE"

# 备份数据库
cp "$PROJECT_DIR/backend/wuwa_calc.db" "$BACKUP_DIR/wuwa_calc_$DATE.db"
echo "数据库已备份"

# 备份uploads目录（仅xlsx文件，不包含_original）
cd "$PROJECT_DIR/backend/uploads"
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" --exclude="*_original.xlsx" *.xlsx 2>/dev/null
echo "uploads目录已备份"

# 导出畅销榜数据为CSV
cd "$PROJECT_DIR/backend"
source venv/bin/activate
python3 << 'PYEOF'
from app.core.database import SessionLocal
from app.models.app_ranking import AppInfo, RankingRecord
from app.models.spreadsheet import Spreadsheet
import csv
import os

backup_dir = "/root/ai/WutheringWavesDPS/backups"
date_str = os.popen('date +%Y%m%d_%H%M%S').read().strip()

db = SessionLocal()

# 导出畅销榜数据
records = db.query(RankingRecord).all()
with open(f"{backup_dir}/ranking_{date_str}.csv", 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['游戏名', '国家', '排名', '时间'])
    for r in records:
        app = db.query(AppInfo).filter(AppInfo.id == r.app_id).first()
        writer.writerow([app.name_cn if app else r.app_id, r.country, r.rank, r.recorded_at])
print(f"畅销榜数据已导出: {len(records)} 条")

# 导出表格列表
sheets = db.query(Spreadsheet).all()
with open(f"{backup_dir}/spreadsheets_{date_str}.csv", 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['ID', '标题', '编号', '文件URL', '浏览数', '创建时间'])
    for s in sheets:
        writer.writerow([s.id, s.title, s.sheet_number, s.file_url, s.view_count, s.created_at])
print(f"表格列表已导出: {len(sheets)} 条")

db.close()
PYEOF

# 清理旧备份（保留最近7天）
find "$BACKUP_DIR" -name "*.db" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.csv" -mtime +7 -delete

# 检查总大小，如果超过50MB则删除最旧的文件
while true; do
    TOTAL_SIZE=$(du -sm "$BACKUP_DIR" | cut -f1)
    if [ "$TOTAL_SIZE" -le "$MAX_SIZE_MB" ]; then
        break
    fi
    # 删除最旧的文件
    OLDEST_FILE=$(ls -t "$BACKUP_DIR" | tail -1)
    if [ -z "$OLDEST_FILE" ]; then
        break
    fi
    rm "$BACKUP_DIR/$OLDEST_FILE"
    echo "删除旧备份: $OLDEST_FILE"
done

echo "备份完成！当前大小: $(du -sh "$BACKUP_DIR" | cut -f1)"
ls -la "$BACKUP_DIR" | tail -10
