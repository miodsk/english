# AGENTS.md

AI 编码代理指南 - 本文件为 AI 编码代理提供项目上下文和编码规范。

## 项目概述

这是一个英语学习平台，采用 pnpm monorepo 架构，包含以下子项目：

- **`backend/server`**: NestJS 后端服务 (Node.js + TypeScript)
- **`fronted`**: Vue 3 前端应用 (Vite + TypeScript)
- **`backend/ai`**: Python FastAPI AI 服务
- **`common`**: 共享类型定义
- **`config`**: 共享配置

## 常用命令

### 根目录

```bash
pnpm dev              # 同时启动前端、后端、AI 服务
pnpm dev:fronted      # 仅启动前端
pnpm dev:server       # 仅启动后端
pnpm dev:ai           # 仅启动 AI 服务
```

### 后端 (backend/server)

```bash
cd backend/server
pnpm start:dev        # 开发模式
pnpm build            # 构建
pnpm format           # 代码格式化
pnpm lint             # ESLint 检查并修复
pnpm test             # 运行所有测试
pnpm test -- path/to/test.spec.ts  # 运行单个测试文件
pnpm test:watch       # 测试监听模式
pnpm test:cov         # 测试覆盖率
pnpm test:e2e         # E2E 测试
```

### 前端 (fronted)

```bash
cd fronted
pnpm dev              # 开发模式
pnpm type-check       # 类型检查
pnpm build            # 构建
pnpm format           # 代码格式化
```

### AI 服务 (backend/ai)

```bash
cd backend/ai
uv run uvicorn src.main:app --reload --port 8000  # 开发模式
```

## 项目架构

### 后端架构

```
backend/server/
├── apps/server/src/          # 主应用
│   ├── main.ts               # 入口：全局前缀 /api，版本控制 URI v1
│   ├── app.module.ts         # 根模块
│   ├── user/                 # 用户模块
│   ├── auth/                 # 认证模块
│   ├── course/               # 课程模块
│   ├── pay/                  # 支付模块
│   ├── socket/               # WebSocket 模块
│   └── learn/                # 学习模块
└── libs/shared/src/          # 共享库
    ├── prisma/               # Prisma 服务
    ├── auth/                 # 认证守卫
    ├── httpfilter/           # HTTP 异常过滤器
    └── response/             # 响应服务
```

**重要配置**:
- HTTP 路由格式: `http://localhost:3000/api/v1/{resource}`
- WebSocket 命名空间: `ws://localhost:3000/{namespace}` (不受全局前缀影响)

### 前端架构

```
fronted/src/
├── App.vue                   # 根组件
├── views/                    # 页面视图
│   ├── Home/                 # 首页
│   ├── Chat/                 # AI 聊天模块 (normal/composition/speak/vocabulary)
│   ├── Course/               # 课程模块
│   ├── WordBook/             # 单词本
│   └── Setting/              # 设置
├── components/               # 公共组件
├── layout/                   # 布局组件
└── stores/                   # Pinia 状态管理
```

### AI 服务架构

```
backend/ai/src/
├── main.py                   # FastAPI 入口
├── routers/                  # 路由模块
│   ├── ai/                   # AI 功能
│   │   ├── normal/           # 日常对话
│   │   ├── composition/      # 作文批改
│   │   └── speak/            # 口语练习
│   └── user/                 # 用户管理
└── services/                 # 服务层
```

## 代码风格规范

### TypeScript 规范

**导入顺序**:
```typescript
// 1. Node.js 内置模块
import { Injectable } from '@nestjs/common';
// 2. 第三方库
import { IsString, IsNotEmpty } from 'class-validator';
// 3. 项目内部模块 - 使用别名
import { PrismaService } from '@lib/shared';
import type { User } from '@en/common/user';
```

**类型导入**: 优先使用 `import type` 导入纯类型

### 后端 NestJS 规范

```typescript
@Controller('user')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Public()
  @Post('login')
  login(@Body() loginUser: UserLogin) {
    return this.userService.login(loginUser);
  }
}
```

### 前端 Vue 3 规范

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
</script>
```

### Python 规范

- 使用 `uv` 作为包管理器
- 使用 FastAPI 和 Pydantic 进行数据验证
- 路由放在 `routers/` 目录，服务放在 `services/` 目录

## 格式化配置

**后端 Prettier** (`.prettierrc`):
```json
{ "singleQuote": true, "trailingComma": "all" }
```

**前端 Prettier** (`.prettierrc.json`):
```json
{ "semi": false, "singleQuote": true, "printWidth": 100 }
```

**ESLint 规则** (后端):
- `@typescript-eslint/no-explicit-any`: off
- `@typescript-eslint/no-floating-promises`: warn
- `@typescript-eslint/no-unsafe-argument`: warn

## 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 文件名 | kebab-case | `user.service.ts`, `auth.guard.ts` |
| 类名 | PascalCase | `UserService`, `AuthGuard` |
| 接口/类型 | PascalCase | `UserLogin`, `Token` |
| 变量/函数 | camelCase | `userId`, `getUserInfo` |
| Vue 组件 | PascalCase | `LoginForm.vue` |
| 路由名称 | kebab-case | `chat-normal`, `chat-composition` |

## 错误处理

后端统一返回格式：
```typescript
// 成功
{ success: true, message: "操作成功", data: {} }
// 失败
{ success: false, message: "错误信息", data: null }
```

## 数据库

使用 Prisma ORM，模型位于 `backend/server/libs/shared/src/generated/prisma/models/`

```bash
cd backend/server
npx prisma generate    # 生成客户端
npx prisma migrate dev # 创建迁移
npx prisma studio      # 打开数据库 GUI
```

## 注意事项

1. **不要添加代码注释**，除非用户明确要求
2. **认证接口使用 `@Public()` 装饰器** 跳过 JWT 验证
3. **WebSocket namespace 不受全局前缀影响**，直接使用 `/namespace`
4. **前端使用 Element Plus** 作为 UI 组件库
5. **前端使用 Tailwind CSS 4** 进行样式编写
6. **共享类型放在 `common/` 目录**，通过 `@en/common` 引用