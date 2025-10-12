<script setup lang="ts">
import { ref, watch } from 'vue'
import { IconDelete, IconPlus, IconUpload } from '@arco-design/web-vue/es/icon'
import type { ApiInterface } from '@/api/interface'
import MonacoEditor from '@/components/MonacoEditor.vue'

interface Props {
  body?: ApiInterface['body']
}

const props = withDefaults(defineProps<Props>(), {
  body: () => ({ type: 'none', content: null })
})

const emit = defineEmits(['update:body'])

// 请求体类型
type BodyType = 'none' | 'form-data' | 'x-www-form-urlencoded' | 'raw' | 'binary'
const bodyType = ref<BodyType>(props.body?.type || 'none')

// 请求体内容
const bodyContent = ref<any>(null)

// raw 类型的语言选择
const rawLanguage = ref('json')

// 表单数据列表
const formDataList = ref<{ key: string, value: string, description: string, enabled: boolean }[]>([
  { key: '', value: '', description: '', enabled: true }
])

// 初始化表单数据
const initFormData = () => {
  if (props.body?.content) {
    if (Array.isArray(props.body.content)) {
      formDataList.value = [...props.body.content]
    } else if (typeof props.body.content === 'object') {
      formDataList.value = Object.entries(props.body.content).map(([key, value]) => ({
        key,
        value: typeof value === 'string' ? value : JSON.stringify(value),
        description: '',
        enabled: true
      }))
    }
  }
  // 确保至少有一个空行
  if (formDataList.value.length === 0) {
    formDataList.value = [{ key: '', value: '', description: '', enabled: true }]
  }
}

// 监听请求体变化
watch(() => props.body, (newBody) => {
  if (newBody) {
    bodyType.value = newBody.type || 'none'
    
    if (newBody.type === 'form-data' || newBody.type === 'x-www-form-urlencoded') {
      formDataList.value = []
      initFormData()
    } else if (newBody.type === 'raw') {
      formDataList.value = [{ key: '', value: '', description: '', enabled: true }]
      if (typeof newBody.content === 'object') {
        bodyContent.value = JSON.stringify(newBody.content, null, 2)
        rawLanguage.value = 'json'
      } else {
        bodyContent.value = newBody.content
        try {
          JSON.parse(newBody.content)
          rawLanguage.value = 'json'
        } catch {
          rawLanguage.value = 'text'
        }
      }
    } else if (newBody.type === 'binary') {
      formDataList.value = [{ key: '', value: '', description: '', enabled: true }]
      if (newBody.content) {
        bodyContent.value = newBody.content
      } else {
        bodyContent.value = null
      }
    } else {
      bodyContent.value = null
      formDataList.value = [{ key: '', value: '', description: '', enabled: true }]
    }
  }
}, { immediate: true, deep: true })

// 监听请求体类型变化
watch(bodyType, (newType, oldType) => {
  // 保存当前数据
  const currentBody = getBody()

  // 根据新类型初始化数据
  if (newType === 'none') {
    bodyContent.value = null
    formDataList.value = [{ key: '', value: '', description: '', enabled: true }]
  } else if (newType === 'form-data' || newType === 'x-www-form-urlencoded') {
    bodyContent.value = null
    // 如果之前是相同类型，保留数据
    if (props.body?.type === newType) {
      initFormData()
    } else {
      formDataList.value = [{ key: '', value: '', description: '', enabled: true }]
    }
  } else if (newType === 'raw') {
    formDataList.value = [{ key: '', value: '', description: '', enabled: true }]
    // 如果之前是 raw 类型，保留数据
    if (props.body?.type === 'raw') {
      bodyContent.value = props.body.content
    } else {
      bodyContent.value = rawLanguage.value === 'json' ? '{}' : ''
    }
  } else if (newType === 'binary') {
    formDataList.value = [{ key: '', value: '', description: '', enabled: true }]
    // 如果之前是 binary 类型，保留数据
    if (props.body?.type === 'binary') {
      bodyContent.value = props.body.content
    } else {
      bodyContent.value = null
    }
  }

  // 发送更新事件
  emit('update:body', {
    type: newType,
    content: getBody().content
  })
})

