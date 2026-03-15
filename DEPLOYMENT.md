# WutheringWavesDPS 生产部署指南

## 域名:earth_americas: 部署到 www.arcanamorning.tech

## 前置条件

- 服务器已安装 Nginx、Supervisor、Python 3.8+、Node.js 16+
- 域名 www.arcanamorning.tech 已解析到服务器 IP

## 部署步骤

### 1. 准备部署目录和权限

```bash
# 创建日志目录
sudo mkdir -p /var/log/wuthering-waves-dps
sudo chown -R www-data:www-data /var/log/wuthering-waves-dps

# 创建必要的目录
sudo mkdir -p /var/www/html

# 设置项目权限
sudo chown -R $USER:$USER /root/ai/WutheringWavesDPS
sudo chmod -R 755 /root/ai/WutheringWavesDPS
```

### 2. 配置 Nginx

```bash
# 复制 Nginx 配置
sudo cp /root/ai/WutheringWavesDPS/deploy/nginx.conf /etc/nginx/sites-available/wuthering-waves-dps

# 创建软链接启用站点
sudo ln -s /etc/nginx/sites-available/wuthering-waves-dps /etc/nginx/sites-enabled/

# 删除默认站点（如果存在
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

### 3. 申请 SSL 证书（使用 Let's Encrypt）

```bash
# 安装 certbot
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d www.arcanamorning.tech

# 按照提示完成申请
```

证书申请成功后，certbot 会自动更新 Nginx 配置，取消注释 SSL 配置中的证书路径。

### 4. 配置 Supervisor

```bash
# 复制 Supervisor 配置
sudo cp /root/ai/WutheringWavesDPS/deploy/supervisor.conf /etc/supervisor/conf.d/wuthering-waves-dps.conf

# 重新加载 Supervisor
sudo supervisorctl reread
sudo supervisorctl update

# 启动服务
sudo supervisorctl start wuthering-waves-dps

# 查看状态
sudo supervisorctl status wuthering-waves-dps
```

### 5. 配置防火墙

```bash
# 允许 SSH、HTTP、HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

### 6. 设置日志轮转

创建 `/etc/logrotate.d/wuthering-waves-dps：

```bash
sudo tee /etc/logrotate.d/wuthering-waves-dps << 'EOF'
/var/log/wuthering-waves-dps/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        supervisorctl signal USR1 wuthering-waves-dps
    endscript
}
EOF
```

### 7. 数据库备份脚本

创建备份脚本：

```bash
sudo tee /opt/backup-wuwa.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/ai/WutheringWavesDPS/backups
mkdir -p $BACKUP_DIR

# 备份 SQLite 数据库
cp /root/ai/WutheringWavesDPS/backend/wuwa_calc.db $BACKUP_DIR/wuwa_calc_$DATE.db

# 压缩备份
gzip $BACKUP_DIR/wuwa_calc_$DATE.db

# 保留最近 7 天的备份
find $BACKUP_DIR/ -name "wuwa_calc_*.db.gz" -mtime +7 -delete
EOF

sudo chmod +x /opt/backup-wuwa.sh
```

添加到 crontab（每天凌晨 2 点备份）：

```bash
sudo crontab -e
```

添加以下内容：
```
0 2 * * * /opt/backup-wuwa.sh
```

## 服务管理命令

### Supervisor 命令

```bash
# 查看状态
sudo supervisorctl status wuthering-waves-dps

# 启动服务
sudo supervisorctl start wuthering-waves-dps

# 停止服务
sudo supervisorctl stop wuthering-waves-dps

# 重启服务
sudo supervisorctl restart wuthering-waves-dps

# 查看日志
sudo tail -f /var/log/wuthering-waves-dps/backend.log
```

### Nginx 命令

```bash
# 测试配置
sudo nginx -t

# 重载配置
sudo systemctl reload nginx

# 重启 Nginx
sudo systemctl restart nginx

# 查看访问日志
sudo tail -f /var/log/nginx/wuthering-waves-dps.access.log

# 查看错误日志
sudo tail -f /var/log/nginx/wuthering-waves-dps.error.log
```

## 访问应用

部署完成后，通过以下地址访问：

- **应用地址**: https://www.arcanamorning.tech/WutheringWavesDPS/
- **API 文档**: https://www.arcanamorning.tech/WutheringWavesDPS/docs

## 默认账号

- **管理员**: admin / admin123
- **测试用户**: person / person

⚠️ **重要**: 部署后立即修改密码！

## 更新部署

当需要更新代码时：

```bash
cd /root/ai/WutheringWavesDPS
git pull

# 重新构建前端
cd frontend
npm install
npm run build

# 重启服务
sudo supervisorctl restart wuthering-waves-dps
```

## 故障排查

### 服务无法启动

```bash
# 检查 Supervisor 日志
sudo supervisorctl tail wuthering-waves-dps

# 检查应用日志
sudo tail -n 100 /var/log/wuthering-waves-dps/backend.log

# 检查 Nginx 错误日志
sudo tail -n 100 /var/log/nginx/wuthering-waves-dps.error.log
```

### 502 Bad Gateway

通常是后端服务没有运行，检查：

```bash
sudo supervisorctl status wuthering-waves-dps
```

如果服务没有运行，尝试启动：

```bash
sudo supervisorctl start wuthering-waves-dps
```

## 安全建议

1. **定期更新系统和依赖包
2. **监控磁盘空间**
3. **定期备份数据库**
4. **使用强密码**
5. **监控访问日志
6. 考虑使用 Fail2ban 防止暴力破解
7. 定期审查用户活动
