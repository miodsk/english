export interface SpeakHistoryMessage {
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface SpeakHistoryThread {
  thread_id: string
  session_id?: string | null
  topic?: string | null
  updated_at: string
  preview?: string | null
}

export interface SpeakHistoryListResponse {
  threads: SpeakHistoryThread[]
}

export interface SpeakHistoryDetailResponse {
  thread_id: string
  session_id?: string | null
  topic?: string | null
  messages: SpeakHistoryMessage[]
}
