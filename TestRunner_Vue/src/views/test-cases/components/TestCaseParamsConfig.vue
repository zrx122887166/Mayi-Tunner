<script setup lang="ts">
import { ref, watch } from 'vue'
import { IconDelete, IconPlus } from '@arco-design/web-vue/es/icon'
import type { KeyValuePair } from '@/types/interface'

interface Props {
  params?: Record<string, any> | KeyValuePair[]
}

const props = withDefaults(defineProps<Props>(), {
  params: () => []
})

const emit = defineEmits(['update:params'])

// 参数列表
const paramsList = ref<KeyValuePair[]>([{ key: '', value: '', description: '', enabled: true }])

// 初始化参数列表
const initParamsList = () => {
  if (Array.isArray(props.params)) {
    paramsList.value = [...props.params]
  } else {
    paramsList.value = Object.entries(props.params || {}).map(([key, value]) => ({
      key,
      value: String(value),
      description: '',
      enabled: true
    }))
  }
  // 确保至少有一个空行
  if (paramsList.value.length === 0) {
    paramsList.value.push({ key: '', value: '', description: '', enabled: true })
  }
}

// 监听参数变化
watch(() => props.params, () => {
  initParamsList()
}, { immediate: true, deep: true })

// 添加参数
const addParam = () => {
  paramsList.value.push({ key: '', value: '', description: '', enabled: true })
}

// 删除参数
const deleteParam = (index: number) => {
  paramsList.value.splice(index, 1)
  // 确保至少有一个空行
  if (paramsList.value.length === 0) {
    paramsList.value.push({ key: '', value: '', description: '', enabled: true })
  }
}

// 获取参数列表
const getParams = () => {
  const params: Record<string, string> = {}
  for (const param of paramsList.value) {
    if (param.enabled && param.key) {
      params[param.key] = param.value
    }
  }
  return params
}

// 导出方法供父组件调用
defineExpose({
  getParams
})
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-p-4 tw-space-y-2">
    <div class="tw-flex-1 tw-min-h-0 tw-overflow-y-auto tw-pr-2">
      <div class="tw-space-y-2">
        <div
          v-for="(param, index) in paramsList"
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
            @click="deleteParam(index)"
          >
            <template #icon><icon-delete /></template>
          </a-button>
        </div>
      </div>
    </div>
    <div>
      <a-button type="outline" @click="addParam">
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