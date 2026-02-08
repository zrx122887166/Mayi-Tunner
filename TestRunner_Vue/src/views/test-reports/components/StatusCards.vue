<template>
  <div class="tw-grid tw-grid-cols-5 tw-gap-4">
    <!-- 成功步骤 -->
    <div class="tw-bg-gray-900/50 tw-backdrop-blur-sm tw-border tw-border-gray-700/30 tw-rounded-lg tw-aspect-square">
      <div class="tw-h-full tw-flex tw-flex-col tw-items-center tw-justify-center tw-px-4">
        <icon-check-circle class="tw-text-5xl tw-text-green-500/70" />
        <p class="tw-text-green-400 tw-text-sm tw-mt-2">成功步骤</p>
        <h3 class="tw-text-3xl tw-font-semibold tw-text-green-500 tw-mt-1">{{ report?.success_count }}</h3>
        <p class="tw-text-gray-400 tw-text-xs tw-mt-1">占比 {{ Number(report?.success_rate || 0) * 100 }}%</p>
      </div>
    </div>

    <!-- 失败步骤 -->
    <div class="tw-bg-gray-900/50 tw-backdrop-blur-sm tw-border tw-border-gray-700/30 tw-rounded-lg tw-aspect-square">
      <div class="tw-h-full tw-flex tw-flex-col tw-items-center tw-justify-center tw-px-4">
        <icon-close-circle class="tw-text-5xl tw-text-red-500/70" />
        <p class="tw-text-red-400 tw-text-sm tw-mt-2">失败步骤</p>
        <h3 class="tw-text-3xl tw-font-semibold tw-text-red-500 tw-mt-1">{{ report?.fail_count }}</h3>
        <p class="tw-text-gray-400 tw-text-xs tw-mt-1">占比 {{ failRate }}%</p>
      </div>
    </div>

    <!-- 错误步骤 -->
    <div class="tw-bg-gray-900/50 tw-backdrop-blur-sm tw-border tw-border-gray-700/30 tw-rounded-lg tw-aspect-square">
      <div class="tw-h-full tw-flex tw-flex-col tw-items-center tw-justify-center tw-px-4">
        <icon-exclamation-circle class="tw-text-5xl tw-text-orange-500/70" />
        <p class="tw-text-orange-400 tw-text-sm tw-mt-2">错误步骤</p>
        <h3 class="tw-text-3xl tw-font-semibold tw-text-orange-500 tw-mt-1">{{ report?.error_count }}</h3>
        <p class="tw-text-gray-400 tw-text-xs tw-mt-1">占比 {{ errorRate }}%</p>
      </div>
    </div>

    <!-- 总步骤 -->
    <div class="tw-bg-gray-900/50 tw-backdrop-blur-sm tw-border tw-border-gray-700/30 tw-rounded-lg tw-aspect-square">
      <div class="tw-h-full tw-flex tw-flex-col tw-items-center tw-justify-center tw-px-4">
        <icon-list class="tw-text-5xl tw-text-blue-500/70" />
        <p class="tw-text-blue-400 tw-text-sm tw-mt-2">总步骤</p>
        <h3 class="tw-text-3xl tw-font-semibold tw-text-blue-500 tw-mt-1">{{ totalSteps }}</h3>
        <p class="tw-text-gray-400 tw-text-xs tw-mt-1">执行完成</p>
      </div>
    </div>

    <!-- 成功率卡片 -->
    <div class="tw-bg-gray-900/50 tw-backdrop-blur-sm tw-border tw-border-gray-700/30 tw-rounded-lg tw-aspect-square">
      <div class="tw-h-full tw-flex tw-flex-col tw-items-center tw-justify-center">
        <div class="tw-relative tw-w-24 tw-h-24">
          <!-- 背景圆环 -->
          <svg class="tw-w-full tw-h-full tw-transform tw--rotate-90">
            <circle
              cx="48"
              cy="48"
              r="44"
              stroke-width="8"
              stroke="rgba(75, 85, 99, 0.3)"
              fill="none"
              class="tw-stroke-current"
            />
            <!-- 进度圆环 -->
            <circle
              cx="48"
              cy="48"
              r="44"
              stroke-width="8"
              :stroke="progressColor"
              fill="none"
              class="tw-stroke-current"
              :style="{
                strokeDasharray: `${2 * Math.PI * 44}`,
                strokeDashoffset: `${2 * Math.PI * 44 * (1 - (report?.success_rate || 0))}`,
                transition: 'stroke-dashoffset 0.5s ease'
              }"
            />
          </svg>
          <!-- 中间的文字 -->
          <div class="tw-absolute tw-inset-0 tw-flex tw-flex-col tw-items-center tw-justify-center">
            <span class="tw-text-2xl tw-font-bold" :class="progressTextColor">
              {{ Math.round((report?.success_rate || 0) * 100) }}%
            </span>
            <span class="tw-text-xs tw-text-gray-400">成功率</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  IconCheckCircle,
  IconCloseCircle,
  IconExclamationCircle,
  IconList
} from '@arco-design/web-vue/es/icon'
import type { TestReportResponse } from '../detail.vue'

const props = defineProps<{
  report: TestReportResponse | null
  totalSteps: number
  failRate: number
  errorRate: number
}>()

const progressColor = computed(() => {
  const rate = props.report?.success_rate || 0
  if (rate >= 0.9) return '#22c55e' // 绿色
  if (rate >= 0.7) return '#f97316' // 橙色
  return '#ef4444' // 红色
})

const progressTextColor = computed(() => {
  const rate = props.report?.success_rate || 0
  if (rate >= 0.9) return 'tw-text-green-500'
  if (rate >= 0.7) return 'tw-text-orange-500'
  return 'tw-text-red-500'
})
</script>

<style scoped>
circle {
  transition: stroke-dashoffset 0.5s ease;
}

.tw-aspect-square {
  @apply tw-transition-all tw-duration-200;
  
  &:hover {
    @apply tw-bg-gray-900/70 tw-border-gray-600/50 tw-transform tw-scale-[1.02];
  }
}
</style> 