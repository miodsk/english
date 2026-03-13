# 英语学习平台架构设计文档

## TL;DR

> **核心目标**: 构建一个综合英语学习平台，支持单词智能推送、AI 口语对话、查词/例句生成、作文批改四大核心功能。
>
> **架构模式**: 前后端分离 + 微服务架构（NestJS 网关 + FastAPI AI 服务）
>
> **技术选型**: Vue3 + NestJS + FastAPI + PostgreSQL + Redis + Milvus + 国产大模型

---

## 1. 系统概览

### 1.1 架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              用户终端                                    │
│                        (Web Browser / PWA)                              │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTPS
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           Nginx (反向代理)                               │
│                    - SSL 终止                                           │
│                    - 静态资源服务                                       │
│                    - 负载均衡（可选）                                   │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Vue 3 SPA   │      │  NestJS Gateway │      │  FastAPI AI     │
│   (前端)      │◄────►│   (API 网关)    │◄────►│   (AI 服务)     │
│   Port: 80    │      │   Port: 3000    │      │   Port: 8000    │
└───────────────┘      └────────┬────────┘      └────────┬────────┘
                                │                        │
        ┌───────────────────────┼────────────────────────┤
        │                       │                        │
        ▼                       ▼                        ▼
┌───────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  PostgreSQL   │      │     Redis       │      │     Milvus      │
│  (主数据库)   │      │  (缓存/会话)    │      │  (向量数据库)   │
│  Port: 5432   │      │   Port: 6379    │      │   Port: 19530   │
└───────────────┘      └─────────────────┘      └─────────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │   外部 AI 服务      │
                    │ - 通义千问 API      │
                    │ - 阿里云语音服务    │
                    └─────────────────────┘
