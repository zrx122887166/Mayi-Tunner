<script setup lang="ts">
import { ref, watch } from 'vue'
import { IconDelete, IconPlus } from '@arco-design/web-vue/es/icon'
import type { KeyValuePair } from '@/api/interface'

interface Props {
  params?: KeyValuePair[]
}

const props = defineProps<Props>()

const params = ref<KeyValuePair[]>([{ key: '', value: '', description: '', enabled: true }])

// 监听props变化
watch(() => props.params, (newParams) => {
  if (newParams && newParams.length > 0) {
    params.value = newParams
  } else {
    params.value = [{ key: '', value: '', description: '', enabled: true }]
  }
}, { immediate: true })

// 添加参数行
const addRow = () => {
  params.value.push({ key: '', value: '', description: '', enabled: true })
}

// 删除参数行
const removeRow = (index: number) => {
  params.value.splice(index, 1)
  // 如果删除后没有行了，添加一个空行
  if (params.value.length === 0) {
    params.value.push({ key: '', value: '', description: '', enabled: true })
  }
}

// 向父组件暴露参数数据
defineExpose({
  getParams: () => params.value.filter(param => param.key || param.value)
})
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-p-4 tw-space-y-2">
    <div class="tw-flex-1 tw-min-h-0 tw-overflow-y-auto tw-pr-2">
      <div class="tw-space-y-2">
        <div
          v-for="(param, index) in params"
          :key="index"
          class="tw-flex tw-items-center tw-gap-2"
        >
          <a-checkbox v-model="param.enabled" />
          <a-input
            v-model="param.key"
            placeholder="Key"
            allow-clear
          />
          <a-input
            v-model="param.value"
            placeholder="Value"
            allow-clear
          />
          <a-input
            v-model="param.description"
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