<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import type { FormInstance } from '@arco-design/web-vue'
import { useProjectStore } from '../../stores/project'
import { IconPlus, IconSearch, IconFolder, IconEdit, IconDelete, IconList, IconApps, IconInfoCircle } from '@arco-design/web-vue/es/icon'
import request from '../../utils/request'
import type { ApiModule, PaginatedData, ApiInterface } from '@/api/interface'
import { getInterfaces } from '@/api/interface'
import ApiDetail from './components/ApiDetail.vue'
import ApiTabs from './components/ApiTabs.vue'
import ModuleTree from './components/ModuleTree.vue'
import ModuleForm from './components/ModuleForm.vue'
import ApiInterfaceList from './components/ApiInterfaceList.vue'
import ApiInterfacePagination from './components/ApiInterfacePagination.vue'
import { useApiTabsStore } from '@/stores/apiTabs'

const projectStore = useProjectStore()
const tabsStore = useApiTabsStore()
const loading = ref(false)
const formLoading = ref(false)
const apis = ref<ApiModule[]>([])
const interfaces = ref<ApiInterface[]>([])
const searchKeyword = ref('')
const selectedApi = ref<ApiModule | undefined>()
const selectedInterface = ref<ApiInterface | undefined>(undefined)
const expandedIds = ref<number[]>([])
const detailKey = ref(0)
// 无模块接口相关状态
const noModuleInterfaces = ref<ApiInterface[]>([])
const hasNoModuleInterfaces = ref(false)
// 自动调试标志
const autoDebug = ref(false)

// 视图模式控制
// 模块树显示模式: 'list' - 列表模式（不显示接口）, 'detail' - 详情模式（显示接口）
const treeDisplayMode = ref<'list' | 'detail'>('detail')
// 视图模式应该根据treeDisplayMode来决定默认值
const viewMode = ref<'list' | 'detail'>('detail')
// 分页相关状态
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})
// 全部接口列表（用于列表模式）
const allInterfaces = ref<ApiInterface[]>([])
// 当前模块名称
const currentModuleName = computed(() => {
  if (!selectedApi.value) return '全部接口'
  return selectedApi.value.name
})

// 获取接口列表（支持分页）
const fetchInterfaceListForDisplay = async () => {
  if (!projectStore.currentProjectId) {
    allInterfaces.value = []
    return
  }

  try {
    loading.value = true
    const params = {
      project_id: Number(projectStore.currentProjectId),
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      ...(selectedApi.value ? { module_id: selectedApi.value.id } : {})
    }
    
    const { data } = await getInterfaces(params)
    if (data) {
      allInterfaces.value = data.results || []
      pagination.value.total = data.count || 0
      console.log(`获取到${data.results?.length || 0}个接口，总数：${data.count}`)
    } else {
      allInterfaces.value = []
      pagination.value.total = 0
    }
  } catch (error: any) {
    Message.error(error.message || '获取接口列表失败')
    allInterfaces.value = []
    pagination.value.total = 0
  } finally {
    loading.value = false
  }
}

// 获取接口列表（用于树形结构）
const fetchInterfaces = async (moduleId?: number | null) => {
  if (!projectStore.currentProjectId) {
    interfaces.value = []
    return
  }

  try {
    loading.value = true
    const { data } = await getInterfaces({
      module_id: moduleId,
      project_id: Number(projectStore.currentProjectId),
      page_size: 1000 // 设置较大的页面大小，确保能显示所有接口
    })
    if (data?.results) {
      interfaces.value = data.results
      console.log(`获取到${data.results.length}个接口`)
      // 如果有选中的接口，更新它的数据
      if (selectedInterface.value) {
        const updatedInterface = data.results.find(item => item.id === selectedInterface.value?.id)
        if (updatedInterface) {
          selectedInterface.value = updatedInterface
        }
      }
    } else {
      interfaces.value = []
    }
  } catch (error: any) {
    Message.error(error.message || '获取接口列表失败')
    interfaces.value = []
  } finally {
    loading.value = false
  }
}

// 获取无模块接口列表
const fetchNoModuleInterfaces = async () => {
  if (!projectStore.currentProjectId) {
    noModuleInterfaces.value = []
    hasNoModuleInterfaces.value = false
    return
  }

  try {
    loading.value = true
    // 使用 getInterfaces 函数并传入 no_module: true 参数
    const { data } = await getInterfaces({
      project_id: Number(projectStore.currentProjectId),
      page_size: 1000,
      no_module: true
    })
    
    if (data?.results && data.results.length > 0) {
      noModuleInterfaces.value = data.results
      hasNoModuleInterfaces.value = true
      console.log(`获取到${data.results.length}个无模块接口`)
    } else {
      noModuleInterfaces.value = []
      hasNoModuleInterfaces.value = false
    }
  } catch (error: any) {
    console.error('获取无模块接口失败:', error)
    noModuleInterfaces.value = []
    hasNoModuleInterfaces.value = false
  } finally {
    loading.value = false
  }
}