```

### 1.2 服务职责划分

| 服务 | 职责 | 技术栈 | 端口 |
|------|------|--------|------|
| **Vue 3 SPA** | 用户界面、交互逻辑 | Vue 3 + Vite + TypeScript | 80 |
| **NestJS Gateway** | 用户认证、业务逻辑、API 聚合 | NestJS + TypeORM | 3000 |
| **FastAPI AI** | AI 功能、LangChain 编排 | FastAPI + LangChain | 8000 |
| **PostgreSQL** | 用户数据、词典、学习记录 | PostgreSQL 15 | 5432 |
| **Redis** | 会话缓存、热点数据、消息队列 | Redis 7 | 6379 |
| **Milvus** | 向量存储、语义检索 | Milvus 2.4 | 19530 |

---

## 2. 服务架构详解

### 2.1 前端层 (Vue 3 SPA)

```
frontend/
├── src/
│   ├── api/                 # API 请求封装
│   │   ├── auth.ts          # 认证相关
│   │   ├── vocabulary.ts    # 词汇相关
│   │   └── ai.ts            # AI 功能
│   ├── components/          # 公共组件
│   │   ├── WordCard.vue     # 单词卡片
│   │   ├── ChatPanel.vue    # 对话面板
│   │   └── VoiceRecorder.vue # 语音录制
│   ├── views/               # 页面视图
│   │   ├── Home.vue         # 首页
│   │   ├── Vocabulary.vue   # 词汇学习
│   │   ├── Chat.vue         # AI 对话
│   │   └── Essay.vue        # 作文批改
│   ├── stores/              # Pinia 状态管理
│   │   ├── user.ts
│   │   ├── vocabulary.ts
│   │   └── chat.ts
│   ├── router/              # 路由配置
│   └── utils/               # 工具函数
├── public/
└── package.json
```

**关键设计点**:
- 使用 Pinia 管理状态，支持持久化到 localStorage
- WebSocket 客户端用于实时语音对话
- 响应式设计，支持移动端访问

### 2.2 NestJS 网关层

```
gateway/
├── src/
│   ├── modules/
│   │   ├── auth/            # 认证模块
│   │   │   ├── auth.controller.ts
│   │   │   ├── auth.service.ts
│   │   │   ├── jwt.strategy.ts
│   │   │   └── dto/
│   │   ├── user/            # 用户模块
│   │   │   ├── user.entity.ts
│   │   │   ├── user.controller.ts
│   │   │   └── user.service.ts
│   │   ├── vocabulary/      # 词汇模块
│   │   │   ├── word.entity.ts
│   │   │   ├── word.controller.ts
│   │   │   └── word.service.ts
│   │   ├── learning/        # 学习记录模块
│   │   │   ├── record.entity.ts
│   │   │   └── memory-curve.service.ts  # 艾宾浩斯记忆曲线
│   │   └── ai/              # AI 服务代理
│   │       ├── ai.controller.ts
│   │       └── ai.service.ts  # HTTP 客户端调用 FastAPI
│   ├── common/
│   │   ├── guards/          # 守卫
│   │   ├── interceptors/    # 拦截器
│   │   ├── filters/         # 异常过滤器
│   │   └── decorators/      # 自定义装饰器
│   ├── config/              # 配置
│   └── main.ts
├── test/
└── package.json
```

**关键设计点**:
- JWT 认证，Token 存储在 Redis
- TypeORM 管理数据库
- HTTP 客户端（Axios）调用 AI 服务
- 记忆曲线算法（SM-2 或自定义）

### 2.3 FastAPI AI 服务层

```
ai-service/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py          # AI 对话
│   │   │   ├── vocabulary.py    # 词汇处理
│   │   │   ├── essay.py         # 作文批改
│   │   │   └── voice.py         # 语音处理
│   │   └── dependencies.py
│   ├── core/
│   │   ├── config.py            # 配置管理
│   │   ├── security.py          # 安全相关
│   │   └── logging.py           # 日志
│   ├── services/
│   │   ├── llm/
│   │   │   ├── base.py          # LLM 基类
│   │   │   ├── tongyi.py        # 通义千问
│   │   │   ├── wenxin.py        # 文心一言
│   │   │   └── deepseek.py      # DeepSeek
│   │   ├── chains/
│   │   │   ├── chat_chain.py    # 对话链
│   │   │   ├── word_chain.py    # 词汇链
│   │   │   └── essay_chain.py   # 作文链
│   │   ├── retrievers/
│   │   │   └── milvus_retriever.py  # Milvus 检索
│   │   └── voice/
│   │       ├── asr.py           # 语音识别
│   │       └── tts.py           # 语音合成
│   ├── models/
│   │   ├── schemas.py           # Pydantic 模型
│   │   └── prompts/             # Prompt 模板
│   └── main.py
├── requirements.txt
└── Dockerfile
```

**关键设计点**:
- LangChain 编排 AI 流程
- 多 LLM 适配器模式，支持切换不同模型
- WebSocket 端点用于流式对话
- Milvus 集成用于语义检索

---

## 3. 数据架构

### 3.1 PostgreSQL 数据模型

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(100),
    avatar_url VARCHAR(500),
    level INTEGER DEFAULT 1,
    experience INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 词典表
CREATE TABLE words (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word VARCHAR(100) UNIQUE NOT NULL,
    phonetic VARCHAR(100),
    meaning TEXT NOT NULL,
    part_of_speech VARCHAR(50),
    difficulty_level INTEGER DEFAULT 1,  -- CEFR: 1-6
    category VARCHAR(50),
    frequency INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 例句表
CREATE TABLE examples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word_id UUID REFERENCES words(id) ON DELETE CASCADE,
    sentence TEXT NOT NULL,
    translation TEXT,
    source VARCHAR(100),
    difficulty INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_examples_word_id ON examples(word_id);
CREATE INDEX idx_examples_difficulty ON examples(difficulty);

-- 学习记录表
CREATE TABLE learning_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    word_id UUID REFERENCES words(id),
    status VARCHAR(20) DEFAULT 'new',  -- new, learning, mastered
    ease_factor FLOAT DEFAULT 2.5,     -- SM-2 算法参数
    interval INTEGER DEFAULT 0,         -- 复习间隔(天)
    repetitions INTEGER DEFAULT 0,      -- 连续正确次数
    next_review_at TIMESTAMP,
    last_review_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, word_id)
);

-- 作文表
CREATE TABLE essays (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    content TEXT NOT NULL,
    feedback TEXT,                      -- AI 批改结果（JSON格式）
    score FLOAT,                        -- 总分
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_essays_user_id ON essays(user_id);
CREATE INDEX idx_essays_status ON essays(status);
CREATE INDEX idx_essays_created_at ON essays(created_at);
```