// 添加表单字段
const addFormField = () => {
  formDataList.value.push({ key: '', value: '', description: '', enabled: true })
}

// 删除表单字段
const deleteFormField = (index: number) => {
  formDataList.value.splice(index, 1)
  if (formDataList.value.length === 0) {
    formDataList.value.push({ key: '', value: '', description: '', enabled: true })
  }
}

// 获取请求体
const getBody = () => {
  if (bodyType.value === 'none') {
    return {
      type: 'none',
      content: null
    }
  }

  if (bodyType.value === 'form-data' || bodyType.value === 'x-www-form-urlencoded') {
    const formData: Record<string, string> = {}
    for (const item of formDataList.value) {
      if (item.enabled && item.key) {
        formData[item.key] = item.value
      }
    }
    return {
      type: bodyType.value,
      content: formData
    }
  }

  if (bodyType.value === 'raw') {
    let content = bodyContent.value
    if (rawLanguage.value === 'json' && typeof content === 'string') {
      try {
        content = JSON.parse(content)
      } catch (e) {
        console.warn('JSON 解析失败:', e)
      }
    }
    return {
      type: 'raw',
      content
    }
  }

  if (bodyType.value === 'binary') {
    return {
      type: 'binary',
      content: bodyContent.value
    }
  }

  return {
    type: 'none',
    content: null
  }
}

// 导出方法供父组件调用
defineExpose({
  getBody
})
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col">
    <!-- 顶部类型选择 -->
    <div class="tw-flex-shrink-0 tw-bg-gray-800 tw-border-b tw-border-gray-700">
      <a-radio-group v-model="bodyType" type="button" class="tw-p-4 tw-w-full">
        <a-radio value="none">none</a-radio>
        <a-radio value="form-data">form-data</a-radio>
        <a-radio value="x-www-form-urlencoded">x-www-form-urlencoded</a-radio>
        <a-radio value="raw">raw</a-radio>
        <a-radio value="binary">binary</a-radio>
      </a-radio-group>
    </div>

    <!-- 内容区域 -->
    <div class="tw-flex-1 tw-min-h-0 tw-p-4">
      <!-- form-data输入 -->
      <div v-if="bodyType === 'form-data' || bodyType === 'x-www-form-urlencoded'" class="tw-h-[400px] tw-flex tw-flex-col">
        <div class="tw-flex-1 tw-min-h-0 tw-overflow-y-auto tw-space-y-2">
          <div v-for="(field, index) in formDataList" :key="index" class="tw-flex tw-items-center tw-gap-2">
            <a-checkbox v-model="field.enabled" />
            <a-input
              v-model="field.key"
              placeholder="Key"
              allow-clear
              class="!tw-w-[200px]"
            />
            <a-input
              v-model="field.value"
              placeholder="Value"
              allow-clear
              class="!tw-w-[200px]"
            />
            <a-input
              v-model="field.description"
              placeholder="Description"
              allow-clear
              class="!tw-flex-1"
            />
            <a-button
              type="text"
              status="danger"
              @click="deleteFormField(index)"
            >
              <template #icon><icon-delete /></template>
            </a-button>
          </div>
        </div>
        <div class="tw-flex-shrink-0 tw-mt-2">
          <a-button type="outline" @click="addFormField">
            <template #icon><icon-plus /></template>
            添加字段
          </a-button>
        </div>
      </div>

      <!-- raw输入 -->
      <div v-if="bodyType === 'raw'" class="tw-flex-1 tw-min-h-0">
        <div class="tw-h-full tw-flex tw-flex-col tw-gap-2">
          <div class="tw-flex-shrink-0">
            <a-radio-group v-model="rawLanguage" type="button" size="small">
              <a-radio value="json">JSON</a-radio>
              <a-radio value="text">Text</a-radio>
              <a-radio value="javascript">JavaScript</a-radio>
              <a-radio value="html">HTML</a-radio>
              <a-radio value="xml">XML</a-radio>
            </a-radio-group>
          </div>
          <div class="tw-flex-1">
            <monaco-editor
              v-model="bodyContent"
              :language="rawLanguage"
              theme="vs-dark"
              class="tw-min-h-[100px]"
            />
          </div>
        </div>
      </div>

      <!-- binary文件上传 -->
      <div v-if="bodyType === 'binary'" class="tw-h-[400px] tw-flex tw-justify-center tw-items-center">
        <div class="tw-relative">
          <a-upload
            action="/"
            :auto-upload="false"
            :limit="1"
            @change="(fileList) => bodyContent = fileList[0]"
          >
            <template #upload-button>
              <div class="tw-border-2 tw-border-dashed tw-border-gray-600 tw-rounded-lg tw-p-4 tw-text-center">
                <p class="tw-text-gray-400">点击或拖拽文件到此处上传</p>
              </div>
            </template>
          </a-upload>
          <div v-if="bodyContent" class="tw-text-gray-400 tw-mt-4 tw-text-center">
            已选择文件: {{ bodyContent.file?.name }} ({{ (bodyContent.file?.size / 1024).toFixed(2) }} KB)
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="postcss" scoped>
:deep(.arco-radio-group-button) {
  @apply tw-bg-gray-900/60 tw-border-gray-700;
  
  .arco-radio-button {
    @apply tw-border-gray-700 tw-text-gray-400;
    
    &.arco-radio-button-checked {
      @apply tw-text-blue-500 tw-bg-blue-500/10;
    }
  }
}

