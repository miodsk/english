import { uploadUrl } from '@/apis'
import Ayanami from '@/assets/avatar/ayanami01.jpg'
import { useUserStore } from '@/stores/user.ts'
import { computed } from 'vue'

export const useAvatar = () => {
  const userStore = useUserStore()
  const avatar = computed(() =>
    userStore.getUser ? uploadUrl + userStore.getUser.avatar : Ayanami,
  )
  return { avatar }
}