### 3.2 Redis 数据结构

```
# 用户会话
session:{user_id} -> {token, expires_at}

# 单词缓存（热点单词）
word:detail:{word} -> JSON(单词详情)

# 用户学习进度缓存
user:progress:{user_id} -> {daily_count, total_count}

# AI 响应缓存
ai:cache:{query_hash} -> JSON(响应内容)

# 今日待复习单词队列
review:queue:{user_id}:today -> LIST(word_ids)
```

### 3.3 Milvus 向量 Schema

```python
from pymilvus import CollectionSchema, FieldSchema, DataType

# 词汇向量集合
word_collection_schema = CollectionSchema(
    fields=[
        FieldSchema(name="word_id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
        FieldSchema(name="word", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="meaning", dtype=DataType.VARCHAR, max_length=2000),
        FieldSchema(name="difficulty", dtype=DataType.INT32),
        FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="word_embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
        FieldSchema(name="meaning_embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
    ],
    description="英语词汇向量集合"
)

# 例句向量集合
sentence_collection_schema = CollectionSchema(
    fields=[
        FieldSchema(name="sentence_id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
        FieldSchema(name="sentence", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="translation", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="word_ids", dtype=DataType.ARRAY, element_type=DataType.VARCHAR, max_capacity=50),
        FieldSchema(name="difficulty", dtype=DataType.INT32),
        FieldSchema(name="sentence_embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
    ],
    description="例句向量集合"
)
```

### 3.4 跨服务 ORM 同步策略

由于 NestJS (TypeORM) 和 FastAPI (SQLAlchemy) 需要访问同一个 PostgreSQL 数据库，采用以下策略确保数据模型一致性：

#### 数据主导原则

**NestJS 作为数据主控方，FastAPI 只读或有限写入**

```
┌─────────────────────────────────────────────────────────────┐
│                      数据流向                                │
│                                                             │
│   用户请求 ──► NestJS Gateway ──► PostgreSQL               │
│                    │                   ▲                   │
│                    │                   │                   │
│                    ▼                   │                   │
│              FastAPI AI ───────────────┘                   │
│              (只读/有限写入)                                │
└─────────────────────────────────────────────────────────────┘
```

#### 职责划分

| 服务 | 数据操作权限 | 职责 |
|------|-------------|------|
| **NestJS** | 全权管理 | 用户、词典、学习记录、作文存储；所有写操作；数据库迁移 |
| **FastAPI** | 只读 + AI 处理 | 只读用户数据、词汇数据；语义检索 (Milvus)；AI 生成结果返回给 NestJS 存储 |

#### NestJS Entity 定义（主）

```typescript
// gateway/src/modules/user/user.entity.ts
import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn } from 'typeorm';

@Entity('users')
export class User {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true })
  email: string;

  @Column({ name: 'password_hash' })
  passwordHash: string;

  @Column({ nullable: true })
  nickname: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;
}
```

#### FastAPI Model 定义（从）

```python
# ai-service/app/models/user.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import uuid

class User(Base):
    """映射已存在的 users 表，不用于创建表"""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False)
```

#### 数据库迁移管理

```bash
# NestJS 独占迁移权限
cd gateway
npm run migration:generate -- -n InitialSchema
npm run migration:run

# FastAPI 不执行迁移，只映射现有表
# 使用 sqlacodegen 可从数据库生成模型（可选）
sqlacodegen postgresql://postgres:password@localhost:5432/english_learning > models.py
```

#### FastAPI 数据访问示例

