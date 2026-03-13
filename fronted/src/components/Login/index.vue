<template>
  <div class="fixed inset-0 bg-black opacity-30 filter blur-sm z-40" v-if="isShowLogin"></div>
  <div class="fixed inset-30 flex items-center justify-center z-50" v-if="isShowLogin">
    <div class="w-[1200px] h-[700px] bg-white rounded-[20px] shadow-2xl overflow-hidden flex">
      <!-- 左侧贪吃蛇游戏区域 -->
      <SneakEater />

      <!-- 右侧表单区域 -->
      <div class="flex-1 flex flex-col justify-center px-12 py-10 bg-white">
        <LoginForm v-if="mode === 'login'" />
        <RegisterForm v-else />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SneakEater from './SneakEater.vue'
import LoginForm from './LoginForm.vue'
import RegisterForm from './RegisterForm.vue'
import { inject, provide, ref } from 'vue'
import { IS_SHOW_LOGIN, LOGIN_MODE } from '@/components/Login/types.ts'
const isShowLogin = inject(IS_SHOW_LOGIN)
const mode = ref<'login' | 'register'>('login')
provide(LOGIN_MODE, mode)
</script>
