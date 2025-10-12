<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { type ApiInterface, type ApiModule, type PaginatedData } from '@/api/interface'
import request from '@/utils/request'
import { useProjectStore } from '@/stores/project'
import { Message } from '@arco-design/web-vue'
import { addTestCaseSteps, type CreateTestCaseData } from '@/api/testcase'
import type { InputInstance } from '@arco-design/web-vue'
import ApiSelectDialogHeader from './ApiSelectDialogHeader.vue'
import ModuleList from './ModuleList.vue'
import InterfaceList from './InterfaceList.vue'
import InterfacePagination from './InterfacePagination.vue'
import CustomDialog from '@/components/CustomDialog.vue'

const props = defineProps<{
  visible: boolean
  testCaseId?: number
  testCase?: {
    name: string
    priority: string
    project: number
    description?: string
    group?: number
    tags?: number[]
    config?: {
      base_url: string
      variables: string | Record<string, any>
      parameters: string | Record<string, any>
      export: string | string[]
      verify: string | boolean
    }
  }
}>()

const emit = defineEmits(['update:visible', 'select'])

// 基础状态
const searchInput = ref<InputInstance>()
const loading = ref(false)
const selectedModuleId = ref<number>()
const expandedModuleIds = ref<number[]>([])

// 数据状态
const modules = ref<ApiModule[]>([])
const currentModule = ref<ApiModule | null>(null)
const interfaces = ref<ApiInterface[]>([])
const selectedKeys = ref<number[]>([])

// 分页状态
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0
})

// Store
const projectStore = useProjectStore()

// 加载模块列表
const loadModules = async () => {
  if (!projectStore.currentProject?.id) {
    console.error('No project selected')
    return
  }
  
  loading.value = true
  modules.value = [] // 重置模块列表
  
  try {
    const { data } = await request.get<PaginatedData<ApiModule>>('/modules/modules/', {
      params: {
        project_id: projectStore.currentProject.id,
        page: 1,
        page_size: 100
      }
    })
    modules.value = data.results
  } catch (error) {
    console.error('Failed to load modules:', error)
    Message.error({
      content: '加载模块列表失败',
      duration: 3000
    })
  } finally {
    loading.value = false
  }
}

// 加载模块下的接口列表
const loadModuleInterfaces = async (moduleId: number, page = 1) => {
  if (!projectStore.currentProject?.id) {
    Message.error({
      content: '未选择项目',
      duration: 3000
    })
    return
  }
  
  loading.value = true
  if (page === 1) {
    interfaces.value = [] // 仅在第一页时重置接口列表
    // 切换模块或第一页时清空选中状态
    selectedKeys.value = []
  }
  
  try {
    const { data } = await request.get<PaginatedData<ApiInterface>>('/interfaces/', {
      params: {
        module_id: moduleId,
        project_id: projectStore.currentProject.id,
        page: page,
        page_size: pagination.value.pageSize
      }
    })
    interfaces.value = data.results
    pagination.value.total = data.count
    pagination.value.current = page
  } catch (error) {
    console.error('Failed to load interfaces:', error)
    Message.error({
      content: '加载接口列表失败',
      duration: 3000
    })
  } finally {
    loading.value = false
  }
}

// 处理分页变化
const handlePageChange = (page: number) => {
  if (currentModule.value) {
    loadModuleInterfaces(currentModule.value.id, page)
  }
}

// 处理每页条数变化
const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  if (currentModule.value) {
    loadModuleInterfaces(currentModule.value.id, 1)
  }
}

// 展开/收起模块
const handleToggleExpand = (moduleId: number) => {
  const index = expandedModuleIds.value.indexOf(moduleId)
  if (index === -1) {
    expandedModuleIds.value.push(moduleId)
  } else {
    expandedModuleIds.value.splice(index, 1)
  }
}