```python
# ai-service/app/services/vocabulary_service.py
from sqlalchemy.orm import Session
from app.models.word import Word

class VocabularyService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_word_by_id(self, word_id: str) -> Word | None:
        """只读查询"""
        return self.db.query(Word).filter(Word.id == word_id).first()
    
    async def get_user_learning_words(self, user_id: str) -> list[Word]:
        """获取用户学习中的单词（只读）"""
        return self.db.query(Word).join(LearningRecord).filter(
            LearningRecord.user_id == user_id,
            LearningRecord.status == 'learning'
        ).all()
```

#### 数据一致性保障

1. **Schema 单一来源**: 所有表结构变更必须通过 NestJS 迁移
2. **类型同步**: FastAPI 模型字段名使用 `snake_case`，与数据库列名一致
3. **只读连接**: FastAPI 可使用只读数据库用户，防止意外写入
4. **API 隔离**: 复杂写入操作通过 NestJS API 完成，FastAPI 专注 AI 逻辑


## 4. API 设计

### 4.1 REST API 概览

#### 认证模块
```
POST   /api/auth/register      # 注册
POST   /api/auth/login         # 登录
POST   /api/auth/logout        # 登出
POST   /api/auth/refresh       # 刷新 Token
GET    /api/auth/profile       # 获取用户信息
```

#### 词汇模块
```
GET    /api/vocabulary/words           # 获取单词列表（分页、筛选）
GET    /api/vocabulary/words/:id       # 获取单词详情
GET    /api/vocabulary/search          # 搜索单词
GET    /api/vocabulary/today           # 今日学习单词
POST   /api/vocabulary/learn           # 标记学习进度
GET    /api/vocabulary/review          # 获取待复习单词
POST   /api/vocabulary/review/submit   # 提交复习结果
```

#### AI 模块（代理到 FastAPI）
```
POST   /api/ai/chat            # AI 对话（普通）
WebSocket /api/ai/chat/stream  # AI 对话（流式）
POST   /api/ai/voice/asr       # 语音识别
POST   /api/ai/voice/tts       # 语音合成
POST   /api/ai/essay/submit    # 提交作文批改
GET    /api/ai/essay/:id       # 获取批改结果
```

### 4.2 服务间通信

#### NestJS → FastAPI (HTTP)

```typescript
// NestJS AI Service
@Injectable()
export class AIService {
  private readonly aiServiceUrl = process.env.AI_SERVICE_URL;

  async chat(message: string, userId: string): Promise<ChatResponse> {
    const response = await this.httpService.post(
      `${this.aiServiceUrl}/api/chat`,
      { message, user_id: userId },
      {
        headers: {
          'X-Internal-Request': 'true',
          'X-User-Id': userId,
        },
        timeout: 30000,
      }
    ).toPromise();
    
    return response.data;
  }
}
```

#### WebSocket 流式对话

```typescript
// NestJS WebSocket Gateway
@WebSocketGateway({ path: '/ws/chat' })
export class ChatGateway implements OnGatewayConnection {
  @WebSocketServer()
  server: Server;

  async handleConnection(client: Socket) {
    // 验证 JWT Token
    const token = client.handshake.auth.token;
    const user = await this.authService.verifyToken(token);
    client.data.user = user;
  }

  @SubscribeMessage('chat')
  async handleMessage(
    @MessageBody() data: { message: string },
    @ConnectedSocket() client: Socket
  ) {
    // 调用 FastAPI 流式接口
    const response = await this.aiService.chatStream(
      data.message,
      client.data.user.id
    );
    
    // 流式返回给客户端
    for await (const chunk of response) {
      client.emit('chat:chunk', chunk);
    }
    client.emit('chat:done');
  }
}
```

---

## 5. AI 功能实现方案

### 5.1 单词智能推送（记忆曲线）

**算法**: 基于 SM-2 算法的改良版本

