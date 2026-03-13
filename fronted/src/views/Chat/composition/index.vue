<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getCompositionHistoryDetailApi,
  gradeCompositionApi,
  listCompositionHistoryApi,
  reviseCompositionApi,
} from '@/apis/composition'
import { useUserStore } from '@/stores/user'
import type {
  CompositionHistoryMessage,
  CompositionHistoryThread,
  CompositionGradeResponse,
  CompositionReviseResponse,
  ExamType,
  TaskType,
} from '@en/common/chat/composition'

const userStore = useUserStore()

const examOptions: Array<{ label: string; value: ExamType }> = [
  { label: 'IELTS', value: 'ielts' },
  { label: 'CET-4', value: 'cet-4' },
  { label: 'CET-6', value: 'cet-6' },
  { label: '考研', value: 'kaoyan' },
]

const taskOptions: Array<{ label: string; value: TaskType }> = [
  { label: '议论文', value: 'opinion_essay' },
  { label: '信件', value: 'letter' },
  { label: '通知', value: 'notice' },
  { label: '图表', value: 'data_graph' },
  { label: '图片写作', value: 'image_drawing' },
  { label: '流程图', value: 'process_map' },
]

const form = reactive({
  topic: '',
  essayText: '',
  examType: 'ielts' as ExamType,
  taskType: 'opinion_essay' as TaskType,
})

const loading = ref(false)
const threadId = ref('')
const sessionId = ref(localStorage.getItem('composition_session_id') || crypto.randomUUID())

if (!localStorage.getItem('composition_session_id')) {
  localStorage.setItem('composition_session_id', sessionId.value)
}

const gradeResult = ref<CompositionGradeResponse | null>(null)
const reviseResult = ref<CompositionReviseResponse | null>(null)
const historyThreads = ref<CompositionHistoryThread[]>([])
const historyMessages = ref<CompositionHistoryMessage[]>([])
const historyLoading = ref(false)

const resolvedUserId = computed(() => {
  return userStore.getUser?.id || 'fronted-demo-user'
})

const ensureThreadId = () => {
  if (!threadId.value) {
    threadId.value = crypto.randomUUID()
  }
}

const validateInput = () => {
  if (!form.topic.trim()) {
    ElMessage.warning('请先输入作文题目')
    return false
  }

  if (!form.essayText.trim()) {
    ElMessage.warning('请先输入作文内容')
    return false
  }

  return true
}

const onGrade = async () => {
  if (!validateInput()) return

  loading.value = true
  reviseResult.value = null

  try {
    ensureThreadId()

    const data = await gradeCompositionApi({
      essay_text: form.essayText,
      exam_type: form.examType,
      task_type: form.taskType,
      topic: form.topic,
      user_id: resolvedUserId.value,
      thread_id: threadId.value,
      session_id: sessionId.value,
    })

    gradeResult.value = data
    threadId.value = data.thread_id
    await refreshHistory()
    await openHistoryThread(data.thread_id)
    ElMessage.success('首稿评分完成')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '首稿评分失败')
  } finally {
    loading.value = false
  }
}

const onRevise = async () => {
  if (!validateInput()) return

  if (!threadId.value) {
    ElMessage.warning('请先完成一次首稿评分，再提交改稿')
    return
  }

  loading.value = true

  try {
    const data = await reviseCompositionApi({
      revised_essay: form.essayText,
      thread_id: threadId.value,
      session_id: sessionId.value,
      user_id: resolvedUserId.value,
      topic: form.topic,
      exam_type: form.examType,
      task_type: form.taskType,
    })

    reviseResult.value = data
    gradeResult.value = data
    threadId.value = data.thread_id
    await refreshHistory()
    await openHistoryThread(data.thread_id)
    ElMessage.success('改稿评分完成')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '改稿评分失败')
  } finally {
    loading.value = false
  }
}

const onNewThread = () => {
  threadId.value = crypto.randomUUID()
  gradeResult.value = null
  reviseResult.value = null
  historyMessages.value = []
  ElMessage.success('已开启新作文线程')
}

const refreshHistory = async () => {
  historyLoading.value = true
  try {
    const data = await listCompositionHistoryApi(resolvedUserId.value)
    historyThreads.value = data.threads
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '获取历史失败')
  } finally {
    historyLoading.value = false
  }
}

const openHistoryThread = async (id: string) => {
  threadId.value = id
  try {
    const detail = await getCompositionHistoryDetailApi(id, resolvedUserId.value)
    historyMessages.value = detail.messages
    if (detail.topic) {
      form.topic = detail.topic
    }
    if (detail.exam_type) {
      form.examType = detail.exam_type
    }
    if (detail.task_type) {
      form.taskType = detail.task_type
    }
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '加载历史详情失败')
  }
}

onMounted(() => {
  refreshHistory()
})
</script>