:deep(.arco-input-wrapper) {
  @apply tw-bg-gray-900/60 tw-border-gray-700 !tw-h-[32px];
  
  input {
    @apply tw-text-gray-200 tw-bg-transparent;
    &::placeholder {
      @apply tw-text-gray-500;
    }
  }
}

:deep(.arco-checkbox) {
  @apply tw-text-gray-400;
}

:deep(.arco-btn-outline) {
  @apply tw-border-gray-600 tw-text-gray-300;
  
  &:hover {
    @apply tw-border-blue-500 tw-text-blue-500;
  }
}

:deep(.arco-btn-text) {
  @apply tw-text-gray-400;
  
  &:hover {
    @apply tw-text-red-500 tw-bg-red-500/10;
  }
}

:deep(.arco-upload) {
  @apply tw-border tw-border-gray-700 tw-rounded tw-p-4 tw-bg-gray-900/60;
}

:deep(.monaco-editor) {
  @apply tw-h-full tw-w-full;
  
  .margin,
  .monaco-editor-background {
    @apply tw-bg-gray-900/60;
  }
}

:deep(.monaco-editor .overflow-guard) {
  @apply tw-h-full tw-w-full;
}

:deep(.monaco-editor .monaco-scrollable-element) {
  @apply tw-h-full tw-w-full;
}

:deep(.monaco-editor .monaco-scrollable-element .monaco-editor-background) {
  @apply tw-bg-gray-900/60;
}

/* 隐藏滚动条但保留滚动效果 */
.tw-overflow-y-auto {
  scrollbar-width: none !important;
  -ms-overflow-style: none !important;
  &::-webkit-scrollbar {
    display: none !important;
  }
}

/* 恢复表单输入框的宽度 */
.tw-flex.tw-items-center.tw-gap-2 {
  .arco-input-wrapper:nth-child(2),
  .arco-input-wrapper:nth-child(3) {
    @apply !tw-w-[200px];
  }
  
  .arco-input-wrapper:nth-child(4) {
    @apply !tw-flex-1;
  }
}
</style> 