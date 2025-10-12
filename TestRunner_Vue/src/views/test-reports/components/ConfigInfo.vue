<template>
  <div class="tw-bg-gray-900/50 tw-backdrop-blur-sm tw-rounded-lg tw-border tw-border-gray-700/30">
    <div class="tw-px-4 tw-pt-2 tw-border-b tw-border-gray-700/30">
      <h3 class="tw-text-lg tw-font-medium tw-text-gray-200 tw--mb-1">配置信息</h3>
    </div>
    <div class="tw-px-4">
      <div class="tw-space-y-3">
        <div class="config-item">
          <div class="tw-flex tw-items-center tw-justify-between tw-mb-2">
            <div class="tw-flex tw-items-center tw-gap-2">
              <p class="tw-text-sm tw-text-gray-400">配置变量</p>
              <span v-if="Object.keys(report?.summary?.in_out?.config_vars || {}).length" class="tw-text-xs tw-text-gray-500">
                ({{ Object.keys(report?.summary?.in_out?.config_vars || {}).length }}个)
              </span>
            </div>
            <div class="tw-flex tw-items-center tw-gap-2">
              <a-button 
                v-if="Object.keys(report?.summary?.in_out?.config_vars || {}).length" 
                type="text" 
                size="mini" 
                @click="toggleDrawer('config_vars')"
              >
                <template #icon><icon-expand class="tw-text-gray-400" /></template>
                查看全部
              </a-button>
              <a-tooltip position="left">
                <template #content>
                  <div class="tw-text-sm">
                    <p>测试执行时的环境配置变量</p>
                  </div>
                </template>
                <icon-info-circle class="tw-text-gray-400 tw-cursor-help" />
              </a-tooltip>
            </div>
          </div>
          <div v-if="Object.keys(report?.summary?.in_out?.config_vars || {}).length" class="tw-bg-gray-800/30 tw-rounded-lg tw-p-3 tw-border tw-border-gray-700/30">
            <div class="tw-space-y-2 tw-max-h-[200px] tw-overflow-y-auto">
              <div v-for="(value, key, index) in report?.summary?.in_out?.config_vars" :key="key" 
                   v-show="index < 3"
                   class="tw-flex tw-items-center tw-justify-between tw-px-2 tw-py-1 tw-rounded tw-bg-gray-800/30">
                <span class="tw-text-sm tw-text-gray-400">{{ key }}</span>
                <div class="tw-flex tw-items-center tw-gap-2">
                  <span class="tw-text-sm tw-text-blue-400 tw-font-mono" :title="value">{{ value && typeof value === 'string' ? (value.length > 20 ? value.substring(0, 20) + '...' : value) : value }}</span>
                  <a-button type="text" size="mini" @click="copyToClipboard(value)">
                    <template #icon><icon-copy class="tw-text-gray-400 hover:tw-text-blue-400" /></template>
                  </a-button>
                </div>
              </div>
              <div v-if="Object.keys(report?.summary?.in_out?.config_vars || {}).length > 3" class="tw-text-center tw-text-xs tw-text-gray-500 tw-mt-2">
                显示前3项，共{{ Object.keys(report?.summary?.in_out?.config_vars || {}).length }}项
              </div>
            </div>
          </div>
          <div v-else class="tw-bg-gray-800/30 tw-rounded-lg tw-p-3 tw-border tw-border-gray-700/30">
            <p class="tw-text-sm tw-text-gray-500 tw-text-center">无配置变量</p>
          </div>
        </div>
        <div class="config-item">
          <div class="tw-flex tw-items-center tw-justify-between tw-mb-2">
            <div class="tw-flex tw-items-center tw-gap-2">
              <p class="tw-text-sm tw-text-gray-400">提取变量</p>
              <span v-if="Object.keys(report?.summary?.in_out?.export_vars || {}).length" class="tw-text-xs tw-text-gray-500">
                ({{ Object.keys(report?.summary?.in_out?.export_vars || {}).length }}个)
              </span>
            </div>
            <div class="tw-flex tw-items-center tw-gap-2">
              <a-button 
                v-if="Object.keys(report?.summary?.in_out?.export_vars || {}).length" 
                type="text" 
                size="mini" 
                @click="toggleDrawer('export_vars')"
              >
                <template #icon><icon-expand class="tw-text-gray-400" /></template>
                查看全部
              </a-button>
              <a-tooltip position="left">
                <template #content>
                  <div class="tw-text-sm">
                    <p>测试执行过程中从响应中提取的变量</p>
                  </div>
                </template>
                <icon-info-circle class="tw-text-gray-400 tw-cursor-help" />
              </a-tooltip>
            </div>
          </div>
          <div v-if="Object.keys(report?.summary?.in_out?.export_vars || {}).length" class="tw-bg-gray-800/30 tw-rounded-lg tw-p-3 tw-border tw-border-gray-700/30">
            <div class="tw-space-y-2 tw-max-h-[200px] tw-overflow-y-auto">
              <div v-for="(value, key, index) in report?.summary?.in_out?.export_vars" :key="key" 
                   v-show="index < 3"
                   class="tw-flex tw-items-center tw-justify-between tw-px-2 tw-py-1 tw-rounded tw-bg-gray-800/30">
                <span class="tw-text-sm tw-text-gray-400">{{ key }}</span>
                <div class="tw-flex tw-items-center tw-gap-2">
                  <span class="tw-text-sm tw-text-green-400 tw-font-mono" :title="value">{{ value && typeof value === 'string' ? (value.length > 20 ? value.substring(0, 20) + '...' : value) : value }}</span>
                  <a-button type="text" size="mini" @click="copyToClipboard(value)">
                    <template #icon><icon-copy class="tw-text-gray-400 hover:tw-text-green-400" /></template>
                  </a-button>
                </div>
              </div>
              <div v-if="Object.keys(report?.summary?.in_out?.export_vars || {}).length > 3" class="tw-text-center tw-text-xs tw-text-gray-500 tw-mt-2">
                显示前3项，共{{ Object.keys(report?.summary?.in_out?.export_vars || {}).length }}项
              </div>
            </div>
          </div>
          <div v-else class="tw-bg-gray-800/30 tw-rounded-lg tw-p-3 tw-border tw-border-gray-700/30">
            <p class="tw-text-sm tw-text-gray-500 tw-text-center">无提取变量</p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 抽屉组件 - 用于显示完整的变量信息 -->
  <a-drawer
    :visible="drawerVisible"
    :width="800"
    @cancel="drawerVisible = false"
    :title="currentDrawerType === 'config_vars' ? '配置变量详情' : '提取变量详情'"
    :footer="false"
    class="custom-drawer"
    :mask="true"
    :mask-style="{ backgroundColor: 'transparent' }"
    :mask-closable="true"
    @close="drawerVisible = false"
  >
    <div class="tw-p-6">
      <div v-if="currentDrawerType === 'config_vars' && Object.keys(report?.summary?.in_out?.config_vars || {}).length" class="tw-space-y-3">
        <div v-for="(value, key) in report?.summary?.in_out?.config_vars" :key="key" class="tw-bg-gray-800/30 tw-rounded-lg tw-p-3 tw-border tw-border-gray-700/30">
          <div class="tw-flex tw-items-start tw-gap-3">
            <div class="tw-flex-1">
              <div class="tw-text-sm tw-text-gray-400">{{ key }}</div>
              <div class="tw-mt-2 tw-bg-gray-900/50 tw-p-2 tw-rounded tw-border tw-border-gray-700/30">
                <div class="tw-text-sm tw-text-blue-400 tw-font-mono tw-break-all">{{ value }}</div>
              </div>
            </div>
            <a-button type="text" size="mini" @click="copyToClipboard(value)">
              <template #icon><icon-copy class="tw-text-gray-400 hover:tw-text-blue-400" /></template>
            </a-button>
          </div>
        </div>
      </div>
      <div v-else-if="currentDrawerType === 'export_vars' && Object.keys(report?.summary?.in_out?.export_vars || {}).length" class="tw-space-y-3">
        <div v-for="(value, key) in report?.summary?.in_out?.export_vars" :key="key" class="tw-bg-gray-800/30 tw-rounded-lg tw-p-3 tw-border tw-border-gray-700/30">
          <div class="tw-flex tw-items-start tw-gap-3">
            <div class="tw-flex-1">
              <div class="tw-text-sm tw-text-gray-400">{{ key }}</div>
              <div class="tw-mt-2 tw-bg-gray-900/50 tw-p-2 tw-rounded tw-border tw-border-gray-700/30">
                <div class="tw-text-sm tw-text-green-400 tw-font-mono tw-break-all">{{ value }}</div>
              </div>
            </div>
            <a-button type="text" size="mini" @click="copyToClipboard(value)">
              <template #icon><icon-copy class="tw-text-gray-400 hover:tw-text-green-400" /></template>
            </a-button>
          </div>
        </div>
      </div>
      <div v-else class="tw-text-center tw-text-gray-400">
        无数据
      </div>
    </div>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { 
  IconInfoCircle, 
  IconCopy, 
  IconExpand 
} from '@arco-design/web-vue/es/icon'
import { Message } from '@arco-design/web-vue'
import type { TestReportResponse } from '../detail.vue'

