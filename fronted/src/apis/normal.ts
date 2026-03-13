import { aiApi } from '@/apis/ai'
import type {
  NormalChatRequest,
  NormalChatResponse,
  NormalHistoryDetailResponse,
  NormalHistoryListResponse,
} from '@en/common/chat/normal'

export const normalChatApi = (payload: NormalChatRequest) => {
  return aiApi
    .post<NormalChatResponse>('/normal/chat', payload)
    .then((res) => res.data)
}

export const listNormalHistoryApi = (userId: string) => {
  return aiApi
    .get<NormalHistoryListResponse>('/normal/history', {
      params: { user_id: userId },
    })
    .then((res) => res.data)
}

export const getNormalHistoryDetailApi = (threadId: string, userId: string) => {
  return aiApi
    .get<NormalHistoryDetailResponse>(`/normal/history/${threadId}`, {
      params: { user_id: userId },
    })
    .then((res) => res.data)
}
