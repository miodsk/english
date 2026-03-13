import { aiApi } from '@/apis/ai'
import type {
  SpeakHistoryDetailResponse,
  SpeakHistoryListResponse,
} from '@en/common/chat/speak'

export const listSpeakHistoryApi = (userId: string) => {
  return aiApi
    .get<SpeakHistoryListResponse>('/speak/history', { params: { user_id: userId } })
    .then((res) => res.data)
}

export const getSpeakHistoryDetailApi = (threadId: string, userId: string) => {
  return aiApi
    .get<SpeakHistoryDetailResponse>(`/speak/history/${threadId}`, {
      params: { user_id: userId },
    })
    .then((res) => res.data)
}
