<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getSpeakHistoryDetailApi, listSpeakHistoryApi } from '@/apis/speak'
import type { SpeakHistoryMessage, SpeakHistoryThread } from '@en/common/chat/speak'

interface StreamMessage {
  id: number
  text: string
  audio: string
  is_end: boolean
  audio_pending?: boolean
  error?: string
}

interface ChatMessage {
  role: 'user' | 'ai'
  content: string
}

type SpeechRecognitionCtor = new () => SpeechRecognition

const userStore = useUserStore()
const userId = computed(() => userStore.getUser?.id || 'fronted-demo-user')

const messages = ref<ChatMessage[]>([])
const transcript = ref('')
const topic = ref('')
const isRecognizing = ref(false)
const isStreaming = ref(false)
const wsReady = ref(false)

const sessionId = ref(localStorage.getItem('speak_session_id') || crypto.randomUUID())
if (!localStorage.getItem('speak_session_id')) {
  localStorage.setItem('speak_session_id', sessionId.value)
}
const threadId = ref<string>(crypto.randomUUID())

const historyThreads = ref<SpeakHistoryThread[]>([])
const historyMessages = ref<SpeakHistoryMessage[]>([])
const historyLoading = ref(false)

let socket: WebSocket | null = null
let isConnecting = false

let audioContext: AudioContext | null = null
const audioQueue: Map<number, ArrayBuffer> = new Map()
const pendingAudioIds: Set<number> = new Set()
const skippedAudioIds: Set<number> = new Set()
let nextPlayId = 1
let isPlaying = false

let recognition: SpeechRecognition | null = null

const initAudioContext = () => {
  if (!audioContext) {
    audioContext = new AudioContext()
  }
  if (audioContext.state === 'suspended') {
    void audioContext.resume()
  }
}

const resetPlayback = () => {
  audioQueue.clear()
  pendingAudioIds.clear()
  skippedAudioIds.clear()
  nextPlayId = 1
  isPlaying = false
}

const base64ToArrayBuffer = (base64: string): ArrayBuffer => {
  const binaryString = atob(base64)
  const bytes = new Uint8Array(binaryString.length)
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i)
  }
  return bytes.buffer
}

const playNextInQueue = async () => {
  if (isPlaying || !audioContext) return

  const audioData = audioQueue.get(nextPlayId)
  if (!audioData) {
    if (skippedAudioIds.has(nextPlayId)) {
      skippedAudioIds.delete(nextPlayId)
      nextPlayId += 1
      void playNextInQueue()
    }
    return
  }

  isPlaying = true
  audioQueue.delete(nextPlayId)

  try {
    const audioBuffer = await audioContext.decodeAudioData(audioData.slice(0))
    const source = audioContext.createBufferSource()
    source.buffer = audioBuffer
    source.connect(audioContext.destination)
    source.onended = () => {
      isPlaying = false
      nextPlayId += 1
      void playNextInQueue()
    }
    source.start(0)
  } catch (e) {
    console.error('音频解码失败', e)
    isPlaying = false
    nextPlayId += 1
    void playNextInQueue()
  }
}

const queueAudio = (msg: StreamMessage) => {
  if (msg.audio_pending) {
    pendingAudioIds.add(msg.id)
    return
  }

  if (!msg.audio) {
    if (pendingAudioIds.has(msg.id)) {
      pendingAudioIds.delete(msg.id)
      skippedAudioIds.add(msg.id)
    } else {
      skippedAudioIds.add(msg.id)
    }
    if (msg.id === nextPlayId) {
      nextPlayId += 1
      void playNextInQueue()
    }
    return
  }

  pendingAudioIds.delete(msg.id)
  try {
    audioQueue.set(msg.id, base64ToArrayBuffer(msg.audio))
    void playNextInQueue()
  } catch (e) {
    console.error('Base64 转音频失败', e)
  }
}

