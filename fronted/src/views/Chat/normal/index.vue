<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getNormalHistoryDetailApi, listNormalHistoryApi } from '@/apis/normal'
import type { NormalHistoryMessage, NormalHistoryThread, NormalMode } from '@en/common/chat/normal'

interface NormalWSChunk {
  id: number
  text: string
  is_end: boolean
  error?: string
  thread_id?: string
  meta?: {
    mode?: NormalMode
    search_context?: string
    thread_id?: string
  }
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

const userStore = useUserStore()
const userId = computed(() => userStore.getUser?.id || 'fronted-demo-user')

const mode = ref<NormalMode>('daily')
const input = ref('')
const sending = ref(false)
const wsReady = ref(false)

const options = reactive({
  enableSearch: false,
  searchQueriesText: '',
})

const sessionId = ref(localStorage.getItem('normal_session_id') || crypto.randomUUID())
if (!localStorage.getItem('normal_session_id')) {
  localStorage.setItem('normal_session_id', sessionId.value)
}
const threadId = ref<string>(crypto.randomUUID())

const messages = ref<ChatMessage[]>([])
const searchContext = ref('')

const historyThreads = ref<NormalHistoryThread[]>([])
const historyMessages = ref<NormalHistoryMessage[]>([])
const historyLoading = ref(false)

let socket: WebSocket | null = null
let isConnecting = false

const parseSearchQueries = (): string[] | undefined => {
  const raw = options.searchQueriesText.trim()
  if (!raw) return undefined
  const arr = raw
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
  return arr.length ? arr : undefined
}

const scrollToBottom = async () => {
  await nextTick()
  const container = document.querySelector('.normal-chat-window')
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

const refreshHistory = async () => {
  historyLoading.value = true
  try {
    const data = await listNormalHistoryApi(userId.value)
    historyThreads.value = data.threads
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '加载日常对话历史失败')
  } finally {
    historyLoading.value = false
  }
}

const openHistoryThread = async (id: string) => {
  threadId.value = id
  try {
    const detail = await getNormalHistoryDetailApi(id, userId.value)
    mode.value = detail.mode
    historyMessages.value = detail.messages
    messages.value = detail.messages.map((item) => ({
      role: item.role,
      content: item.content,
    }))
    await scrollToBottom()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '加载线程详情失败')
  }
}

const connectWS = () => {
  if (isConnecting || (socket && socket.readyState === WebSocket.OPEN)) return
  isConnecting = true

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  socket = new WebSocket(`${protocol}//${window.location.host}/api/ai/normal/ws`)

  socket.onopen = () => {
    isConnecting = false
    wsReady.value = true
  }

  socket.onmessage = async (event) => {
    const data: NormalWSChunk = JSON.parse(event.data)

    if (data.meta?.search_context !== undefined) {
      searchContext.value = data.meta.search_context || ''
    }
    if (data.meta?.thread_id) {
      threadId.value = data.meta.thread_id
    }

    if (data.text) {
      const last = messages.value[messages.value.length - 1]
      if (last && last.role === 'assistant') {
        last.content += data.text
      }
      await scrollToBottom()
    }

    if (data.is_end) {
      sending.value = false
      if (data.error) {
        ElMessage.error(data.error)
      }
      if (data.thread_id) {
        threadId.value = data.thread_id
      }
      await refreshHistory()
    }
  }

  socket.onerror = () => {
    isConnecting = false
    wsReady.value = false
    sending.value = false
    ElMessage.error('normal ws 连接错误')
  }

  socket.onclose = () => {
    isConnecting = false
    wsReady.value = false
    sending.value = false
  }
}

const sendMessage = () => {
  const content = input.value.trim()
  if (!content) {
    ElMessage.warning('请输入消息')
    return
  }
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    ElMessage.warning('WS 未连接，请稍后重试')
    return
  }

  messages.value.push({ role: 'user', content })
  messages.value.push({ role: 'assistant', content: '' })
  sending.value = true
  searchContext.value = ''

  socket.send(
    JSON.stringify({
      message: content,
      mode: mode.value,
      enable_search: options.enableSearch,
      search_queries: parseSearchQueries(),
      user_id: userId.value,
      session_id: sessionId.value,
      thread_id: threadId.value,
    }),
  )

  input.value = ''
  void scrollToBottom()
}

