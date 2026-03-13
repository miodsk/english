# NestJS Backend Server

**Parent:** `backend/`

## OVERVIEW

NestJS REST API + WebSocket server for English learning platform. Handles user auth, courses, payments, word books, and learning progress. Uses Prisma ORM with PostgreSQL.

## STRUCTURE

```
apps/server/src/           # Main application
├── main.ts                # Entry: global prefix /api, version URI v1
├── app.module.ts          # Root module
├── user/                  # User CRUD + profile
├── auth/                  # JWT auth service
├── course/                # Course catalog
├── pay/                   # WeChat payment integration
├── socket/                # WebSocket gateway
├── learn/                 # Learning progress
├── word-book/             # Word book CRUD
└── digest/                # BullMQ job queue

libs/shared/src/           # Shared library
├── prisma/                # PrismaService (singleton)
├── auth/                  # JwtAuthGuard + @Public() decorator
├── response/              # Unified response wrapper
├── httpfilter/            # Global exception filter
├── minio/                 # MinIO file storage
├── pay/                   # Payment utilities
└── email/                 # Email service
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add new module | `apps/server/src/` - nest g module |
| Modify auth | `libs/shared/src/auth/` + `apps/server/src/auth/` |
| Change response format | `libs/shared/src/response/response.service.ts` |
| Add Prisma model | `prisma/schema.prisma` → npx prisma generate |
| WebSocket handlers | `apps/server/src/socket/socket.gateway.ts` |
| Background jobs | `apps/server/src/digest/` |
| Database seed | `prisma/seed.ts` |

## CONVENTIONS

### Module Pattern
```typescript
// Each module follows NestJS standard
@Module({ imports: [], controllers: [], providers: [] })
export class UserModule {}

// Controllers use constructor injection
@Controller('user')
export class UserController {
  constructor(private readonly userService: UserService) {}
}
```

### Response Format
```typescript
// All endpoints return via ResponseService
{ success: true, message: "...", data: {} }
{ success: false, message: "...", data: null }
```

### Auth Pattern
```typescript
@Public()  // Skip JWT guard for this endpoint
@Post('login')
login() {}

// All other endpoints require JWT by default
```

### Path Aliases
```typescript
import { PrismaService } from '@lib/shared'  // libs/shared
import type { User } from '@en/common/user'   // common package
```

## ANTI-PATTERNS

- **Don't** add code comments unless explicitly requested
- **Don't** forget `@Public()` on auth endpoints
- **Don't** use `any` type without justification (ESLint: off but avoid)
- **Don't** modify `generated/prisma/` files directly - use schema.prisma

## COMMANDS

```bash
pnpm start:dev          # Development server (port 3000)
pnpm build              # Build to dist/
pnpm lint               # ESLint + auto-fix
pnpm test               # Jest unit tests
pnpm test:e2e           # E2E tests
npx prisma studio       # Database GUI
npx prisma migrate dev  # Create migration
```

## NOTES

- **HTTP prefix**: All routes are `/api/v1/{resource}`
- **WebSocket**: No global prefix - use `/socket` namespace directly
- **Prisma**: Models in `libs/shared/src/generated/prisma/models/`
- **Port**: Default 3000
- **JWT**: Secret in `.env`