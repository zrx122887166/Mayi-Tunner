<template>
  <div class="tw-bg-gray-900/50 tw-backdrop-blur-sm tw-rounded-lg tw-border tw-border-gray-700/30">
    <div class="tw-px-4 tw-py-3 tw-border-b tw-border-gray-700/30">
      <span class="tw-text-gray-300 tw-text-base tw-font-medium">执行日志</span>
    </div>
    <div class="tw-p-4">
      <div class="tw-bg-gray-800/30 tw-rounded-lg tw-border tw-border-gray-700/30 tw-transition-all tw-duration-200 hover:tw-bg-gray-800/50 hover:tw-border-gray-600/50">
        <pre class="tw-p-4 tw-text-sm tw-font-mono tw-text-gray-300 tw-overflow-x-auto tw-whitespace-pre-wrap">{{ report?.summary?.log }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TestReportResponse } from '../detail.vue'

defineProps<{
  report: TestReportResponse | null
}>()
</script>

<style scoped>
pre {
  scrollbar-width: none;
  -ms-overflow-style: none;
  &::-webkit-scrollbar {
    display: none;
  }
}
</style> 