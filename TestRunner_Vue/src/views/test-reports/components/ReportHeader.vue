<template>
  <div class="tw-bg-gray-800/50 tw-backdrop-blur-sm tw-border-b tw-border-gray-700/50 tw-sticky tw-top-0 tw-z-10">
    <div class="tw-px-6 tw-py-4">
      <div class="tw-flex tw-items-center tw-justify-between">
        <div class="tw-flex tw-items-center tw-gap-4">
          <a-button class="custom-back-button" @click="$emit('back')">
            <template #icon><icon-left /></template>
            返回
          </a-button>
          <div>
            <h2 class="tw-text-xl tw-font-medium tw-text-gray-100">{{ report?.name }}</h2>
            <div class="tw-flex tw-items-center tw-gap-2 tw-mt-1">
              <icon-code class="tw-text-gray-400" />
              <span class="tw-text-gray-400">{{ report?.testcase_name }}</span>
            </div>
          </div>
        </div>
        <div class="tw-flex tw-items-center tw-gap-4">
          <div class="tw-flex tw-flex-col tw-items-end">
            <a-tag :color="getStatusColor(report?.status)" size="medium">
              {{ getStatusText(report?.status) }}
            </a-tag>
            <span class="tw-text-xs tw-text-gray-400 tw-mt-1">执行时长: {{ formatDuration(report?.duration) }}</span>
          </div>
          <a-button type="outline" status="success" @click="$emit('export')">
            <template #icon><icon-download /></template>
            导出报告
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { IconLeft, IconCode, IconDownload } from '@arco-design/web-vue/es/icon'
import { formatDuration } from '@/utils/format'
import type { TestReportResponse } from '../detail.vue'

defineProps<{
  report: TestReportResponse | null
  loading: boolean
}>()

defineEmits<{
  (e: 'back'): void
  (e: 'export'): void
}>()

const getStatusColor = (status?: string) => {
  const statusMap: Record<string, string> = {
    success: 'green',
    failure: 'red',
    error: 'orange',
  }
  return statusMap[status || ''] || 'gray'
}

const getStatusText = (status?: string) => {
  const statusMap: Record<string, string> = {
    success: '成功',
    failure: '失败',
    error: '错误',
  }
  return statusMap[status || ''] || '未知'
}
</script>

<style scoped>
.custom-back-button {
  @apply !tw-bg-gray-700/50 !tw-border-gray-600 !tw-text-gray-300;
  
  &:hover {
    @apply !tw-bg-gray-700 !tw-border-gray-500 !tw-text-gray-200;
  }
  
  &:active {
    @apply !tw-bg-gray-800 !tw-border-gray-600 !tw-text-gray-300;
  }
}
</style> 