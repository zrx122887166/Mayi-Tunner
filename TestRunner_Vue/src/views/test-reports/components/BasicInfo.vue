<template>
  <div class="tw-bg-gray-900/50 tw-backdrop-blur-sm tw-rounded-lg tw-border tw-border-gray-700/30">
    <div class="tw-p-4 tw-border-b tw-border-gray-700/30">
      <h3 class="tw-text-lg tw-font-medium tw-text-gray-200">基本信息</h3>
    </div>
    <div class="tw-p-4">
      <div class="tw-grid tw-grid-cols-2 tw-gap-4">
        <!-- 左列 -->
        <div class="tw-space-y-3">
          <!-- 报告ID -->
          <div class="info-item">
            <icon-code class="tw-text-lg tw-text-gray-400" />
            <div class="tw-flex-1">
              <div class="tw-text-sm tw-text-gray-400">报告ID</div>
              <div class="tw-text-base tw-text-gray-200 tw-mt-1">{{ report?.id }}</div>
            </div>
          </div>
          
          <!-- 测试用例 -->
          <div class="info-item">
            <icon-code class="tw-text-lg tw-text-gray-400" />
            <div class="tw-flex-1">
              <div class="tw-text-sm tw-text-gray-400">测试用例</div>
              <div class="tw-text-base tw-text-gray-200 tw-mt-1">{{ report?.testcase_name }}</div>
              <div class="tw-text-sm tw-text-gray-400 tw-mt-1">用例ID: {{ report?.testcase }}</div>
            </div>
          </div>

          <!-- 开始时间 -->
          <div class="info-item">
            <icon-calendar class="tw-text-lg tw-text-gray-400" />
            <div class="tw-flex-1">
              <div class="tw-text-sm tw-text-gray-400">开始时间</div>
              <div class="tw-text-base tw-text-gray-200 tw-mt-1">{{ formatDateTime(report?.start_time) }}</div>
            </div>
          </div>
        </div>

        <!-- 右列 -->
        <div class="tw-space-y-3">
          <!-- 执行环境 -->
          <div class="info-item">
            <icon-desktop class="tw-text-lg tw-text-gray-400" />
            <div class="tw-flex-1">
              <div class="tw-text-sm tw-text-gray-400">执行环境</div>
              <div class="tw-text-base tw-text-gray-200 tw-mt-1">{{ report?.environment_info?.name }}</div>
              <div class="tw-text-sm tw-text-gray-400 tw-mt-1">环境ID: {{ report?.environment }}</div>
              <div class="tw-text-sm tw-text-gray-400 tw-mt-1">项目: {{ report?.environment_info?.project?.name }} (ID: {{ report?.environment_info?.project?.id }})</div>
              <div v-if="report?.environment_info?.base_url" class="tw-text-sm tw-text-blue-400 tw-font-mono tw-mt-1">
                Base URL: {{ report?.environment_info?.base_url }}
              </div>
              <div v-if="report?.environment_info?.description" class="tw-text-sm tw-text-gray-400 tw-mt-1">
                描述: {{ report?.environment_info?.description }}
              </div>
            </div>
          </div>

          <!-- 执行人 -->
          <div class="info-item">
            <icon-user class="tw-text-xl tw-text-gray-400" />
            <div class="tw-flex-1">
              <div class="tw-text-sm tw-text-gray-400">执行人</div>
              <div class="tw-text-base tw-text-gray-200 tw-mt-1">{{ report?.executed_by_info?.username }}</div>
              <div class="tw-text-sm tw-text-gray-400 tw-mt-1">用户ID: {{ report?.executed_by }}</div>
              <div class="tw-text-sm tw-text-gray-400 tw-mt-1">邮箱: {{ report?.executed_by_info?.email || '未设置' }}</div>
              <div v-if="report?.executed_by_info?.first_name || report?.executed_by_info?.last_name" class="tw-text-sm tw-text-gray-400 tw-mt-1">
                姓名: {{ [report?.executed_by_info?.first_name, report?.executed_by_info?.last_name].filter(Boolean).join(' ') }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { IconCalendar, IconDesktop, IconUser, IconInfoCircle, IconCode } from '@arco-design/web-vue/es/icon'
import { formatDateTime } from '@/utils/format'
import type { TestReportResponse } from '../detail.vue'

defineProps<{
  report: TestReportResponse | null
}>()
</script>

<style scoped>
.info-item {
  @apply tw-flex tw-items-start tw-gap-3 tw-p-3 tw-rounded-lg tw-bg-gray-800/30 tw-border tw-border-gray-700/30 tw-transition-all tw-duration-200;
  
  &:hover {
    @apply tw-bg-gray-800/50 tw-border-gray-600/50;
  }
}
</style> 