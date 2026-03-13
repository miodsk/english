<template>
  <div class="mx-auto w-[1200px] px-4 py-6">
    <div class="flex items-center justify-between">
      <div>
        <div class="text-xl font-extrabold text-slate-900">设置</div>
        <div class="mt-1 text-sm text-slate-500">在这里修改你的个人信息与头像</div>
      </div>

      <div class="flex gap-2">
        <el-button>重置</el-button>
        <el-button @click="onSave" type="primary">保存</el-button>
      </div>
    </div>

    <el-row :gutter="16" class="mt-4">
      <el-col :span="8">
        <el-card shadow="never">
          <template #header>
            <div class="font-bold">头像</div>
          </template>

          <div class="flex items-center gap-4">
            <img
              class="w-20 h-20 rounded-full object-cover border-2 border-gray-200"
              :src="avatar"
              loading="lazy"
              referrerpolicy="no-referrer"
            />

            <div class="flex flex-col gap-2">
              <el-upload
                :show-file-list="false"
                :auto-upload="false"
                accept="image/*"
                :on-change="onAvatarSelect"
              >
                <el-button type="primary">选择头像</el-button>
              </el-upload>

              <div class="text-xs text-slate-500">支持 png/jpg/webp，建议小于 2MB</div>
            </div>
          </div>
        </el-card>

        <el-card shadow="never" class="mt-4">
          <template #header>
            <div class="font-bold">账号</div>
          </template>

          <div class="text-sm text-slate-600">
            <div class="flex items-center justify-between">
              <span>登录状态</span>
              <el-tag type="success"> 已登录 </el-tag>
            </div>
            <div></div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <div class="font-bold">个人信息</div>
          </template>

          <el-form label-width="140px" :model="form" :rules="rules" ref="formRef" status-icon>
            <el-form-item label="用户名：" prop="name">
              <el-input v-model="form.name" placeholder="请输入用户名" clearable />
            </el-form-item>

            <el-form-item label="邮箱：" prop="email">
              <el-input v-model="form.email" placeholder="请输入邮箱" clearable />
            </el-form-item>

            <el-form-item label="定时任务：" prop="isTimingTask">
              <el-switch v-model="form.isTimingTask" />
            </el-form-item>
            <el-form-item label="定时任务时间：" prop="timingTaskTime">
              <div>
                <el-time-picker
                  format="HH:mm:ss"
                  value-format="HH:mm:ss"
                  v-model="form.timingTaskTime"
                  placeholder="请选择定时任务时间"
                />
                <div class="text-xs text-slate-500 mt-3">
                  tips:只有填写邮箱并且开启定时任务，才能收到每日打卡提醒
                </div>
              </div>
            </el-form-item>

            <el-form-item label="地址：" prop="address">
              <el-input v-model="form.address" placeholder="请输入地址" clearable />
            </el-form-item>

            <el-form-item label="签名：" prop="bio">
              <el-input
                v-model="form.bio"
                placeholder="写点什么介绍一下自己"
                type="textarea"
                :rows="4"
                maxlength="120"
                show-word-limit
              />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never" class="mt-4">
          <template #header>
            <div class="font-bold">危险操作</div>
          </template>

          <div class="flex items-center justify-between">
            <div>
              <div class="font-bold text-slate-900">退出登录</div>
              <div class="text-sm text-slate-500">清除本地登录状态</div>
            </div>
            <el-button @click="logoutHandle" type="danger" plain> 退出 </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, useTemplateRef, onMounted } from 'vue'
import type { UserUpdate } from '@en/common/user'
import type { FormRules, UploadFile } from 'element-plus'
import { uploadAvatar, updateUser } from '@/apis/user'
import { uploadUrl } from '@/apis'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { useAvatar } from '@/hooks/useAvatar'
import Ayanami from '@/assets/avatar/ayanami01.jpg'
const { avatar } = useAvatar()
const userStore = useUserStore()
const userInfo = userStore.getUser
const form = ref<UserUpdate>({
  name: '',
  email: '',
  isTimingTask: false,
  timingTaskTime: '',
  address: '',
  bio: '',
})
const formRef = useTemplateRef('formRef')
const rules: FormRules = {
  name: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    {
      required: false,
      message: '请输入邮箱',
      trigger: 'blur',
    },
    {
      validator: (rule, value, callback) => {
        if (value && !/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(value)) {
          callback(new Error('请输入有效的邮箱地址'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  isTimingTask: [
    { required: true, message: '请选择是否开启定时任务', trigger: 'change', type: 'boolean' },
  ],
  timingTaskTime: [{ required: true, message: '请选择定时任务时间', trigger: 'change' }],
}
const onAvatarSelect = async (file: UploadFile) => {
  const formData = new FormData()
  formData.append('file', file.raw as File)
  const res = await uploadAvatar(formData)
  if (res.success && res.data) {
    form.value.avatar = res.data.databaseUrl
    previewUrl.value = res.data.previewUrl
  } else {
    ElMessage.error(res.message)
  }
}
const onSave = async () => {
  const res = await updateUser(form.value)
  console.log(res.data)
  if (res.success) {
    ElMessage.success('保存成功')
    userStore.updateUser(res.data!)
  } else {
    ElMessage.error(res.message)
  }
}
const logoutHandle = () => {
  console.log('logoutHandle')
}
onMounted(() => {
  if (userInfo) {
    form.value = {
      name: userInfo.name,
      email: userInfo.email,
      avatar: userInfo.avatar,
      isTimingTask: userInfo.isTimingTask,
      timingTaskTime: userInfo.timingTaskTime,
      address: userInfo.address,
      bio: userInfo.bio,
    }
  }
})
</script>
