<!-- 测试用例关联接口弹窗 -->
<template>
  <div class="referenced-interfaces-dialog">
    <div v-if="visible" class="tw-fixed tw-inset-0 tw-z-[1000] tw-flex tw-items-center tw-justify-center">
      <!-- 遮罩层 -->
      <div class="tw-fixed tw-inset-0 tw-bg-black/60 tw-backdrop-blur-sm" @click="handleClose"></div>
      <!-- 卡片 -->
      <a-card 
        :bordered="false"
        class="dialog-card tw-w-[1000px] tw-max-h-[85vh] tw-relative tw-z-[1001]"
      >
        <template #title>
          <div class="tw-flex tw-justify-between tw-items-center">
            <span class="tw-text-gray-100 tw-text-lg tw-font-medium">测试用例「{{ testcaseName }}」关联接口</span>
            <a-button type="text" class="hover:tw-bg-gray-700/50 tw-rounded-lg" @click="handleClose">
              <template #icon>
                <icon-close />
              </template>
            </a-button>
          </div>
        </template>
        <div class="tw-flex tw-flex-col tw-h-[calc(85vh-120px)]">
          <a-spin :loading="loading" class="tw-flex-1 tw-min-h-0">
            <div class="tw-h-full tw-flex tw-flex-col">
              <div class="tw-flex-1 tw-overflow-auto">
                <a-table
                  :data="currentPageData"
                  :pagination="false"
                  :bordered="false"
                  size="small"
                  class="!tw-w-full custom-table"
                  :scroll="{ y: '100%' }"
                  :scrollbar="false"
                >
                  <template #columns>
                    <a-table-column title="序号" align="center" :width="80">
                      <template #cell="{ record }">
                        <div class="tw-flex tw-justify-center tw-items-center">
                          <a-tag>{{ record.step.order }}</a-tag>
                        </div>
                      </template>
                    </a-table-column>
                    <a-table-column title="步骤名称" align="center" :width="200">
                      <template #cell="{ record }">
                        <a-typography-paragraph :ellipsis="{ rows: 1 }" class="!tw-text-center">
                          {{ record.step.name }}
                        </a-typography-paragraph>
                      </template>
                    </a-table-column>
                    <a-table-column title="接口名称" align="center" :width="200">
                      <template #cell="{ record }">
                        <a-typography-paragraph :ellipsis="{ rows: 1 }" class="!tw-text-center">
                          {{ record.interface.name }}
                        </a-typography-paragraph>
                      </template>
                    </a-table-column>
                    <a-table-column title="请求方法" align="center" :width="100">
                      <template #cell="{ record }">
                        <div class="tw-flex tw-justify-center tw-items-center">
                          <a-tag :color="getMethodColor(record.interface.method)">
                            {{ record.interface.method }}
                          </a-tag>
                        </div>
                      </template>
                    </a-table-column>
                    <a-table-column title="接口地址" align="center" :width="200">
                      <template #cell="{ record }">
                        <a-typography-paragraph :ellipsis="{ rows: 1 }" class="!tw-text-center">
                          {{ record.interface.url }}
                        </a-typography-paragraph>
                      </template>
                    </a-table-column>
                    <a-table-column title="所属模块" align="center">
                      <template #cell="{ record }">
                        <span class="tw-block tw-text-center">{{ record.interface.module?.name || '-' }}</span>
                      </template>
                    </a-table-column>
                  </template>
                </a-table>
              </div>
              <!-- 分页器 -->
              <div v-if="interfaces?.length > 0" class="tw-flex tw-justify-end tw-pt-4 tw-mt-auto tw-border-t tw-border-gray-700">
                <a-pagination
                  v-model:current="currentPage"
                  :total="interfaces?.length || 0"
                  :page-size="pageSize"
                  show-total
                  show-page-size
                  :page-size-options="[10, 20, 50, interfaces?.length || 0]"
                  size="small"
                  @change="handlePageChange"
                  @page-size-change="handlePageSizeChange"
                />
              </div>
            </div>
          </a-spin>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, watch, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconClose } from '@arco-design/web-vue/es/icon'
