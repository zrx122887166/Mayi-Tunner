<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import { useProjectStore } from '../../stores/project'
import {
  getEnvironments, 
  createEnvironment, 
  deleteEnvironment, 
  updateEnvironment, 
  cloneEnvironment, 
  getEnvironmentDetail,
  type Environment,
  type EnvironmentVariable,
  batchCreateVariables
} from '../../api/environment'
import { getDatabaseConfigs, type DatabaseConfig } from '../../api/databaseConfig'
import EnvironmentList from './components/EnvironmentList.vue'
import EnvironmentForm from './components/EnvironmentForm.vue'
import GlobalHeadersPanel from './components/GlobalHeadersPanel.vue'
import DatabaseConfigPanel from './components/DatabaseConfigPanel.vue'
import {
  IconPlus,
  IconEdit,
  IconStorage,
  IconCopy,
  IconSettings,
  IconLink,
  IconFile,
  IconInfoCircle
} from '@arco-design/web-vue/es/icon'

const projectStore = useProjectStore()
const loading = ref(false)
const formLoading = ref(false)
const environments = ref<Environment[]>([])
const searchKeyword = ref('')
const activeTab = ref('list') // 'list' | 'create' | 'edit' | 'detail' | 'global-headers' | 'database-config'
const selectedEnvironment = ref<Environment | null>(null)
const showGlobalHeaders = ref(false)
const showDatabaseConfig = ref(false)
const globalHeadersPanel = ref<{ handleCreate: () => void } | null>(null)
const databaseConfigPanel = ref<{ handleCreate: () => void } | null>(null)

interface FormData {
  id?: number
  name: string
  base_url: string
  description: string
  project: number
  is_active: boolean
  variables: EnvironmentVariable[]
  database_config?: number | null
  verify_ssl?: boolean
}

// 创建环境相关
const createForm = ref<FormData>({
  name: '',
  base_url: '',
  description: '',
  project: 0,
  is_active: true,
  variables: [],
  database_config: "null" as any,
  verify_ssl: true
})

// 删除环境相关
const handleDelete = async (record: Environment) => {
  try {
    loading.value = true
    await deleteEnvironment(record.id)
    Message.success('删除环境成功')
    await fetchEnvironments()
    if (selectedEnvironment.value?.id === record.id) {
      selectedEnvironment.value = null
      activeTab.value = 'list'
    }
  } catch (error) {
    console.error('删除环境错误:', error)
    Message.error('删除环境失败')
  } finally {
    loading.value = false
  }
}

// 切换到创建环境
const switchToCreate = () => {
  if (!projectStore.currentProjectId) {
    Message.warning('请先选择项目')
    return
  }
  createForm.value = {
    name: '',
    base_url: '',
    description: '',
    project: Number(projectStore.currentProjectId),
    is_active: true,
    variables: [],
    database_config: "null" as any,
    verify_ssl: true
  }
  activeTab.value = 'create'
  selectedEnvironment.value = null
}

// 创建环境
const handleCreate = async () => {
  try {
    formLoading.value = true
    
    // 处理database_config值，将字符串"null"转换为null
    const formData = { ...createForm.value };
    if (formData.database_config === "null") {
      formData.database_config = null;
    }
    
    const response = await createEnvironment(formData)

    if (response.status === 'success' && response.data) {
      // 如果有变量列表，调用批量创建变量的接口
      if (createForm.value.variables.length > 0) {
        try {
          await batchCreateVariables({
            environment_id: response.data.id,
            variables: createForm.value.variables.map(v => ({
              name: v.name,
              value: v.value,
              type: v.type,
              description: v.description || '',
              is_sensitive: v.is_sensitive
            }))
          })
        } catch (error: any) {
          console.error('批量创建变量失败:', error)
          Message.warning('环境创建成功，但变量创建失败')
        }
      }
      
      Message.success('创建环境成功')
      resetCreateForm()
      await fetchEnvironments()
      // 切换到列表页
      activeTab.value = 'list'
    }
  } catch (error: any) {
    console.error('创建环境失败:', error)
    Message.error(error.message || '创建环境失败')
  } finally {
    formLoading.value = false
  }
}

