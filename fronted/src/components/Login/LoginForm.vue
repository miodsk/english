<template>
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-800 mb-2">欢迎回来</h1>
    <p class="text-gray-500 text-sm">请登录您的账户以继续</p>
  </div>

  <el-form ref="formRef" :model="form" :rules="rules" class="space-y-6">
    <el-form-item prop="phone">
      <el-input
        v-model="form.phone"
        placeholder="请输入手机号"
        size="large"
        class="h-12"
        :prefix-icon="User"
      />
    </el-form-item>

    <el-form-item prop="password">
      <el-input
        v-model="form.password"
        type="password"
        placeholder="请输入密码"
        size="large"
        class="h-12"
        :prefix-icon="Lock"
        show-password
      />
    </el-form-item>

    <el-form-item class="pt-4">
      <el-button
        type="primary"
        size="large"
        class="w-full h-12 text-base font-semibold bg-linear-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 border-0"
        @click="handleLogin"
      >
        登录
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, toRaw, useTemplateRef } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { login } from '@/apis/user'
import md5 from 'md5'
import { ElMessage } from 'element-plus'
import { useLogin } from '@/hooks/useLogin.ts'
const { hide } = useLogin()
import { useUserStore } from '@/stores/user.ts'
const userStore = useUserStore()
const formRef = useTemplateRef('formRef')
const form = ref({
  phone: '',
  password: '',
})

const rules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const handleLogin = async () => {
  await formRef.value?.validate()

  const body = { ...toRaw(form.value) }

  try {
    const res = await login({
      ...body,
      password: md5(body.password),
    })
    if (res.code == 200) {
      ElMessage.success('登录成功')
      if (res.data) {
        userStore.setUser(res.data)
      }
      hide()
    }
  } catch (e: any) {
    ElMessage.error(e.response.data.message || '登录失败')
  }
}
</script>