// 选择模块
const handleModuleSelect = async (module: ApiModule) => {
  try {
    loading.value = true
    selectedModuleId.value = module.id
    currentModule.value = module
    // 切换模块时也清空选中状态
    selectedKeys.value = []
    await loadModuleInterfaces(module.id)
  } catch (error) {
    console.error('Failed to load module interfaces:', error)
    selectedModuleId.value = undefined
    currentModule.value = null
  } finally {
    loading.value = false
  }
}

// 选择接口
const handleConfirm = () => {
  if (selectedKeys.value.length === 0) {
    Message.warning('请至少选择一个接口')
    return
  }
  
  const selectedInterfaces = interfaces.value.filter(api => selectedKeys.value.includes(api.id!))
  emit('select', selectedInterfaces)
  // 确认后立即清空选中状态
  selectedKeys.value = []
  emit('update:visible', false)
}

// 处理选择变化
const handleSelectionChange = (keys: number[]) => {
  // 确保只更新为新的选择，而不是累加
  selectedKeys.value = keys.map(k => Number(k))
}

// 处理行点击
const handleRowClick = (record: ApiInterface) => {
  const id = record.id!
  const index = selectedKeys.value.indexOf(id)
  if (index === -1) {
    selectedKeys.value = [...selectedKeys.value, id]
  } else {
    selectedKeys.value = selectedKeys.value.filter(key => key !== id)
  }
}

// 关闭弹窗
const handleClose = () => {
  emit('update:visible', false)
}

// 重置弹窗状态
const resetDialogState = () => {
  // 清空所有选中状态
  selectedKeys.value = []
  interfaces.value = []
  currentModule.value = null
  selectedModuleId.value = undefined
  expandedModuleIds.value = []
  pagination.value = {
    current: 1,
    pageSize: 10,
    total: 0
  }
}

// 监听visible prop变化
watch(() => props.visible, async (newVal, oldVal) => {
  if (newVal && !oldVal) {
    // 从关闭状态变为打开状态时，重置所有状态
    resetDialogState()
    // 使用 nextTick 确保 DOM 更新完成后再加载数据
    await nextTick()
    // 重新加载模块列表
    loadModules()
  } else if (!newVal && oldVal) {
    // 从打开状态变为关闭状态时，也重置状态
    resetDialogState()
  }
}, { immediate: false })

// 监听visible变化（用于CustomDialog的事件）
const handleVisibleChange = (value: boolean) => {
  if (!value) {
    // 关闭时触发更新
    emit('update:visible', false)
  }
}

// 初始化
onMounted(() => {
  // 不在mounted时加载，等待弹窗打开时再加载
  // loadModules()
})
</script>

<template>
  <CustomDialog
    :visible="visible"
    :width="1000"
    :mask-closable="false"
    @update:visible="handleVisibleChange"
    @close="handleClose"
  >
    <div class="api-select-dialog">
      <div class="tw-flex tw-flex-col tw-gap-4">
        <ApiSelectDialogHeader @close="handleClose" />
        
        <div class="tw-flex tw-gap-4">
          <ModuleList
            :modules="modules"
            :expanded-ids="expandedModuleIds"
            :selected-id="selectedModuleId"
            :loading="loading"
            @select="handleModuleSelect"
            @toggle-expand="handleToggleExpand"
          />

          <div class="tw-flex-1 tw-flex tw-flex-col tw-gap-4">
            <InterfaceList
              :interfaces="interfaces"
              :selected-keys="selectedKeys"
              :loading="loading"
              :current-module-name="currentModule?.name"
              @selection-change="handleSelectionChange"
              @row-click="handleRowClick"
              @confirm="handleConfirm"
            />
            
            <InterfacePagination
              :current="pagination.current"
              :page-size="pagination.pageSize"
              :total="pagination.total"
              @change="handlePageChange"
              @page-size-change="handlePageSizeChange"
            />
          </div>
        </div>
      </div>
    </div>
  </CustomDialog>
</template>

<style scoped>
.api-select-dialog {
  @apply tw-bg-transparent tw-text-gray-300 tw-p-6;
}
</style>