// 获取环境列表
const fetchEnvironments = async () => {
  if (!projectStore.currentProjectId) {
    environments.value = []
    return
  }

  try {
    loading.value = true
    const response = await getEnvironments({
      project_id: Number(projectStore.currentProjectId)
    })
    environments.value = response.data.results
    console.log('获取到的环境列表:', response.data.results)
    
    // 获取数据库配置信息，用于显示数据库配置名称
    await enrichEnvironmentsWithDatabaseConfigNames()
  } catch (error) {
    console.error('获取环境列表失败:', error)
    Message.error('获取环境列表失败')
  } finally {
    loading.value = false
  }
}

// 加载数据库配置名称
const enrichEnvironmentsWithDatabaseConfigNames = async () => {
  try {
    // 检查是否有环境关联了数据库配置
    const hasDbConfig = environments.value.some(env => env.database_config)
    if (!hasDbConfig) return
    
    // 获取数据库配置信息
    const response = await getDatabaseConfigs(Number(projectStore.currentProjectId))
    console.log('数据库配置响应:', response)
    
    // 获取实际的数据库配置数组
    let dbConfigs: DatabaseConfig[] = []
    const responseData = response.data
    
    // 判断是否是分页格式的响应
    if (responseData && typeof responseData === 'object' && 'results' in responseData && Array.isArray(responseData.results)) {
      dbConfigs = responseData.results
      console.log('从分页结果中获取数据库配置:', dbConfigs)
    } else if (Array.isArray(responseData)) {
      dbConfigs = responseData
      console.log('直接使用数据库配置数组:', dbConfigs)
    }
    
    if (dbConfigs.length > 0) {
      // 创建一个数据库配置ID到名称的映射
      const dbConfigMap = new Map<number, string>()
      dbConfigs.forEach(config => {
        dbConfigMap.set(config.id, config.name)
      })
      
      // 更新环境的数据库配置名称
      environments.value.forEach(env => {
        if (env.database_config && dbConfigMap.has(env.database_config)) {
          env.database_config_name = dbConfigMap.get(env.database_config)
        }
      })
    }
  } catch (error) {
    console.error('获取数据库配置信息失败:', error)
  }
}

// 监听项目变化
watch(
  () => projectStore.currentProjectId,
  () => {
    fetchEnvironments()
    activeTab.value = 'list'
    selectedEnvironment.value = null
  }
)

// 编辑环境相关
const editForm = ref<FormData>({
  name: '',
  base_url: '',
  description: '',
  project: 0,
  is_active: true,
  variables: [],
  database_config: null,
  verify_ssl: true
})

// 查看环境详情
const handleViewDetail = async (record: Environment) => {
  try {
    // 设置加载状态
    loading.value = true
    
    // 设置选中的环境，使UI立即响应
    selectedEnvironment.value = record
    
    // 切换到详情页面，使UI立即响应用户操作
    activeTab.value = 'detail'
    
    // 然后异步请求最新数据
    const response = await getEnvironmentDetail(record.id)
    if (response.data) {
      // 更新为最新数据
      selectedEnvironment.value = response.data
    }
  } catch (error) {
    console.error('获取环境详情失败:', error)
    Message.error('获取环境详情失败')
    // 如果获取详情失败，仍使用列表中的数据
    // selectedEnvironment.value 已设置，无需再次设置
  } finally {
    loading.value = false
  }
}

// 编辑环境
const handleEdit = async (record: Environment) => {
  try {
    loading.value = true
    formLoading.value = true  // 同时设置表单加载状态
    
    // 先切换到编辑页面并设置初始数据，让用户看到响应
    activeTab.value = 'edit'
    selectedEnvironment.value = record
    
    // 使用记录中的数据先初始化表单
    editForm.value = {
      id: record.id,
      name: record.name,
      base_url: record.base_url,
      description: record.description || '',
      project: record.project,
      is_active: record.is_active,
      variables: record.variables || [],
      database_config: record.database_config || "null",
      verify_ssl: record.verify_ssl !== false
    }
    
    // 然后异步获取完整数据
    const detailResponse = await getEnvironmentDetail(record.id)
    if (detailResponse.data) {
      const updatedRecord = detailResponse.data
      console.log('获取到完整的环境详情:', JSON.stringify(updatedRecord))
      
      // 更新选中的环境
      selectedEnvironment.value = updatedRecord
      
      // 设置数据库配置值
      let updatedDatabaseConfig = "null"
      if (updatedRecord.database_config_info) {
        console.log('从 database_config_info 获取数据库配置:', updatedRecord.database_config_info)
        updatedDatabaseConfig = updatedRecord.database_config_info.id
      }
      
      // 更新编辑表单
      editForm.value = {
        id: updatedRecord.id,
        name: updatedRecord.name,
        base_url: updatedRecord.base_url,
        description: updatedRecord.description || '',
        project: updatedRecord.project_info.id,
        is_active: updatedRecord.is_active,
        variables: updatedRecord.variables || [],
        database_config: updatedDatabaseConfig,
        verify_ssl: updatedRecord.verify_ssl !== false,
        database_config_info: updatedRecord.database_config_info
      }
      
      console.log('编辑表单已更新:', {
        database_config: updatedDatabaseConfig,
        database_config_info: updatedRecord.database_config_info
      })
    }
  } catch (error) {
    console.error('获取环境详情失败:', error)
    Message.error('获取环境详情失败')
  } finally {
    loading.value = false
    formLoading.value = false  // 确保加载状态被重置
  }
}

