# English Learning Platform

AI 驱动的英语学习平台，支持日常对话、作文批改、口语练习和单词学习。

## 技术栈

| 服务 | 技术栈 | 端口 |
|------|--------|------|
| 前端 | Vue 3 + Vite + Element Plus + Tailwind CSS 4 | 5173 |
| 后端 | NestJS + Prisma + PostgreSQL | 3000 |
| AI 服务 | FastAPI + LangChain + LangGraph | 8000 |

## 环境要求

- Node.js >= 18
- pnpm >= 8
- Python >= 3.12
- uv (Python 包管理器)
- PostgreSQL
- Redis
- MinIO (文件存储)
- Milvus (向量数据库，用于 AI 功能)

## 快速开始

### 1. 安装依赖

```bash
# 安装 Node.js 依赖
pnpm install

# 安装 Python 依赖
cd backend/ai && uv sync && cd ../..
```

### 2. 配置环境变量

**后端配置** (`backend/server/.env`)：

```env
# 数据库
DATABASE_URL="postgresql://postgres:password@localhost:5432/english"

# JWT
JWT_SECRET_KEY="your-jwt-secret"

# MinIO (文件存储)
MINIO_ENDPOINT="localhost"
MINIO_PORT=9000
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin"
MINIO_BUCKET="english"
MINIO_USE_SSL=false

# 支付宝沙箱 (可选)
ALIPAY_APP_ID=""
ALIPAY_GATEWAY="https://openapi-sandbox.dl.alipaydev.com/gateway.do"
ALIPAY_PUBLIC_KEY=""
ALIPAY_PRIVATE_KEY=""
ALIPAY_NOTIFY_URL=""

# 邮件服务 (可选)
EMAIL_HOST="smtp.qq.com"
EMAIL_PORT=465
EMAIL_USER="your-email@qq.com"
EMAIL_PASSWORD="your-smtp-password"
EMAIL_FROM="your-email@qq.com"
EMAIL_USE_SSL=1

# Redis
REDIS_HOST="localhost"
REDIS_PORT=6379

# TTS 语音
SAKIKO_VOICE_ID="cosyvoice-v3.5-plus-sakiko-xxx"
```

**AI 服务配置** (`backend/ai/.env`)：

```env
# 数据库
DATABASE_URL="postgresql://postgres:password@localhost:5432/english"

# LLM 提供商 (至少配置一个)
DASHSCOPE_API_KEY=""      # 通义千问
DEEPSEEK_API_KEY=""       # DeepSeek
ZHIPU_API_KEY=""          # 智谱 AI

# 向量数据库
MILVUS_URI="http://localhost:19530"
MILVUS_DB_NAME="default"

# MinIO
MINIO_ENDPOINT="localhost"
MINIO_PORT=9000
MINIO_ACCESS_KEY="minioadmin"
MINIO_SECRET_KEY="minioadmin"
MINIO_BUCKET="english"

# LangSmith (可选，用于追踪)
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY=""
LANGSMITH_PROJECT="english"

# Tavily (AI 搜索工具)
TAVILY_API_KEY=""

# TTS 语音
SAKIKO_VOICE_ID="cosyvoice-v3.5-plus-sakiko-xxx"
JWT_SECRET_KEY="your-jwt-secret"
```

**前端配置** (`fronted/.env`)：

```env
PORT=3000
HOST=localhost
VITE_PORT=3000
VITE_DEV=true
```

### 3. 初始化数据库

```bash
cd backend/server

# 生成 Prisma 客户端
npx prisma generate

# 运行数据库迁移
npx prisma migrate dev

# (可选) 填充种子数据
npx prisma db seed
```

### 4. 启动服务

**方式一：同时启动所有服务**

```bash
pnpm dev
```

**方式二：分别启动各服务**

```bash
# 终端 1 - 前端
pnpm dev:fronted

# 终端 2 - 后端
pnpm dev:server

# 终端 3 - AI 服务
pnpm dev:ai
```

### 5. 访问应用

- 前端：http://localhost:5173
- 后端 API：http://localhost:3000/api/v1
- AI 服务：http://localhost:8000
- API 文档：http://localhost:8000/docs (FastAPI Swagger)

## 外部服务

| 服务 | 用途 | 默认端口 |
|------|------|----------|
| PostgreSQL | 主数据库 | 5432 |
| Redis | 缓存/队列 | 6379 |
| MinIO | 文件存储 | 9000 |
| Milvus | 向量数据库 | 19530 |

## 项目结构

```
├── backend/
│   ├── server/          # NestJS 后端服务
│   │   ├── apps/server/src/    # 业务模块
│   │   ├── libs/shared/        # 共享库
│   │   └── prisma/             # 数据库模型
│   └── ai/              # FastAPI AI 服务
│       └── src/
│           ├── routers/ai/     # AI 功能模块
│           │   ├── normal/      # 日常对话
│           │   ├── composition/ # 作文批改
│           │   └── speak/       # 口语练习
│           └── services/        # LLM/TTS 服务
├── fronted/             # Vue 3 前端
│   └── src/
│       ├── views/              # 页面
│       ├── components/         # 组件
│       ├── apis/               # API 封装
│       └── hooks/              # 组合式函数
├── common/              # 共享 TypeScript 类型
└── config/              # 共享配置
```

## 常用命令

```bash
# 后端
cd backend/server
pnpm start:dev          # 开发模式
pnpm build              # 构建
pnpm lint               # 代码检查
pnpm test               # 测试
npx prisma studio       # 数据库 GUI

# 前端
cd fronted
pnpm dev                # 开发模式
pnpm build              # 构建
pnpm type-check         # 类型检查

# AI 服务
cd backend/ai
uv run uvicorn src.main:app --reload  # 开发模式
```

## 功能特性

- **日常对话**：AI 驱动的英语日常对话练习
- **作文批改**：IELTS 作文智能评分与修改建议
- **口语练习**：语音识别 + TTS 语音合成
- **单词本**：SM-2 间隔重复记忆算法
- **课程学习**：在线课程与学习进度跟踪

## License

MIT