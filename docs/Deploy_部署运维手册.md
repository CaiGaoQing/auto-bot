# 部署运维手册

**版本**: v1.0  
**日期**: 2024-01-16

---

## 1. 部署模式

### 1.1 模式对比

| 模式 | 组件 | 适用场景 | 复杂度 |
|------|------|----------|--------|
| **本地模式** | CLI | 个人开发 | ⭐ |
| **单机模式** | CLI + 后端 + MySQL | 个人/小团队 | ⭐⭐ |
| **完整模式** | 全部组件 | 团队/生产 | ⭐⭐⭐ |

---

## 2. 本地模式部署

### 2.1 系统要求

| 组件 | 最低要求 |
|------|----------|
| Python | 3.11+ |
| 磁盘 | 1GB |
| 内存 | 512MB |

### 2.2 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-org/ai-auto.git
cd ai-auto

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -e .

# 4. 初始化配置
auto init

# 5. 配置 AI 提供商
auto config provider add --name openai --api-key "sk-xxx"

# 6. 验证安装
auto --version
auto chat "你好"
```

### 2.3 配置文件

配置文件位置: `~/.auto/config.yaml`

```yaml
# ~/.auto/config.yaml

# 运行模式
mode: local  # local | remote

# 数据存储
storage:
  type: sqlite
  path: ~/.auto/data.db

# 工作空间默认路径
workspace:
  default_path: ~/auto-workspaces

# 默认 AI 配置
ai:
  default_provider: openai
  default_model: gpt-4o

# 日志配置
logging:
  level: INFO
  file: ~/.auto/logs/auto.log
```

---

## 3. 单机 Docker 部署

### 3.1 系统要求

| 组件 | 最低要求 |
|------|----------|
| Docker | 20.10+ |
| Docker Compose | 2.0+ |
| CPU | 2 核 |
| 内存 | 4GB |
| 磁盘 | 20GB |

### 3.2 目录结构

```
deploy/
├── docker-compose.yml
├── .env
├── nginx/
│   └── nginx.conf
├── mysql/
│   └── init.sql
└── data/
    ├── mysql/
    ├── redis/
    └── uploads/
```

### 3.3 环境变量

```bash
# .env

# 基础配置
APP_ENV=production
APP_SECRET_KEY=your-secret-key-here
APP_DEBUG=false

# 数据库配置
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=ai_assistant
MYSQL_USER=auto
MYSQL_PASSWORD=your-db-password

# Redis 配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# AI 配置 (可选，也可通过 Web/CLI 配置)
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1

# 加密密钥 (用于加密 API Key)
ENCRYPTION_KEY=your-32-byte-encryption-key

# JWT 配置
JWT_SECRET_KEY=your-jwt-secret
JWT_EXPIRE_HOURS=24
```

### 3.4 Docker Compose

```yaml
# docker-compose.yml

version: '3.8'

services:
  # 后端 API
  api:
    image: ai-auto/api:latest
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=${APP_ENV}
      - MYSQL_HOST=${MYSQL_HOST}
      - MYSQL_PORT=${MYSQL_PORT}
      - MYSQL_DATABASE=${MYSQL_DATABASE}
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - REDIS_HOST=${REDIS_HOST}
      - REDIS_PORT=${REDIS_PORT}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    volumes:
      - ./data/uploads:/app/uploads
      - ./data/workspaces:/app/workspaces
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Celery Worker
  worker:
    image: ai-auto/api:latest
    command: celery -A app.celery worker -l info
    environment:
      - APP_ENV=${APP_ENV}
      - MYSQL_HOST=${MYSQL_HOST}
      - MYSQL_DATABASE=${MYSQL_DATABASE}
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - REDIS_HOST=${REDIS_HOST}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    volumes:
      - ./data/uploads:/app/uploads
      - ./data/workspaces:/app/workspaces
    depends_on:
      - api
      - redis
    restart: unless-stopped

  # Celery Beat (定时任务)
  beat:
    image: ai-auto/api:latest
    command: celery -A app.celery beat -l info
    environment:
      - APP_ENV=${APP_ENV}
      - MYSQL_HOST=${MYSQL_HOST}
      - REDIS_HOST=${REDIS_HOST}
    depends_on:
      - api
      - redis
    restart: unless-stopped

  # Web 前端 (可选)
  web:
    image: ai-auto/web:latest
    build:
      context: ./web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api:8000
    depends_on:
      - api
    restart: unless-stopped

  # MySQL
  mysql:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-root}
      - MYSQL_DATABASE=${MYSQL_DATABASE}
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
    volumes:
      - ./data/mysql:/var/lib/mysql
      - ./mysql/init.sql:/docker-entrypoint-initdb.d/init.sql
    command: --default-authentication-plugin=mysql_native_password --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - ./data/redis:/data
    restart: unless-stopped

  # Nginx (反向代理)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - api
      - web
    restart: unless-stopped

