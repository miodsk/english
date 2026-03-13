import axios from 'axios'

const timeout = 100000

export const aiApi = axios.create({
  baseURL: '/api/ai',
  timeout: timeout,
})
export const tts = (text: string) => {
  return aiApi.post(
    '/ai/tts',
    { text },
    {
      responseType: 'blob',
    },
  )
}