// 表单相关状态
const formVisible = ref(false)
const formType = ref<'create' | 'edit'>('create')
const formParentId = ref<number | undefined>()
const currentModule = ref<ApiModule | undefined>()

// 获取API模块列表
const fetchApiModules = async () => {
  if (!projectStore.currentProjectId) {
    apis.value = []
    return
  }

  try {
    loading.value = true
    const { data: responseData } = await request.get<PaginatedData<ApiModule>>('/modules/modules/', {
      params: {
        page: 1,
        page_size: 100,
        project_id: projectStore.currentProjectId
      }
    })
    
    if (responseData?.results) {
      apis.value = responseData.results
    } else {
      apis.value = []
    }
    
    // 获取无模块接口
    await fetchNoModuleInterfaces()
  } catch (error: any) {
    Message.error(error.message || '获取模块列表失败')
    apis.value = []
  } finally {
    loading.value = false
  }
}

// 过滤后的模块列表
const getFilteredModules = computed(() => {
  if (!searchKeyword.value) return apis.value

  const keyword = searchKeyword.value.toLowerCase()
  
  const filterModules = (modules: ApiModule[]): ApiModule[] => {
    return modules.reduce((filtered: ApiModule[], module) => {
      const isMatch = module.name.toLowerCase().includes(keyword)
      const children = module.children ? filterModules(module.children) : []
      
      if (isMatch || children.length > 0) {
        filtered.push({
          ...module,
          children: children
        })
      }
      
      return filtered
    }, [])
  }

  return filterModules(apis.value)
})

// 切换展开状态
const handleToggleExpand = async (moduleId: number) => {
  const index = expandedIds.value.indexOf(moduleId)
  if (index === -1) {
    expandedIds.value.push(moduleId)
  } else {
    expandedIds.value.splice(index, 1)
  }
  // 同时获取该模块的接口列表
  await fetchInterfaces(moduleId)
}

// 选择模块
const handleSelectModule = async (module: ApiModule) => {
  selectedApi.value = module
  
  // 根据树显示模式决定右侧显示什么
  if (treeDisplayMode.value === 'list') {
    // 列表模式：点击模块显示接口列表
    viewMode.value = 'list'
    pagination.value.page = 1 // 重置页码
    
    try {
      loading.value = true
      const { data } = await getInterfaces({
        module_id: module.id,
        project_id: Number(projectStore.currentProjectId),
        page_size: 1000 // 设置较大的页面大小，确保能显示所有接口
      })
      
      if (data?.results && data.results.length > 0) {
        console.log(`模块${module.name}获取到${data.results.length}个接口`)
      }
      interfaces.value = data?.results || []
    } catch (error: any) {
      Message.error(error.message || '获取接口列表失败')
      interfaces.value = []
    } finally {
      loading.value = false
    }
    
    // 获取用于列表显示的接口数据
    await fetchInterfaceListForDisplay()
  } else {
    // 详情模式：保持原有逻辑，展开模块显示接口
    try {
      loading.value = true
      const { data } = await getInterfaces({
        module_id: module.id,
        project_id: Number(projectStore.currentProjectId),
        page_size: 1000
      })
      
      if (data?.results && data.results.length > 0) {
        console.log(`模块${module.name}获取到${data.results.length}个接口`)
        // 如果有接口数据，就展开该模块
        if (!expandedIds.value.includes(module.id)) {
          expandedIds.value.push(module.id)
        }
      }
      interfaces.value = data?.results || []
    } catch (error: any) {
      Message.error(error.message || '获取接口列表失败')
      interfaces.value = []
    } finally {
      loading.value = false
    }
  }
}

// 打开创建模块表单
const handleOpenCreateForm = (parentId?: number) => {
  formType.value = 'create'
  formParentId.value = parentId
  currentModule.value = undefined
  formVisible.value = true
}

// 打开编辑模块表单
const handleOpenEditForm = (module: ApiModule) => {
  formType.value = 'edit'
  currentModule.value = module
  formVisible.value = true
}

// 处理表单提交
const handleFormSubmit = async (formData: any) => {
  if (!projectStore.currentProjectId) {
    Message.warning('请先选择项目')
    return
  }

  try {
    formLoading.value = true
    if (formType.value === 'create') {
      const data = {
        ...formData,
        project: Number(projectStore.currentProjectId)
      }
      await request.post('/modules/modules/', data)
      Message.success('创建模块成功')
    } else {
      await request.put(`/modules/modules/${currentModule.value?.id}/`, formData)
      Message.success('更新模块成功')
    }
    formVisible.value = false
    fetchApiModules()
  } catch (error: any) {
    Message.error(error.message || `${formType.value === 'create' ? '创建' : '更新'}模块失败`)
  } finally {
    formLoading.value = false
  }
}