networks:
  default:
    name: ai-auto-network
```

### 3.5 Nginx 配置

```nginx
# nginx/nginx.conf

events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    upstream web {
        server web:3000;
    }

    # API 服务
    server {
        listen 80;
        server_name api.example.com;

        location / {
            proxy_pass http://api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket 支持
            proxy_read_timeout 86400;
        }
    }

    # Web 前端
    server {
        listen 80;
        server_name app.example.com;

        location / {
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        location /api {
            proxy_pass http://api;
            proxy_set_header Host $host;
        }
    }
}
```

### 3.6 部署命令

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down

# 重启单个服务
docker-compose restart api

# 查看状态
docker-compose ps

# 进入容器
docker-compose exec api bash

# 数据库迁移
docker-compose exec api alembic upgrade head
```

---

## 4. 数据库初始化

### 4.1 MySQL 初始化脚本

```sql
-- mysql/init.sql

-- 创建数据库
CREATE DATABASE IF NOT EXISTS ai_assistant
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER IF NOT EXISTS 'auto'@'%' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON ai_assistant.* TO 'auto'@'%';
FLUSH PRIVILEGES;

USE ai_assistant;

-- 创建表结构 (由 Alembic 管理，这里只是备用)
-- 见 Database_数据库设计.md
```

### 4.2 Alembic 迁移

```bash
# 生成迁移
alembic revision --autogenerate -m "initial"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1

# 查看历史
alembic history
```

---

## 5. 环境配置

### 5.1 开发环境

```yaml
# config/development.yaml

debug: true
log_level: DEBUG

database:
  echo: true  # 打印 SQL

cors:
  allow_origins: ["*"]

ai:
  timeout: 120
  retry: 3
```

### 5.2 生产环境

```yaml
# config/production.yaml

debug: false
log_level: INFO

database:
  pool_size: 20
  max_overflow: 10
  echo: false

cors:
  allow_origins:
    - "https://app.example.com"

ai:
  timeout: 60
  retry: 2

security:
  rate_limit:
    enabled: true
    requests_per_minute: 1000
```

---

## 6. SSL 配置

### 6.1 Let's Encrypt

```bash
# 安装 certbot
apt install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d api.example.com -d app.example.com

# 自动续期
certbot renew --dry-run
```

### 6.2 Nginx SSL 配置

```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    location / {
        proxy_pass http://api;
        # ... 其他配置
    }
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name api.example.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 7. 监控配置

### 7.1 日志配置

```yaml
# config/logging.yaml

version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  json:
    class: pythonjsonlogger.jsonlogger.JsonFormatter
    format: '%(asctime)s %(name)s %(levelname)s %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    formatter: standard
    level: INFO
    
  file:
    class: logging.handlers.RotatingFileHandler
    filename: /var/log/auto/app.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
    formatter: json

root:
  level: INFO
  handlers: [console, file]
```

### 7.2 Prometheus 指标

```python
# app/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# 请求计数
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# 请求延迟
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# AI 请求
AI_REQUEST_COUNT = Counter(
    'ai_requests_total',
    'Total AI requests',
    ['provider', 'model', 'status']
)

# Token 使用
TOKEN_USAGE = Counter(
    'token_usage_total',
    'Total tokens used',
    ['provider', 'model', 'type']
)

# 活跃连接
ACTIVE_CONNECTIONS = Gauge(
    'active_websocket_connections',
    'Active WebSocket connections'
)
```

### 7.3 Prometheus 配置

```yaml
# prometheus/prometheus.yml

global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-auto-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

  - job_name: 'mysql'
    static_configs:
      - targets: ['mysql-exporter:9104']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### 7.4 Grafana Dashboard