const newThread = () => {
  threadId.value = crypto.randomUUID()
  messages.value = []
  historyMessages.value = []
  searchContext.value = ''
  ElMessage.success('已创建新日常对话线程')
}

onMounted(async () => {
  connectWS()
  await refreshHistory()
})

onUnmounted(() => {
  socket?.close()
})
</script>

<template>
  <div class="w-[1400px] mx-auto mt-8 grid grid-cols-[300px_2fr_1fr] gap-6">
    <el-card shadow="never">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-medium">日常对话历史</span>
          <el-button text size="small" :loading="historyLoading" @click="refreshHistory">刷新</el-button>
        </div>
      </template>

      <div class="space-y-2 mb-4 max-h-[620px] overflow-y-auto">
        <div
          v-for="item in historyThreads"
          :key="item.thread_id"
          class="p-2 rounded border cursor-pointer transition-all"
          :class="threadId === item.thread_id ? 'border-purple-400 bg-purple-50' : 'border-gray-200 hover:border-purple-300'"
          @click="openHistoryThread(item.thread_id)"
        >
          <div class="text-xs text-gray-500">{{ item.updated_at }}</div>
          <div class="text-xs mt-1">模式：{{ item.mode }}</div>
          <div class="text-sm text-gray-700 mt-1 truncate">{{ item.preview || '暂无预览' }}</div>
        </div>
        <div v-if="!historyThreads.length" class="text-sm text-gray-500">暂无历史记录</div>
      </div>

      <el-button class="w-full" @click="newThread">新建会话线程</el-button>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-medium">日常对话</span>
          <span class="text-xs" :class="wsReady ? 'text-green-600' : 'text-red-500'">
            {{ wsReady ? 'WS 已连接' : 'WS 未连接' }}
          </span>
        </div>
      </template>

      <div class="normal-chat-window h-[560px] overflow-y-auto p-3 bg-gray-50 rounded">
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="mb-3"
          :class="msg.role === 'user' ? 'text-right' : 'text-left'"
        >
          <div class="text-xs text-gray-500 mb-1">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
          <div
            class="inline-block max-w-[85%] p-2 rounded whitespace-pre-wrap"
            :class="msg.role === 'user' ? 'bg-purple-600 text-white' : 'bg-white text-gray-800'"
          >
            {{ msg.content }}
          </div>
        </div>
      </div>

      <div class="mt-3 flex gap-3">
        <el-select v-model="mode" class="w-[220px]">
          <el-option label="日常模式 (deepseek-chat)" value="daily" />
          <el-option label="深度思考 (deepseek-reasoner)" value="reasoning" />
        </el-select>
        <el-checkbox v-model="options.enableSearch">启用搜索增强</el-checkbox>
      </div>

      <el-input
        v-if="options.enableSearch"
        v-model="options.searchQueriesText"
        class="mt-3"
        type="textarea"
        :rows="3"
        placeholder="搜索关键词（每行一个，不填默认用消息本身）"
      />

      <div class="mt-3 flex gap-2">
        <el-input
          v-model="input"
          placeholder="输入消息并发送（支持流式输出）"
          @keyup.enter="sendMessage"
          :disabled="sending"
        />
        <el-button type="primary" :loading="sending" @click="sendMessage">发送</el-button>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="font-medium">上下文与状态</div>
      </template>

      <div class="text-xs text-gray-600 space-y-2">
        <div>thread_id: {{ threadId }}</div>
        <div>session_id: {{ sessionId }}</div>
        <div>mode: {{ mode }}</div>
      </div>

      <div class="mt-3">
        <div class="text-sm font-medium mb-1">搜索上下文</div>
        <div class="text-xs whitespace-pre-wrap p-2 rounded bg-gray-50 max-h-[480px] overflow-y-auto">
          {{ searchContext || '未使用搜索或暂无搜索结果' }}
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped></style>