import { getTestCaseReferencedInterfaces, type ReferencedInterface } from '@/api/testcase'

const props = defineProps<{
  visible: boolean
  testcaseId: number
  testcaseName: string
}>()

const emit = defineEmits<{
  (e: 'update:visible', visible: boolean): void
  (e: 'close'): void
}>()

const loading = ref(false)
const interfaces = ref<ReferencedInterface[]>([])
const currentPage = ref(1)
const pageSize = ref(10)

// 计算当前页数据
const currentPageData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return interfaces.value?.slice(start, end) || []
})

// 获取关联接口数据
const fetchReferencedInterfaces = async () => {
  try {
    loading.value = true
    const res = await getTestCaseReferencedInterfaces(props.testcaseId)
    if (res.status === 'success') {
      // 转换接口返回的数据结构为组件期望的结构
      interfaces.value = []
      if (res.data && Array.isArray(res.data)) {
        res.data.forEach(item => {
          if (item.steps && Array.isArray(item.steps)) {
            item.steps.forEach((step: {
              id: number;
              name: string;
              order: number;
              sync_fields: any[];
              last_sync_time: string | null;
            }) => {
              interfaces.value.push({
                interface: {
                  id: item.id,
                  name: item.name,
                  method: item.method,
                  url: item.url,
                  // 如果module是字符串，将其转换为对象格式
                  module: typeof item.module === 'string' 
                    ? { id: 0, name: item.module } 
                    : (item.module || null),
                  // 添加缺少的project属性
                  project: { id: props.testcaseId, name: props.testcaseName }
                },
                step: {
                  id: step.id,
                  name: step.name,
                  order: step.order
                }
              })
            })
          }
        })
      }
    } else {
      Message.error('获取关联接口失败')
    }
  } catch (error) {
    console.error('获取关联接口失败:', error)
    Message.error('获取关联接口失败')
  } finally {
    loading.value = false
  }
}

// 根据请求方法返回不同的颜色
const getMethodColor = (method: string) => {
  const colorMap: Record<string, string> = {
    GET: 'blue',
    POST: 'green',
    PUT: 'orange',
    DELETE: 'red',
    PATCH: 'purple'
  }
  return colorMap[method] || 'gray'
}

const handleClose = () => {
  emit('update:visible', false)
  emit('close')
}

// 处理页码变化
const handlePageChange = (page: number) => {
  currentPage.value = page
}

// 处理每页显示数量变化
const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

// 重置页码
const resetPagination = () => {
  currentPage.value = 1
}

// 修改监听器，重置分页
watch(
  () => props.visible,
  (newVal) => {
    if (newVal && props.testcaseId) {
      resetPagination()
      fetchReferencedInterfaces()
    } else {
      interfaces.value = []
    }
  }
)
</script>

<style scoped>
.referenced-interfaces-dialog {
  @apply tw-relative;
  z-index: 1000;
}

.dialog-card {
  @apply !tw-bg-gray-800 !tw-border-gray-700 tw-rounded-xl tw-overflow-hidden tw-flex tw-flex-col;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1), 0 8px 20px -4px rgba(0, 0, 0, 0.5) !important;
  animation: dialogSlideIn 0.2s ease-out;
}

@keyframes dialogSlideIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

:deep(.arco-card-header) {
  @apply !tw-border-gray-700 !tw-bg-gray-800/80 !tw-backdrop-blur-sm;
  padding: 16px 8px !important;
  border-bottom-width: 1px !important;
}

:deep(.arco-card-body) {
  @apply !tw-bg-gray-800/80 !tw-backdrop-blur-sm !tw-flex-1 !tw-overflow-hidden;
  padding: 16px 8px !important;
}

/* 表格样式 */
:deep(.arco-table) {
  background: transparent !important;
}

