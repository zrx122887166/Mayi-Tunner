<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconPlus, IconEmpty, IconStar, IconDelete } from '@arco-design/web-vue/es/icon'
import { syncApi, type SyncConfig } from '@/api/sync'
import type { TableColumnData } from '@arco-design/web-vue'
import { useProjectStore } from '@/stores/project'
import SyncHistory from './history.vue'
import ApiConfig from './api-config.vue'

const projectStore = useProjectStore()
const loading = ref(false)
const configs = ref<SyncConfig[]>([])
const activeConfigId = ref<number | null>(null)
const showCreateModal = ref(false)
const isEditing = ref(false)
const editingConfigId = ref<number | null>(null)
const activeTab = ref('config')

const formModel = ref({
  name: '',
  description: '',
  sync_fields: [] as string[],
  sync_enabled: true,
  sync_mode: 'manual' as 'manual' | 'auto',
  is_active: false
})

const fieldOptions = [
  { label: '请求方法', value: 'method' },
  { label: 'URL', value: 'url' },
  { label: '请求头', value: 'headers' },
  { label: '查询参数', value: 'params' },
  { label: '请求体', value: 'body' },
  { label: '前置钩子', value: 'setup_hooks' },
  { label: '后置钩子', value: 'teardown_hooks' },
  { label: '变量定义', value: 'variables' },
  { label: '断言规则', value: 'validators' },
  { label: '提取变量', value: 'extract' }
]

const columns: TableColumnData[] = [
  {
    title: '序号',
    width: 80,
    align: 'center',
    slotName: 'index'
  },
  {
    title: '配置名称',
    dataIndex: 'name',
    slotName: 'name'
  },
  {
    title: '同步字段',
    dataIndex: 'sync_fields',
    slotName: 'sync_fields'
  },
  {
    title: '同步模式',
    dataIndex: 'sync_mode_display'
  },
  {
    title: '状态',
    slotName: 'status'
  },
  {
    title: '创建信息',
    slotName: 'created_info'
  },
  {
    title: '操作',
    width: 100,
    slotName: 'operations'
  }
]

