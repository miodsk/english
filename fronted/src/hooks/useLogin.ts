import { inject, ref } from 'vue'
import { IS_SHOW_LOGIN } from '@/components/Login/types.ts'
import { useUserStore } from '@/stores/user.ts'
export function useLogin() {
  const userStore = useUserStore()
  const isShowLogin = inject(IS_SHOW_LOGIN, ref(false))

  function login() {
    return new Promise((resolve, reject) => {
      if (userStore.getUser) {
        resolve(userStore.getUser)
      } else {
        isShowLogin.value = true
        reject(new Error('请先登录'))
      }
    })
  }

  function hide() {
    isShowLogin.value = false
  }

  return {
    login,
    hide,
  }
}
