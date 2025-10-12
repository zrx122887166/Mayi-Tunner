<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-gap-4 tw-p-4">
    <!-- 搜索区域 -->
    <div class="tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-px-6 tw-py-5 tw-flex tw-justify-between tw-items-center">
      <div class="tw-flex tw-items-center tw-gap-4">
        <a-input-search
          v-model="searchQuery"
          placeholder="搜索报告名称或用例名称"
          class="tw-w-64"
          allow-clear
          @search="handleSearch"
          @press-enter="handleSearch"
          @clear="handleSearch"
        />
        <a-select
          v-model="filterStatus"
          placeholder="执行状态"
          allow-clear
          @change="handleFilterChange"
          class="tw-w-32"
        >
          <a-option value="success">成功</a-option>
          <a-option value="failure">失败</a-option>
          <a-option value="error">错误</a-option>
        </a-select>
      </div>
    </div>

    <!-- 表格区域 -->
    <div class="tw-flex-1 tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-overflow-hidden tw-flex tw-items-center tw-justify-center">
      <a-spin :loading="loading" dot class="tw-h-full tw-w-full">
        <!-- 未选择项目的空状态 -->
        <div v-if="!currentProjectId" class="tw-h-full tw-w-full tw-flex tw-flex-col tw-items-center tw-justify-center tw-p-8 tw-text-center">
          <div class="tw-text-6xl tw-mb-6 tw-text-gray-600">
            <icon-apps class="tw-opacity-50" />
          </div>
          <h2 class="tw-text-2xl tw-font-medium tw-mb-2 tw-text-gray-300">请先选择项目</h2>
          <p class="tw-text-gray-500 tw-mb-8 tw-text-center tw-max-w-md">
            测试报告需要基于项目查看，请先从项目管理中选择一个项目
          </p>
          <a-button type="primary" size="large" @click="router.push('/projects')">
            选择项目
          </a-button>
        </div>
        
        <!-- 数据为空的提示 -->
        <div v-else-if="reports.length === 0 && !loading" class="tw-h-full tw-w-full tw-flex tw-flex-col tw-items-center tw-justify-center tw-p-8 tw-text-center">
          <div class="tw-text-6xl tw-mb-6 tw-text-gray-600">
            <icon-file class="tw-opacity-50" />
          </div>
          <h2 class="tw-text-2xl tw-font-medium tw-mb-2 tw-text-gray-300">暂无测试报告</h2>
          <p class="tw-text-gray-500 tw-mb-8 tw-text-center tw-max-w-md">
            当前项目尚未生成任何测试报告，请先执行测试用例
          </p>
        </div>
        
        <div v-else class="tw-h-full tw-w-full">
          <div class="table-container">
          <a-table
            :data="reports"
            :loading="loading"
            :pagination="false"
            :scroll="{ y: '100%' }"
            class="custom-table"
          >
            <template #columns>
              <a-table-column title="报告名称" data-index="name" :width="300" align="center">
                <template #cell="{ record }">
                  <div class="tw-flex tw-items-center tw-justify-center tw-gap-2">
                    <icon-file class="tw-text-blue-500 tw-flex-shrink-0" />
                    <a-link @click="viewReport(record.id)" class="tw-truncate">{{ record.name }}</a-link>
                  </div>
                </template>
              </a-table-column>
              <a-table-column title="用例名称" data-index="testcase_name" :width="250" align="center">
                <template #cell="{ record }">
                  <div class="tw-flex tw-items-center tw-justify-center tw-gap-2">
                    <icon-code class="tw-text-gray-400" />
                    <span class="tw-text-gray-300">{{ record.testcase_name }}</span>
                  </div>
                </template>
              </a-table-column>
              <a-table-column title="状态" data-index="status" align="center">
                <template #cell="{ record }">
                  <a-tag :color="getStatusColor(record.status)">
                    {{ getStatusText(record.status) }}
                  </a-tag>
                </template>
              </a-table-column>
              <a-table-column title="执行结果" align="center">
                <template #cell="{ record }">
                  <div class="tw-flex tw-items-center tw-gap-4 tw-justify-center">
                    <div class="tw-text-center">
                      <div class="tw-text-sm tw-font-medium tw-text-green-500">{{ record.success_count }}</div>
                      <div class="tw-text-xs tw-text-gray-400">成功</div>
                    </div>
                    <div class="tw-text-center">
                      <div class="tw-text-sm tw-font-medium tw-text-red-500">{{ record.fail_count }}</div>
                      <div class="tw-text-xs tw-text-gray-400">失败</div>
                    </div>
                    <div class="tw-text-center">
                      <div class="tw-text-sm tw-font-medium tw-text-orange-500">{{ record.error_count }}</div>
                      <div class="tw-text-xs tw-text-gray-400">错误</div>
                    </div>
                  </div>
                </template>
              </a-table-column>
              <a-table-column title="成功率" data-index="success_rate" align="center">
                <template #cell="{ record }">
                  <a-progress
                    :percent="record.success_rate"
                    size="small"
                    :stroke-width="4"
                    :color="getProgressColor(record.success_rate)"
                  />
                </template>
              </a-table-column>
              <a-table-column title="执行时间" data-index="start_time" :width="180" align="center">
                <template #cell="{ record }">
                  <span class="tw-text-gray-300">{{ formatDateTime(record.start_time) }}</span>
                </template>
              </a-table-column>
              <a-table-column title="执行时长" data-index="duration" align="center">
                <template #cell="{ record }">
                  <span class="tw-text-gray-300">{{ formatDuration(record.duration) }}</span>
                </template>
              </a-table-column>
              <a-table-column title="执行环境" data-index="environment_name" align="center">
                <template #cell="{ record }">
                  <a-tag color="arcoblue" size="small">{{ record.environment_name }}</a-tag>
                </template>
              </a-table-column>
              <a-table-column title="执行人" data-index="executed_by_name" align="center">
                <template #cell="{ record }">
                  <div class="tw-flex tw-items-center tw-justify-center tw-gap-1">
                    <icon-user class="tw-text-gray-400" />
                    <span class="tw-text-gray-300">{{ record.executed_by_name }}</span>
                  </div>
                </template>
              </a-table-column>
            </template>
          </a-table>
          </div>
        </div>
      </a-spin>
    </div>

    <!-- 分页区域 -->
    <div class="tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-px-6 tw-py-5">
      <a-pagination
        v-model:current="pagination.current"
        v-model:page_size="pagination.page_size"
        :total="pagination.total"
        show-total
        show-jumper
        show-page-size
        class="tw-flex tw-justify-end"
        @change="onPageChange"
        @page-size-change="onPageSizeChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { getTestReports } from '@/api/testreport'
