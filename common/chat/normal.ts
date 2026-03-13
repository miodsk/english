export type NormalMode = 'daily' | 'reasoning'

export interface NormalChatRequest {
  message: string
  mode?: NormalMode
  enable_search?: boolean
  search_queries?: string[]
}

export interface NormalChatResponse {
  mode: NormalMode
  enable_search: boolean
  search_context: string
  answer: string
}

export interface NormalHistoryMessage {
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface NormalHistoryThread {
  thread_id: string
  session_id?: string | null
  mode: NormalMode
  updated_at: string
  preview?: string | null
}

export interface NormalHistoryListResponse {
  threads: NormalHistoryThread[]
}

export interface NormalHistoryDetailResponse {
  thread_id: string
  session_id?: string | null
  mode: NormalMode
  messages: NormalHistoryMessage[]
}
