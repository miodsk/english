<script setup lang="ts">
import { RouterView } from 'vue-router'
import Search from '@/components/Search/index.vue'
import Login from '@/components/Login/index.vue'
import { provide, ref, watch } from 'vue'
import { IS_SHOW_LOGIN } from '@/components/Login/types.ts'
import { useUserStore } from '@/stores/user.ts'
import { useSocket } from '@/hooks/useSocket.ts'
import { Tracker } from '@en/tracker'
import { config } from '@/apis/tracker/index.ts'
const tracker = new Tracker(config)
provide(IS_SHOW_LOGIN, ref(false))
const userStore = useUserStore()
const { connect, disconnect } = useSocket()
watch(
  () => userStore.user?.id,
  (newVal, oldVal) => {
    if (newVal) {
      tracker.setUserId(newVal)
      connect()
    } else {
      disconnect()
    }
  },
  {
    immediate: true,
  },
)
</script>

<template>
  <RouterView />
  <Search />
  <Login />
</template>

<style scoped></style>
