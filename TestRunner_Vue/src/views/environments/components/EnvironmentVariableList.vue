<script setup lang="ts">
import { ref } from 'vue'
import type { EnvironmentVariable } from '../../../api/environment'
import {
  IconCode,
  IconEdit,
  IconDelete,
  IconInfoCircle,
  IconLock,
} from '@arco-design/web-vue/es/icon'

interface Props {
  variables: EnvironmentVariable[]
}

interface Emits {
  (e: 'edit', index: number): void
  (e: 'delete', index: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const getTypeLabel = (type: string) => {
  const types = {
    text: '文本',
    number: '数字',
    boolean: '布尔值',
    json: 'JSON'
  }
  return types[type as keyof typeof types] || type
}
</script>

<template>
  <div class="tw-overflow-y-auto tw-max-h-[calc(100vh-24rem)]">
    <div
      v-for="(variable, index) in variables"
      :key="index"
      class="tw-flex tw-items-start tw-gap-3 tw-p-3 tw-bg-gray-900/60 tw-rounded-lg tw-border tw-border-gray-800/60 hover:tw-border-gray-700/60 tw-transition-colors tw-mb-2 tw-group"
    >
      <!-- 左侧图标 -->
      <div class="tw-w-8 tw-h-8 tw-rounded-lg tw-bg-purple-500/10 tw-flex tw-items-center tw-justify-center">
        <icon-code class="tw-text-purple-400" />
      </div>

      <!-- 中间内容 -->
      <div class="tw-flex-1 tw-min-w-0">
        <!-- 标题和描述 -->
        <div class="tw-mb-2">
          <div class="tw-flex tw-items-center tw-gap-2">
            <span class="tw-text-sm tw-font-medium tw-text-gray-300">变量 #{{ index + 1 }}</span>
            <span class="tw-text-xs tw-text-gray-500">·</span>
            <span class="tw-text-xs tw-text-gray-400 tw-truncate">{{ variable.description || '暂无描述' }}</span>
            <a-tag v-if="variable.is_sensitive" size="small" status="danger">
              <template #icon><icon-lock /></template>
              敏感
            </a-tag>
          </div>
        </div>

        <!-- 变量信息 -->
        <div class="tw-grid tw-grid-cols-3 tw-gap-4">
          <div class="tw-space-y-1">
            <div class="tw-text-xs tw-text-gray-400">变量名</div>
            <div class="tw-text-sm tw-text-gray-300 tw-truncate">{{ variable.name }}</div>
          </div>
          <div class="tw-space-y-1">
            <div class="tw-text-xs tw-text-gray-400">变量值</div>
            <div class="tw-text-sm tw-text-gray-300 tw-truncate">
              <span v-if="variable.is_sensitive">******</span>
              <span v-else>{{ variable.value }}</span>
            </div>
          </div>
          <div class="tw-space-y-1">
            <div class="tw-text-xs tw-text-gray-400">类型</div>
            <div class="tw-text-sm tw-text-gray-300">{{ getTypeLabel(variable.type) }}</div>
          </div>
        </div>
      </div>

      <!-- 右侧操作按钮 -->
      <div class="tw-flex tw-items-center tw-gap-2 tw-opacity-0 group-hover:tw-opacity-100 tw-transition-opacity">
        <a-button
          type="text"
          size="mini"
          @click="emit('edit', index)"
        >
          <template #icon><icon-edit class="tw-text-gray-400" /></template>
        </a-button>
        <a-button
          type="text"
          status="danger"
          size="mini"
          @click="emit('delete', index)"
        >
          <template #icon><icon-delete /></template>
        </a-button>
      </div>
    </div>
  </div>
</template> 