const handleEditSubmit = async () => {
  if (!selectedEnvironment.value) return
  
  try {
    formLoading.value = true
    
    // 准备提交数据
    const formData = { ...editForm.value }
    
    // 处理数据库配置
    if (formData.database_config === "null") {
      formData.database_config = null
    }
    
    // 移除不需要提交的字段
    delete formData.database_config_info
    
    // 提交更新
    const response = await updateEnvironment(selectedEnvironment.value.id, formData)
    
    if (response.data) {
      Message.success('更新环境成功')
      
      // 获取最新数据
      const detailResponse = await getEnvironmentDetail(selectedEnvironment.value.id)
      if (detailResponse.data) {
        const updatedEnv = detailResponse.data
        
        // 更新选中的环境
        selectedEnvironment.value = updatedEnv
        
        // 设置数据库配置值
        let updatedDatabaseConfig = "null"
        if (updatedEnv.database_config_info) {
          updatedDatabaseConfig = updatedEnv.database_config_info.id
        }
        
        // 更新编辑表单
        editForm.value = {
          id: updatedEnv.id,
          name: updatedEnv.name,
          base_url: updatedEnv.base_url,
          description: updatedEnv.description || '',
          project: updatedEnv.project_info.id,
          is_active: updatedEnv.is_active,
          variables: updatedEnv.variables || [],
          database_config: updatedDatabaseConfig,
          verify_ssl: updatedEnv.verify_ssl !== false,
          database_config_info: updatedEnv.database_config_info
        }
      }
      
      // 刷新环境列表
      fetchEnvironments()
    }
  } catch (error) {
    console.error('更新环境失败:', error)
    Message.error('更新环境失败')
  } finally {
    formLoading.value = false
  }
}

const resetCreateForm = () => {
  createForm.value = {
    name: '',
    base_url: '',
    description: '',
    project: Number(projectStore.currentProjectId),
    is_active: true,
    variables: [],
    database_config: "null" as any,
    verify_ssl: true
  }
}

// 克隆环境
const handleClone = async (record: Environment) => {
  try {
    loading.value = true
    const cloneResponse = await cloneEnvironment(record.id, {
      project_id: record.project,
      name: `${record.name} - 副本`
    })
    
    if (cloneResponse.data) {
      Message.success('克隆环境成功')
      
      // 异步刷新环境列表
      fetchEnvironments().then(() => {
        // 列表刷新后，找到新克隆的环境并选中它
        const clonedEnv = environments.value.find(env => env.id === cloneResponse.data.id)
        if (clonedEnv) {
          // 直接查看克隆的环境详情
          handleViewDetail(clonedEnv).catch(err => {
            console.error('查看克隆环境详情失败:', err)
          })
        }
      }).catch(err => {
        console.error('刷新环境列表失败:', err)
      })
    }
  } catch (error: any) {
    console.error('克隆环境失败:', error)
    Message.error(error.message || '克隆环境失败')
  } finally {
    loading.value = false
  }
}

// 添加计算属性
const currentForm = computed({
  get: () => activeTab.value === 'edit' ? editForm.value : createForm.value,
  set: (value) => {
  if (activeTab.value === 'edit') {
      editForm.value = value
  } else {
      createForm.value = value
  }
}
})

// 添加对 selectedEnvironment 的监听
watch(() => selectedEnvironment.value, (newVal) => {
  console.log('选中的环境:', newVal)
}, { deep: true })

