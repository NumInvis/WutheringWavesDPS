#!/bin/bash

# WutheringWavesDPS 一键部署脚本
# 部署到 www.arcanamorning.tech

set -e

echo "============================================="
echo "  WutheringWavesDPS 生产部署脚本"
echo "  域名: www.arcanamorning.tech"
echo "============================================="

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 项目目录
PROJECT_DIR="/root/ai/WutheringWavesDPS"
cd "$PROJECT_DIR"

echo ""
echo -e "${GREEN}[1/9] 检测系统类型...${NC}"

# 使用 OpenCloudOS/RHEL 配置
PKG_MGR="dnf"
PKG_INSTALL="dnf install -y"
PKG_UPDATE="dnf check-update || true"
NGINX_CONF_DIR="/etc/nginx/conf.d"
NGINX_ENABLED_DIR=""
WWW_USER="nginx"
WWW_GROUP="nginx"

echo -e "${GREEN}✓ 使用 OpenCloudOS 配置${NC}"

echo ""
echo -e "${GREEN}[2/9] 安装必要软件...${NC}"

# 安装软件
$PKG_INSTALL nginx-core supervisor python3 python3-pip nodejs npm git

# 启用并启动服务
systemctl enable --now nginx
systemctl enable --now supervisord || systemctl enable --now supervisor

echo -e "${GREEN}✓ 软件安装完成${NC}"

echo ""
echo -e "${GREEN}[3/9] 创建必要目录...${NC}"

mkdir -p /var/log/wuthering-waves-dps
chown -R $WWW_USER:$WWW_GROUP /var/log/wuthering-waves-dps
mkdir -p /var/www/html
mkdir -p "$PROJECT_DIR/backups"
mkdir -p "$PROJECT_DIR/backend/uploads"
mkdir -p "$PROJECT_DIR/frontend/dist"

echo -e "${GREEN}✓ 目录创建完成${NC}"

echo ""
echo -e "${GREEN}[4/9] 配置后端环境...${NC}"

cd "$PROJECT_DIR/backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 -c "from app.database import init_db; init_db()"

echo -e "${GREEN}✓ 后端环境配置完成${NC}"

echo ""
echo -e "${GREEN}[5/9] 构建前端...${NC}"

cd "$PROJECT_DIR/frontend"

npm install
npm run build

echo -e "${GREEN}✓ 前端构建完成${NC}"

echo ""
echo -e "${GREEN}[6/9] 配置 Nginx...${NC}"

cd "$PROJECT_DIR"

cp "$PROJECT_DIR/deploy/nginx.conf" "$NGINX_CONF_DIR/wuthering-waves-dps.conf"

if nginx -t; then
    systemctl reload nginx
    echo -e "${GREEN}✓ Nginx 配置完成${NC}"
else
    echo -e "${RED}Nginx 配置错误，请检查${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}[7/9] 配置 Supervisor...${NC}"

sed -i "s/www-data/$WWW_USER/g" "$PROJECT_DIR/deploy/supervisor.conf"
sed -i "s/www-data/$WWW_GROUP/g" "$PROJECT_DIR/deploy/supervisor.conf"

if [ -f /etc/supervisor/conf.d/wuthering-waves-dps.conf ]; then
    cp /etc/supervisor/conf.d/wuthering-waves-dps.conf /etc/supervisor/conf.d/wuthering-waves-dps.conf.backup
fi

cp "$PROJECT_DIR/deploy/supervisor.conf" /etc/supervisor/conf.d/wuthering-waves-dps.conf

supervisorctl reread
supervisorctl update

echo -e "${GREEN}✓ Supervisor 配置完成${NC}"

echo ""
echo -e "${YELLOW}[8/9] 配置日志轮转...${NC}"

cat > /etc/logrotate.d/wuthering-waves-dps << EOF
/var/log/wuthering-waves-dps/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 $WWW_USER $WWW_GROUP
    sharedscripts
    postrotate
        supervisorctl signal USR1 wuthering-waves-dps 2>/dev/null || true
    endscript
}
EOF

echo -e "${GREEN}✓ 日志轮转配置完成${NC}"

echo ""
echo -e "${YELLOW}[9/9] 启动服务...${NC}"

supervisorctl start wuthering-waves-dps || supervisorctl restart wuthering-waves-dps

sleep 3

if supervisorctl status wuthering-waves-dps | grep -q "RUNNING"; then
    echo -e "${GREEN}✓ 服务启动成功${NC}"
else
    echo -e "${RED}✗ 服务启动失败，请检查日志${NC}"
    supervisorctl tail wuthering-waves-dps
    exit 1
fi

echo ""
echo "============================================="
echo -e "${GREEN}  部署完成！${NC}"
echo "============================================="
echo ""
echo "📋 下一步操作："
echo ""
echo "1. 申请 SSL 证书："
echo "   sudo dnf install -y certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d www.arcanamorning.tech"
echo ""
echo "2. 访问应用："
echo "   http://www.arcanamorning.tech/WutheringWavesDPS/"
echo ""
echo "3. 默认账号（请立即修改）："
echo "   管理员: admin / admin123"
echo "   测试用户: person / person"
echo ""
echo "4. 查看服务状态："
echo "   sudo supervisorctl status wuthering-waves-dps"
echo ""
echo "5. 查看日志："
echo "   应用日志: sudo tail -f /var/log/wuthering-waves-dps/backend.log"
echo "   Nginx日志: sudo tail -f /var/log/nginx/access.log"
echo ""
echo "============================================="