const scrollToBottom = async () => {
  await nextTick()
  const container = document.querySelector('.chat-window')
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

const refreshHistory = async () => {
  historyLoading.value = true
  try {
    const data = await listSpeakHistoryApi(userId.value)
    historyThreads.value = data.threads
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '加载口语历史失败')
  } finally {
    historyLoading.value = false
  }
}

const openHistoryThread = async (id: string) => {
  threadId.value = id
  messages.value = []
  try {
    const detail = await getSpeakHistoryDetailApi(id, userId.value)
    topic.value = detail.topic || topic.value
    historyMessages.value = detail.messages
    messages.value = detail.messages.map((msg) => ({
      role: msg.role === 'assistant' ? 'ai' : 'user',
      content: msg.content,
    }))
    await scrollToBottom()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '加载口语线程失败')
  }
}

const dispatchTextToAI = (text: string) => {
  const content = text.trim()
  if (!content) return
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    ElMessage.warning('WS 未连接，稍后重试')
    return
  }

  resetPlayback()
  initAudioContext()
  messages.value.push({ role: 'user', content })
  messages.value.push({ role: 'ai', content: '' })
  socket.send(
    JSON.stringify({
      text: content,
      user_id: userId.value,
      session_id: sessionId.value,
      thread_id: threadId.value,
      topic: topic.value,
    }),
  )
  isStreaming.value = true
  void scrollToBottom()
}

const connectWS = () => {
  if (isConnecting || (socket && socket.readyState === WebSocket.OPEN)) return

  isConnecting = true
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  socket = new WebSocket(`${protocol}//${window.location.host}/api/ai/speak/ws`)

  socket.onopen = () => {
    isConnecting = false
    wsReady.value = true
    initAudioContext()
  }

  socket.onmessage = async (event) => {
    try {
      const data: StreamMessage = JSON.parse(event.data)

      if (data.text) {
        const last = messages.value[messages.value.length - 1]
        if (last && last.role === 'ai') {
          last.content += data.text
        }
        await scrollToBottom()
      }

      if (!data.is_end) {
        queueAudio(data)
      } else {
        isStreaming.value = false
        if (data.error) {
          ElMessage.error(data.error)
        } else {
          await refreshHistory()
        }
      }
    } catch (e) {
      console.error('WS 消息处理失败', e)
    }
  }

  socket.onclose = () => {
    wsReady.value = false
    isConnecting = false
    isStreaming.value = false
  }

  socket.onerror = () => {
    wsReady.value = false
    isConnecting = false
    isStreaming.value = false
    ElMessage.error('WS 连接错误')
  }
}

const setupASR = () => {
  const Ctor =
    (window as unknown as { SpeechRecognition?: SpeechRecognitionCtor }).SpeechRecognition ||
    (window as unknown as { webkitSpeechRecognition?: SpeechRecognitionCtor })
      .webkitSpeechRecognition

  if (!Ctor) {
    ElMessage.warning('当前浏览器不支持 Web Speech API，请手动输入转写')
    return
  }

  recognition = new Ctor()
  recognition.lang = 'en-US'
  recognition.continuous = false
  recognition.interimResults = true

  recognition.onstart = () => {
    isRecognizing.value = true
    transcript.value = ''
  }

  recognition.onresult = (event) => {
    let finalText = ''
    let interimText = ''

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const piece = event.results[i][0]?.transcript || ''
      if (event.results[i].isFinal) {
        finalText += piece
      } else {
        interimText += piece
      }
    }

    transcript.value = `${finalText} ${interimText}`.trim()
  }

  recognition.onend = () => {
    isRecognizing.value = false
    if (transcript.value.trim()) {
      dispatchTextToAI(transcript.value)
      transcript.value = ''
    }
  }

  recognition.onerror = (e) => {
    isRecognizing.value = false
    ElMessage.error(`ASR 错误: ${e.error}`)
  }
}

const startASR = () => {
  if (!recognition) setupASR()
  if (!recognition || isRecognizing.value) return
  recognition.start()
}

const stopASR = () => {
  if (recognition && isRecognizing.value) recognition.stop()
}

const sendManual = () => {
  dispatchTextToAI(transcript.value)
  transcript.value = ''
}

