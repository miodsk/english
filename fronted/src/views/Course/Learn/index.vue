<template>
  <div class="min-h-[60vh] bg-zinc-50/80">
    <div class="w-[1200px] mx-auto px-4 pt-12 pb-24">
      <header class="mb-10 text-center">
        <h1 class="text-3xl font-bold text-zinc-900 tracking-tight sm:text-4xl">{{ title }}</h1>
        <p class="mt-3 text-zinc-500 text-sm">请根据释义和翻译拼写单词</p>
      </header>

      <el-skeleton v-if="isLoading" :rows="10" animated />

      <div v-if="list.length === 0" class="flex justify-center py-20">
        <el-empty description="暂无单词或您尚未购买该课程" />
      </div>

      <template v-else>
        <!-- 本组已学完 -->
        <div
          v-if="currentIndex >= list.length"
          class="text-center py-16 px-6 bg-white rounded-2xl border border-zinc-100 shadow-sm"
        >
          <p class="text-zinc-600 mb-6">本组 10 个词已学完</p>
          <el-button type="primary" size="large" @click="saveWordMaster"> 再练一组 </el-button>
        </div>

        <!-- 当前单词卡片 -->
        <div v-else>
          <div class="mb-4 flex items-center justify-between text-sm text-zinc-500">
            <span>第 {{ currentIndex + 1 }} / {{ list.length }} 个</span>
          </div>
          <article class="bg-white rounded-2xl border border-zinc-100 shadow-sm overflow-hidden">
            <div class="p-8 sm:p-10 relative">
              <div class="flex justify-center mb-6">
                <div
                  :class="{ 'filter blur-md select-none': isWordBlurred }"
                  class="transition-all duration-300 min-h-10 flex flex-col items-center text-center"
                >
                  <div class="text-2xl sm:text-3xl font-bold text-indigo-600 tracking-tight">
                    {{ currentWord?.word }}
                  </div>
                  <div class="flex items-center justify-center gap-2 mt-1">
                    <span v-if="currentWord?.phonetic" class="text-base text-zinc-500 font-mono">
                      {{ currentWord.phonetic }}
                    </span>
                    <el-icon
                      v-if="currentWord?.word"
                      class="shrink-0 cursor-pointer text-slate-400 hover:text-indigo-400 transition-colors"
                      :size="18"
                      title="发音"
                      @click="playAudio(currentWord!.word)"
                    >
                      <VideoPlay />
                    </el-icon>
                  </div>
                </div>
                <el-icon
                  class="absolute! right-10 top-10 cursor-pointer text-slate-400 hover:text-indigo-400 transition-colors"
                  :size="18"
                  :title="isWordBlurred ? '点击显示单词' : '点击隐藏单词'"
                  @click="isWordBlurred = !isWordBlurred"
                >
                  <View v-if="isWordBlurred" />
                  <Hide v-else />
                </el-icon>
              </div>
              <!-- 释义 -->
              <div class="mb-4 rounded-lg bg-zinc-50/80 border border-zinc-100 p-4">
                <p class="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-2">释义</p>
                <div
                  class="text-zinc-700 leading-relaxed prose prose-sm max-w-none"
                  v-html="currentWord?.definition"
                />
              </div>
              <!-- 翻译 -->
              <div class="rounded-lg bg-zinc-50/80 border border-zinc-100 p-4">
                <p class="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-2">翻译</p>
                <div
                  class="text-zinc-600 leading-relaxed whitespace-pre-line prose prose-sm max-w-none"
                  v-html="currentWord?.translation"
                />
              </div>
              <!--拼写练习-->
              <div class="rounded-lg bg-zinc-50/80 border border-zinc-100 p-4">
                <p class="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-2">拼写</p>
                <div class="flex items-center gap-2 justify-center">
                  <input
                    :maxlength="1"
                    ref="inputRefs"
                    @input="onInput(index)"
                    v-for="(item, index) in wordList"
                    @keydown="onKeyDown(index, $event)"
                    :key="index"
                    type="text"
                    v-model="item.input"
                    :class="{
                      'border-indigo-500!': item.isTrue === true,
                      'border-red-500!': item.isTrue === false,
                    }"
                    class="border-0 border-b-2 border-zinc-300 focus:border-indigo-500 bg-transparent outline-none w-10 text-center text-2xl font-bold"
                  />
                </div>
              </div>
              <!--控制按钮-->
              <div class="flex justify-end gap-2">
                <el-button type="primary" @click="pagePrev"> 上一个 </el-button>
                <el-button type="primary" @click="pageNext"> 下一个 </el-button>
              </div>
            </div>
          </article>
        </div>
      </template>
    </div>
  </div>
