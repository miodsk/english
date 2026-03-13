import { io, type Socket } from 'socket.io-client'
import { socketUrl } from '@/apis'
import { useUserStore } from '@/stores/user.ts'

let socket: Socket | null = null

export const useSocket = () => {
  const userStore = useUserStore()
  const connect = () => {
    const userId = userStore.user?.id
    if (!userId) return
    if (socket) return
    socket = io(socketUrl, {
      transports: ['websocket'],
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 3,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
      query: {
        userId,
      },
    })
  }

  const disconnect = () => {
    if (socket) {
      socket.disconnect()
      socket.removeAllListeners()
      socket = null
    }
  }

  const getSocket = (): Socket | null => {
    return socket
  }

  return { connect, disconnect, getSocket }
}