// 删除模块
const handleDelete = async (module: ApiModule) => {
  Modal.error({
    title: '确认删除',
    content: `确定要删除模块"${module.name}"吗？删除后将同时删除该模块下的所有接口，且不可恢复。`,
    hideCancel: false,
    okText: '确定',
    cancelText: '取消',
    okButtonProps: {
      status: 'danger'
    },
    onOk: async () => {
      try {
        formLoading.value = true
        await request.delete(`/modules/modules/${module.id}/`)
        Message.success('删除模块成功')
        if (selectedApi.value?.id === module.id) {
          selectedApi.value = undefined
        }
        fetchApiModules()
      } catch (error: any) {
        Message.error(error.message || '删除模块失败')
      } finally {
        formLoading.value = false
      }
    }
  })
}

// 选择接口
const handleSelectInterface = (api: ApiInterface) => {
  console.log('父组件收到接口选择事件:', api)
  selectedInterface.value = api
  viewMode.value = 'detail' // 切换到详情模式
  
  // 创建或激活页签
  const tabId = tabsStore.openOrActivateInterface(api)
  
  // 如果是已存在的页签，强制触发状态恢复
  const existingTab = tabsStore.tabs.find(t => t.id === tabId)
  if (existingTab && existingTab.activeTab) {
    // 使用 nextTick 确保在下个渲染周期恢复状态
    nextTick(() => {
      // 通过更新 detailKey 来触发组件重新挂载，确保状态恢复
      detailKey.value++
    })
  }
  
  console.log('已更新选中的接口:', selectedInterface.value)
}

// 更新接口
const handleUpdateInterface = (api: ApiInterface) => {
  console.log('更新接口信息:', api)
  // 不要严格检查接口完整性，使用存在的数据
  if (api) {
    console.log('接收到接口数据，设置为当前选中接口:', api)
    // 设置当前选中的接口
    selectedInterface.value = api
    
    // 如果接口有ID且在接口列表中存在，则更新列表中的数据
    if (api.id) {
      const index = interfaces.value.findIndex(item => item.id === api.id)
      if (index !== -1) {
        interfaces.value[index] = api
      } else {
        // 如果接口列表中不存在该接口，添加到接口列表中
        console.log('接口列表中未找到该接口，添加到列表中:', api)
        interfaces.value.push(api)
      }
    }
    
    // 确保在下一个tick渲染完成后，detailKey不会导致selectedInterface被清空
    nextTick(() => {
      console.log('确认选中接口状态:', selectedInterface.value)
    })
  }
}

// 删除接口
const handleDeleteInterface = (api: ApiInterface) => {
  const modalLoading = ref(false)
  
  Modal.error({
    title: '确认删除',
    content: `确定要删除接口"${api.name}"吗？删除后不可恢复。`,
    hideCancel: false,
    okText: '确定',
    cancelText: '取消',
    okButtonProps: {
      status: 'danger'
    },
    async onOk() {
      if (modalLoading.value) return
      modalLoading.value = true
      
      try {
        await request.delete(`/interfaces/${api.id}/`)
        Message.success('删除接口成功')
        
        // 如果删除的是当前选中的接口，清空选中状态
        if (selectedInterface.value?.id === api.id) {
          selectedInterface.value = undefined
        }
        
        // 如果接口有模块ID，刷新该模块的接口列表
        if (api.module) {
          // 确保模块是展开状态
          if (!expandedIds.value.includes(api.module)) {
            expandedIds.value.push(api.module)
          }
          
          // 先从expandedIds中移除，再添加回来，强制刷新
          const index = expandedIds.value.indexOf(api.module)
          if (index > -1) {
            expandedIds.value.splice(index, 1)
            // 使用nextTick确保DOM更新后再重新展开
            nextTick(() => {
              expandedIds.value.push(api.module)
              // 刷新模块的接口列表
              fetchInterfaces(api.module)
            })
          }
        } else {
          // 如果是无模块接口，刷新无模块接口列表
          await fetchNoModuleInterfaces()
        }
      } catch (error: any) {
        Message.error(error.message || '删除接口失败')
      } finally {
        modalLoading.value = false
      }
    }
  })
}

// 编辑接口 - 进入接口详情编辑页面
const handleEditInterface = (api: ApiInterface) => {
  console.log('编辑接口:', api)
  selectedInterface.value = api
  // 创建或激活页签
  const tabId = tabsStore.openOrActivateInterface(api)
  viewMode.value = 'detail' // 切换到详情模式进行编辑
  
  // 如果是已存在的页签，强制触发状态恢复
  const existingTab = tabsStore.tabs.find(t => t.id === tabId)
  if (existingTab && existingTab.activeTab) {
    nextTick(() => {
      detailKey.value++
    })
  }
}

