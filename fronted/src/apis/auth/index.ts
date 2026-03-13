import axios from 'axios'
import type { Token } from '@en/common/user'
import type { Response } from '@/apis'
const refreshServer = axios.create({
  baseURL: '/api/v1',
  timeout: 50000,
})

refreshServer.interceptors.response.use((res) => res.data)

export const refreshTokenApi = (data: Omit<Token, 'accessToken'>): Promise<Response<Token>> => {
  return refreshServer.post('/user/refreshToken', data)
}