// 切换到全局请求头
const handleSelectGlobalHeaders = () => {
  showGlobalHeaders.value = true
  showDatabaseConfig.value = false
  selectedEnvironment.value = null
  activeTab.value = 'global-headers'
}

// 切换到数据库配置
const handleSelectDatabaseConfig = () => {
  showDatabaseConfig.value = true
  showGlobalHeaders.value = false
  selectedEnvironment.value = null
  activeTab.value = 'database-config'
}

onMounted(() => {
  if (projectStore.currentProjectId) {
    fetchEnvironments()
  }
})
</script>

<template>
  <div class="tw-p-4 tw-h-full tw-flex tw-gap-4 tw-overflow-hidden">
    <!-- 环境列表面板 -->
    <div class="tw-w-90 tw-flex-shrink-0 tw-h-full tw-overflow-hidden">
      <EnvironmentList
        :environments="environments"
        :selectedEnvironment="selectedEnvironment"
        :loading="loading"
        :searchKeyword="searchKeyword"
        :showGlobalHeaders="showGlobalHeaders"
        :showDatabaseConfig="showDatabaseConfig"
        @update:searchKeyword="searchKeyword = $event"
        @select="handleViewDetail"
        @create="switchToCreate"
        @selectGlobalHeaders="handleSelectGlobalHeaders"
        @selectDatabaseConfig="handleSelectDatabaseConfig"
      />
    </div>

    <!-- 右侧内容区域 - 使用单一卡片设计 -->
    <div class="tw-flex-1 tw-min-w-0 tw-overflow-hidden right-content tw-bg-[#1D2433] tw-rounded-lg tw-border tw-border-gray-800">
      <!-- 列表状态 -->
      <div v-if="activeTab === 'list'" class="tw-h-full tw-flex tw-flex-col">
        <div class="content-header">
          <div class="tw-flex tw-items-center tw-justify-between tw-w-full">
            <div class="tw-flex tw-items-center tw-gap-3">
              <div class="tw-w-10 tw-h-10 tw-rounded-lg tw-bg-blue-500/10 tw-flex tw-items-center tw-justify-center">
                <IconStorage class="tw-text-blue-500 tw-text-xl" />
              </div>
              <h2 class="tw-text-xl tw-font-medium tw-text-gray-100">环境管理</h2>
            </div>
            <div class="tw-flex tw-gap-2">
              <a-button type="outline" size="small" @click="switchToCreate">
                <template #icon><IconPlus /></template>
                创建新环境
              </a-button>
              <a-button type="outline" size="small" @click="handleSelectGlobalHeaders">
                <template #icon><IconSettings /></template>
                全局请求头
              </a-button>
              <a-button type="outline" size="small" @click="handleSelectDatabaseConfig">
                <template #icon><IconStorage /></template>
                数据库配置
              </a-button>
            </div>
          </div>
        </div>
        
        <div class="content-body tw-flex tw-items-center tw-justify-center">
          <div class="tw-text-center">
            <div class="tw-mb-6">
              <div class="tw-w-20 tw-h-20 tw-rounded-full tw-bg-gray-800/80 tw-flex tw-items-center tw-justify-center tw-mx-auto">
                <IconStorage class="tw-text-gray-500 tw-text-3xl" />
              </div>
            </div>
            <div class="tw-mb-3 tw-text-xl tw-text-gray-300">请选择一个环境</div>
            <div class="tw-max-w-md tw-mx-auto tw-text-gray-400 tw-mb-6">
              从左侧列表选择一个环境进行查看和编辑，或者使用右上角的按钮进行创建或管理全局请求头
            </div>
          </div>
        </div>
      </div>

      <!-- 创建环境表单 -->
      <div v-else-if="activeTab === 'create'" class="tw-h-full tw-flex tw-flex-col">
        <div class="content-header">
          <div class="tw-flex tw-items-center tw-justify-between tw-w-full">
            <div class="tw-flex tw-items-center tw-gap-3">
              <h2 class="tw-text-xl tw-font-medium tw-text-gray-100">创建新环境</h2>
            </div>
            <div class="tw-flex tw-items-center tw-gap-2">
              <a-button type="primary" size="small" @click="handleCreate">
                <template #icon><IconPlus /></template>
                创建环境
              </a-button>
              <a-button type="outline" size="small" @click="activeTab = 'list'">
                返回
              </a-button>
            </div>
          </div>
        </div>
        
        <div class="content-body">
          <EnvironmentForm
            v-model="createForm"
            :loading="formLoading"
            mode="create"
            @cancel="activeTab = 'list'"
            @submit="handleCreate"
            :key="`create-form`"
          />
        </div>
      </div>

      <!-- 编辑环境表单 -->
      <div v-else-if="activeTab === 'edit'" class="tw-h-full tw-flex tw-flex-col">
        <div class="content-header">
          <div class="tw-flex tw-items-center tw-justify-between tw-w-full">
            <div class="tw-flex tw-items-center tw-gap-3">
              <h2 class="tw-text-xl tw-font-medium tw-text-gray-100">{{ editForm.name }}</h2>
            </div>
            <div class="tw-flex tw-items-center tw-gap-2">
              <a-button type="primary" size="small" @click="handleEditSubmit">
                <template #icon><IconEdit /></template>
                保存更改
              </a-button>
              <a-button type="outline" size="small" @click="activeTab = 'detail'">
                返回
              </a-button>
            </div>
          </div>
        </div>
        
        <div class="content-body">
          <EnvironmentForm
            v-model="editForm"
            :loading="formLoading"
            mode="edit"
            @cancel="activeTab = 'detail'"
            @submit="handleEditSubmit"
            :key="`edit-form-${editForm.id}`"
          />
        </div>
      </div>

      <!-- 环境详情 -->
      <div v-else-if="activeTab === 'detail' && selectedEnvironment" class="tw-h-full tw-flex tw-flex-col">
        <div class="content-header">
          <div class="tw-flex tw-items-center tw-justify-between tw-w-full">
            <div class="tw-flex tw-items-center tw-gap-3">
              <div class="tw-w-10 tw-h-10 tw-rounded-lg tw-bg-blue-500/10 tw-flex tw-items-center tw-justify-center">
                <IconStorage class="tw-text-blue-500 tw-text-xl" />
              </div>
              <div>
                <div class="tw-flex tw-items-center tw-gap-2">
                  <h2 class="tw-text-xl tw-font-medium tw-text-gray-100">{{ selectedEnvironment.name }}</h2>
                  <a-tag
                    :color="selectedEnvironment.is_active ? 'green' : 'red'"
                    size="small"
                  >{{ selectedEnvironment.is_active ? '启用' : '禁用' }}</a-tag>
                </div>
                <div class="tw-text-gray-400 tw-text-sm tw-truncate tw-max-w-md">{{ selectedEnvironment.base_url }}</div>
              </div>
            </div>
            <div class="tw-flex tw-gap-2">
              <a-button type="outline" size="small" @click="() => handleEdit(selectedEnvironment!)">
                <template #icon><IconEdit /></template>
                编辑
              </a-button>
              <a-button type="outline" size="small" @click="handleClone(selectedEnvironment!)">
                <template #icon><IconCopy /></template>
                克隆
              </a-button>
              <a-popconfirm
                content="确定要删除这个环境吗？"
                type="warning"
                position="left"
                @ok="handleDelete(selectedEnvironment!)"
              >
                <a-button type="outline" status="danger" size="small">
                  删除
                </a-button>
              </a-popconfirm>
              <a-button type="outline" size="small" @click="activeTab = 'list'">
                返回
              </a-button>
            </div>
          </div>
        </div>
        
        <div class="content-body">
          <div class="tw-h-full tw-overflow-y-auto tw-overflow-x-hidden custom-scrollbar tw-space-y-4 tw-pb-4 tw-pr-1">
            <!-- 基本信息卡片 -->
            <div class="tw-space-y-6 tw-overflow-hidden">
              <!-- 所属项目 -->
              <div class="tw-space-y-2">
                <div class="tw-flex tw-items-center tw-gap-2">
                  <icon-storage class="tw-text-gray-400" />
                  <span class="tw-text-gray-300 tw-font-medium">所属项目</span>
                </div>
                <div class="tw-p-3 tw-bg-gray-800/50 tw-rounded-lg tw-text-gray-300 tw-break-all">
                  {{ selectedEnvironment.project_info?.name || selectedEnvironment.project_name }}
                </div>
              </div>
              
              <!-- 父环境 -->
              <div class="tw-space-y-2" v-if="selectedEnvironment.parent_info">
                <div class="tw-flex tw-items-center tw-gap-2">
                  <icon-storage class="tw-text-gray-400" />
                  <span class="tw-text-gray-300 tw-font-medium">父环境</span>
                </div>
                <div class="tw-p-3 tw-bg-gray-800/50 tw-rounded-lg tw-text-gray-300 tw-break-all">
                  {{ selectedEnvironment.parent_info.name }}
                </div>
              </div>
              
              <!-- 基础URL -->
              <div class="tw-space-y-2">
                <div class="tw-flex tw-items-center tw-gap-2">
                  <icon-link class="tw-text-gray-400" />
                  <span class="tw-text-gray-300 tw-font-medium">基础 URL</span>
                </div>
                <div class="tw-p-3 tw-bg-gray-800/50 tw-rounded-lg tw-text-gray-300 tw-break-all">
                  {{ selectedEnvironment.base_url }}
                </div>
              </div>
              
              <!-- 验证SSL -->
              <div class="tw-space-y-2">
                <div class="tw-flex tw-items-center tw-gap-2">
                  <icon-link class="tw-text-gray-400" />
                  <span class="tw-text-gray-300 tw-font-medium">验证SSL</span>
                </div>
                <div class="tw-p-3 tw-bg-gray-800/50 tw-rounded-lg tw-text-gray-300 tw-break-all">
                  {{ selectedEnvironment.verify_ssl !== false ? '是' : '否' }}
                </div>
              </div>
              
              <!-- 关联数据库配置 - 使用新的数据结构 -->
              <div class="tw-space-y-2" v-if="selectedEnvironment.database_config_info">
                <div class="tw-flex tw-items-center tw-gap-2">
                  <icon-storage class="tw-text-gray-400" />
                  <span class="tw-text-gray-300 tw-font-medium">关联数据库</span>
                </div>
                <div class="tw-p-3 tw-bg-gray-800/50 tw-rounded-lg tw-text-gray-300 tw-space-y-2">
                  <div class="tw-flex tw-items-center tw-gap-2 tw-flex-wrap">
                    <span class="tw-text-gray-400">名称：</span>
                    <span class="tw-break-all">{{ selectedEnvironment.database_config_info.name }}</span>
                  </div>
                  <div class="tw-flex tw-items-center tw-gap-2 tw-flex-wrap">
                    <span class="tw-text-gray-400">类型：</span>
                    <span>{{ selectedEnvironment.database_config_info.db_type }}</span>
                  </div>
                  <div class="tw-flex tw-items-center tw-gap-2 tw-flex-wrap">
                    <span class="tw-text-gray-400">主机：</span>
                    <span>{{ selectedEnvironment.database_config_info.host }}</span>
                  </div>
                </div>
              </div>
              
              <!-- 保留旧的数据库配置显示方式作为备选，防止旧接口数据结构导致显示问题 -->
              <div class="tw-space-y-2" v-else-if="selectedEnvironment.database_config">
                <div class="tw-flex tw-items-center tw-gap-2">
                  <icon-storage class="tw-text-gray-400" />
                  <span class="tw-text-gray-300 tw-font-medium">关联数据库</span>
                </div>
                <div class="tw-p-3 tw-bg-gray-800/50 tw-rounded-lg tw-text-gray-300 tw-break-all">
                  <span class="tw-flex tw-items-center tw-gap-2">
                    <span class="tw-inline-flex tw-items-center tw-justify-center tw-w-6 tw-h-6 tw-rounded-full tw-bg-purple-500/10">
                      <icon-storage class="tw-text-purple-400 tw-text-sm" />
                    </span>
                    {{ selectedEnvironment.database_config_name || `数据库配置 ID: ${selectedEnvironment.database_config}` }}
                  </span>
                </div>
              </div>
              
              <!-- 描述 -->
              <div class="tw-space-y-2" v-if="selectedEnvironment.description">
                <div class="tw-flex tw-items-center tw-gap-2">
                  <icon-file class="tw-text-gray-400" />
                  <span class="tw-text-gray-300 tw-font-medium">描述</span>
                </div>
                <div class="tw-p-3 tw-bg-gray-800/50 tw-rounded-lg tw-text-gray-300 tw-whitespace-pre-wrap">
                  {{ selectedEnvironment.description }}
                </div>
              </div>
              <!-- 创建信息 -->
              <div class="tw-space-y-2">
                <div class="tw-flex tw-items-center tw-gap-2">
                  <icon-info-circle class="tw-text-gray-400" />
                  <span class="tw-text-gray-300 tw-font-medium">创建信息</span>
                </div>
                <div class="tw-p-3 tw-bg-gray-800/50 tw-rounded-lg tw-text-gray-300 tw-space-y-2">
                  <div class="tw-flex tw-items-center tw-gap-2 tw-flex-wrap">
                    <span class="tw-text-gray-400">创建人：</span>
                    <span class="tw-break-all">{{ selectedEnvironment.created_by_name }}</span>
                  </div>
                  <div class="tw-flex tw-items-center tw-gap-2 tw-flex-wrap">
                    <span class="tw-text-gray-400">创建时间：</span>
                    <span>{{ new Date(selectedEnvironment.created_time).toLocaleString('zh-CN') }}</span>
                  </div>
                  <div class="tw-flex tw-items-center tw-gap-2 tw-flex-wrap">
                    <span class="tw-text-gray-400">更新时间：</span>
                    <span>{{ new Date(selectedEnvironment.updated_time).toLocaleString('zh-CN') }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 环境变量列表 -->
            <div class="tw-space-y-4 tw-mt-8">
              <div class="tw-flex tw-items-center tw-justify-between">
                <div class="tw-flex tw-items-center tw-gap-2">
                  <icon-storage class="tw-text-gray-400" />
                  <span class="tw-text-gray-300 tw-font-medium">环境变量</span>
                </div>
              </div>
              <div class="tw-space-y-4">
                <div
                  v-for="(variable, index) in selectedEnvironment.variables"
                  :key="index"
                  class="tw-flex tw-items-start tw-gap-3 tw-p-3 tw-bg-gray-900/60 tw-rounded-lg"
                >
                  <div class="tw-w-8 tw-h-8 tw-rounded-lg tw-bg-purple-500/10 tw-flex tw-items-center tw-justify-center tw-flex-shrink-0">
                    <icon-storage class="tw-text-purple-400" />
                  </div>
                  <div class="tw-flex-1 tw-min-w-0 tw-overflow-hidden">
                    <div class="tw-flex tw-items-center tw-gap-2 tw-mb-2 tw-flex-wrap">
                      <span class="tw-text-sm tw-font-medium tw-text-gray-300">{{ variable.name }}</span>
                      <span class="tw-text-xs tw-text-gray-500">·</span>
                      <span class="tw-text-xs tw-text-gray-400 tw-truncate">{{ variable.description || '暂无描述' }}</span>
                    </div>
                    <div class="tw-space-y-1 tw-overflow-hidden">
                      <div class="tw-text-xs tw-text-gray-400">变量值</div>
                      <div class="tw-text-sm tw-text-gray-300 tw-break-all tw-p-2 tw-bg-gray-800/50 tw-rounded">{{ variable.value }}</div>
                    </div>
                  </div>
                </div>
                
                <!-- 无变量时的提示 -->
                <div
                  v-if="!selectedEnvironment.variables?.length"
                  class="tw-text-center tw-py-8 tw-text-gray-400"
                >
                  暂无环境变量
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 全局请求头面板 -->
      <div v-else-if="activeTab === 'global-headers'" class="tw-h-full tw-flex tw-flex-col">
        <div class="content-header">
          <div class="tw-flex tw-items-center tw-justify-between tw-w-full">
            <div class="tw-flex tw-items-center tw-gap-3">
              <div class="tw-w-10 tw-h-10 tw-rounded-lg tw-bg-teal-500/10 tw-flex tw-items-center tw-justify-center">
                <IconSettings class="tw-text-teal-500 tw-text-xl" />
              </div>
              <div>
                <h2 class="tw-text-xl tw-font-medium tw-text-gray-100">全局请求头</h2>
                <div class="tw-text-gray-400 tw-text-sm">项目级别的请求头设置</div>
              </div>
            </div>
            <div class="tw-flex tw-gap-2">
              <a-button type="primary" size="small" @click="globalHeadersPanel?.handleCreate?.()">
                <template #icon><IconPlus /></template>
                添加请求头
              </a-button>
              <a-button type="outline" size="small" @click="activeTab = 'list'">
                返回
              </a-button>
            </div>
          </div>
        </div>
        
        <div class="content-body">
          <GlobalHeadersPanel ref="globalHeadersPanel" />
        </div>
      </div>

      <!-- 数据库配置面板 -->
      <div v-else-if="activeTab === 'database-config'" class="tw-h-full tw-flex tw-flex-col">
        <div class="content-header">
          <div class="tw-flex tw-items-center tw-justify-between tw-w-full">
            <div class="tw-flex tw-items-center tw-gap-3">
              <div class="tw-w-10 tw-h-10 tw-rounded-lg tw-bg-purple-500/10 tw-flex tw-items-center tw-justify-center">
                <IconStorage class="tw-text-purple-500 tw-text-xl" />
              </div>
              <div>
                <h2 class="tw-text-xl tw-font-medium tw-text-gray-100">数据库配置</h2>
                <div class="tw-text-gray-400 tw-text-sm">数据库配置设置</div>
              </div>
            </div>
            <div class="tw-flex tw-gap-2">
              <a-button type="primary" size="small" @click="databaseConfigPanel?.handleCreate?.()">
                <template #icon><IconPlus /></template>
                添加配置
              </a-button>
              <a-button type="outline" size="small" @click="activeTab = 'list'">
                返回
              </a-button>
            </div>
          </div>
        </div>
        
        <div class="content-body">
          <DatabaseConfigPanel ref="databaseConfigPanel" />
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="postcss" scoped>
/* 滚动条样式 */
:deep(.arco-scrollbar),
.custom-scrollbar {
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
  
  &::-webkit-scrollbar {
    display: none; /* Chrome, Safari, Opera*/
  }
}

/* 右侧内容区域样式 */
.right-content {
  display: flex;
  flex-direction: column;
}

/* 内容头部样式 */
.content-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid rgba(55, 65, 81, 0.5);
}