// 选择无模块接口
const handleSelectNoModuleInterface = async (api: ApiInterface) => {
  try {
    loading.value = true
    // 获取接口详情
    const { data } = await request.get<ApiInterface>(`/interfaces/${api.id}/`)
    selectedInterface.value = data
    // 创建或激活页签
    const tabId = tabsStore.openOrActivateInterface(data)
    // 切换到详情视图
    viewMode.value = 'detail'
    
    // 如果是已存在的页签，强制触发状态恢复
    const existingTab = tabsStore.tabs.find(t => t.id === tabId)
    if (existingTab && existingTab.activeTab) {
      nextTick(() => {
        detailKey.value++
      })
    }
    
    // 刷新无模块接口列表
    await fetchNoModuleInterfaces()
  } catch (error: any) {
    console.error('获取接口详情失败:', error)
    Message.error('获取接口详情失败')
    selectedInterface.value = api
    // 创建或激活页签
    const tabId = tabsStore.openOrActivateInterface(api)
    
    // 如果是已存在的页签，强制触发状态恢复
    const existingTab = tabsStore.tabs.find(t => t.id === tabId)
    if (existingTab && existingTab.activeTab) {
      nextTick(() => {
        detailKey.value++
      })
    }
    
    // 即使出错也要切换到详情视图
    viewMode.value = 'detail'
  } finally {
    loading.value = false
  }
}

// 处理接口刷新
const handleRefresh = async (moduleId?: number) => {
  try {
    loading.value = true
    console.log('刷新模块:', moduleId, '当前选中接口:', selectedInterface.value)
    
    // 如果有模块ID，确保模块是展开状态
    if (moduleId && !expandedIds.value.includes(moduleId)) {
      expandedIds.value.push(moduleId)
    }
    
    // 同时刷新模块列表和接口列表
    if (moduleId) {
      await Promise.all([
        fetchApiModules(),
        fetchInterfaces(moduleId)
      ])
    } else {
      // 如果是刷新无模块接口
      await Promise.all([
        fetchApiModules(),
        fetchNoModuleInterfaces() // 使用专门的无模块接口获取函数
      ])
    }

    // 如果有选中的接口且有ID，尝试在刷新后的接口列表中找到它
    if (selectedInterface.value && selectedInterface.value.id) {
      // 根据是否有模块ID决定在哪个列表中查找
      const list = moduleId ? interfaces.value : noModuleInterfaces.value
      const updatedInterface = list.find(item => item.id === selectedInterface.value?.id)
      if (updatedInterface) {
        console.log('更新选中接口:', updatedInterface)
        selectedInterface.value = updatedInterface
      }
    } else {
      // 如果没有选中的接口或选中的接口没有ID，查看是否有刚刚创建的新接口
      const list = moduleId ? interfaces.value : noModuleInterfaces.value
      if (list.length > 0) {
        // 获取最后一个接口作为新创建的接口
        const latestInterface = list[list.length - 1]
        console.log('选中最新创建的接口:', latestInterface)
        selectedInterface.value = latestInterface
      }
    }

    // 如果有模块ID，强制刷新模块展开状态
    if (moduleId) {
      const index = expandedIds.value.indexOf(moduleId)
      if (index > -1) {
        expandedIds.value.splice(index, 1)
        // 使用nextTick确保DOM更新后再重新展开
        nextTick(() => {
          expandedIds.value.push(moduleId)
        })
      }
    }
  } catch (error: any) {
    Message.error(error.message || '刷新接口列表失败')
  } finally {
    loading.value = false
  }
}

// 处理分页变化
const handlePageChange = (page: number) => {
  pagination.value.page = page
  fetchInterfaceListForDisplay()
}

// 处理每页数量变化
const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1 // 重置到第一页
  fetchInterfaceListForDisplay()
}

// 返回列表视图
const handleBackToList = () => {
  viewMode.value = 'list'
  selectedInterface.value = undefined
}

// 显示全部接口
const handleShowAllInterfaces = async () => {
  selectedApi.value = undefined
  viewMode.value = 'list'
  pagination.value.page = 1
  await fetchInterfaceListForDisplay()
}

// 处理列表中的接口操作 - 调试接口
const handleInterfaceRun = async (api: ApiInterface) => {
  console.log('调试接口:', api)
  // 先选中该接口
  selectedInterface.value = api
  // 创建或激活页签
  const tabId = tabsStore.openOrActivateInterface(api)
  // 设置自动调试标志
  autoDebug.value = true
  // 切换到详情模式
  viewMode.value = 'detail'
  
  // 如果是已存在的页签，强制触发状态恢复
  const existingTab = tabsStore.tabs.find(t => t.id === tabId)
  if (existingTab && existingTab.activeTab) {
    nextTick(() => {
      detailKey.value++
    })
  }
  // 在详情页面中会自动触发调试
}

