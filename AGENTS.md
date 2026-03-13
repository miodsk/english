# AGENTS.md

**Generated:** 2026-03-13
**Commit:** 7acd27c
**Branch:** main

## OVERVIEW

English learning platform with AI features. pnpm monorepo: NestJS backend, Vue 3 frontend, FastAPI AI service.

## STRUCTURE

```
├── backend/server/   # NestJS REST API + WebSocket (port 3000)
├── backend/ai/       # FastAPI AI service (port 8000) - NOT in pnpm workspace
├── fronted/          # Vue 3 frontend (port 5173)
├── common/           # Shared TypeScript types (@en/common)
├── config/           # Shared configuration
└── insertDB/         # Database seed utility - NOT in pnpm workspace
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| NestJS module | `backend/server/apps/server/src/` |
| Prisma models | `backend/server/prisma/schema.prisma` |
| Vue pages | `fronted/src/views/` |
| AI workflows | `backend/ai/src/routers/ai/` |
| Shared types | `common/` - domain-based subdirs |
| API routes | Backend: `*/{module}/{module}.controller.ts` |

## COMMANDS

```bash
pnpm dev              # Start all services (frontend + backend + AI)
pnpm dev:fronted      # Frontend only
pnpm dev:server       # Backend only
pnpm dev:ai           # AI service only
```

## CONVENTIONS

### Import Aliases
```typescript
import { PrismaService } from '@lib/shared'     // backend/server/libs/shared
import type { User } from '@en/common/user'      // common package
```

### Naming
| Type | Convention | Example |
|------|------------|---------|
| Files | kebab-case | `user.service.ts` |
| Classes | PascalCase | `UserService` |
| Vue components | PascalCase | `LoginForm.vue` |
| Routes | kebab-case | `chat-normal` |

### Response Format (Backend)
```typescript
{ success: true, message: "...", data: {} }
{ success: false, message: "...", data: null }
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