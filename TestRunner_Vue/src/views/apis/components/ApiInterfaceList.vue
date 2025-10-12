<script setup lang="ts">
import { ref, computed } from 'vue'
import { IconSearch, IconSend, IconEdit, IconDelete, IconClockCircle } from '@arco-design/web-vue/es/icon'
import type { ApiInterface } from '@/api/interface'
import { formatRelativeTime, formatShortDateTime } from '@/utils/format'

interface Props {
  interfaces: ApiInterface[]
  loading?: boolean
  selectedInterfaceId?: number
  currentModuleName?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  interfaces: () => []
})

const emit = defineEmits<{
  'interface-select': [api: ApiInterface]
  'interface-edit': [api: ApiInterface]
  'interface-delete': [api: ApiInterface]
  'interface-run': [api: ApiInterface]
}>()

// 搜索关键字
const searchKeyword = ref('')

// 过滤后的接口列表
const filteredInterfaces = computed(() => {
  if (!searchKeyword.value) return props.interfaces
  
  const keyword = searchKeyword.value.toLowerCase()
  return props.interfaces.filter(item =>
    item.name.toLowerCase().includes(keyword) ||
    item.url.toLowerCase().includes(keyword) ||
    item.method.toLowerCase().includes(keyword)
  )
})

// 处理接口点击
const handleRowClick = (record: any) => {
  emit('interface-select', record as ApiInterface)
}

// 获取方法颜色
const getMethodColor = (method: string) => {
  const colors: Record<string, string> = {
    GET: 'green',
    POST: 'blue',
    PUT: 'orange',
    DELETE: 'red',
    PATCH: 'arcoblue',
    HEAD: 'purple',
    OPTIONS: 'cyan'
  }
  return colors[method] || 'gray'
}
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col">
    <!-- 搜索区域 -->
    <div class="tw-p-4">
      <div class="tw-flex tw-items-center tw-justify-between">
        <div class="tw-flex tw-items-center tw-gap-3">
          <span class="tw-text-gray-300">{{ currentModuleName || '全部接口' }}</span>
          <a-tag size="small">{{ filteredInterfaces.length }} 个接口</a-tag>
        </div>
        <a-input-search
          v-model="searchKeyword"
          placeholder="搜索接口名称、URL或方法"
          class="tw-w-64"
          allow-clear
        />
      </div>
    </div>

    <!-- 表格区域 -->
    <div class="tw-flex-1 tw-overflow-hidden">
      <a-spin :loading="loading" dot class="tw-h-full">
        <a-table
          :data="filteredInterfaces"
          :pagination="false"
          :scroll="{ y: 'calc(100vh - 360px)' }"
          class="custom-table"
          row-key="id"
          :row-class="(record) => record.id === selectedInterfaceId ? 'selected-row' : ''"
          @row-click="handleRowClick"
        >
          <template #columns>
            <a-table-column title="ID" data-index="id" :width="70" align="center" />
            <a-table-column title="请求方法" data-index="method" :width="100" align="center">
              <template #cell="{ record }">
                <a-tag
                  :color="getMethodColor(record.method)"
                  size="small"
                  class="!tw-font-medium"
                >
                  {{ record.method }}
                </a-tag>
              </template>
            </a-table-column>
            <a-table-column title="接口名称" data-index="name" align="center">
              <template #cell="{ record }">
                <span class="tw-cursor-pointer hover:tw-text-blue-400">{{ record.name }}</span>
              </template>
            </a-table-column>
            <a-table-column title="URL" data-index="url">
              <template #cell="{ record }">
                <span class="tw-text-gray-400">{{ record.url }}</span>
              </template>
            </a-table-column>
            <a-table-column title="创建时间" data-index="created_time" :width="150" align="center">
              <template #cell="{ record }">
                <a-tooltip v-if="record.created_time" :content="formatShortDateTime(record.created_time)">
                  <div class="tw-flex tw-items-center tw-gap-1 tw-justify-center">
                    <icon-clock-circle class="tw-text-gray-500" :size="14" />
                    <span class="tw-text-gray-400 tw-text-xs">
                      {{ formatRelativeTime(record.created_time) }}
                    </span>
                  </div>
                </a-tooltip>
                <span v-else class="tw-text-gray-400">-</span>
              </template>
            </a-table-column>
            <a-table-column title="更新时间" data-index="updated_time" :width="150" align="center">
              <template #cell="{ record }">
                <a-tooltip v-if="record.updated_time" :content="formatShortDateTime(record.updated_time)">
                  <div class="tw-flex tw-items-center tw-gap-1 tw-justify-center">
                    <icon-clock-circle class="tw-text-blue-400" :size="14" />
                    <span class="tw-text-gray-400 tw-text-xs">
                      {{ formatRelativeTime(record.updated_time) }}
                    </span>
                  </div>
                </a-tooltip>
                <span v-else class="tw-text-gray-400">-</span>
              </template>
            </a-table-column>
            <a-table-column title="操作" align="center" :width="150">
              <template #cell="{ record }">
                <div class="tw-flex tw-justify-center tw-gap-1">
                  <a-button
                    type="text"
                    size="mini"
                    @click.stop="$emit('interface-run', record)"
                    title="调试接口"
                  >
                    <template #icon><icon-send /></template>
                  </a-button>
                  <a-button
                    type="text"
                    size="mini"
                    @click.stop="$emit('interface-edit', record)"
                    title="编辑接口"
                  >
                    <template #icon><icon-edit /></template>
                  </a-button>
                  <a-button
                    type="text"
                    size="mini"
                    status="danger"
                    @click.stop="$emit('interface-delete', record)"
                    title="删除接口"
                  >
                    <template #icon><icon-delete /></template>
                  </a-button>
                </div>
              </template>
            </a-table-column>
          </template>
        </a-table>
      </a-spin>
    </div>
  </div>
</template>

<style lang="postcss" scoped>
.custom-table {
  @apply tw-h-full;
}

.custom-table :deep(.arco-table) {
  background-color: transparent !important;
}

.custom-table :deep(.arco-table-container) {
  background-color: transparent !important;
  border: none !important;
}

.custom-table :deep(.arco-table-body) {
  background-color: transparent !important;
}

/* 隐藏所有滚动条但保留滚动功能 */
.custom-table :deep(*::-webkit-scrollbar) {
  width: 0 !important;
  height: 0 !important;
  display: none !important;
}

/* Firefox */
.custom-table :deep(*) {
  scrollbar-width: none !important;
}

/* IE 和 Edge */
.custom-table :deep(*) {
  -ms-overflow-style: none !important;
}

.custom-table :deep(.arco-table-header) {
  background-color: rgba(30, 41, 59, 0.5) !important;
  position: sticky;
  top: 0;
  z-index: 2;
}

.custom-table :deep(.arco-table-content) {
  background-color: transparent !important;
}

.custom-table :deep(.arco-spin) {
  @apply tw-h-full tw-flex tw-flex-col;
}

.custom-table :deep(.arco-spin-children) {
  @apply tw-h-full tw-flex tw-flex-col;
}

/* 选中行样式 */
.custom-table :deep(.selected-row) {
  background-color: rgba(59, 130, 246, 0.1) !important;
}

.custom-table :deep(.arco-table-tr:hover) {
  background-color: rgba(59, 130, 246, 0.05) !important;
  cursor: pointer;
}

/* 空状态样式 */
:deep(.arco-empty) {
  @apply tw-text-gray-500;
}
</style>