<script setup lang="ts">
import { ref, onMounted, watch, h } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconRefresh } from '@arco-design/web-vue/es/icon'
import { syncApi, type SyncHistory } from '@/api/sync'
import type { TableColumnData } from '@arco-design/web-vue'
import { useProjectStore } from '@/stores/project'
import VueJsonPretty from 'vue-json-pretty'

const projectStore = useProjectStore()
const loading = ref(false)
const histories = ref<SyncHistory[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const showDetailModal = ref(false)
const currentHistory = ref<SyncHistory | null>(null)
const diffFields = ref<Array<{ key: string; oldValue: any; newValue: any; changed: boolean }>>([])
const showUnchanged = ref(false)

const columns: TableColumnData[] = [
  {
    title: '序号',
    width: 80,
    align: 'center',
    slotName: 'index'
  },
  {
    title: '配置名称',
    slotName: 'config_name'
  },
  {
    title: '同步字段',
    slotName: 'sync_fields'
  },
  {
    title: '同步状态',
    width: 100,
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

const fetchHistories = async () => {
  if (!projectStore.currentProject?.id) {
    Message.error('请先选择项目')
    return
  }

  try {
    loading.value = true
    const response = await syncApi.getHistories({
      project_id: projectStore.currentProject.id,
      page: currentPage.value,
      page_size: pageSize.value
    })
    
    // 打印原始响应，帮助调试
    console.log('同步历史API响应:', response);
    
    // 确保我们使用的是响应中的data字段
    const responseData = response.data;
    
    // 检查API返回的数据结构
    if ((responseData as any).results) {
      // 新的API结构
      histories.value = (responseData as any).results;
      total.value = (responseData as any).count || 0;
    } else if (responseData.histories) {
      // 旧的API结构
      histories.value = responseData.histories;
      total.value = responseData.total || 0;
    } else {
      console.error('未知的API响应结构:', responseData);
      histories.value = [];
      total.value = 0;
    }
  } catch (error) {
    Message.error('获取同步历史失败')
    console.error(error)
    histories.value = [];
    total.value = 0;
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchHistories()
}

const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchHistories()
}

const handleViewDetail = async (record: SyncHistory) => {
  try {
    loading.value = true
    const response = await syncApi.getHistoryDetail(record.id)
    currentHistory.value = response.data
    processDiffData() // 处理数据对比
    showDetailModal.value = true
  } catch (error) {
    Message.error('获取历史详情失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleRollback = async (record: SyncHistory) => {
  const configName = record.sync_config_info?.name || record.config?.name || '此历史记录';
  
  Modal.warning({
    title: '确认回滚',
    content: `确定要回滚到"${configName}"吗？此操作可能影响当前配置。`,
    okText: '确认回滚',
    cancelText: '取消',
    async onOk() {
      try {
        loading.value = true
        await syncApi.rollbackHistory(record.id)
        Message.success('回滚成功')
        await fetchHistories()
      } catch (error) {
        Message.error('回滚失败')
        console.error(error)
      } finally {
        loading.value = false
      }
    }
  })
}

// 处理数据对比
const processDiffData = () => {
  if (!currentHistory.value) return
  
  const oldData = currentHistory.value.old_data || {}
  const newData = currentHistory.value.new_data || {}
  const allKeys = new Set([...Object.keys(oldData), ...Object.keys(newData)])
  
  diffFields.value = Array.from(allKeys).map(key => {
    const oldValue = oldData[key]
    const newValue = newData[key]
    return {
      key,
      oldValue,
      newValue,
      changed: JSON.stringify(oldValue) !== JSON.stringify(newValue)
    }
  }).sort((a, b) => {
    // 把变更的字段排在前面
    if (a.changed && !b.changed) return -1
    if (!a.changed && b.changed) return 1
    return a.key.localeCompare(b.key)
  })
}

// 格式化值的显示
const formatValue = (value: any): string => {
  if (value === undefined) return '未设置'
  if (value === null) return 'null'
  if (typeof value === 'object') {
    try {
      const formatted = JSON.stringify(value, null, 1)
        .split('\n')
        .map((line, index) => {
          const indentMatch = line.match(/^(\s*)/)
          const indent = indentMatch ? indentMatch[1].length : 0
          
          // 处理键值对行
          if (line.includes(':')) {
            const [key, ...rest] = line.split(':')
            const value = rest.join(':')
            return `${' '.repeat(indent)}<span class="tw-text-blue-400">${key.replace(/[",]/g, '')}</span>:${value}`
          }
          
          // 处理数组项
          if (line.trim().startsWith('"')) {
            return `${' '.repeat(indent)}<span class="tw-text-green-400">${line}</span>`
          }
          
          // 处理数字
          if (/^(\s*)-?\d+/.test(line)) {
            return `${' '.repeat(indent)}<span class="tw-text-yellow-400">${line}</span>`
          }
          
          // 处理布尔值和 null
          if (/true|false|null/.test(line)) {
            return `${' '.repeat(indent)}<span class="tw-text-purple-400">${line}</span>`
          }
          
          // 处理括号和逗号
          return line.replace(/[{}\[\],]/g, match => `<span class="tw-text-gray-500">${match}</span>`)
        })
        .join('\n')
      return formatted
    } catch (e) {
      return String(value)
    }
  }
  return String(value)
}

// 获取字段说明
const getFieldDescription = (key: string): string => {
  const descriptions: Record<string, string> = {
    name: '配置名称',
    description: '配置描述',
    status: '状态',
    created_time: '创建时间',
    updated_time: '更新时间',
    method: '请求方法',
    url: '请求地址',
    headers: '请求头',
    params: '查询参数',
    body: '请求体',
    setup_hooks: '前置钩子',
    teardown_hooks: '后置钩子',
    variables: '变量定义',
    validators: '断言规则',
    extract: '提取变量',
    // 添加更多同步字段的中文映射
    request_type: '请求类型',
    timeout: '超时时间',
    verify: 'SSL验证',
    allow_redirects: '允许重定向',
    base_url: '基础URL',
    json: 'JSON数据',
    data: '表单数据',
    files: '文件数据',
    auth: '认证信息',
    cookies: 'Cookie信息',
    proxies: '代理设置',
    env: '环境变量',
    export: '导出变量',
    validate: '验证规则',
    retry_times: '重试次数',
    retry_interval: '重试间隔',
    weight: '权重',
    priority: '优先级',
    skip: '是否跳过',
    times: '执行次数'
  }
  return descriptions[key] || key
}

watch(() => projectStore.currentProject?.id, (newProjectId: number | undefined) => {
  if (newProjectId) {
    currentPage.value = 1
    fetchHistories()
  } else {
    histories.value = []
    total.value = 0
  }
})

onMounted(() => {
  if (projectStore.currentProject?.id) {
    fetchHistories()
  }
})
</script>

<template>
  <div>
    <div class="tw-flex tw-justify-end tw-mb-6">
      <a-button type="outline" :loading="loading" @click="fetchHistories">
        <template #icon>
          <icon-refresh />
        </template>
        刷新
      </a-button>
    </div>

    <a-table
      :loading="loading"
      :data="histories"
      :columns="columns"
      :pagination="{
        total,
        current: currentPage,
        pageSize,
        showTotal: true,
        showJumper: true,
        showPageSize: true
      }"
      :bordered="true"
      :stripe="true"
      class="custom-table"
      @page-change="handlePageChange"
      @page-size-change="handlePageSizeChange"
    >
      <template #index="{ rowIndex }">
        {{ (currentPage - 1) * pageSize + rowIndex + 1 }}
      </template>

      <template #config_name="{ record }">
        <span>{{ record.sync_config_info?.name || record.config?.name || '-' }}</span>
      </template>

      <template #sync_fields="{ record }">
        <div class="tw-flex tw-flex-wrap tw-gap-1">
          <a-tag
            v-for="field in record.sync_fields"
            :key="field"
            color="arcoblue"
            size="small"
          >
            {{ getFieldDescription(field) }}
          </a-tag>
        </div>
      </template>

      <template #status="{ record }">
        <a-tag 
          :color="record.sync_status === 'success' || record.status === 'success' ? 'green' : 'red'"
          size="medium"
          class="tw-min-w-[60px] tw-text-center"
        >
          {{ (record.sync_status === 'success' || record.status === 'success') ? '成功' : '失败' }}
        </a-tag>
        <a-tooltip v-if="record.error_message">
          <template #content>
            {{ record.error_message }}
          </template>
          <icon-exclamation-circle class="tw-text-red-500 tw-ml-1" />
        </a-tooltip>
      </template>

      <template #created_info="{ record }">
        <div class="tw-flex tw-flex-col tw-gap-1 tw-text-sm">
          <span>操作者：{{ record.operator_info?.username || record.created_by_info?.username || '-' }}</span>
          <span>时间：{{ record.sync_time ? new Date(record.sync_time).toLocaleString() : (record.created_time ? new Date(record.created_time).toLocaleString() : '-') }}</span>
        </div>
      </template>

      <template #operations="{ record }">
        <div class="tw-flex tw-gap-2">
          <a-button
            type="text"
            size="mini"
            :loading="loading"
            @click="handleViewDetail(record)"
          >
            详情
          </a-button>
          <a-button
            v-if="record.sync_status === 'success' || record.status === 'success'"
            type="text"
            status="warning"
            size="mini"
            :loading="loading"
            @click="handleRollback(record)"
          >
            回滚
          </a-button>
        </div>
      </template>
    </a-table>

    <!-- 详情弹窗 -->
    <a-modal
      v-model:visible="showDetailModal"
      title="同步历史详情"
      :width="900"
      class="custom-card"
      @cancel="currentHistory = null"
    >
      <!-- 自定义描述列表 -->
      <div class="tw-bg-gray-900/30 tw-p-3 tw-rounded-lg">
        <div class="tw-grid tw-grid-cols-4 tw-gap-3">
          <!-- 配置名称 -->
          <div class="tw-border tw-border-gray-700 tw-rounded">
            <div class="tw-bg-gray-800/70 tw-py-2 tw-px-3 tw-font-medium tw-text-gray-400 tw-border-b tw-border-gray-700">
              配置名称
            </div>
            <div class="tw-bg-gray-800/30 tw-py-2 tw-px-3 tw-text-gray-300">
              {{ currentHistory?.sync_config_info?.name || currentHistory?.config?.name || '-' }}
            </div>
          </div>
          
          <!-- 同步状态 -->
          <div class="tw-border tw-border-gray-700 tw-rounded">
            <div class="tw-bg-gray-800/70 tw-py-2 tw-px-3 tw-font-medium tw-text-gray-400 tw-border-b tw-border-gray-700">
              同步状态
            </div>
            <div class="tw-bg-gray-800/30 tw-py-2 tw-px-3 tw-text-gray-300">
              <span 
                :class="[
                  'tw-px-2 tw-py-0.5 tw-rounded tw-text-white', 
                  (currentHistory?.sync_status === 'success' || currentHistory?.status === 'success') 
                    ? 'tw-bg-green-500' 
                    : 'tw-bg-red-500'
                ]"
              >
                {{ (currentHistory?.sync_status === 'success' || currentHistory?.status === 'success') ? '成功' : '失败' }}
              </span>
            </div>
          </div>
          
          <!-- 操作人 -->
          <div class="tw-border tw-border-gray-700 tw-rounded">
            <div class="tw-bg-gray-800/70 tw-py-2 tw-px-3 tw-font-medium tw-text-gray-400 tw-border-b tw-border-gray-700">
              操作人
            </div>
            <div class="tw-bg-gray-800/30 tw-py-2 tw-px-3 tw-text-gray-300 tw-text-xs">
              <div>{{ currentHistory?.operator_info?.username || currentHistory?.created_by_info?.username || '-' }}</div>
              <div class="tw-text-gray-400 tw-mt-0.5">
                {{ currentHistory?.sync_time 
                  ? new Date(currentHistory.sync_time).toLocaleString() 
                  : (currentHistory?.created_time ? new Date(currentHistory.created_time).toLocaleString() : '-') }}
              </div>
            </div>
          </div>
          
          <!-- 错误信息 -->
          <div class="tw-border tw-border-gray-700 tw-rounded">
            <div class="tw-bg-gray-800/70 tw-py-2 tw-px-3 tw-font-medium tw-text-gray-400 tw-border-b tw-border-gray-700">
              错误信息
            </div>
            <div class="tw-bg-gray-800/30 tw-py-2 tw-px-3 tw-text-gray-300 tw-text-xs tw-overflow-auto tw-max-h-[60px]">
              {{ currentHistory?.error_message || '-' }}
            </div>
          </div>
          
          <!-- 同步字段 -->
          <div class="tw-border tw-border-gray-700 tw-rounded tw-col-span-4">
            <div class="tw-bg-gray-800/70 tw-py-1.5 tw-px-3 tw-font-medium tw-text-gray-400 tw-border-b tw-border-gray-700 tw-flex tw-items-center tw-justify-between">
              <span>同步字段</span>
              <span class="tw-text-xs tw-font-normal">共 {{ currentHistory?.sync_fields?.length || 0 }} 个字段</span>
            </div>
            <div class="tw-bg-gray-800/30 tw-p-2">
              <div v-if="currentHistory?.sync_fields?.length" class="tw-flex tw-flex-wrap tw-gap-1.5">
                <a-tag
                  v-for="field in currentHistory.sync_fields"
                  :key="field"
                  color="arcoblue"
                  size="small"
                >
                  {{ getFieldDescription(field) }}
                </a-tag>
              </div>
              <div v-else class="tw-text-gray-400 tw-text-sm">暂无同步字段</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 显示新旧数据对比 -->
      <div v-if="currentHistory?.old_data || currentHistory?.new_data" class="tw-mt-3">
        <div class="tw-mb-3">
          <div class="tw-flex tw-items-center tw-justify-between">
            <h3 class="tw-text-gray-400 tw-text-sm tw-font-medium tw-flex tw-items-center">
              <span class="tw-inline-block tw-w-1.5 tw-h-1.5 tw-bg-blue-500 tw-rounded-full tw-mr-1.5"></span>
              数据变更详情
            </h3>
            <a-button
              type="text"
              size="mini"
              class="tw-text-gray-400 hover:tw-text-gray-300"
              @click="showUnchanged = !showUnchanged"
            >
              {{ showUnchanged ? '收起未变更字段' : '显示未变更字段' }}
            </a-button>
          </div>
        </div>
        
        <div class="tw-bg-gray-900/30 tw-rounded-lg tw-border tw-border-gray-700/50">
          <!-- 表头 -->
          <div class="tw-grid tw-grid-cols-12 tw-gap-3 tw-py-1.5 tw-px-3 tw-bg-gray-800/50 tw-border-b tw-border-gray-700/50">
            <div class="tw-col-span-2 tw-text-gray-400 tw-text-xs tw-font-medium">字段名称</div>
            <div class="tw-col-span-5 tw-text-gray-400 tw-text-xs tw-font-medium tw-flex tw-items-center">
              <span class="tw-inline-block tw-w-1.5 tw-h-1.5 tw-bg-red-500/70 tw-rounded-full tw-mr-1.5"></span>
              变更前
            </div>
            <div class="tw-col-span-5 tw-text-gray-400 tw-text-xs tw-font-medium tw-flex tw-items-center">
              <span class="tw-inline-block tw-w-1.5 tw-h-1.5 tw-bg-green-500/70 tw-rounded-full tw-mr-1.5"></span>
              变更后
            </div>
          </div>
          
          <!-- 字段列表 -->
          <div class="tw-divide-y tw-divide-gray-700/50">
            <div
              v-for="field in diffFields"
              :key="field.key"
              v-show="field.changed || showUnchanged"
              :class="[
                'tw-grid tw-grid-cols-12 tw-gap-3 tw-py-2 tw-px-3',
                field.changed ? 'tw-bg-blue-500/5' : '',
                'hover:tw-bg-gray-800/30'
              ]"
            >
              <!-- 字段名称 -->
              <div class="tw-col-span-2 tw-flex tw-flex-col tw-justify-center">
                <div class="tw-text-sm tw-text-gray-300 tw-font-medium">
                  {{ getFieldDescription(field.key) }}
                </div>
                <div class="tw-text-xs tw-text-gray-500 tw-mt-0.5">
                  {{ field.key }}
                </div>
              </div>
              
              <!-- 旧值 -->
              <div class="tw-col-span-5">
                <div 
                  :class="[
                    'tw-rounded tw-p-1 tw-text-sm tw-font-mono tw-leading-5',
                    field.changed ? 'tw-bg-red-500/10 tw-text-red-300' : 'tw-bg-gray-800/30 tw-text-gray-400'
                  ]"
                >
                  <pre class="tw-whitespace-pre-wrap tw-break-all tw-text-left" v-html="formatValue(field.oldValue)"></pre>
                </div>
              </div>
              
              <!-- 新值 -->
              <div class="tw-col-span-5">
                <div 
                  :class="[
                    'tw-rounded tw-p-1 tw-text-sm tw-font-mono tw-leading-5',
                    field.changed ? 'tw-bg-green-500/10 tw-text-green-300' : 'tw-bg-gray-800/30 tw-text-gray-400'
                  ]"
                >
                  <pre class="tw-whitespace-pre-wrap tw-break-all tw-text-left" v-html="formatValue(field.newValue)"></pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<style scoped>
