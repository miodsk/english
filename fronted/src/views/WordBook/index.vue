<script setup lang="ts">
import {Reading, CollectionTag, Microphone } from '@element-plus/icons-vue'
import { type Response } from '@/apis'
import { getWordListApi } from '@/apis/word-book'
import { onMounted, ref } from 'vue'
import { type WordQuery, type WordList } from '@en/common/word'
import {useAudio,type Options} from '@/hooks/useAudio.ts'
// 1. 初始化 query，建议把布尔值字段显式声明
const { playAudio } = useAudio({
  rate:0.7,
  volume:1,
  pitch:1,
  lang:'en-US'
})
const query = ref<WordQuery>({
  page: 1,
  pageSize: 10, // 3列布局，建议用3的倍数
  word: '',
})

const wordList = ref<WordList>({
  list: [],
  total: 0,
})

const loading = ref(false)

const getWordList = async () => {
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

// 搜索处理函数：重置页码到第1页
const handleSearch = () => {
  query.value.page = 1
  getWordList()
}

onMounted(() => {
  getWordList()
})
</script>

<template>
  <div
    class="w-[1200px] mx-auto mt-10 bg-linear-to-br from-blue-50 to-indigo-50 rounded-[20px] p-10 shadow-lg min-h-[500px]"
  >
    <div class="mb-8">
      <div class="flex items-center gap-2 mb-2">
        <el-icon color="#2563EB" size="24"><Reading /></el-icon>
        <span class="text-2xl font-bold text-gray-800">词库列表</span>
      </div>
      <div class="text-sm text-gray-500">
        词典来源：牛津、高考、GRE、TOEFL、IELTS、四六级、考研等
      </div>
    </div>

    <div class="flex items-center flex-wrap gap-4 mb-8 bg-white/50 p-4 rounded-xl">
      <el-input
        v-model="query.word"
        placeholder="请输入单词，回车搜索"
        class="!w-[300px]"
        clearable
        @keyup.enter="handleSearch"
        @clear="handleSearch"
      ></el-input>

      <div class="flex items-center gap-3">
        <el-checkbox v-model="query.gk" @change="handleSearch">高考</el-checkbox>
        <el-checkbox v-model="query.zk" @change="handleSearch">中考</el-checkbox>
        <el-checkbox v-model="query.gre" @change="handleSearch">GRE</el-checkbox>
        <el-checkbox v-model="query.toefl" @change="handleSearch">TOEFL</el-checkbox>
        <el-checkbox v-model="query.ielts" @change="handleSearch">IELTS</el-checkbox>
        <el-checkbox v-model="query.cet6" @change="handleSearch">六级</el-checkbox>
        <el-checkbox v-model="query.cet4" @change="handleSearch">四级</el-checkbox>
        <el-checkbox v-model="query.ky" @change="handleSearch">考研</el-checkbox>
      </div>

      <el-button type="primary" @click="handleSearch" :loading="loading">搜索</el-button>
    </div>

    <div v-loading="loading">
      <div class="grid grid-cols-3 gap-6">
        <div
          v-for="item in wordList.list"
          :key="item.id"
          class="group relative bg-white h-[250px] flex flex-col border border-blue-100 rounded-[20px] p-5 cursor-pointer transition-all duration-300 shadow-sm hover:shadow-xl hover:-translate-y-1.5 hover:border-blue-300"
        >
          <div class="flex justify-between items-start mb-2">
            <div>
              <h3
                class="text-2xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors"
              >
                {{ item.word.startsWith('-') ? item.word.slice(1) : item.word }}
              </h3>
              <div class="flex items-center gap-2 mt-1">
                <span
                  v-if="item.pos"
                  class="text-xs font-bold px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded italic"
                >
                  {{ item.pos }}
                </span>
                <span class="text-sm text-gray-400 font-mono">/{{ item.phonetic }}/</span>
                <el-icon class="text-blue-400 hover:text-blue-600 transition-colors"
                  ><Microphone @click="playAudio(item.word)"
                /></el-icon>
              </div>
            </div>
            <div class="text-gray-300 group-hover:text-blue-200">
              <el-icon size="20"><CollectionTag /></el-icon>
            </div>
          </div>

          <div class="flex-grow overflow-hidden flex flex-col gap-3">
            <p
              v-if="item.definition"
              class="text-sm text-gray-500 line-clamp-2 leading-relaxed italic"
            >
              {{ item.definition }}
            </p>

            <div class="bg-slate-50 rounded-lg p-3 ">
              <div
                v-html="item.translation"
                class="text-sm text-gray-700 line-clamp-3 font-medium leading-normal"
              ></div>
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-gray-100 flex flex-wrap gap-1.5">
            <el-tag v-if="item.gk" size="small" effect="light" round>高考</el-tag>
            <el-tag v-if="item.zk" size="small" effect="light" round>中考</el-tag>
            <el-tag v-if="item.cet4" size="small" effect="light" type="info" round>四级</el-tag>
            <el-tag v-if="item.cet6" size="small" effect="light" type="info" round>六级</el-tag>
            <el-tag v-if="item.ky" size="small" effect="dark" type="danger" round>考研</el-tag>
            <el-tag v-if="item.ielts" size="small" effect="light" type="warning" round
              >IELTS</el-tag
            >

            <span
              v-if="!item.gk && !item.zk && !item.ky"
              class="text-[10px] text-gray-300 uppercase tracking-widest"
              >General Vocabulary</span
            >
          </div>
        </div>
      </div>

      <div class="mt-10 flex justify-center">
        <el-pagination
          background
          layout="total, prev, pager, next, sizes"
          v-model:current-page="query.page"
          v-model:page-size="query.pageSize"
          :total="wordList.total"
          @current-change="getWordList"
          @size-change="handleSearch"
        />
      </div>
    </div>
  </div>
</template>