导入预配置的 Dashboard:

```json
{
  "dashboard": {
    "title": "AI Auto Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Token Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(token_usage_total[1h])) by (model)"
          }
        ]
      }
    ]
  }
}
```

---

## 8. 备份与恢复

### 8.1 备份策略

| 类型 | 频率 | 保留时间 | 存储位置 |
|------|------|----------|----------|
| 全量备份 | 每天 02:00 | 30天 | S3/OSS |
| 增量备份 | 每小时 | 7天 | 本地 |
| 实时同步 | 实时 | - | 从库 |

### 8.2 备份脚本

```bash
#!/bin/bash
# scripts/backup.sh

set -e

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup"
S3_BUCKET="s3://your-bucket/backups"

# MySQL 备份
echo "Backing up MySQL..."
docker-compose exec -T mysql mysqldump \
    -u${MYSQL_USER} -p${MYSQL_PASSWORD} \
    --single-transaction \
    --routines \
    --triggers \
    ${MYSQL_DATABASE} | gzip > "${BACKUP_DIR}/mysql_${DATE}.sql.gz"

# Redis 备份
echo "Backing up Redis..."
docker-compose exec -T redis redis-cli -a ${REDIS_PASSWORD} BGSAVE
sleep 5
docker cp $(docker-compose ps -q redis):/data/dump.rdb "${BACKUP_DIR}/redis_${DATE}.rdb"

# 上传文件备份
echo "Backing up uploads..."
tar -czf "${BACKUP_DIR}/uploads_${DATE}.tar.gz" ./data/uploads

# 上传到 S3
echo "Uploading to S3..."
aws s3 cp "${BACKUP_DIR}/mysql_${DATE}.sql.gz" "${S3_BUCKET}/mysql/"
aws s3 cp "${BACKUP_DIR}/redis_${DATE}.rdb" "${S3_BUCKET}/redis/"
aws s3 cp "${BACKUP_DIR}/uploads_${DATE}.tar.gz" "${S3_BUCKET}/uploads/"

# 清理旧备份
find ${BACKUP_DIR} -type f -mtime +7 -delete

echo "Backup completed!"
```

### 8.3 恢复脚本

```bash
#!/bin/bash
# scripts/restore.sh

set -e

BACKUP_DATE=$1

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: ./restore.sh <backup_date>"
    echo "Example: ./restore.sh 20240116_020000"
    exit 1
fi

BACKUP_DIR="/backup"
S3_BUCKET="s3://your-bucket/backups"

# 下载备份
echo "Downloading backups..."
aws s3 cp "${S3_BUCKET}/mysql/mysql_${BACKUP_DATE}.sql.gz" "${BACKUP_DIR}/"
aws s3 cp "${S3_BUCKET}/redis/redis_${BACKUP_DATE}.rdb" "${BACKUP_DIR}/"
aws s3 cp "${S3_BUCKET}/uploads/uploads_${BACKUP_DATE}.tar.gz" "${BACKUP_DIR}/"

# 停止服务
echo "Stopping services..."
docker-compose stop api worker beat

# 恢复 MySQL
echo "Restoring MySQL..."
gunzip -c "${BACKUP_DIR}/mysql_${BACKUP_DATE}.sql.gz" | \
    docker-compose exec -T mysql mysql -u${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}

# 恢复 Redis
echo "Restoring Redis..."
docker-compose stop redis
docker cp "${BACKUP_DIR}/redis_${BACKUP_DATE}.rdb" $(docker-compose ps -q redis):/data/dump.rdb
docker-compose start redis

# 恢复文件
echo "Restoring uploads..."
tar -xzf "${BACKUP_DIR}/uploads_${BACKUP_DATE}.tar.gz" -C ./data/

# 启动服务
echo "Starting services..."
docker-compose start api worker beat

echo "Restore completed!"
```

### 8.4 定时任务

```bash
# /etc/cron.d/ai-auto-backup

# 每天凌晨 2 点全量备份
0 2 * * * root /opt/ai-auto/scripts/backup.sh >> /var/log/backup.log 2>&1

# 每小时增量备份
0 * * * * root /opt/ai-auto/scripts/incremental_backup.sh >> /var/log/backup.log 2>&1
```

---

## 9. 故障排查

### 9.1 常见问题

#### 问题: API 无法启动

