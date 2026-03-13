<template>
  <div class="w-[1000px] mx-auto mt-10">
    <el-card shadow="never" class="mb-6">
      <div class="text-2xl font-semibold">AI 学习助手</div>
      <div class="text-gray-500 mt-2">请选择你要进入的学习模式</div>
    </el-card>

    <div class="grid grid-cols-4 gap-5">
      <el-card shadow="hover" class="cursor-pointer" @click="goTo('chat-normal')">
        <div class="text-lg font-medium">日常对话</div>
        <div class="text-sm text-gray-500 mt-2">支持日常模式与深度思考 + 搜索增强</div>
      </el-card>

      <el-card shadow="hover" class="cursor-pointer" @click="goTo('chat-composition')">
        <div class="text-lg font-medium">作文批改</div>
        <div class="text-sm text-gray-500 mt-2">提交作文、查看评分、迭代改稿</div>
      </el-card>

      <el-card shadow="hover" class="cursor-pointer" @click="goTo('chat-speak')">
        <div class="text-lg font-medium">口语练习</div>
        <div class="text-sm text-gray-500 mt-2">口语对话、发音与表达练习</div>
      </el-card>

      <el-card shadow="hover" class="cursor-pointer" @click="goTo('chat-vocabulary')">
        <div class="text-lg font-medium">单词练习</div>
        <div class="text-sm text-gray-500 mt-2">单词记忆、复习与掌握度提升</div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goTo = (name: 'chat-normal' | 'chat-composition' | 'chat-speak' | 'chat-vocabulary') => {
  router.push({ name })
}
</script>
