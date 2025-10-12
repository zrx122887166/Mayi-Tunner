<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'
import { getTestCases, runTestCase, deleteTestCase, type TestCase, type TestCaseQueryParams } from '@/api/testcase'
import { useProjectStore } from '@/stores/project'
import { useEnvironmentStore } from '@/stores/environment'
import TestCaseSearch from './components/TestCaseSearch.vue'
import TestCaseFilter from './components/TestCaseFilter.vue'
import TestCaseTable from './components/TestCaseTable.vue'
import ReferencedInterfacesDialog from './components/ReferencedInterfacesDialog.vue'

const router = useRouter()
const projectStore = useProjectStore()
const environmentStore = useEnvironmentStore()
const loading = ref(false)
const testcases = ref<TestCase[]>([])

// 查询参数
const queryParams = reactive<TestCaseQueryParams>({
  name: '',
  description: '',
  project: projectStore.currentProjectId ? Number(projectStore.currentProjectId) : undefined,  // 从 store 获取当前项目 ID
  priority: undefined,
  group: undefined,
  tags: undefined,
  ordering: '-created_time',
  page: 1,
  page_size: 10
})

const pagination = reactive({
  current: 1,
  page_size: 10,
  total: 0,
  showTotal: true,
  showJumper: true,
  showPageSize: true
})