defineProps<{
  report: TestReportResponse | null
}>()

// 抽屉组件状态控制
const drawerVisible = ref(false)
const currentDrawerType = ref<'config_vars' | 'export_vars' | null>(null)

/**
 * 切换抽屉的显示状态，并设置要显示的数据类型
 * @param type 数据类型（配置变量或提取变量）
 */
const toggleDrawer = (type: 'config_vars' | 'export_vars') => {
  currentDrawerType.value = type
  drawerVisible.value = true
}

/**
 * 将文本复制到剪贴板
 * @param text 要复制的文本
 */
const copyToClipboard = async (text: string) => {
  try {
    if (text === null || text === undefined) {
      Message.warning('复制内容为空')
      return
    }
    await navigator.clipboard.writeText(String(text))
    Message.success('复制成功')
  } catch (err) {
    Message.error('复制失败')
  }
}
</script>

<style scoped>
pre {
  scrollbar-width: none;
  -ms-overflow-style: none;
  &::-webkit-scrollbar {
    display: none;
  }
}

.config-item {
  @apply tw-transition-all tw-duration-200;

  &:hover {
    .tw-bg-gray-800\/30 {
      @apply tw-bg-gray-800/50 tw-border-gray-600/50;
    }
  }
}

/* 自定义滚动条样式 */
.tw-overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-color: rgba(107, 114, 128, 0.3) transparent;
  
  &::-webkit-scrollbar {
    width: 4px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background-color: rgba(107, 114, 128, 0.3);
    border-radius: 4px;
  }
}

/* 自定义抽屉组件样式 */
:deep(.custom-drawer) {
  .arco-drawer-container {
    @apply !tw-bg-transparent !important;
  }

  .arco-drawer-header {
    @apply !tw-bg-gray-900 !tw-border-b !tw-border-gray-700/30 !important;
    background-color: rgb(31, 41, 55) !important;
  }

  .arco-drawer-body {
    @apply !tw-bg-gray-900 !important;
    background-color: rgb(31, 41, 55) !important;
  }

  .arco-drawer-content {
    @apply !tw-bg-gray-900 !important;
    background-color: rgb(31, 41, 55) !important;
  }

  .arco-drawer-wrapper {
    @apply !tw-bg-gray-900 !important;
    background-color: rgb(31, 41, 55) !important;
  }
}

/* 全局样式覆盖 - 确保抽屉组件样式具有最高优先级 */
:global(.arco-drawer-container) {
  background-color: transparent !important;
}

:global(.arco-drawer-header),
:global(.arco-drawer-body),
:global(.arco-drawer-content),
:global(.arco-drawer-wrapper) {
  background-color: rgb(31, 41, 55) !important;
}
</style> 