</template>
<script setup lang="ts">
import { useRoute } from 'vue-router'
import { ref, onMounted, computed, watch, useTemplateRef, nextTick } from 'vue'
import type { Word, WordList } from '@en/common/word'
import { useAudio } from '@/hooks/useAudio.ts'
import { useUserStore } from '@/stores/user.ts'
import { View, Hide, VideoPause, VideoPlay } from '@element-plus/icons-vue'
import { getWordList, saveWordMaster as saveWordMasterApi } from '@/apis/learn'
import { ElMessage } from 'element-plus'
interface WordItem {
  word: string
  input: string
  isTrue: boolean | undefined
}
const userStore = useUserStore()
const { playAudio } = useAudio({})
const route = useRoute()
const { courseId, title } = route.params
const isLoading = ref(false)
const currentIndex = ref(0)
const isWordBlurred = ref(true)
const list = ref<Word[]>([])
const inputRefs = useTemplateRef<HTMLInputElement[]>('inputRefs')
const currentWord = computed<Word | undefined>(() => {
  return list.value[currentIndex.value]
})
const getWordListData = async () => {
  isLoading.value = true
  const res = await getWordList(courseId as string)
  if (res.success) {
    list.value = res.data
  } else {
    ElMessage.error('获取单词列表失败')
  }
  isLoading.value = false
}
const wordList = ref<WordItem[]>([])
const pagePrev = () => {
  if (wordList.value.some((item) => item.isTrue === false)) {
    ElMessage.warning('请先完成当前单词的练习')
    return
  }
  currentIndex.value--
}
const pageNext = () => {
  if (wordList.value.some((item) => item.isTrue === false)) {
    ElMessage.warning('请先完成当前单词的练习')
    return
  }
  currentIndex.value++
}
const onInput = (index: number) => {
  const current = wordList.value[index]
  if (current) {
    current.isTrue = current.input === current.word
  }
  nextTick(() => {
    const inputs = inputRefs.value
    if (index < wordList.value.length - 1) {
      inputs?.[index + 1]?.focus()
    }
  })
  console.log('onInput', current, index)
}
const onKeyDown = (index: number, event: KeyboardEvent) => {
  console.log('onKeyDown', index, event.key)
  if (event.key === 'Backspace') {
    event.preventDefault()
    const current = wordList.value[index]
    if (current) {
      current.input = ''
      current.isTrue = undefined
    }
    nextTick(() => {
      const inputs = inputRefs.value
      if (index > 0) {
        inputs?.[index - 1]?.focus()
      }
    })
  }
  if (event.key.length == 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
    const current = wordList.value[index]!
    // 如果是输入字符，且没有按下 Ctrl、Meta、Alt 键，则自动跳转到下一个输入框
    if (current.input && index < wordList.value.length - 1) {
      event.preventDefault()
      const next = wordList.value[index + 1]!
      next.input = event.key
      next.isTrue = next.word === event.key
      nextTick(() => {
        const inputs = inputRefs.value
        if (index < wordList.value.length - 1) {
          inputs?.[index + 1]?.focus()
        }
      })
    }
  }
}
const saveWordMaster = async () => {
  console.log('saveWordMaster')
  const wordIds = list.value.map((item) => item.id)
  const res = await saveWordMasterApi(wordIds)
  if (res.success) {
    currentIndex.value = 0
    ElMessage.success(res.message)
    await getWordListData()
  } else {
    ElMessage.error(res.message)
  }
  userStore.updateWordNumber(10)
}
watch(
  currentWord,
  (newWord) => {
    isWordBlurred.value = true
    const current = currentWord.value?.word || ''
    wordList.value = Array.from(current).map((item) => {
      return {
        word: item,
        input: '',
        isTrue: undefined,
      }
    })
  },
  {
    immediate: true,
  },
)
onMounted(() => {
  getWordListData()
})
</script>
