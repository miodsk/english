import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

import type { User, WebResultUser, Token, UserUpdate } from '@en/common/user'

export const useUserStore = defineStore(
  'user',
  () => {
    // --- State (状态) ---
    const user = ref<WebResultUser | null>(null)
    const setUser = (data: WebResultUser) => {
      user.value = data
    }
    const getAccessToken = computed(() => user.value?.token.accessToken)
    const getRefreshToken = computed(() => user.value?.token.refreshToken)
    const updateToken = (newToken: Token) => {
      if (user.value) {
        user.value.token = newToken
      }
    }
    const updateUser = (newUser: UserUpdate) => {
      if (user.value) {
        user.value = {
          ...user.value,
          ...newUser,
        }
      }
    }
    const updateWordNumber = (newWordNumber: number) => {
      if (user.value) {
        user.value.wordNumber = newWordNumber
      }
    }
    const getUser = computed(() => user.value)
    const logout = () => {
      user.value = null
    }
    return {
      user,
      setUser,
      getUser,
      logout,
      getAccessToken,
      getRefreshToken,
      updateWordNumber,
      updateToken,
      updateUser,
    }
  },
  {
    persist: true,
  },
)
