<script setup lang="ts">
import { ref, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'

interface Message {
  role: 'user' | 'ai'
  content: string
}

interface AudioMessage {
  id: number
  text: string
  audio: string  // base64编码的MP3
  is_end: boolean
  audio_pending?: boolean
  error?: string
}

const userInput = ref('')
const messages = ref<Message[]>([])
const isStreaming = ref(false)
const pendingMessage = ref<string | null>(null)
let socket: WebSocket | null = null
let isConnecting = false

// --- Web Audio API 播放器 ---
let audioContext: AudioContext | null = null
const audioQueue: Map<number, { text: string; audioData: ArrayBuffer }> = new Map()
const pendingAudioIds: Set<number> = new Set()
const skippedAudioIds: Set<number> = new Set()
let nextPlayId = 1
let isPlaying = false

// 初始化AudioContext
const initAudioContext = () => {
  if (!audioContext) {
    audioContext = new AudioContext()
  }
  // 如果被暂停，恢复它
  if (audioContext.state === 'suspended') {
    audioContext.resume()
  }
}

// Base64转ArrayBuffer
const base64ToArrayBuffer = (base64: string): ArrayBuffer => {
  const binaryString = atob(base64)
  const bytes = new Uint8Array(binaryString.length)
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i)
  }
  return bytes.buffer
}

// 播放下一个音频（按序列ID顺序）
const playNextInQueue = async () => {
  if (isPlaying || !audioContext) return
  
  const audioItem = audioQueue.get(nextPlayId)
  if (!audioItem) {
    if (skippedAudioIds.has(nextPlayId)) {
      skippedAudioIds.delete(nextPlayId)
      nextPlayId++
      playNextInQueue()
    }
    // 当前ID还没到，等待
    return
  }
  
  isPlaying = true
  audioQueue.delete(nextPlayId)
  
  try {
    // 解码音频数据
    const audioBuffer = await audioContext.decodeAudioData(audioItem.audioData.slice(0))
    
    // 创建音频源
    const source = audioContext.createBufferSource()
    source.buffer = audioBuffer
    source.connect(audioContext.destination)
    
    // 播放结束后播放下一个
    source.onended = () => {
      isPlaying = false
      nextPlayId++
      playNextInQueue()
    }
    
    source.start(0)
  } catch (error) {
    console.error(`音频解码失败 (id=${nextPlayId}):`, error)
    isPlaying = false
    nextPlayId++
    playNextInQueue()
  }
}

// 添加音频到队列
const queueAudio = (msg: AudioMessage) => {
  if (msg.audio_pending) {
    pendingAudioIds.add(msg.id)
    return
  }

  if (!msg.audio || msg.audio.length === 0) {
    // 如果该ID声明了“音频稍后到达”，先不要跳过
    if (pendingAudioIds.has(msg.id)) {
      // 若再次收到该ID且仍无音频，视为该片段无音频，跳过并继续
      pendingAudioIds.delete(msg.id)
      skippedAudioIds.add(msg.id)
      if (msg.id === nextPlayId) {
        nextPlayId++
        playNextInQueue()
      }
      return
    }

    // 没有音频数据，跳过这个ID
    skippedAudioIds.add(msg.id)
    if (msg.id === nextPlayId) {
      nextPlayId++
      playNextInQueue()
    }
    return
  }
  
  try {
    pendingAudioIds.delete(msg.id)
    const audioData = base64ToArrayBuffer(msg.audio)
    audioQueue.set(msg.id, { text: msg.text, audioData })
    
    // 尝试播放
    playNextInQueue()
  } catch (error) {
    console.error('Base64解码失败:', error)
  }
}

// 重置播放状态
const resetPlayback = () => {
  audioQueue.clear()
  pendingAudioIds.clear()
  skippedAudioIds.clear()
  nextPlayId = 1
  isPlaying = false
}

// WebSocket连接
const connectWS = () => {
  if (isConnecting || (socket && socket.readyState === WebSocket.OPEN)) {
    return
  }

  isConnecting = true
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  socket = new WebSocket(`${protocol}//${window.location.host}/api/ai/ws`)
  
  socket.onopen = () => {
    console.log('WebSocket 已连接')
    isConnecting = false
    initAudioContext()

    // 连接建立后自动发送排队消息
    if (pendingMessage.value && !isStreaming.value) {
      dispatchMessage(pendingMessage.value)
      pendingMessage.value = null
    }
  }
  
  socket.onmessage = async (event) => {
    try {
      // 所有消息都是JSON格式
      const data: AudioMessage = JSON.parse(event.data)
      
      // 更新文本显示
      if (data.text) {
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg && lastMsg.role === 'ai') {
          lastMsg.content += data.text
        }
        await scrollToBottom()
      }
      
      // 处理音频
      if (!data.is_end) {
        queueAudio(data)
      } else {
        // 结束标记
        isStreaming.value = false
        
        if (data.error) {
          ElMessage.error(data.error)
        }
      }
    } catch (error) {
      console.error('消息处理错误:', error)
    }
  }
  
  socket.onclose = () => {
    isStreaming.value = false
    isConnecting = false
    pendingMessage.value = null
    console.log('连接已关闭')
  }
  
  socket.onerror = () => {
    ElMessage.error('网络连接异常')
    isStreaming.value = false
    isConnecting = false
    pendingMessage.value = null
  }
}

const dispatchMessage = (text: string) => {
  // 重置播放状态
  resetPlayback()
  initAudioContext()

  messages.value.push({ role: 'user', content: text })
  messages.value.push({ role: 'ai', content: '' })

  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ text }))
    isStreaming.value = true
  }
}

const sendMessage = () => {
  const text = userInput.value.trim()
  if (!text || isStreaming.value) return

  if (socket?.readyState === WebSocket.OPEN) {
    dispatchMessage(text)
    userInput.value = ''
  } else {
    pendingMessage.value = text
    ElMessage.warning('连接建立中，将自动发送消息')
    connectWS()
    userInput.value = ''
  }
}

const scrollToBottom = async () => {
  await nextTick()
  const container = document.querySelector('.chat-window')
  if (container) {
    container.scrollTop = container.scrollHeight
  }
}

onUnmounted(() => {
  socket?.close()
  if (audioContext) {
    audioContext.close()
  }
})

// 初始连接
connectWS()
</script>

<template>
  <div class="chat-container">
    <div class="chat-window">
      <div v-for="(msg, index) in messages" :key="index" :class="['msg-wrapper', msg.role]">
        <div class="avatar">{{ msg.role === 'ai' ? '祥' : '我' }}</div>
        <div class="content">{{ msg.content }}</div>
      </div>
    </div>
    <div class="input-area">
      <el-input
        v-model="userInput"
        placeholder="和丰川祥子聊点什么..."
        @keyup.enter="sendMessage"
        :disabled="isStreaming"
      >
        <template #append>
          <el-button @click="sendMessage" :loading="isStreaming">发送</el-button>
        </template>
      </el-input>
    </div>
  </div>
</template>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}
.chat-window {
  flex: 1;
  min-height: 400px;
  overflow-y: auto;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
  margin-bottom: 20px;
}
.msg-wrapper {
  display: flex;
  margin-bottom: 15px;
  align-items: flex-start;
}
.msg-wrapper.ai {
  flex-direction: row;
}
.msg-wrapper.user {
  flex-direction: row-reverse;
}
.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}
.content {
  max-width: 70%;
  padding: 10px;
  border-radius: 8px;
  margin: 0 10px;
  background: white;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
}
.user .content {
  background: #95ec69;
}
.input-area {
  margin-top: auto;
}
.el-input {
  width: 100%;
}
</style>
