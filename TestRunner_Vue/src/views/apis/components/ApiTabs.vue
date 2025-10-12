<script setup lang="ts">
import { computed } from 'vue'
import { IconClose, IconPlus, IconSend } from '@arco-design/web-vue/es/icon'
import { useApiTabsStore } from '@/stores/apiTabs'
import type { ApiInterface } from '@/api/interface'

const props = defineProps<{
  currentInterface?: ApiInterface
}>()

const emit = defineEmits<{
  'tab-change': [tabId: string]
}>()

const tabsStore = useApiTabsStore()

// 计算属性
const tabs = computed(() => tabsStore.tabs)
const activeTabId = computed(() => tabsStore.activeTabId)

// 切换页签
const handleTabClick = (tabId: string) => {
  tabsStore.activateTab(tabId)
  emit('tab-change', tabId)
}

// 关闭页签
const handleCloseTab = (e: Event, tabId: string) => {
  e.stopPropagation()
  tabsStore.removeTab(tabId)
}


// 获取页签显示名称
const getTabLabel = (tab: any) => {
  const method = tab.method || 'GET'
  const name = tab.name || '新接口'
  return `${method} ${name}`
}

// 获取页签颜色
const getMethodColor = (method: string) => {
  switch (method?.toUpperCase()) {
    case 'GET': return 'tw-text-blue-500'
    case 'POST': return 'tw-text-green-500'
    case 'PUT': return 'tw-text-orange-500'
    case 'DELETE': return 'tw-text-red-500'
    case 'PATCH': return 'tw-text-purple-500'
    default: return 'tw-text-gray-400'
  }
}
</script>

<template>
  <!-- 独立的卡片样式容器 -->
  <div class="api-tabs-card tw-mx-0.5 tw-mb-2 tw-bg-gray-800 tw-rounded-lg tw-shadow-lg tw-overflow-hidden">
    <div class="tw-px-2 tw-py-2">
      <div class="tw-flex tw-items-center tw-gap-2 tw-overflow-x-auto tw-scrollbar-thin">
        <!-- 页签列表 -->
        <div
          v-for="tab in tabs"
          :key="tab.id"
          class="tw-group tw-flex tw-items-center tw-gap-2 tw-px-3 tw-py-2 tw-rounded-md tw-cursor-pointer tw-min-w-max tw-transition-all tw-border"
          :class="tab.id === activeTabId
            ? 'tw-bg-blue-500/20 tw-border-blue-500/50 tw-text-blue-400'
            : 'tw-bg-gray-700/30 tw-border-gray-700 tw-text-gray-300 hover:tw-bg-gray-700/50 hover:tw-border-gray-600'"
          @click="handleTabClick(tab.id)"
        >
          <!-- 请求方法标签 -->
          <span
            class="tw-text-xs tw-font-bold"
            :class="tab.id === activeTabId ? 'tw-opacity-100' : getMethodColor(tab.method)"
          >
            {{ tab.method }}
          </span>
          
          <!-- 接口名称 -->
          <span
            class="tw-text-sm tw-max-w-[180px] tw-truncate"
            :class="tab.id === activeTabId ? 'tw-font-medium' : ''"
            :title="tab.name"
          >
            {{ tab.name }}
          </span>
          
          <!-- 响应状态指示器 -->
          <div v-if="tab.response?.status" class="tw-flex tw-items-center">
            <div
              class="tw-w-2 tw-h-2 tw-rounded-full tw-animate-pulse"
              :class="{
                'tw-bg-green-500': tab.response.status >= 200 && tab.response.status < 300,
                'tw-bg-red-500': tab.response.status >= 400,
                'tw-bg-yellow-500': tab.response.status >= 300 && tab.response.status < 400
              }"
            ></div>
          </div>
          
          <!-- 关闭按钮 - 只显示X -->
          <icon-close
            class="tw-ml-1 tw-w-3.5 tw-h-3.5 tw-cursor-pointer tw-transition-all"
            :class="tab.id === activeTabId
              ? 'tw-opacity-60 hover:tw-opacity-100 hover:tw-text-red-400'
              : 'tw-opacity-0 group-hover:tw-opacity-60 group-hover:hover:tw-opacity-100 group-hover:hover:tw-text-red-400'"
            @click="handleCloseTab($event, tab.id)"
            title="关闭页签"
          />
        </div>
        
        <!-- 提示文本（当没有页签时显示） -->
        <div v-if="tabs.length === 0" class="tw-text-gray-500 tw-text-sm tw-py-1 tw-px-3">
          请从左侧选择或创建接口开始调试
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="postcss" scoped>
/* 自定义滚动条样式 */
.tw-scrollbar-thin {
  scrollbar-width: thin;
  scrollbar-color: rgba(156, 163, 175, 0.3) transparent;
}

.tw-scrollbar-thin::-webkit-scrollbar {
  height: 6px;
}

.tw-scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}

.tw-scrollbar-thin::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.3);
  border-radius: 3px;
}

.tw-scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background-color: rgba(156, 163, 175, 0.5);
}
</style>