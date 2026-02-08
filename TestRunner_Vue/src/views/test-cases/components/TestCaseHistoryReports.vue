<script setup lang="ts">
import { ref, onMounted, h, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Message, Tag as ATag, Button as AButton } from '@arco-design/web-vue'
import type { TableColumnData } from '@arco-design/web-vue'
import { getTestCaseHistoryReports, type TestCaseHistoryReport } from '@/api/testcase'
import dayjs from 'dayjs'

// 格式化执行时长
const formatDuration = (ms: number): string => {
  // 对毫秒值进行四舍五入，保留2位小数
  const roundedMs = Math.round(ms * 100) / 100
  
  if (roundedMs < 1) {
    return `${roundedMs.toFixed(2)}ms`
  }
  
  if (roundedMs < 1000) {
    return `${Math.round(roundedMs)}ms`
  }
  
  const seconds = Math.floor(roundedMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (hours > 0) {
    const remainingMinutes = minutes % 60
    const remainingSeconds = seconds % 60
    return `${hours}h ${remainingMinutes}m ${remainingSeconds}s`
  }
  
  if (minutes > 0) {
    const remainingSeconds = seconds % 60
    return `${minutes}m ${remainingSeconds}s`
  }
  
  return `${seconds}s`
}

const props = defineProps<{
  testcaseId: number
  pagination: {
    current: number
    pageSize: number
    total: number
    showTotal: boolean
    showJumper: boolean
    showPageSize: boolean
  }
}>()

const emit = defineEmits(['update:pagination'])

const router = useRouter()
const loading = ref(false)
const reports = ref<TestCaseHistoryReport[]>([])

// 表格列配置
const columns: TableColumnData[] = [
  {
    title: '#',
    width: 80,
    align: 'center' as const,
    render: (data) => {
      const currentPage = props.pagination.current
      const pageSize = props.pagination.pageSize
      return ((currentPage - 1) * pageSize + data.rowIndex + 1)
    }
  },
  {
    title: '报告ID',
    dataIndex: 'id',
    width: 80,
    align: 'center' as const
  },
  {
    title: '报告名称',
    dataIndex: 'name',
    ellipsis: true,
    align: 'center' as const
  },
  {
    title: '执行状态',
    dataIndex: 'status',
    width: 100,
    align: 'center' as const,
    render: (data) => h(ATag, {
      color: (data.record as TestCaseHistoryReport).status === 'success' ? 'green' :
            (data.record as TestCaseHistoryReport).status === 'failure' ? 'red' : 'orange'
    }, () => (data.record as TestCaseHistoryReport).status === 'success' ? '成功' :
           (data.record as TestCaseHistoryReport).status === 'failure' ? '失败' : '错误')
  },
  {
    title: '成功率',
    dataIndex: 'success_rate',
    width: 100,
    align: 'center' as const,
    render: (data) => `${Number((data.record as TestCaseHistoryReport).success_rate) * 100}%`
  },
  {
    title: '步骤统计',
    dataIndex: 'steps',
    width: 200,
    align: 'center' as const,
    render: (data) => {
      const record = data.record as TestCaseHistoryReport
      return h('div', {
        class: 'tw-flex tw-items-center tw-justify-center tw-gap-2'
      }, [
        h(ATag, { 
          color: 'green',
          class: record.success_count === 0 ? 'tw-opacity-50' : ''
        }, () => `成功: ${record.success_count}`),
        h(ATag, { 
          color: 'red',
          class: record.fail_count === 0 ? 'tw-opacity-50' : ''
        }, () => `失败: ${record.fail_count}`),
        h(ATag, { 
          color: 'orange',
          class: record.error_count === 0 ? 'tw-opacity-50' : ''
        }, () => `错误: ${record.error_count}`)
      ])
    }
  },
  {
    title: '执行时长',
    dataIndex: 'duration',
    width: 100,
    align: 'center' as const,
    render: (data) => formatDuration((data.record as TestCaseHistoryReport).duration)
  },
  {
    title: '执行时间',
    dataIndex: 'start_time',
    width: 180,
    align: 'center' as const,
    render: (data) => dayjs((data.record as TestCaseHistoryReport).start_time).format('YYYY-MM-DD HH:mm:ss')
  },
  {
    title: '执行环境',
    dataIndex: 'environment_name',
    width: 120,
    align: 'center' as const,
    render: (data) => (data.record as TestCaseHistoryReport).environment_name || '-'
  },
  {
    title: '操作',
    width: 120,
    align: 'center' as const,
    render: (data) => h('div', {
      class: 'tw-flex tw-items-center tw-justify-center tw-gap-2'
    }, [
      h(AButton, {
        type: 'text',
        size: 'small',
        onClick: () => handleViewDetail(data.record as TestCaseHistoryReport)
      }, () => '查看详情')
    ])
  }
]

// 获取历史报告列表
const fetchHistoryReports = async () => {
  try {
    loading.value = true
    const response = await getTestCaseHistoryReports(props.testcaseId, {
      page: props.pagination.current,
      page_size: props.pagination.pageSize
    })
    
    if (response && response.status === 'success') {
      const { data } = response
      reports.value = data.results || []
      emit('update:pagination', {
        ...props.pagination,
        total: data.count || 0
      })
    } else {
      throw new Error(response?.message || '获取历史报告列表失败')
    }
  } catch (error) {
    console.error('获取历史报告列表失败:', error)
    Message.error(error instanceof Error ? error.message : '获取历史报告列表失败')
    reports.value = []
  } finally {
    loading.value = false
  }
}

// 查看报告详情
const handleViewDetail = (report: TestCaseHistoryReport) => {
  router.push(`/test-reports/${report.id}`)
}

// 监听分页变化
watch(() => props.pagination.current, (newPage) => {
  fetchHistoryReports()
})

watch(() => props.pagination.pageSize, (newPageSize) => {
  fetchHistoryReports()
})

onMounted(() => {
  fetchHistoryReports()
})
</script>

<template>
  <div class="tw-h-full">
    <a-table
      :data="reports"
      :columns="columns"
      :loading="loading"
      :pagination="false"
      :bordered="false"
      :stripe="true"
    >
      <template #empty>
        <div class="tw-text-center tw-py-8 tw-text-gray-400">
          暂无历史报告
        </div>
      </template>
    </a-table>
  </div>
</template>

<style scoped>
:deep(.arco-table) {
  @apply !tw-bg-transparent;
  
  .arco-table-th {
    @apply !tw-bg-gray-800/30 !tw-text-gray-300 !tw-border-gray-700;
  }
  
  .arco-table-td {
    @apply !tw-bg-transparent !tw-text-gray-300 !tw-border-gray-700;
  }
  
  .arco-table-tr:hover .arco-table-td {
    @apply !tw-bg-gray-800/30;
  }
}

/* 分页样式 */
:deep(.arco-pagination) {
  .arco-pagination-item {
    border-radius: 4px !important;
    color: #94a3b8 !important;
    background-color: transparent !important;
    border: 1px solid transparent !important;
    
    &:hover {
      color: #60a5fa !important;
      background-color: rgba(59, 130, 246, 0.1) !important;
      border-color: rgba(59, 130, 246, 0.2) !important;
    }
    
    &.arco-pagination-item-active {
      background-color: rgba(59, 130, 246, 0.2) !important;
      color: #60a5fa !important;
      border-color: rgba(59, 130, 246, 0.3) !important;
    }
  }

  .arco-pagination-jumper {
    .arco-input {
      border-radius: 4px !important;
      background-color: rgba(30, 41, 59, 0.5) !important;
      border: 1px solid rgba(148, 163, 184, 0.1) !important;
      color: #e2e8f0 !important;

      &:hover, &:focus {
        border-color: rgba(59, 130, 246, 0.5) !important;
        background-color: rgba(30, 41, 59, 0.7) !important;
      }
    }
  }
}
</style> 