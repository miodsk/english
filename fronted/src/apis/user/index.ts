import { type Response, serverApi } from '@/apis'
import type {
  UserLogin,
  UserRegister,
  WebResultUser,
  AvatarResult,
  UserUpdate,
  UserInfo,
} from '@en/common/user'

export const login = (data: UserLogin): Promise<Response<WebResultUser>> => {
  return serverApi.post('/user/login', data)
}
export const register = (data: UserRegister): Promise<Response<WebResultUser>> => {
  return serverApi.post('/user/register', data)
}
export const uploadAvatar = (file: FormData): Promise<Response<AvatarResult>> => {
  return serverApi.post('/user/upload', file)
}
export const updateUser = (data: UserUpdate): Promise<Response<UserUpdate>> => {
  return serverApi.post('/user/update', data)
}
export const getUserInfo = (): Promise<Response<UserInfo>> => {
  return serverApi.get('/user/info')
}