```python
# FastAPI - 记忆曲线服务
class MemoryCurveService:
    def calculate_next_review(
        self,
        quality: int,  # 0-5, 用户回答质量
        current_ease: float,
        current_interval: int,
        repetitions: int
    ) -> dict:
        """
        SM-2 算法核心逻辑
        quality: 0-5 (完全忘记 - 完美回答)
        返回: {ease_factor, interval, repetitions, next_review_date}
        """
        if quality >= 3:
            # 回答正确
            if repetitions == 0:
                interval = 1
            elif repetitions == 1:
                interval = 6
            else:
                interval = round(current_interval * current_ease)
            repetitions += 1
        else:
            # 回答错误
            repetitions = 0
            interval = 1
        
        # 更新 ease factor
        new_ease = current_ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ease = max(1.3, new_ease)
        
        return {
            'ease_factor': new_ease,
            'interval': interval,
            'repetitions': repetitions,
            'next_review_at': datetime.now() + timedelta(days=interval)
        }
```

### 5.2 AI 口语对话

**流程**:
```
用户语音 → ASR(阿里云) → 文本 → LLM(通义千问) → 文本 → TTS(阿里云) → 语音
```

```python
# FastAPI - 对话链
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

class ChatChain:
    def __init__(self, llm):
        self.llm = llm
        self.memory = ConversationBufferMemory(return_messages=True)
        self.chain = ConversationChain(
            llm=llm,
            memory=self.memory,
            prompt=self._build_prompt()
        )
    
    def _build_prompt(self):
        return PromptTemplate.from_template(
            """你是一个专业的英语口语陪练老师。
            请用简单、地道的英语回复学生。
            如果学生有语法错误，请温和地纠正。
            
            对话历史:
            {history}
            
            学生: {input}
            老师:"""
        )
    
    async def chat(self, message: str) -> str:
        return await self.chain.arun(input=message)
```

### 5.3 查词/例句生成

**流程**:
1. Milvus 语义检索相似单词/例句
2. LLM 生成个性化例句

```python
# FastAPI - 词汇服务
class VocabularyService:
    def __init__(self, milvus_store, llm):
        self.milvus = milvus_store
        self.llm = llm
    
    async def lookup_word(self, word: str) -> dict:
        # 1. 从 Milvus 检索相似单词
        similar_words = await self.milvus.similarity_search(
            query=word,
            k=5
        )
        
        # 2. LLM 生成例句
        examples = await self._generate_examples(word)
        
        return {
            'word': word,
            'similar_words': similar_words,
            'generated_examples': examples
        }
    
    async def _generate_examples(self, word: str) -> list[str]:
        prompt = f"请用'{word}'生成3个不同场景的英语例句，并附带中文翻译。"
        response = await self.llm.agenerate([prompt])
        return self._parse_examples(response)
```

### 5.4 作文批改

**流程**: 异步处理（用户提交后，后台处理，通知结果）

```python
# FastAPI - 作文批改链
class EssayGradingChain:
    def __init__(self, llm):
        self.llm = llm
        self.prompt = PromptTemplate.from_template(
            """请批改以下英语作文，从以下维度评分(1-10分)：
            1. 语法正确性
            2. 词汇丰富度
            3. 句式多样性
            4. 内容连贯性
            5. 整体表达
            
            作文:
            {essay}
            
            请以JSON格式返回：
            {{
                "scores": {{"grammar": X, "vocabulary": X, "variety": X, "coherence": X, "overall": X}},
                "total_score": X,
                "corrections": ["具体错误和修改建议"],
                "suggestions": ["整体改进建议"]
            }}"""
        )
    
    async def grade(self, essay: str) -> dict:
        response = await self.llm.agenerate([self.prompt.format(essay=essay)])
        return json.loads(response)
```

---

## 6. 部署架构

### 6.1 Docker Compose 配置