```bash
# 检查日志
docker-compose logs api

# 检查端口
netstat -tlnp | grep 8000

# 检查数据库连接
docker-compose exec api python -c "from app.db import engine; engine.connect()"
```

#### 问题: 数据库连接失败

```bash
# 检查 MySQL 状态
docker-compose exec mysql mysqladmin -u root -p status

# 检查网络
docker network inspect ai-auto-network

# 测试连接
docker-compose exec api mysql -h mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -e "SELECT 1"
```

#### 问题: Redis 连接失败

```bash
# 检查 Redis 状态
docker-compose exec redis redis-cli -a ${REDIS_PASSWORD} ping

# 检查内存
docker-compose exec redis redis-cli -a ${REDIS_PASSWORD} info memory
```

#### 问题: AI 请求超时

```bash
# 检查 AI 提供商状态
curl -X POST https://api.openai.com/v1/chat/completions \
    -H "Authorization: Bearer ${OPENAI_API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]}'

# 检查网络延迟
ping api.openai.com

# 检查代理配置
curl -v https://api.openai.com
```

### 9.2 日志分析

```bash
# 查看 API 错误日志
docker-compose logs api 2>&1 | grep -i error

# 查看最近 100 行
docker-compose logs --tail 100 api

# 实时日志
docker-compose logs -f api

# 导出日志
docker-compose logs api > api.log
```

### 9.3 性能分析

```bash
# 查看容器资源使用
docker stats

# 查看 MySQL 慢查询
docker-compose exec mysql mysqladmin -u root -p processlist

# 查看 Redis 慢查询
docker-compose exec redis redis-cli -a ${REDIS_PASSWORD} slowlog get 10
```

---

## 10. 升级指南

### 10.1 升级流程

```bash
# 1. 备份数据
./scripts/backup.sh

# 2. 拉取新版本
git pull origin main
docker-compose pull

# 3. 停止服务
docker-compose down

# 4. 执行数据库迁移
docker-compose run --rm api alembic upgrade head

# 5. 启动新版本
docker-compose up -d

# 6. 验证
docker-compose ps
curl http://localhost:8000/api/v1/health

# 7. 如果失败，回滚
./scripts/restore.sh <backup_date>
git checkout <previous_version>
docker-compose up -d
```

### 10.2 版本兼容性

| 版本 | MySQL | Redis | Python | Node.js |
|------|-------|-------|--------|---------|
| 1.0.x | 8.0+ | 7.0+ | 3.11+ | 18+ |

---

## 11. 安全加固

### 11.1 网络安全

```bash
# 防火墙配置
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable

# 只允许内网访问数据库
iptables -A INPUT -p tcp --dport 3306 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 3306 -j DROP
```

### 11.2 密钥管理

```bash
# 使用 Docker Secrets (Swarm 模式)
echo "your-secret" | docker secret create mysql_password -

# 或使用环境变量加密
# 使用 HashiCorp Vault 管理密钥
```

### 11.3 安全检查清单

- [ ] 所有密码使用强密码
- [ ] 数据库只允许内网访问
- [ ] 启用 HTTPS
- [ ] 配置防火墙
- [ ] 定期更新系统和依赖
- [ ] 启用审计日志
- [ ] 配置速率限制
- [ ] 敏感数据加密存储

---

## 附录

### A. 快速命令参考

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 重启
docker-compose restart

# 日志
docker-compose logs -f <service>

# 进入容器
docker-compose exec <service> bash

# 数据库迁移
docker-compose exec api alembic upgrade head

# 备份
./scripts/backup.sh

# 恢复
./scripts/restore.sh <date>
```

### B. 端口列表

| 服务 | 端口 | 说明 |
|------|------|------|
| API | 8000 | REST API |
| Web | 3000 | 前端页面 |
| MySQL | 3306 | 数据库 |
| Redis | 6379 | 缓存 |
| Nginx | 80/443 | 反向代理 |
| Prometheus | 9090 | 监控 |
| Grafana | 3001 | 仪表盘 |

### C. 健康检查端点

| 端点 | 说明 |
|------|------|
| GET /api/v1/health | 健康状态 |
| GET /api/v1/ready | 就绪状态 |
| GET /api/v1/live | 存活状态 |
| GET /metrics | Prometheus 指标 |
