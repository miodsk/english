<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'
import { onMounted, ref, watch } from 'vue'
import { getWordListApi } from '@/apis/word-book'
import _ from 'lodash'
import type { WordList, Word, WordQuery } from '@en/common/word'

const query = ref<WordQuery>({
  page: 1,
  pageSize: 10,
  word: '',
})

const wordList = ref<WordList>({
  list: [],
  total: 0,
})

const loading = ref(false)

// 1. 基础请求函数
const getWordList = async () => {
  // 如果搜索词为空，可以考虑是否清空列表或返回
  if (!query.value.word) {
    wordList.value = { list: [], total: 0 }
    return
  }

  loading.value = true
  try {
    const res = await getWordListApi(query.value)
    if (res) {
      wordList.value = res
    }
  } finally {
    loading.value = false
  }
}

// 2. 搜索处理：重置页码并请求
const handleSearch = () => {
  query.value.page = 1
  getWordList()
}

const debouncedSearch = _.debounce(handleSearch, 300)

// 4. 监听搜索词变化
watch(
  () => query.value.word,
  () => {
    debouncedSearch()
  },
)

onMounted(() => {
  // 如果初始化需要展示数据则保留，否则搜索组件通常初始为空
  // getWordList()
})
window.addEventListener('keydown', (e: KeyboardEvent) => {
  if (e.key === 'f' && e.ctrlKey) {
    e.preventDefault()
    isShow.value = true
    document.body.style.overflow = 'hidden'
  }
  if (e.key === 'Escape') {
    isShow.value = false
    query.value.word = ''
    document.body.style.overflow = 'auto'
  }
})
const isShow = ref(false)

// 假设的复制函数
const copyWord = (word: string) => {
  navigator.clipboard.writeText(word)
  ElMessage.success('复制成功')
}
</script>

<template>
  <div
    v-if="isShow"
    class="fixed inset-0 w-full h-full z-40 bg-black/30 backdrop-blur-sm"
    @click="isShow = false"
  />

  <Transition name="fade">
    <div v-if="isShow" class="fixed inset-0 shadow-lg z-50 p-30 pt-20 pointer-events-none">
      <div class="w-1/2 mx-auto pointer-events-auto">
        <div
          :class="wordList.list.length > 0 ? 'rounded-t-[10px]' : 'rounded-[10px]'"
          class="flex items-center gap-2 shadow-lg p-3 bg-white transition-all"
        >
          <el-icon size="20" :class="{ 'animate-spin': loading }">
            <Search v-if="!loading" />
            <Loading v-else />
          </el-icon>
          <input
            v-focus
            placeholder="输入单词自动搜索..."
            type="text"
            v-model="query.word"
            class="w-full h-full text-sm border-none p-2 focus:outline-none"
          />
        </div>

        <div
          v-if="wordList.list.length > 0"
          class="bg-white max-h-[500px] border-t border-gray-100 overflow-y-auto rounded-b-[10px] shadow-xl"
        >
          <div
            @click="copyWord(item.word)"
            v-for="item in wordList.list"
            :key="item.id"
            class="hover:bg-blue-50 text-gray-800 p-4 cursor-pointer border-b border-gray-50 last:border-none transition-colors"
          >
            <div class="text-sm font-semibold text-blue-600 mb-1">{{ item.word }}</div>
            <div
              v-html="item.translation"
              class="text-sm text-gray-700 mb-1 overflow-hidden line-clamp-2"
            />
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