.custom-card {
  @apply tw-bg-gray-800 tw-rounded-lg tw-shadow-lg tw-border tw-border-gray-700/50;
}

:deep(.arco-table) {
  @apply tw-bg-transparent;
}

:deep(.arco-table-th) {
  @apply tw-bg-gray-950 tw-text-gray-200 tw-border-gray-700;
}

:deep(.arco-table-td) {
  @apply tw-bg-gray-800 tw-text-gray-300 tw-border-gray-700;
}

:deep(.arco-table-tr:hover .arco-table-td) {
  @apply tw-bg-gray-700;
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

:deep(.arco-modal-body) {
  @apply tw-p-4;
}

:deep(.arco-modal-footer) {
  @apply tw-border-t tw-border-gray-700 tw-py-2;
}

.json-key {
  @apply tw-text-blue-400;
}

.json-string {
  @apply tw-text-green-400;
}

.json-number {
  @apply tw-text-yellow-400;
}

.json-boolean {
  @apply tw-text-purple-400;
}

.json-null {
  @apply tw-text-red-400;
}

.json-diff-old {
  @apply tw-bg-red-500/70;
}

.json-diff-new {
  @apply tw-bg-green-500/70;
}

.diff-panel {
  @apply tw-flex tw-flex-col;
}

.diff-content {
  @apply tw-h-[350px] tw-overflow-auto tw-p-3;
}

:deep(.vjs-tree) {
  @apply tw-text-sm tw-font-mono;
}

:deep(.vjs-tree .vjs-tree__node) {
  @apply tw-text-gray-300;
}

:deep(.vjs-tree .vjs-tree__node:hover) {
  @apply tw-bg-gray-700/50;
}

:deep(.vjs-tree .vjs-tree__node--selected) {
  @apply tw-bg-blue-500/20 !tw-text-blue-400;
}

:deep(.vjs-tree .vjs-tree__bracket) {
  @apply tw-text-gray-500;
}

:deep(.vjs-tree .vjs-tree__key) {
  @apply tw-text-blue-400;
}

:deep(.vjs-tree .vjs-tree__value) {
  @apply tw-text-green-400;
}

:deep(.vjs-tree .vjs-tree__value_null) {
  @apply tw-text-red-400;
}

:deep(.vjs-tree .vjs-tree__value_number) {
  @apply tw-text-yellow-400;
}

:deep(.vjs-tree .vjs-tree__value_boolean) {
  @apply tw-text-purple-400;
}

:deep(.old-json .vjs-tree__changed) {
  @apply tw-bg-red-500/20 tw-text-red-400;
}

:deep(.new-json .vjs-tree__changed) {
  @apply tw-bg-green-500/20 tw-text-green-400;
}

:deep(.vjs-tree .vjs-tree__highlight) {
  @apply tw-bg-yellow-500/30 tw-text-yellow-300;
}

:deep(.vjs-tree .vjs-tree__length) {
  @apply tw-text-gray-500 tw-text-xs;
}
</style> 