```yaml
version: '3.8'

services:
  # 前端
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - gateway
    networks:
      - frontend

  # NestJS 网关
  gateway:
    build:
      context: ./gateway
      dockerfile: Dockerfile
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/english_learning
      - REDIS_URL=redis://redis:6379
      - AI_SERVICE_URL=http://ai-service:8000
      - JWT_SECRET=${JWT_SECRET}
    ports:
      - "3000:3000"
    depends_on:
      - postgres
      - redis
    networks:
      - frontend
      - backend
    restart: unless-stopped

  # FastAPI AI 服务
  ai-service:
    build:
      context: ./ai-service
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/english_learning
      - MILVUS_HOST=milvus
      - MILVUS_PORT=19530
      - TONGYI_API_KEY=${TONGYI_API_KEY}
      - ALIYUN_ASR_APP_KEY=${ALIYUN_ASR_APP_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - milvus
    networks:
      - backend
    restart: unless-stopped

  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=english_learning
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - backend
    restart: unless-stopped

  # Redis
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    networks:
      - backend
    restart: unless-stopped

  # Milvus Standalone
  milvus:
    image: milvusdb/milvus:v2.4-latest
    command: ["milvus", "run", "standalone"]
    environment:
      - ETCD_USE_EMBED=true
      - COMMON_STORAGETYPE=local
    volumes:
      - milvus-data:/var/lib/milvus
    ports:
      - "19530:19530"
    networks:
      - backend
    restart: unless-stopped

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge

volumes:
  postgres-data:
  redis-data:
  milvus-data:
```

### 6.2 环境变量配置

```bash
# .env
# 数据库
DATABASE_URL=postgresql://postgres:password@postgres:5432/english_learning

# Redis
REDIS_URL=redis://redis:6379

# JWT
JWT_SECRET=your-super-secret-key-change-in-production
JWT_EXPIRES_IN=7d

# AI 服务
AI_SERVICE_URL=http://ai-service:8000

# 通义千问
TONGYI_API_KEY=sk-xxx

# 阿里云语音服务
ALIYUN_ASR_APP_KEY=xxx
ALIYUN_ACCESS_KEY_ID=xxx
ALIYUN_ACCESS_KEY_SECRET=xxx

# Milvus
MILVUS_HOST=milvus
MILVUS_PORT=19530
```

---

## 7. 开发路线图

### Phase 1: 基础架构（2周）
- [ ] 项目初始化（前端 + NestJS + FastAPI）
- [ ] Docker Compose 配置
- [ ] 数据库 Schema 设计和迁移
- [ ] JWT 认证流程

### Phase 2: 核心功能（3周）
- [ ] 词典模块（CRUD + 搜索）
- [ ] 单词学习模块
- [ ] 记忆曲线算法
- [ ] Milvus 集成

### Phase 3: AI 功能（3周）
- [ ] 通义千问集成
- [ ] 对话功能（文本）
- [ ] 作文批改
- [ ] 词汇例句生成

### Phase 4: 语音功能（2周）
- [ ] 阿里云 ASR/TTS 集成
- [ ] 语音对话功能
- [ ] WebSocket 流式通信

### Phase 5: 优化和部署（1周）
- [ ] 性能优化
- [ ] 错误处理
- [ ] 日志和监控
- [ ] 生产部署

---

## 8. 安全考虑

### 8.1 认证授权
- JWT Token 认证，存储在 Redis
- Token 有效期 7 天，支持刷新
- 敏感操作需要二次验证

### 8.2 API 安全
- 所有 API 需要 HTTPS
- Rate Limiting 防止滥用
- CORS 配置白名单

### 8.3 数据安全
- 密码使用 bcrypt 加密
- 敏感配置使用环境变量
- 数据库定期备份

### 8.4 AI 服务安全
- 内部服务间通信使用验证 Token
- LLM 输出过滤敏感内容
- API Key 不暴露给前端

---

## 9. 可扩展性路径

当用户规模增长时，可按以下路径扩展：

1. **10-100 用户**: 单机部署足够，优化缓存策略
2. **100-1000 用户**: 
   - 增加 Nginx 负载均衡
   - PostgreSQL 主从复制
   - Redis 哨兵模式
3. **1000+ 用户**:
   - Kubernetes 部署
   - 数据库分库分表
   - 消息队列解耦异步任务
   - CDN 加速静态资源

---

## 成功标准

- [ ] 用户可以注册、登录
- [ ] 用户可以浏览、搜索单词
- [ ] 用户可以进行单词学习，系统根据记忆曲线推送复习
- [ ] 用户可以与 AI 进行英语对话
- [ ] 用户可以提交作文并获取批改结果
- [ ] 所有服务可通过 Docker Compose 一键启动