const fetchConfigs = async () => {
  if (!projectStore.currentProject?.id) {
    Message.error('请先选择项目')
    return
  }

  try {
    loading.value = true
    const { data } = await syncApi.getConfigs(projectStore.currentProject.id)
    configs.value = data.configs
    activeConfigId.value = data.active_config_id
  } catch (error) {
    Message.error('获取配置列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 监听项目变化时重新获取配置列表
watch(() => projectStore.currentProject?.id, (newProjectId: number | undefined) => {
  if (newProjectId) {
    fetchConfigs()
  } else {
    configs.value = []
    activeConfigId.value = null
  }
})

const handleEdit = (record: SyncConfig) => {
  isEditing.value = true
  editingConfigId.value = record.id
  formModel.value = {
    name: record.name,
    description: record.description || '',
    sync_fields: record.sync_fields,
    sync_enabled: record.sync_enabled,
    sync_mode: record.sync_mode,
    is_active: record.is_active
  }
  showCreateModal.value = true
}

const handleSubmit = async () => {
  if (!projectStore.currentProject?.id) {
    Message.error('请先选择项目')
    return
  }

  try {
    loading.value = true
    const data = {
      project: projectStore.currentProject.id,
      name: formModel.value.name,
      description: formModel.value.description,
      sync_fields: formModel.value.sync_fields,
      sync_enabled: formModel.value.sync_enabled,
      sync_mode: formModel.value.sync_mode,
      is_active: formModel.value.is_active
    }

    if (isEditing.value && editingConfigId.value) {
      await syncApi.updateConfig(editingConfigId.value, data)
      Message.success('更新配置成功')
    } else {
      await syncApi.createConfig(data)
      Message.success('创建配置成功')
    }
    
    showCreateModal.value = false
    Object.assign(formModel, {
      name: '',
      description: '',
      sync_fields: [],
      sync_enabled: true,
      sync_mode: 'manual',
      is_active: false
    })
    isEditing.value = false
    editingConfigId.value = null
    await fetchConfigs()
  } catch (error: any) {
    if (error.errors) {
      const errorMessages = Object.values(error.errors).flat()
      Message.error(errorMessages.join(', '))
    } else {
      Message.error(isEditing.value ? '更新配置失败' : '创建配置失败')
    }
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleActivateConfig = async (configId: number) => {
  try {
    loading.value = true
    await syncApi.setActiveConfig(configId)
    Message.success('切换配置成功')
    await fetchConfigs()
  } catch (error) {
    Message.error('切换配置失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleDelete = async (record: SyncConfig) => {
  Modal.warning({
    title: '确认删除',
    content: `确定要删除配置"${record.name}"吗？此操作不可恢复。`,
    okText: '确认删除',
    cancelText: '取消',
    async onOk() {
      try {
        loading.value = true
        await syncApi.deleteConfig(record.id)
        Message.success('删除配置成功')
        await fetchConfigs()
      } catch (error) {
        Message.error('删除配置失败')
        console.error(error)
      } finally {
        loading.value = false
      }
    }
  })
}

onMounted(() => {
  if (projectStore.currentProject?.id) {
    fetchConfigs()
  }
})
</script>

<template>
  <div class="tw-p-6 main-container">
    <div class="custom-card tw-p-6">
      <div class="tw-flex tw-items-center tw-justify-between tw-mb-6">
        <div class="tw-flex tw-items-center">
          <h1 class="tw-text-2xl tw-font-semibold tw-text-gray-100">同步配置</h1>
          <a-tabs type="text" v-model:activeKey="activeTab" class="tw-ml-8">
            <a-tab-pane key="config" title="配置管理" />
            <a-tab-pane key="api-config" title="接口同步配置" />
            <a-tab-pane key="history" title="同步历史" />
          </a-tabs>
        </div>
        <div v-if="activeTab === 'config'" class="tw-flex tw-gap-2">
          <a-button 
            type="outline" 
            :loading="loading" 
            @click="showCreateModal = true"
          >
            <template #icon>
              <icon-plus />
            </template>
            新建配置
          </a-button>
        </div>
      </div>

      <div class="tw-mt-4">
        <template v-if="activeTab === 'config'">
          <a-table
            :loading="loading"
            :data="configs"
            :columns="columns"
            :pagination="false"
            :bordered="true"
            :stripe="true"
            class="custom-table"
          >
            <template #empty>
              <div class="tw-flex tw-flex-col tw-items-center tw-justify-center tw-py-8">
                <IconEmpty class="tw-text-gray-600 tw-w-12 tw-h-12 tw-mb-4" />
                <div class="tw-text-gray-400 tw-mb-6">暂无同步配置</div>
                <a-button type="outline" @click="showCreateModal = true">
                  <template #icon>
                    <icon-plus />
                  </template>
                  新建配置
                </a-button>
              </div>
            </template>

            <template #name="{ record }">
              <div 
                class="tw-flex tw-flex-col tw-cursor-pointer tw-p-1 tw-rounded hover:tw-bg-gray-700 tw-transition-all tw-duration-200" 
                @click="handleEdit(record)"
              >
                <span class="tw-font-medium tw-text-blue-400 hover:tw-text-blue-300">{{ record.name }}</span>
                <span v-if="record.description" class="tw-text-gray-400 tw-text-sm">{{ record.description }}</span>
              </div>
            </template>

            <template #sync_fields="{ record }">
              <div class="tw-flex tw-flex-wrap tw-gap-1">
                <a-tag 
                  v-for="field in record.sync_fields" 
                  :key="field"
                  color="arcoblue"
                  size="small"
                >
                  {{ fieldOptions.find(opt => opt.value === field)?.label }}
                </a-tag>
              </div>
            </template>

            <template #status="{ record }">
              <div class="tw-flex tw-gap-1">
                <a-tag v-if="record.is_current" color="arcoblue">当前配置</a-tag>
                <a-tag v-if="!record.sync_enabled" color="red">已禁用</a-tag>
              </div>
            </template>

            <template #created_info="{ record }">
              <div class="tw-flex tw-flex-col tw-gap-1 tw-text-sm">
                <span>创建者：{{ record.created_by_info?.username || '-' }}</span>
                <span>创建时间：{{ record.created_time ? new Date(record.created_time).toLocaleString() : '-' }}</span>
              </div>
            </template>

            <template #operations="{ record }">
              <div class="tw-flex tw-gap-2">
                <a-button
                  v-if="!record.is_current"
                  type="outline"
                  size="mini"
                  :loading="loading"
                  @click="handleActivateConfig(record.id)"
                >
                  设为当前配置
                </a-button>
                <a-button
                  v-if="!record.is_current"
                  type="outline"
                  status="danger"
                  size="mini"
                  :loading="loading"
                  @click="handleDelete(record)"
                >
                  <template #icon>
                    <icon-delete />
                  </template>
                </a-button>
              </div>
            </template>

            <template #index="{ rowIndex }">
              {{ rowIndex + 1 }}
            </template>
          </a-table>
        </template>
        <template v-else-if="activeTab === 'api-config'">
          <api-config />
        </template>
        <template v-else>
          <sync-history />
        </template>
      </div>

      <!-- 创建配置弹窗 -->
      <a-modal
        v-model:visible="showCreateModal"
        :title="isEditing ? '编辑配置' : '新建配置'"
        class="custom-card"
        @ok="handleSubmit"
        @cancel="() => {
          showCreateModal = false
          isEditing = false
          editingConfigId = null
          Object.assign(formModel, {
            name: '',
            description: '',
            sync_fields: [],
            sync_enabled: true,
            sync_mode: 'manual',
            is_active: false
          })
        }"
      >
        <a-form :model="formModel" layout="vertical">
          <a-form-item field="name" label="配置名称" required>
            <a-input
              v-model="formModel.name"
              placeholder="请输入配置名称"
              allow-clear
            />
          </a-form-item>

          <a-form-item field="description" label="配置描述">
            <a-textarea
              v-model="formModel.description"
              placeholder="请输入配置描述"
              allow-clear
            />
          </a-form-item>

          <a-form-item field="sync_fields" label="同步字段" required>
            <a-select
              v-model="formModel.sync_fields"
              placeholder="请选择同步字段"
              multiple
            >
              <a-option
                v-for="option in fieldOptions"
                :key="option.value"
                :value="option.value"
                :label="option.label"
              />
            </a-select>
          </a-form-item>

          <a-form-item field="sync_mode" label="同步模式" required>
            <a-radio-group v-model="formModel.sync_mode">
              <a-radio value="manual">手动同步</a-radio>
              <a-radio value="auto">自动同步</a-radio>
            </a-radio-group>
          </a-form-item>

          <div class="tw-flex tw-justify-between tw-items-center tw-mt-4 tw-pt-4 tw-border-t tw-border-gray-700">
            <a-checkbox v-model="formModel.sync_enabled">
              <template #default>
                <span class="tw-text-gray-300">启用同步</span>
              </template>
            </a-checkbox>
            <a-checkbox v-model="formModel.is_active">
              <template #default>
                <span class="tw-text-gray-300">设为当前配置</span>
              </template>
            </a-checkbox>
          </div>
        </a-form>
      </a-modal>
    </div>
  </div>
</template>

<style scoped>
.main-container {
  height: 100%;
  overflow-y: auto;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

.main-container::-webkit-scrollbar {
  display: none; /* Chrome, Safari, Opera */
}

:deep(.arco-form-item-label-col) {
  @apply tw-text-gray-300;
}

:deep(.arco-radio) {
  @apply tw-text-gray-300;
}

:deep(.arco-checkbox) {
  @apply tw-text-gray-300;
}

:deep(.arco-input-wrapper) {
  @apply tw-bg-gray-700 tw-border-gray-600;
}

:deep(.arco-input-wrapper:hover) {
  @apply tw-border-blue-500;
}

:deep(.arco-input) {
  @apply tw-text-gray-300;
}

:deep(.arco-textarea) {
  @apply tw-bg-gray-700 tw-border-gray-600 tw-text-gray-300;
}

:deep(.arco-textarea:hover) {
  @apply tw-border-blue-500;
}

:deep(.arco-select-view) {
  @apply tw-bg-gray-700 tw-border-gray-600 tw-text-gray-300;
}

:deep(.arco-select-view:hover) {
  @apply tw-border-blue-500;
}

:deep(.arco-modal) {
  @apply tw-bg-gray-800;
}

:deep(.arco-modal-header) {
  @apply tw-bg-gray-800 tw-border-gray-700;
}

:deep(.arco-modal-title) {
  @apply tw-text-gray-200;
}

:deep(.arco-modal-footer) {
  @apply tw-bg-gray-800 tw-border-gray-700;
}

:deep(.custom-table) {
  @apply tw-bg-transparent tw-rounded-lg tw-overflow-hidden tw-border tw-border-gray-700;
}

:deep(.custom-table .arco-table-container) {
  @apply tw-border-gray-700;
}

:deep(.custom-table .arco-table-th) {
  @apply tw-bg-gray-950 tw-text-gray-200 tw-border-gray-700 tw-font-medium tw-text-sm;
}

:deep(.custom-table .arco-table-th .arco-table-th-cell) {
  @apply tw-py-4;
}

:deep(.custom-table .arco-table-th:first-child) {
  @apply tw-rounded-tl-lg;
}

:deep(.custom-table .arco-table-th:last-child) {
  @apply tw-rounded-tr-lg;
}

:deep(.custom-table .arco-table-tr:last-child .arco-table-td:first-child) {
  @apply tw-rounded-bl-lg;
}

:deep(.custom-table .arco-table-tr:last-child .arco-table-td:last-child) {
  @apply tw-rounded-br-lg;
}

:deep(.custom-table .arco-table-td) {
  @apply tw-bg-gray-800 tw-text-gray-300 tw-border-gray-700;
}

:deep(.custom-table .arco-table-tr:hover .arco-table-td) {
  @apply tw-bg-gray-700;
}

:deep(.custom-table .arco-table-border-cell .arco-table-td) {
  @apply tw-border-gray-700;
}

/* 隐藏默认滚动条 */
:deep(.arco-table-body) {
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
  &::-webkit-scrollbar {
    display: none; /* Chrome, Safari, Opera */
  }
}

:deep(.arco-table-header) {
  scrollbar-width: none;
  -ms-overflow-style: none;
  &::-webkit-scrollbar {
    display: none;
  }
}

:deep(.arco-modal-body) {
  scrollbar-width: none;
  -ms-overflow-style: none;
  &::-webkit-scrollbar {
    display: none;
  }
}

.custom-card {
  @apply tw-bg-gray-800 tw-rounded-lg tw-shadow-lg tw-border tw-border-gray-700/50;
}

:deep(.arco-tabs) {
  @apply tw-flex tw-items-center;
}

:deep(.arco-tabs-nav) {
  @apply tw-border-0 tw-min-h-0 tw-h-auto tw-m-0;
}

:deep(.arco-tabs-nav-tab) {
  @apply tw-bg-transparent tw-min-h-0 tw-h-auto tw-m-0;
}

:deep(.arco-tabs-nav-tab-list) {
  @apply tw-bg-transparent tw-border-0 tw-min-h-0 tw-h-auto tw-m-0;
}

:deep(.arco-tabs-tab) {
  @apply tw-text-gray-400 tw-px-3 tw-py-0 tw-h-auto tw-leading-none;
}

:deep(.arco-tabs-tab-active) {
  @apply tw-text-blue-400;
}

:deep(.arco-tabs-content) {
  @apply tw-bg-transparent tw-border-0;
}
</style> 