// 处理模块树中的接口运行 - 调试接口
const handleRunInterface = async (api: ApiInterface) => {
  console.log('从模块树调试接口:', api)
  // 先选中该接口
  selectedInterface.value = api
  // 创建或激活页签
  const tabId = tabsStore.openOrActivateInterface(api)
  // 设置自动调试标志
  autoDebug.value = true
  // 切换到详情模式
  viewMode.value = 'detail'
  
  // 如果是已存在的页签，强制触发状态恢复
  const existingTab = tabsStore.tabs.find(t => t.id === tabId)
  if (existingTab && existingTab.activeTab) {
    nextTick(() => {
      detailKey.value++
    })
  }
  // 在详情页面中会自动触发调试
}

// 监听项目变化
watch(
  () => projectStore.currentProjectId,
  () => {
    fetchApiModules()
    selectedApi.value = undefined
    selectedInterface.value = undefined
    interfaces.value = []
    noModuleInterfaces.value = []
    hasNoModuleInterfaces.value = false
    expandedIds.value = []
    // 根据treeDisplayMode决定viewMode的默认值
    viewMode.value = treeDisplayMode.value === 'detail' ? 'detail' : 'list'
    pagination.value.page = 1
    fetchInterfaceListForDisplay()
  }
)


// 新建接口
const handleCreateInterface = () => {
  // 清空选中的接口,但保留选中的模块
  console.log('准备创建新接口，清空当前选中接口')
  selectedInterface.value = undefined
  
  // 切换到详情视图模式
  viewMode.value = 'detail'
  
  // 创建新的空白页签
  tabsStore.createTab()
  
  // 强制重新渲染右侧组件，确保所有状态都被重置
  detailKey.value++
  
  // 使用nextTick确保在DOM更新后执行
  nextTick(() => {
    console.log('创建新接口模式已准备就绪')
  })
}

// 处理接口详情更新时，保存到当前页签
watch(() => selectedInterface.value, (newInterface) => {
  if (newInterface && tabsStore.activeTabId) {
    const activeTab = tabsStore.tabs.find(t => t.id === tabsStore.activeTabId)
    if (activeTab) {
      // 更新页签的接口信息
      tabsStore.updateTabRequest(tabsStore.activeTabId, {
        method: newInterface.method,
        url: newInterface.url,
        name: newInterface.name,
        module: newInterface.module,
        params: newInterface.params,
        headers: newInterface.headers,
        body: newInterface.body,
        setupHooks: newInterface.setup_hooks,
        teardownHooks: newInterface.teardown_hooks,
        extractRules: newInterface.extract,
        assertRules: newInterface.validators
      })
    }
  }
}, { deep: true })

// 处理页签切换
const handleTabChange = (tabId: string) => {
  const tab = tabsStore.tabs.find(t => t.id === tabId)
  if (tab) {
    // 恢复页签的接口数据（不重新加载）
    if (tab.interfaceId) {
      // 尝试从各个列表中找到接口数据
      const foundInterface = [...interfaces.value, ...noModuleInterfaces.value, ...allInterfaces.value]
        .find(api => api.id === tab.interfaceId)
      
      if (foundInterface) {
        // 创建一个包含页签保存数据的接口对象
        selectedInterface.value = {
          ...foundInterface,
          // 恢复页签中保存的请求数据
          params: tab.params || foundInterface.params,
          headers: tab.headers || foundInterface.headers,
          body: tab.body || foundInterface.body,
          setup_hooks: tab.setupHooks || foundInterface.setup_hooks,
          teardown_hooks: tab.teardownHooks || foundInterface.teardown_hooks,
          extract: tab.extractRules || foundInterface.extract,
          validators: tab.assertRules || foundInterface.validators
        }
      } else {
        selectedInterface.value = undefined
      }
    } else {
      // 新建接口页签
      selectedInterface.value = undefined
    }
    
    viewMode.value = 'detail'
    // 不再强制刷新，让 ApiDetail 组件自己处理状态恢复
    // detailKey.value++
  }
}

// 初始化时恢复页签
onMounted(() => {
  // 恢复本地存储的页签
  tabsStore.loadFromLocalStorage()
  
  if (projectStore.currentProjectId) {
    fetchApiModules()
    fetchInterfaceListForDisplay() // 默认加载全部接口
  }
})

// 保存页签到本地存储
watch(() => tabsStore.tabs, () => {
  tabsStore.saveToLocalStorage()
}, { deep: true })
</script>

