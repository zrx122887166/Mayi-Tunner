<script setup lang="ts">
import { ref, watch } from 'vue'
import { IconDelete, IconPlus } from '@arco-design/web-vue/es/icon'
import type { KeyValuePair } from '@/types/interface'

interface Props {
  headers?: Record<string, any> | KeyValuePair[]
}

const props = withDefaults(defineProps<Props>(), {
  headers: () => []
})

const emit = defineEmits(['update:headers'])

// 请求头列表
const headersList = ref<KeyValuePair[]>([{ key: '', value: '', description: '', enabled: true }])

// 初始化请求头列表
const initHeadersList = () => {
  if (Array.isArray(props.headers)) {
    headersList.value = [...props.headers]
  } else {
    headersList.value = Object.entries(props.headers || {}).map(([key, value]) => ({
      key,
      value: String(value),
      description: '',
      enabled: true
    }))
  }
  // 确保至少有一个空行
  if (headersList.value.length === 0) {
    headersList.value.push({ key: '', value: '', description: '', enabled: true })
  }
}

// 监听请求头变化
watch(() => props.headers, () => {
  initHeadersList()
}, { immediate: true, deep: true })

// 添加请求头
const addHeader = () => {
  headersList.value.push({ key: '', value: '', description: '', enabled: true })
}

// 删除请求头
const deleteHeader = (index: number) => {
  headersList.value.splice(index, 1)
  // 确保至少有一个空行
  if (headersList.value.length === 0) {
    headersList.value.push({ key: '', value: '', description: '', enabled: true })
  }
}

// 获取请求头列表
const getHeaders = () => {
  const headers: Record<string, string> = {}
  for (const header of headersList.value) {
    if (header.enabled && header.key) {
      headers[header.key] = header.value
    }
  }
  return headers
}

// 导出方法供父组件调用
defineExpose({
  getHeaders
})
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-p-4 tw-space-y-2">
    <div class="tw-flex-1 tw-min-h-0 tw-overflow-y-auto tw-pr-2">
      <div class="tw-space-y-2">
        <div
          v-for="(header, index) in headersList"
          :key="index"
          class="tw-flex tw-items-center tw-gap-2"
        >
          <a-checkbox v-model="header.enabled" />
          <a-input
            v-model="header.key"
            placeholder="Key"
            allow-clear
          />
          <a-input
            v-model="header.value"
            placeholder="Value"
            allow-clear
          />
          <a-input
            v-model="header.description"
            placeholder="Description"
            allow-clear
          />
          <a-button
            type="text"
            status="danger"
            @click="deleteHeader(index)"
          >
            <template #icon><icon-delete /></template>
          </a-button>
        </div>
      </div>
    </div>
    <div>
      <a-button type="outline" @click="addHeader">
        <template #icon><icon-plus /></template>
        添加参数
      </a-button>
    </div>
  </div>
</template>

<style lang="postcss" scoped>
:deep(.arco-input-wrapper) {
  @apply tw-bg-gray-900/60 tw-border-gray-700;
  
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
</style> 