import axios, { type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { useUserStore } from '@/stores/user.ts'
import router from '@/router/index.ts'
import { refreshTokenApi } from '@/apis/auth'
import { ElMessage } from 'element-plus'
// --- 1. 类型定义 ---
export interface Response<T = any> {
  timestamp: string
  data: T
  path: string
  code: number
  message: string
  success: boolean
}

// 队列成员接口：必须包含 resolve 和 reject
interface PendingRequest {
  resolve: (token: string) => void
  reject: (err: any) => void
}

// --- 2. 基础配置 ---
export const uploadUrl = import.meta.env.DEV ? 'http://10.46.2.76:9100' : '待定'
export const socketUrl = import.meta.env.DEV ? 'localhost:3000/pay' : '待定'
export const timeout = 50000
export const serverApi = axios.create({
  baseURL: '/api/v1',
  timeout: timeout,
})

// --- 3. 核心变量 (控制并发) ---
let isRefreshing = false // 锁：标记是否正在刷新中
let requestQueue: PendingRequest[] = [] // 休息室：存放等待刷新结果的请求

// --- 4. 响应拦截器 ---
serverApi.interceptors.response.use(
  (res: AxiosResponse) => res.data, // 直接提取业务数据
  async (error) => {
    if (error.code == 'ERR_NETWORK') {
      ElMessage.error('请求超时，请稍后再试')
      return Promise.reject(error)
    }
    ElMessage.error(error.response?.data?.message || '请求失败')
    const { config, response } = error
    const userStore = useUserStore()

    // 只有 401 (Unauthorized) 且不是刷新接口本身报错时，才尝试刷新
    if (response?.status !== 401) {
      return Promise.reject(error)
    }

    const refreshToken = userStore.getRefreshToken
    const accessToken = userStore.getAccessToken

    // 如果连 Token 都没有，直接去登录
    if (!refreshToken || !accessToken) {
      handleLogout()
      return Promise.reject(error)
    }

    const originalRequest = config as AxiosRequestConfig

    // 【场景 A】：如果正在刷新中，将当前请求包装成 Promise 放入队列挂起
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        requestQueue.push({
          resolve: (newAccessToken: string) => {
            // 用新 Token 替换旧 Header 并重试
            if (originalRequest.headers) {
              originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`
            }
            resolve(serverApi(originalRequest))
          },
          reject: (err: any) => {
            reject(err)
          },
        })
      })
    }

    // 【场景 B】：第一个触发过期的请求，负责去换票
    isRefreshing = true

    try {
      const res = await refreshTokenApi({ refreshToken })

      if (res.success && res.data) {
        // 1. 更新本地存储的 Token
        userStore.updateToken(res.data)
        const newAccessToken = userStore.getAccessToken!

        // 2. 通知“休息室”里排队的所有请求，用新 Token 去重试
        requestQueue.forEach((item) => item.resolve(newAccessToken))

        // 3. 自己也要带上新 Token 重试第一次失败的请求
        if (originalRequest.headers) {
          originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`
        }
        return serverApi(originalRequest)
      } else {
        // 换票失败：后端明确告知换不了（比如 RT 也过期了）
        handleLogout()
        const err = new Error(res.message || '登录已过期')
        requestQueue.forEach((item) => item.reject(err)) // 让队列里的请求全部报错
        return Promise.reject(err)
      }
    } catch (refreshError) {
      // 换票异常：网络崩溃或 500
      requestQueue.forEach((item) => item.reject(refreshError))
      handleLogout()
      return Promise.reject(refreshError)
    } finally {
      // 重置状态
      isRefreshing = false
      requestQueue = []
    }
  },
)

// --- 5. 请求拦截器 (注入 Token) ---
serverApi.interceptors.request.use((config) => {
  const userStore = useUserStore()
  const token = userStore.getAccessToken
  if (token && config.headers) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// --- 6. 辅助工具 ---
async function handleLogout() {
  const userStore = useUserStore()
  userStore.logout()
  if (router.currentRoute.value.path !== '/') {
    await router.replace('/')
  }
}

// --- 7. 其他实例 (可选) ---
export const aiApi = axios.create({
  baseURL: '/api/ai/v1',
  timeout: timeout,
})
aiApi.interceptors.response.use((res) => res.data)