<template>
  <div class="api-management tw-h-full tw-flex tw-p-2 tw-gap-2">
    <!-- 左侧模块列表 -->
    <div class="tw-w-80 tw-flex tw-flex-col">
      <div class="tw-flex-1 tw-bg-gray-800 tw-rounded-lg tw-shadow-lg tw-overflow-hidden tw-flex tw-flex-col">
        <!-- 顶部标题和搜索栏 -->
        <div class="tw-p-4 tw-border-b tw-border-gray-700/50 tw-flex-shrink-0">
          <!-- 模式切换按钮 -->
          <div class="tw-flex tw-justify-center tw-items-center tw-gap-2 tw-mb-4">
            <span class="tw-text-xs tw-text-gray-400">列表</span>
            <a-switch
              v-model="treeDisplayMode"
              checked-value="detail"
              unchecked-value="list"
              @change="(val: string | number | boolean) => { viewMode = val === 'detail' ? 'detail' : 'list' }"
            >
              <template #checked>
                <icon-apps :size="14" />
              </template>
              <template #unchecked>
                <icon-list :size="14" />
              </template>
            </a-switch>
            <span class="tw-text-xs tw-text-gray-400">详情</span>
            <a-tooltip content="列表模式：点击模块显示接口列表；详情模式：展开显示模块下的接口" position="right">
              <icon-info-circle class="tw-text-gray-400 tw-cursor-help" :size="14" />
            </a-tooltip>
          </div>
          
          <div class="tw-flex tw-justify-between tw-items-center tw-mb-4">
            <h2 class="tw-text-lg tw-font-medium tw-text-gray-100">模块列表</h2>
            <div class="tw-flex tw-items-center tw-gap-2">
              <a-button type="text" size="small" @click="handleShowAllInterfaces" :title="'显示全部接口列表'">
                <template #icon><icon-list /></template>
              </a-button>
              <a-button type="text" size="small" @click="handleOpenCreateForm()">
                <template #icon><icon-plus /></template>
                模块
              </a-button>
              <a-button type="text" size="small" @click="handleCreateInterface">
                <template #icon><icon-plus /></template>
                接口
              </a-button>
            </div>
          </div>
          <a-input-search
            v-model="searchKeyword"
            placeholder="搜索模块..."
            allow-clear
          >
            <template #prefix>
              <icon-search />
            </template>
          </a-input-search>
        </div>

        <!-- 模块列表内容 -->
        <div class="tw-flex-1 tw-min-h-0 tw-overflow-hidden">
          <a-spin :loading="loading" dot class="!tw-block tw-h-full">
            <div class="tw-h-full tw-overflow-y-auto tw-scrollbar-hide">
              <div class="tw-py-2">
                <a-empty v-if="apis.length === 0" class="tw-p-4">
                  暂无模块数据
                </a-empty>
                <template v-else>
                  <div class="tw-space-y-1.5 tw-m-2">
                    <!-- 未选择模块接口 -->
                    <div v-if="hasNoModuleInterfaces" class="tw-mb-3">
                      <div 
                        class="tw-flex tw-items-center tw-justify-between tw-px-3 tw-py-2 tw-rounded-md tw-cursor-pointer hover:tw-bg-gray-700/30"
                        :class="{ 'tw-bg-gray-700/50': selectedApi === undefined && noModuleInterfaces.length > 0 }"
                        @click="selectedApi = undefined; interfaces = []; expandedIds = []"
                      >
                        <div class="tw-flex tw-items-center tw-gap-2">
                          <icon-folder class="tw-text-gray-400" />
                          <span class="tw-text-gray-300">未选择模块接口</span>
                          <a-tag size="small" type="arcoblue">{{ noModuleInterfaces.length }}</a-tag>
                        </div>
                        <div class="tw-flex tw-items-center">
                          <a-button type="text" size="mini" @click.stop="handleCreateInterface">
                            <template #icon><icon-plus /></template>
                          </a-button>
                        </div>
                      </div>
                      
                      <!-- 无模块接口列表 -->
                      <div v-if="selectedApi === undefined" class="tw-mt-1">
                        <a-spin :loading="loading" dot>
                          <div class="tw-flex tw-flex-col tw-px-4">
                            <div 
                              v-for="api in noModuleInterfaces" 
                              :key="api.id"
                              class="!tw-w-full !tw-px-6 !tw-py-2 !tw-text-sm !tw-text-gray-400 hover:!tw-text-gray-300 !tw-rounded !tw-bg-[rgb(70,84,102,0.2)] hover:!tw-bg-[rgb(70,84,102,0.4)] !tw-min-w-0 !tw-cursor-pointer !tw-mt-1"
                              :class="{ '!tw-bg-[rgb(70,84,102,0.4)]': selectedInterface?.id === api.id }"
                              @click="handleSelectNoModuleInterface(api)"
                            >
                              <div class="!tw-flex !tw-items-center !tw-justify-between">
                                <div class="!tw-flex !tw-items-center !tw-gap-2 !tw-min-w-0 !tw-flex-1">
                                  <a-tag
                                    :color="api.method === 'GET' ? 'blue' : api.method === 'POST' ? 'green' : api.method === 'PUT' ? 'orange' : 'red'"
                                    class="!tw-w-16 !tw-flex !tw-justify-center !tw-flex-shrink-0"
                                  >
                                    {{ api.method }}
                                  </a-tag>
                                  <span class="!tw-truncate" :title="api.name">{{ api.name }}</span>
                                </div>
                                <div class="!tw-flex !tw-items-center">
                                  <a-button
                                    type="text"
                                    size="mini"
                                    class="!tw-p-0 !tw-text-[#6b7785] hover:!tw-text-[#86909c]"
                                    @click.stop="handleRunInterface(api)"
                                    title="调试接口"
                                  >
                                    <template #icon><icon-send /></template>
                                  </a-button>
                                  <a-button
                                    type="text"
                                    size="mini"
                                    class="!tw-p-0 !tw-text-[#6b7785] hover:!tw-text-[#86909c]"
                                    @click.stop="handleEditInterface(api)"
                                    title="编辑接口"
                                  >
                                    <template #icon><icon-edit /></template>
                                  </a-button>
                                  <a-button
                                    type="text"
                                    size="mini"
                                    class="!tw-p-0 !tw-text-[#6b7785] hover:!tw-text-[#86909c]"
                                    @click.stop="handleDeleteInterface(api)"
                                  >
                                    <template #icon><icon-delete /></template>
                                  </a-button>
                                </div>
                              </div>
                            </div>
                          </div>
                        </a-spin>
                      </div>
                    </div>
                    
                    <!-- 常规模块列表 -->
                    <ModuleTree
                      v-for="module in getFilteredModules"
                      :key="module.id"
                      :module="module"
                      :expanded-ids="expandedIds"
                      :selected-id="selectedApi?.id"
                      :form-loading="formLoading"
                      :display-mode="treeDisplayMode"
                      @select="handleSelectModule"
                      @toggle-expand="handleToggleExpand"
                      @edit="handleOpenEditForm"
                      @add-child="handleOpenCreateForm"
                      @delete="handleDelete"
                      @edit-interface="handleEditInterface"
                      @delete-interface="handleDeleteInterface"
                      @run-interface="handleRunInterface"
                      @select-interface="handleSelectInterface"
                    />
                  </div>
                </template>
              </div>
            </div>
          </a-spin>
        </div>
      </div>
    </div>

    <!-- 右侧内容区域 -->
    <div class="tw-flex-1 tw-min-w-0 tw-overflow-hidden tw-flex tw-flex-col">
      <!-- 列表视图 -->
      <div v-if="viewMode === 'list'" class="tw-h-full tw-flex tw-flex-col tw-bg-gray-800 tw-rounded-lg tw-shadow-lg tw-overflow-hidden">
        <!-- 顶部工具栏 -->
        <div v-if="selectedInterface" class="tw-p-3 tw-border-b tw-border-gray-700 tw-flex tw-items-center tw-justify-between">
          <div class="tw-text-sm tw-text-gray-400">
            已选择接口: <span class="tw-text-gray-200">{{ selectedInterface.name }}</span>
          </div>
          <a-button size="small" type="primary" @click="viewMode = 'detail'">
            查看详情
          </a-button>
        </div>
        
        <!-- 接口列表 -->
        <div class="tw-flex-1 tw-overflow-hidden">
          <ApiInterfaceList
            :interfaces="allInterfaces"
            :loading="loading"
            :selected-interface-id="selectedInterface?.id"
            :current-module-name="currentModuleName"
            @interface-select="handleSelectInterface"
            @interface-edit="handleEditInterface"
            @interface-delete="handleDeleteInterface"
            @interface-run="handleInterfaceRun"
          />
        </div>
        
        <!-- 分页区域 -->
        <div v-if="pagination.total > 0" class="tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-p-6">
          <ApiInterfacePagination
            :total="pagination.total"
            :page-size="pagination.pageSize"
            :current-page="pagination.page"
            @page-change="handlePageChange"
            @page-size-change="handlePageSizeChange"
          />
        </div>
      </div>
      
      <!-- 详情视图 -->
      <div v-else class="tw-h-full tw-flex tw-flex-col tw-bg-gray-800 tw-rounded-lg tw-shadow-lg tw-overflow-hidden">
        <!-- 页签栏 -->
        <ApiTabs
          :current-interface="selectedInterface"
          @tab-change="handleTabChange"
          @new-interface="handleCreateInterface"
        />
        
        <!-- 接口详情 -->
        <ApiDetail
          :key="detailKey"
          :module="selectedApi"
          :modules="getFilteredModules"
          :interface="selectedInterface"
          :auto-debug="autoDebug"
          @refresh="handleRefresh"
          @update:interface="handleUpdateInterface"
          @debug-completed="autoDebug = false"
          class="tw-flex-1"
        />
      </div>
    </div>

    <!-- 模块表单弹窗 -->
    <ModuleForm
      v-model:visible="formVisible"
      :type="formType"
      :loading="formLoading"
      :apis="apis"
      :current-module="currentModule"
      :parent-id="formParentId"
      @submit="handleFormSubmit"
    />
  </div>
