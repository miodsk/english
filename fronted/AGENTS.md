# Vue 3 Frontend

**Parent:** Root

## OVERVIEW

Vue 3 + Vite frontend for English learning platform. Features AI chat (composition/speak/normal), course learning, word book with SM-2 spaced repetition. Uses Element Plus + Tailwind CSS 4.

## STRUCTURE

```
src/
├── main.ts                # App entry
├── App.vue                # Root component
├── views/                 # Page components
│   ├── Home/              # Landing with 3D model
│   ├── Chat/              # AI chat modules
│   │   ├── normal/        # Daily conversation
│   │   ├── composition/   # Essay grading
│   │   ├── speak/         # Oral practice
│   │   └── vocabulary/    # Word learning
│   ├── Course/            # Course catalog + learning
│   ├── WordBook/          # Word book management
│   └── Setting/           # User settings
├── components/            # Shared components
│   ├── Login/             # Auth forms
│   ├── Search/            # Search component
│   └── Wave/              # Audio waveform
├── layout/                # Page layouts
│   ├── Sidebar/           # Navigation
│   ├── Header/            # Top bar
│   └── Content/           # Main content area
├── apis/                  # API modules by domain
├── hooks/                 # Composables
├── stores/                # Pinia state
├── router/                # Vue Router
└── directives/            # Custom directives
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add new page | `src/views/` + `src/router/` |
| Add API call | `src/apis/` - domain-based modules |
| Modify auth | `src/components/Login/` + `src/hooks/useLogin.ts` |
| Socket connection | `src/hooks/useSocket.ts` |
| Audio handling | `src/hooks/useAudio.ts` + `src/components/Wave/` |
| State management | `src/stores/` - Pinia stores |
| Styling | Tailwind CSS 4 classes in components |

## CONVENTIONS

### Component Style
```vue
<script setup lang="ts">
import { ref } from 'vue'
const loading = ref(false)
</script>

<template>
  <el-button :loading="loading">Submit</el-button>
</template>
```

### API Pattern
```typescript
// src/apis/user/index.ts
export const getUserInfo = () => request.get<User>('/user/info')
```

### Router Naming
- Route names: `kebab-case` (e.g., `chat-normal`, `chat-composition`)
- Component files: `PascalCase.vue`

### Styling
- Use Tailwind CSS 4 utility classes
- Element Plus components for UI elements
- Custom styles in `<style scoped>` when needed

## ANTI-PATTERNS

- **Don't** add code comments unless requested
- **Don't** use Options API - always use `<script setup>`
- **Don't** forget to handle loading/error states
- **Don't** hardcode API URLs - use `src/apis/`

## COMMANDS

```bash
pnpm dev           # Development server (port 5173)
pnpm build         # Build to dist/
pnpm preview       # Preview production build
pnpm type-check    # TypeScript check
pnpm format        # Prettier format
```

## NOTES

- **UI Library**: Element Plus
- **CSS**: Tailwind CSS 4
- **State**: Pinia stores in `src/stores/`
- **Auth**: JWT stored in localStorage, managed by `useLogin` hook
- **API Base**: Configured in `src/apis/index.ts`
- **WebSocket**: Connected via `useSocket` hook