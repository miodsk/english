import { aiApi } from '@/apis/ai'
import type {
  CompositionHistoryDetailResponse,
  CompositionHistoryListResponse,
  CompositionGradeRequest,
  CompositionGradeResponse,
  CompositionReviseRequest,
  CompositionReviseResponse,
} from '@en/common/chat/composition'

export const gradeCompositionApi = (payload: CompositionGradeRequest) => {
  return aiApi
    .post<CompositionGradeResponse>('/composition/grade', payload)
    .then((res) => res.data)
}

export const reviseCompositionApi = (payload: CompositionReviseRequest) => {
  return aiApi
    .post<CompositionReviseResponse>('/composition/revise', payload)
    .then((res) => res.data)
}

export const listCompositionHistoryApi = (userId: string) => {
  return aiApi
    .get<CompositionHistoryListResponse>('/composition/history', {
      params: { user_id: userId },
    })
    .then((res) => res.data)
}

export const getCompositionHistoryDetailApi = (threadId: string, userId: string) => {
  return aiApi
    .get<CompositionHistoryDetailResponse>(`/composition/history/${threadId}`, {
      params: { user_id: userId },
    })
    .then((res) => res.data)
}