/* 内容主体样式 */
.content-body {
  flex: 1;
  overflow: auto;
  padding: 1.5rem;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
  
  &::-webkit-scrollbar {
    display: none; /* Chrome, Safari, Opera*/
  }
}

/* 特殊处理全局请求头面板的容器 */
.content-body.tw-p-0 {
  padding: 0;
}

/* 图标容器样式 */
.tw-w-10.tw-h-10.tw-rounded-lg {
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }
}

/* 标题样式 */
h2.tw-text-xl {
  line-height: 1.3;
}

/* 圆形图标背景 */
.tw-rounded-full.tw-bg-gray-800\/80 {
  box-shadow: 0 0 15px rgba(30, 41, 59, 0.4);
  transition: all 0.3s ease;
  
  &:hover {
    transform: scale(1.05);
    box-shadow: 0 0 20px rgba(30, 41, 59, 0.6);
  }
}

/* 按钮样式增强 */
:deep(.arco-btn) {
  transition: all 0.2s ease;
  
  &:hover {
    transform: translateY(-1px);
  }
}

/* 表格通用样式 */
:deep(.arco-table) {
  border-radius: 0.5rem;
  overflow: hidden;

  .arco-table-th {
    height: 2.75rem;
    color: rgba(209, 213, 219, 1);
    font-weight: 500;
    background-color: rgba(31, 41, 55, 0.5);
    border-bottom: 1px solid rgba(75, 85, 99, 0.4) !important;
  }

  .arco-table-td {
    background-color: transparent;
    color: rgba(209, 213, 219, 1);
    border-bottom: 1px solid rgba(75, 85, 99, 0.2) !important;
  }

  .arco-table-tr:hover .arco-table-td {
    background-color: rgba(31, 41, 55, 0.3) !important;
  }
}

/* 表单样式 */
:deep(.arco-form-item-label) {
  color: rgba(209, 213, 219, 1);
}

:deep(.arco-input-wrapper),
:deep(.arco-textarea-wrapper) {
  background-color: rgba(17, 24, 39, 1);
  border: 1px solid rgba(55, 65, 81, 0.7);
}

:deep(.arco-input),
:deep(.arco-textarea) {
  color: rgba(209, 213, 219, 1);
  background-color: rgba(17, 24, 39, 1);
}

:deep(.arco-switch) {
  background-color: rgba(239, 68, 68, 0.2);
}

:deep(.arco-switch-checked) {
  background-color: rgba(16, 185, 129, 0.2);
}
</style> 