</template>

<style lang="postcss" scoped>
/* Switch 开关样式增强 */
:deep(.arco-switch) {
  @apply tw-bg-gray-700 tw-border tw-border-gray-600;
  
  &.arco-switch-checked {
    @apply tw-bg-blue-500 tw-border-blue-500;
  }
  
  .arco-switch-handle {
    @apply tw-bg-gray-100;
  }
}

/* 继承全局样式 */
:deep(.arco-empty) {
  @apply tw-text-gray-500;
}

:deep(.arco-btn-primary) {
  @apply tw-bg-blue-500 hover:tw-bg-blue-600 tw-border-blue-500 hover:tw-border-blue-600;
}

:deep(.arco-tag-arcoblue) {
  @apply tw-bg-blue-500/20 tw-text-blue-500 tw-border-blue-500/20;
}

/* 加载遮罩样式 */
:deep(.arco-spin) {
  .arco-spin-mask {
    @apply tw-bg-transparent;
  }
  .arco-spin-dot {
    @apply tw-border-blue-500;
  }
}

/* 隐藏滚动条但保留滚动功能 */
.tw-scrollbar-hide {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}

.tw-scrollbar-hide::-webkit-scrollbar {
  display: none;  /* Chrome, Safari and Opera */
}

/* 树形控件样式 */
:deep(.arco-tree) {
  @apply tw-bg-transparent;

  .arco-tree-node {
    @apply tw-bg-transparent hover:tw-bg-gray-700/30;
    
    &.arco-tree-node-selected {
      @apply tw-bg-gray-700/50;
    }
  }

  .arco-tree-node-title {
    @apply tw-flex-1;
  }

  .arco-tree-node-switcher {
    @apply tw-text-gray-400;
  }
}

