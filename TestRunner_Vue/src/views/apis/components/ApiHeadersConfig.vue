<script setup lang="ts">
import { ref, watch } from 'vue'
import { IconDelete, IconPlus } from '@arco-design/web-vue/es/icon'
import type { KeyValuePair } from '@/api/interface'

interface Props {
  headers?: KeyValuePair[]
}

const props = defineProps<Props>()

const headers = ref<KeyValuePair[]>([{ key: '', value: '', description: '', enabled: true }])

// 监听props变化
watch(() => props.headers, (newHeaders) => {
  if (newHeaders && newHeaders.length > 0) {
    headers.value = newHeaders
  } else {
    headers.value = [{ key: '', value: '', description: '', enabled: true }]
  }
}, { immediate: true })

// 添加Header行
const addRow = () => {
  headers.value.push({ key: '', value: '', description: '', enabled: true })
}

// 删除Header行
const removeRow = (index: number) => {
  headers.value.splice(index, 1)
  // 如果删除后没有行了，添加一个空行
  if (headers.value.length === 0) {
    headers.value.push({ key: '', value: '', description: '', enabled: true })
  }
}

// 向父组件暴露headers数据
defineExpose({
  getHeaders: () => headers.value.filter(header => header.key || header.value)
})
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-p-4 tw-space-y-2">
    <div class="tw-flex-1 tw-min-h-0 tw-overflow-y-auto tw-pr-2">
      <div class="tw-space-y-2">
        <div
          v-for="(header, index) in headers"
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
            @click="removeRow(index)"
          >
            <template #icon><icon-delete /></template>
          </a-button>
        </div>
      </div>
    </div>
    <div>
      <a-button type="outline" @click="addRow">
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
</style>