/* 表格容器样式 */
:deep(.arco-table-container) {
  @apply !tw-h-full;
  border: none !important;
  background: transparent !important;
}

:deep(.arco-table-body) {
  @apply !tw-h-full !tw-overflow-auto;
}

:deep(.arco-table-header) {
  @apply !tw-sticky !tw-top-0 !tw-z-10;
  border: none !important;
  background: rgba(31, 41, 55, 0.8) !important;
  backdrop-filter: blur(8px) !important;
}

:deep(.arco-table-size-small .arco-table-th) {
  padding: 8px 4px !important;
  white-space: nowrap !important;
  background: transparent !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #94a3b8 !important;
  font-weight: 500 !important;
  height: 36px !important;
  line-height: 20px !important;
}

:deep(.arco-table-size-small .arco-table-td) {
  padding: 8px 4px !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #e2e8f0 !important;
  background: transparent !important;
  height: 36px !important;
  line-height: 20px !important;
}

:deep(.arco-table-td), :deep(.arco-table-th) {
  @apply !tw-align-middle;
}

:deep(.arco-typography) {
  color: #e2e8f0 !important;
  margin-bottom: 0 !important;
}

/* 标签样式 */
:deep(.arco-tag) {
  border: none !important;
  font-weight: 500 !important;
  padding: 2px 8px !important;
  border-radius: 4px !important;
  font-size: 12px !important;
  line-height: 18px !important;
  transition: all 0.2s ease-in-out !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  min-width: 60px !important;
  
  &.arco-tag-blue {
    color: #60a5fa !important;
    background-color: rgba(59, 130, 246, 0.1) !important;
  }
  
  &.arco-tag-green {
    color: #4ade80 !important;
    background-color: rgba(74, 222, 128, 0.1) !important;
  }
  
  &.arco-tag-orange {
    color: #fb923c !important;
    background-color: rgba(251, 146, 60, 0.1) !important;
  }
  
  &.arco-tag-red {
    color: #f87171 !important;
    background-color: rgba(248, 113, 113, 0.1) !important;
  }
  
  &.arco-tag-purple {
    color: #c084fc !important;
    background-color: rgba(192, 132, 252, 0.1) !important;
  }
}

/* Loading 样式 */
:deep(.arco-spin) {
  .arco-spin-dot-list {
    .arco-spin-dot-item {
      background-color: #60a5fa !important;
    }
  }
}

/* 自定义表格样式 */
:deep(.custom-table) {
  .arco-table-body,
  .arco-scrollbar,
  .arco-scrollbar-container,
  .arco-table-body-wrapper,
  .arco-scrollbar__wrap,
  .arco-virtual-list,
  .arco-virtual-list-holder {
    &::-webkit-scrollbar {
      width: 0 !important;
      height: 0 !important;
      display: none !important;
    }
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
  }
}

/* 分页样式 */
:deep(.arco-pagination) {
  .arco-pagination-item {
    @apply !tw-bg-transparent !tw-border-gray-700 !tw-text-gray-400;
    
    &:hover {
      @apply !tw-border-blue-500 !tw-text-blue-500 !tw-bg-blue-500/10;
    }
    
    &.arco-pagination-item-active {
      @apply !tw-border-blue-500 !tw-text-blue-500 !tw-bg-blue-500/10;
    }
  }

  .arco-pagination-total {
    @apply !tw-text-gray-400;
  }

  .arco-select-view {
    @apply !tw-bg-transparent !tw-border-gray-700 !tw-text-gray-400;

    &:hover {
      @apply !tw-border-blue-500;
    }
  }

  .arco-pagination-jumper {
    .arco-input {
      @apply !tw-bg-transparent !tw-border-gray-700 !tw-text-gray-400;

      &:hover {
        @apply !tw-border-blue-500;
      }

      &:focus {
        @apply !tw-border-blue-500 !tw-ring-1 !tw-ring-blue-500/20;
      }
    }
  }
}
</style> 