import { formatDateTime, formatDuration } from '@/utils/format'
import { useProjectStore } from '@/stores/project'
import { 
  IconFile, 
  IconCode,
  IconUser,
  IconApps,
} from '@arco-design/web-vue/es/icon'

const router = useRouter()
const projectStore = useProjectStore()
const reports = ref([])
const loading = ref(false)
const searchQuery = ref('')
const filterStatus = ref('')

// 获取当前项目ID
const currentProjectId = computed(() => {
  return projectStore.currentProject?.id || null
})

const pagination = ref({
  total: 0,
  current: 1,
  page_size: 10,
  showTotal: true,
  showJumper: true,
  showPageSize: true,
})

const getStatusColor = (status: string) => {
  const statusMap: Record<string, string> = {
    success: 'green',
    failure: 'red',
    error: 'orange',
  }
  return statusMap[status] || 'gray'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    success: '成功',
    failure: '失败',
    error: '错误',
  }
  return statusMap[status] || '未知'
}

const getProgressColor = (rate: number) => {
  if (rate >= 0.9) return '#00B42A'
  if (rate >= 0.7) return '#FF7D00'
  return '#F53F3F'
}

const fetchReports = async () => {
  // 如果当前没有选择项目，则返回空列表
  if (!currentProjectId.value) {
    reports.value = []
    pagination.value.total = 0
    return
  }
  
  try {
    loading.value = true
    const response = await getTestReports({
      page: pagination.value.current,
      page_size: pagination.value.page_size,
      search: searchQuery.value,
      status: filterStatus.value || undefined,
      project: currentProjectId.value, // 添加项目ID过滤
    })
    reports.value = response.data.results
    pagination.value.total = response.data.count
  } catch (error) {
    Message.error('获取测试报告列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.value.current = 1
  fetchReports()
}

const handleFilterChange = () => {
  pagination.value.current = 1
  fetchReports()
}

const onPageChange = (current: number) => {
  pagination.value.current = current
  fetchReports()
}

const onPageSizeChange = (size: number) => {
  pagination.value.page_size = size
  pagination.value.current = 1
  fetchReports()
}

const viewReport = (id: number) => {
  router.push(`/test-reports/${id}`)
}

// 监听当前项目ID的变化，在变化时重新获取测试报告列表
watch(currentProjectId, (newProjectId, oldProjectId) => {
  if (newProjectId !== oldProjectId) {
    // 重置过滤条件
    searchQuery.value = ''
    filterStatus.value = ''
    
    // 重置分页
    pagination.value.current = 1
    pagination.value.page_size = 10
    
    // 重新获取测试报告
    fetchReports()
  }
}, { immediate: false })

onMounted(() => {
  fetchReports()
})

// 组件卸载时清理资源
onUnmounted(() => {
  // 如果有需要清理的资源，可以在这里添加
})
</script>

<style lang="postcss" scoped>
.table-container {
  @apply tw-h-full tw-w-full tw-flex tw-flex-col tw-min-h-0;
}

.custom-table {
  @apply tw-h-full;
}

.custom-table :deep(.arco-table-container) {
  @apply tw-h-full;
}

.custom-table :deep(.arco-table-content) {
  @apply tw-h-full;
}

.custom-table :deep(.arco-table-body) {
  @apply tw-h-full;
}

.custom-table :deep(.arco-table-header) {
  position: sticky;
  top: 0;
  z-index: 2;
}

.custom-table :deep(.arco-spin) {
  @apply tw-h-full tw-flex tw-flex-col;
}

.custom-table :deep(.arco-spin-children) {
  @apply tw-h-full tw-flex tw-flex-col;
}

.custom-table :deep(.arco-table-td) {
  background-color: transparent !important;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1) !important;
  color: #cbd5e1 !important;
  text-align: center !important;
}

.custom-table :deep(.arco-table-tr) {
  background-color: transparent !important;
}

.custom-table :deep(.arco-table-tr:hover) {
  background-color: rgba(30, 41, 59, 0.5) !important;
}

/* 分页样式 */
:deep(.arco-pagination) {
  .arco-pagination-item {
    border-radius: 6px !important;
    color: #94a3b8 !important;
    background-color: transparent !important;
    
    &:hover {
      color: #60a5fa !important;
      background-color: rgba(59, 130, 246, 0.1) !important;
    }
    
    &.arco-pagination-item-active {
      background-color: rgba(59, 130, 246, 0.2) !important;
      color: #60a5fa !important;
    }
  }

  .arco-pagination-jumper {
    .arco-input {
      border-radius: 6px !important;
      background-color: rgba(30, 41, 59, 0.5) !important;
      border-color: rgba(148, 163, 184, 0.1) !important;
      color: #e2e8f0 !important;

      &:hover, &:focus {
        border-color: #60a5fa !important;
      }
    }
  }

  .arco-pagination-total {
    color: #94a3b8 !important;
  }
}

/* 搜索框样式 */
:deep(.arco-input-wrapper) {
  background-color: rgba(30, 41, 59, 0.5) !important;
  border-color: rgba(148, 163, 184, 0.1) !important;

  &:hover, &:focus-within {
    border-color: #60a5fa !important;
  }

  .arco-input {
    color: #e2e8f0 !important;
  }

  .arco-input-prefix, .arco-input-suffix {
    color: #94a3b8 !important;
  }
}

/* 表格样式 */
.custom-table :deep(.arco-table-th) {
  background-color: rgba(30, 41, 59, 0.5) !important;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1) !important;
  color: #e2e8f0 !important;
  font-weight: 500 !important;
  text-align: center !important;
}
</style> 