<template>
  <div class="w-[1400px] mx-auto mt-8 grid grid-cols-[300px_2fr_1fr] gap-6">
    <el-card shadow="never">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-medium">历史消息</span>
          <el-button text size="small" @click="refreshHistory" :loading="historyLoading"
            >刷新</el-button
          >
        </div>
      </template>

      <div class="space-y-2 mb-4 max-h-[280px] overflow-y-auto">
        <div
          v-for="item in historyThreads"
          :key="item.thread_id"
          class="p-2 rounded border cursor-pointer transition-all"
          :class="
            threadId === item.thread_id
              ? 'border-purple-400 bg-purple-50'
              : 'border-gray-200 hover:border-purple-300'
          "
          @click="openHistoryThread(item.thread_id)"
        >
          <div class="text-xs text-gray-500">{{ item.updated_at }}</div>
          <div class="text-sm font-medium truncate">{{ item.topic || '未命名题目' }}</div>
          <div class="text-xs text-gray-600 mt-1 truncate">{{ item.preview || '暂无预览' }}</div>
        </div>
        <div v-if="!historyThreads.length" class="text-sm text-gray-500">暂无历史记录</div>
      </div>

      <div class="font-medium mb-2">消息明细</div>
      <div class="max-h-[320px] overflow-y-auto space-y-2">
        <div v-for="(msg, idx) in historyMessages" :key="idx" class="p-2 rounded bg-gray-50">
          <div class="text-xs text-gray-500">{{ msg.created_at }}</div>
          <div class="text-xs font-medium mb-1">{{ msg.role === 'user' ? '用户' : '助手' }}</div>
          <div class="text-sm whitespace-pre-wrap">{{ msg.content }}</div>
        </div>
        <div v-if="!historyMessages.length" class="text-sm text-gray-500">
          请选择左侧线程查看详情
        </div>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="font-medium">作文批改 Agent</span>
          <div class="text-xs text-gray-500">thread_id: {{ threadId || '未创建' }}</div>
        </div>
      </template>

      <el-form label-position="top">
        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="考试类型，目前只能选雅思，因为milvus只存了雅思范文">
            <el-select v-model="form.examType" class="w-full">
              <el-option
                v-for="item in examOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="任务类型">
            <el-select v-model="form.taskType" class="w-full">
              <el-option
                v-for="item in taskOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="作文题目">
          <el-input v-model="form.topic" placeholder="请输入作文题目" />
        </el-form-item>

        <el-form-item label="作文正文 / 修改稿正文">
          <el-input
            v-model="form.essayText"
            type="textarea"
            :rows="16"
            placeholder="请输入作文内容，改稿时直接在这里修改后点击“提交修改稿”"
          />
        </el-form-item>

        <div class="flex gap-3">
          <el-button type="primary" :loading="loading" @click="onGrade">首稿评分</el-button>
          <el-button type="success" :loading="loading" @click="onRevise">提交修改稿</el-button>
          <el-button :loading="loading" @click="onNewThread">新建作文线程</el-button>
        </div>
      </el-form>
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="font-medium">评分结果</div>
      </template>

      <div v-if="!gradeResult" class="text-sm text-gray-500">暂无结果，请先提交首稿评分。</div>

      <div v-else class="space-y-4 text-sm">
        <div class="grid grid-cols-2 gap-2">
          <div class="p-2 rounded bg-gray-50">总分：{{ gradeResult.band_score }}</div>
          <div class="p-2 rounded bg-gray-50">
            需继续修改：{{ gradeResult.needs_revision ? '是' : '否' }}
          </div>
          <div class="p-2 rounded bg-gray-50 col-span-2">
            当前步骤：{{ gradeResult.current_step || '-' }}
          </div>
        </div>

        <div v-if="reviseResult" class="p-3 rounded bg-green-50 border border-green-200">
          <div>上次分数：{{ reviseResult.previous_band_score }}</div>
          <div>本次分数：{{ reviseResult.band_score }}</div>
          <div>提升值：{{ reviseResult.delta }}</div>
          <div>是否进步：{{ reviseResult.improved ? '是' : '否' }}</div>
        </div>

        <div>
          <div class="font-medium mb-1">维度分数</div>
          <div class="space-y-1">
            <div
              v-for="(value, key) in gradeResult.scores"
              :key="key"
              class="p-2 rounded bg-gray-50"
            >
              {{ key }}: {{ value }}
            </div>
          </div>
        </div>

        <div>
          <div class="font-medium mb-1">错误检测</div>
          <div v-if="!gradeResult.errors?.length" class="p-2 rounded bg-gray-50">
            未检测到明显错误
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="(item, idx) in gradeResult.errors"
              :key="idx"
              class="p-2 rounded bg-gray-50 border border-gray-200"
            >
              <div><span class="font-medium">类型：</span>{{ item.type }}</div>
              <div><span class="font-medium">原文：</span>{{ item.original }}</div>
              <div><span class="font-medium">建议：</span>{{ item.suggestion }}</div>
              <div><span class="font-medium">原因：</span>{{ item.reason }}</div>
              <div><span class="font-medium">严重度：</span>{{ item.severity }}</div>
            </div>
          </div>
        </div>

        <div>
          <div class="font-medium mb-1">评分说明</div>
          <div class="whitespace-pre-wrap p-2 rounded bg-gray-50">
            {{ gradeResult.score_explanation || '-' }}
          </div>
        </div>

        <div>
          <div class="font-medium mb-1">改进建议</div>
          <ul class="list-disc pl-5 space-y-1">
            <li v-for="(item, idx) in gradeResult.suggestions" :key="idx">{{ item }}</li>
          </ul>
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped></style>