const newThread = () => {
  threadId.value = crypto.randomUUID()
  messages.value = []
  historyMessages.value = []
  ElMessage.success('已创建新口语线程')
}

onMounted(async () => {
  connectWS()
  setupASR()
  await refreshHistory()
})

onUnmounted(() => {
  if (recognition && isRecognizing.value) {
    recognition.stop()
  }
  socket?.close()
  if (audioContext) {
    void audioContext.close()
  }
})
</script>

<template>
  <div class="w-[1400px] mx-auto mt-8 grid grid-cols-[300px_2fr_1fr] gap-6">
    <el-card shadow="never">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-medium">口语会话历史</span>
          <el-button text size="small" :loading="historyLoading" @click="refreshHistory">
            刷新
          </el-button>
        </div>
      </template>

      <div class="space-y-2 mb-4 max-h-[280px] overflow-y-auto">
        <div
          v-for="item in historyThreads"
          :key="item.thread_id"
          class="p-2 rounded border cursor-pointer transition-all"
          :class="threadId === item.thread_id ? 'border-purple-400 bg-purple-50' : 'border-gray-200 hover:border-purple-300'"
          @click="openHistoryThread(item.thread_id)"
        >
          <div class="text-xs text-gray-500">{{ item.updated_at }}</div>
          <div class="text-sm font-medium truncate">{{ item.topic || '未命名口语主题' }}</div>
          <div class="text-xs text-gray-600 mt-1 truncate">{{ item.preview || '暂无预览' }}</div>
        </div>
        <div v-if="!historyThreads.length" class="text-sm text-gray-500">暂无历史记录</div>
      </div>

      <el-button class="w-full" @click="newThread">新建会话线程</el-button>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-medium">口语实时对话（ASR → LLM → TTS）</span>
          <span class="text-xs" :class="wsReady ? 'text-green-600' : 'text-red-500'">
            {{ wsReady ? 'WS 已连接' : 'WS 未连接' }}
          </span>
        </div>
      </template>

      <el-input
        v-model="topic"
        class="mb-3"
        placeholder="可选：输入本轮口语主题（用于历史归档）"
      />

      <div class="chat-window h-[470px] overflow-y-auto p-3 bg-gray-50 rounded">
        <div v-for="(item, idx) in messages" :key="idx" class="mb-3">
          <div class="text-xs text-gray-500 mb-1">{{ item.role === 'user' ? '你' : 'AI' }}</div>
          <div class="p-2 rounded bg-white whitespace-pre-wrap">{{ item.content }}</div>
        </div>
      </div>

      <div class="mt-4 space-y-3">
        <el-input
          v-model="transcript"
          type="textarea"
          :rows="3"
          placeholder="语音识别文本会出现在这里，也可以手动输入后发送"
          :disabled="isStreaming"
        />

        <div class="flex gap-3">
          <el-button type="primary" :disabled="isRecognizing || isStreaming" @click="startASR">
            开始说话
          </el-button>
          <el-button type="warning" :disabled="!isRecognizing" @click="stopASR">
            停止说话
          </el-button>
          <el-button :disabled="!transcript.trim() || isStreaming" @click="sendManual">
            发送文本
          </el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="font-medium">状态说明</div>
      </template>
      <ul class="text-sm leading-7 text-gray-600">
        <li>1. 点击“开始说话”进行 ASR（浏览器识别）</li>
        <li>2. 识别结束后文本通过 WS 发给 AI</li>
        <li>3. AI 流式返回文本 + base64 音频</li>
        <li>4. 前端按序列号顺序播放 TTS 音频</li>
        <li>5. 每轮对话会自动写入会话历史</li>
      </ul>
      <div class="mt-4 text-xs text-gray-500">
        当前状态：{{ isRecognizing ? '识别中' : isStreaming ? 'AI 回复中' : '空闲' }}
      </div>
      <div class="mt-2 text-xs text-gray-500">当前 thread_id: {{ threadId }}</div>
    </el-card>
  </div>
</template>

<style scoped></style>