// 获取测试用例列表
const fetchTestCases = async (page: number = 1) => {
  try {
    loading.value = true
    queryParams.page = page
    queryParams.page_size = pagination.page_size
    
    const response = await getTestCases(queryParams)
    if (response && response.status === 'success') {
      const { data } = response
      testcases.value = data.results || []
      pagination.total = data.count || 0
      pagination.current = page
    } else {
      throw new Error(response?.message || '获取测试用例列表失败')
    }
  } catch (error) {
    console.error('Failed to fetch test cases:', error)
    Message.error(error instanceof Error ? error.message : '获取测试用例列表失败，请检查网络连接或刷新页面重试')
    testcases.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

// 监听当前项目变化
watch(() => projectStore.currentProjectId, (newProjectId) => {
  if (newProjectId) {
    queryParams.project = Number(newProjectId)
    pagination.current = 1
    fetchTestCases(1)
  }
})

// 处理排序变化
const handleSortChange = (dataIndex: string, direction: string) => {
  queryParams.ordering = direction === 'ascend' ? dataIndex : `-${dataIndex}`
  fetchTestCases()
}

// 处理分页变化
const handlePageChange = (current: number) => {
  pagination.current = current
  fetchTestCases(current)
}

// 处理搜索
const handleSearch = () => {
  pagination.current = 1
  fetchTestCases(1)
}

// 重置搜索
const handleReset = () => {
  Object.assign(queryParams, {
    name: '',
    description: '',
    project: undefined,
    priority: undefined,
    group: undefined,
    tags: undefined,
    ordering: '-created_time',
    page: 1,
    page_size: pagination.page_size
  })
  pagination.current = 1
  fetchTestCases(1)
}

// 更新搜索参数
const updateSearchParams = (data: Pick<TestCaseQueryParams, 'name' | 'description'>) => {
  Object.assign(queryParams, data)
}

// 更新过滤参数
const updateFilterParams = (data: Pick<TestCaseQueryParams, 'priority' | 'group' | 'tags'>) => {
  Object.assign(queryParams, data)
}

// 新建用例
const handleCreate = () => {
  router.push({
    name: 'test-case-create',
    query: { projectId: queryParams.project }
  })
}

// 编辑用例
const handleEdit = (testcase: TestCase) => {
  router.push({
    name: 'test-case-edit',
    params: { id: testcase.id },
    query: { projectId: queryParams.project }
  })
}

// 运行用例
const handleRun = async (testcase: TestCase) => {
  if (!environmentStore.currentEnvironmentId) {
    Message.warning('请先选择环境')
    return
  }

  try {
    loading.value = true
    const response = await runTestCase(testcase.id, {
      environment: Number(environmentStore.currentEnvironmentId)
    })
    if (response && response.status === 'success') {
      Message.success(response.message || '用例运行成功')
    } else {
      throw new Error(response?.message || '运行用例失败')
    }
  } catch (error) {
    console.error('运行用例失败:', error)
    Message.error(error instanceof Error ? error.message : '运行用例失败')
  } finally {
    loading.value = false
  }
}

// 查看报告
const handleReport = (testcase: TestCase) => {
  router.push({
    name: 'test-case-reports',
    params: { id: testcase.id },
    query: { projectId: queryParams.project }
  })
}

// 关联接口弹窗
const referencedInterfacesVisible = ref(false)
const currentTestcase = ref<TestCase | null>(null)

// 查看关联接口
const handleLink = (testcase: TestCase) => {
  currentTestcase.value = testcase
  referencedInterfacesVisible.value = true
}

// 关闭关联接口弹窗
const handleReferencedInterfacesClose = () => {
  currentTestcase.value = null
}

// 删除用例
const handleDelete = async (testcase: TestCase) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除测试用例「${testcase.name}」吗？删除后将同时删除所有测试步骤和执行记录，且无法恢复。`,
    okText: '确认删除',
    cancelText: '取消',
    okButtonProps: {
      status: 'danger'
    },
    async onOk() {
      try {
        loading.value = true
        await deleteTestCase(testcase.id)
        // 204 状态码表示删除成功
        Message.success('测试用例删除成功')
        await fetchTestCases(pagination.current)
      } catch (error: any) {
        console.error('删除测试用例失败:', error)
        if (error.response) {
          const { status, data } = error.response
          switch (status) {
            case 404:
              Message.error('测试用例不存在')
              break
            case 403:
              Message.error('您没有权限删除此测试用例')
              break
            case 401:
              Message.error('请先登录')
              break
            default:
              Message.error(data.message || '删除失败')
          }
        } else {
          Message.error('网络错误，请稍后重试')
        }
      } finally {
        loading.value = false
      }
    }
  })
}

// 处理每页条数变化
const handlePageSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.current = 1
  fetchTestCases(1)
}

// 初始加载
fetchTestCases()
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-gap-4 tw-p-4">
    <!-- 搜索区域 -->
    <div class="tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-px-6 tw-py-5 tw-space-y-4">
      <div class="tw-flex tw-items-center tw-gap-4">
        <div class="tw-flex-1">
          <TestCaseSearch
            :model-value="{ name: queryParams.name, description: queryParams.description }"
            @update:model-value="updateSearchParams"
            @search="handleSearch"
            @reset="handleReset"
          />
        </div>
        <div class="tw-flex-1">
          <TestCaseFilter
            :model-value="{
              priority: queryParams.priority,
              group: queryParams.group,
              tags: queryParams.tags
            }"
            :project-id="queryParams.project"
            @update:model-value="updateFilterParams"
            @search="handleSearch"
          />
        </div>
        <div class="tw-flex tw-items-center tw-gap-2">
          <a-button class="custom-reset-button" @click="handleReset">
            重置
          </a-button>
          <a-button type="primary" class="custom-add-button" @click="handleCreate">
            新增用例
          </a-button>
        </div>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="tw-flex-1 tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-overflow-hidden">
      <div class="tw-p-6">
        <TestCaseTable
          :data="testcases"
          :loading="loading"
          @sort="handleSortChange"
          @run="handleRun"
          @link="handleLink"
          @report="handleReport"
          @edit="handleEdit"
          @delete="handleDelete"
        />
      </div>
    </div>

    <!-- 分页区域 -->
    <div class="tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-px-6 tw-py-5">
      <a-pagination
        v-model:current="pagination.current"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        show-total
        show-jumper
        show-page-size
        class="tw-flex tw-justify-end"
        @change="handlePageChange"
        @page-size-change="handlePageSizeChange"
      />
    </div>

    <!-- 关联接口弹窗 -->
    <ReferencedInterfacesDialog
      v-model:visible="referencedInterfacesVisible"
      :testcase-id="currentTestcase?.id || 0"
      :testcase-name="currentTestcase?.name || ''"
      @close="handleReferencedInterfacesClose"
    />
  </div>
</template>

<style scoped>
/* 自定义滚动条 */
.custom-scrollbar {
  scrollbar-width: none !important;
  -ms-overflow-style: none !important;
  &::-webkit-scrollbar {
    display: none !important;
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

  .arco-pagination-total {
    color: #94a3b8 !important;
  }

  .arco-select-view {
    background-color: rgba(30, 41, 59, 0.5) !important;
    border: 1px solid rgba(148, 163, 184, 0.1) !important;
    border-radius: 4px !important;

    &:hover {
      border-color: rgba(59, 130, 246, 0.5) !important;
      background-color: rgba(30, 41, 59, 0.7) !important;
    }
  }
}

.custom-reset-button {
  background: rgba(148, 163, 184, 0.1) !important;
  border: 1px solid rgba(148, 163, 184, 0.2) !important;
  color: #94a3b8 !important;
  padding: 0 24px !important;
  height: 36px !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  transition: all 0.3s ease !important;

  &:hover {
    background: rgba(148, 163, 184, 0.2) !important;
    border-color: rgba(148, 163, 184, 0.3) !important;
    color: #e2e8f0 !important;
    transform: translateY(-1px) !important;
  }

  &:active {
    transform: translateY(1px) !important;
  }
}

.custom-add-button {
  background: linear-gradient(to right, #3b82f6, #1d4ed8) !important;
  border: none !important;
  padding: 0 24px !important;
  height: 36px !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  transition: all 0.3s ease !important;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3) !important;

  &:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
    background: linear-gradient(to right, #2563eb, #60a5fa) !important;
  }

  &:active {
    transform: translateY(1px) !important;
    box-shadow: 0 1px 3px rgba(59, 130, 246, 0.3) !important;
  }
}
</style>