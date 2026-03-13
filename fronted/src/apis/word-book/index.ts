import {serverApi,type Response} from '@/apis'
import type {WordQuery,WordList} from '@en/common/word'


export const getWordListApi = async (query: WordQuery): Promise<WordList> => {
  const res:Response<WordList> = await serverApi.get('/word-book', {
    params: query,
  })
  return res.data || {
    list:[],
    total:0
  }
}
