import { serverApi, type Response } from '@/apis'
import type { WordList, Word } from '@en/common/word'
import type { ResultLearn } from '../../../../common/learn'

export const getWordList = (courseId: string): Promise<Response<Word[]>> => {
  return serverApi.get(`/learn/word/${courseId}`)
}
export const saveWordMaster = (wordIds: string[]): Promise<Response<ResultLearn>> => {
  return serverApi.post('/learn/word/master', { wordIds })
}