/* 弹窗样式 */
:global(.arco-modal-container) {
  .arco-modal-error {
    .arco-modal-title {
      @apply tw-text-gray-100;
    }
    .arco-modal-body {
      @apply tw-text-center;
    }
  }
}

:global(.arco-modal-wrapper) {
  .arco-modal {
    @apply tw-bg-gray-800 tw-border tw-border-gray-700;

    .arco-modal-header {
      @apply tw-bg-gray-800 tw-border-b tw-border-gray-700;
      .arco-modal-title {
        @apply tw-text-gray-100;
      }
    }

    .arco-modal-body {
      @apply tw-bg-gray-800 tw-text-center;
    }

    .arco-modal-content {
      @apply tw-bg-gray-800 tw-text-gray-300;
    }

    .arco-modal-footer {
      @apply tw-bg-gray-800 tw-border-t tw-border-gray-700;
    }

    .arco-form-item-label {
      @apply tw-text-gray-300;
    }

    .arco-input-wrapper {
      @apply tw-bg-gray-900/60 tw-border-gray-700;
      input {
        @apply tw-text-gray-200;
        &::placeholder {
          @apply tw-text-gray-500;
        }
      }
    }

    .arco-select-view {
      @apply tw-bg-gray-900/60 tw-border-gray-700;
      .arco-select-view-value {
        @apply tw-text-gray-200;
      }
    }

    .arco-btn-secondary {
      @apply tw-bg-gray-700 tw-border-gray-600 tw-text-gray-300;
      
      &:hover {
        @apply tw-bg-gray-600 tw-border-gray-500;
      }
    }

    .arco-btn-primary {
      @apply tw-bg-blue-500 tw-border-blue-500 tw-text-white;
      
      &:hover {
        @apply tw-bg-blue-600 tw-border-blue-600;
      }
    }

    .arco-btn-danger {
      @apply tw-bg-red-500 tw-border-red-500 tw-text-white;
      
      &:hover {
        @apply tw-bg-red-600 tw-border-red-600;
      }
    }
  }
}

:deep(.arco-select-dropdown) {
  @apply tw-bg-gray-800 tw-border tw-border-gray-700;

  .arco-select-option {
    @apply tw-text-gray-200;

    &:hover {
      @apply tw-bg-gray-700/50;
    }

    &.arco-select-option-active {
      @apply tw-bg-gray-700;
    }
  }
}
</style>