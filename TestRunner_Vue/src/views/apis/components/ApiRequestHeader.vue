<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { IconSend, IconSave, IconRight, IconDown, IconBug } from '@arco-design/web-vue/es/icon'
import { useEnvironmentStore } from '@/stores/environment'
import type { ApiInterface } from '@/api/interface'
import { quickDebugInterface, type QuickDebugInterfaceRequest } from '@/api/interface'
import { useProjectStore } from '@/stores/project'
import { Message } from '@arco-design/web-vue'

// 扩展 ApiInterface 类型
interface ExtendedApiInterface extends ApiInterface {
  module_info?: ApiModule
}

interface Props {
  modules?: ApiModule[]
  interface?: ApiInterface
  savingLoading?: boolean
  sendingLoading?: boolean
  quickDebugLoading?: boolean
}

// 获取环境store
const environmentStore = useEnvironmentStore()

// 获取当前项目的store
const projectStore = useProjectStore()
const currentProjectId = computed(() => {
  if (projectStore.currentProject) {
    return projectStore.currentProject.id
  }
  return undefined
})

// 获取当前环境的base_url
const currentEnvironmentBaseUrl = computed(() => {
  const currentEnv = environmentStore.environments.find(
    env => env.id === Number(environmentStore.currentEnvironmentId)
  )
  return currentEnv?.base_url || ''
})

// 跟踪展开的模块ID
const expandedModules = ref<number[]>([])

// 处理模块数据，添加level属性，只显示展开的模块
const processModules = (modules: ApiModule[], level = 0): (ApiModule & { level: number })[] => {
  return modules.reduce((acc: (ApiModule & { level: number })[], module) => {
    acc.push({ ...module, level })
    if (module.children?.length && expandedModules.value.includes(module.id)) {
      acc.push(...processModules(module.children, level + 1))
    }
    return acc
  }, [])
}

// 处理模块展开/收起
const toggleModule = (moduleId: number, event: Event) => {
  event.preventDefault()
  event.stopPropagation()
  const index = expandedModules.value.indexOf(moduleId)
  if (index === -1) {
    expandedModules.value.push(moduleId)
  } else {
    expandedModules.value.splice(index, 1)
  }
}

interface ApiModule {
  id: number
  name: string
  project: number
  parent: number | null
  description: string | null
  create_time: string
  update_time: string
  children?: ApiModule[]
}

const props = withDefaults(defineProps<Props>(), {
  modules: () => [],
  interface: undefined,
  savingLoading: false,
  sendingLoading: false,
  quickDebugLoading: false
})

// 处理后的模块列表
const processedModules = computed(() => {
  return processModules(props.modules)
})

// 接口名称
const apiName = ref('')
// 选择的模块
const selectedModule = ref<number>()
// 请求URL
const requestUrl = ref('')
// 当前选中的请求方法
const selectedMethod = ref('GET')

// 请求方法选项
const httpMethods = [
  { label: 'GET', value: 'GET', color: 'tw-bg-blue-500/80' },
  { label: 'POST', value: 'POST', color: 'tw-bg-green-500/80' },
  { label: 'PUT', value: 'PUT', color: 'tw-bg-orange-500/80' },
  { label: 'DELETE', value: 'DELETE', color: 'tw-bg-red-500/80' },
  { label: 'PATCH', value: 'PATCH', color: 'tw-bg-red-500/80' }
]

// 下拉框显示状态
const popupVisible = ref(false)

const emit = defineEmits(['send', 'save'])

// 发送请求
const handleSend = () => {
  console.log('发送请求，接口ID:', props.interface?.id)
  emit('send', {
    method: selectedMethod.value,
    url: requestUrl.value,
    id: props.interface?.id
  })
}

// 保存用例
const handleSave = () => {
  emit('save', {
    name: apiName.value,
    method: selectedMethod.value,
    url: requestUrl.value,
    module: selectedModule.value,
    id: props.interface?.id
  })
}

// 选择请求方法
const selectMethod = (method: string) => {
  selectedMethod.value = method
  popupVisible.value = false
}

// 获取当前方法的颜色
const getCurrentMethodColor = () => {
  return httpMethods.find(m => m.value === selectedMethod.value)?.color || 'tw-bg-gray-600'
}

// 监听接口数据变化
watch(() => props.interface, (newInterface) => {
  console.log('接口数据更新：', newInterface)
  if (newInterface) {
    // 更新表单数据
    apiName.value = newInterface.name || ''
    selectedMethod.value = newInterface.method || 'GET'
    requestUrl.value = newInterface.url || ''
    selectedModule.value = newInterface.module

    // 如果有 module_info，展开所有父模块
    if (newInterface.module_info) {
      let currentModule = newInterface.module_info
      while (currentModule) {
        if (currentModule.id && !expandedModules.value.includes(currentModule.id)) {
          expandedModules.value.push(currentModule.id)
        }
        // 找到父模块
        currentModule = props.modules.find(m => m.id === currentModule.parent) as ApiModule | undefined
      }
    }
  } else {
    // 清空表单数据
    apiName.value = ''
    selectedMethod.value = 'GET'
    requestUrl.value = ''
    selectedModule.value = undefined
  }
}, { immediate: true, deep: true })

const handleQuickDebug = async () => {
  if (!requestUrl.value) {
    Message.warning('请输入接口地址')
    return
  }

  if (!currentProjectId.value) {
    Message.warning('请先选择项目')
    return
  }

  // 准备请求数据
  const request: QuickDebugInterfaceRequest = {
    project_id: currentProjectId.value,
    method: selectedMethod.value,
    url: requestUrl.value,
    environment_id: environmentStore.currentEnvironmentId ? parseInt(environmentStore.currentEnvironmentId) : undefined,
    headers: {},
    params: {},
    body: null
  }

  // 通知父组件获取其他配置数据并发送请求
  emit('send', {
    method: selectedMethod.value,
    url: requestUrl.value,
    quickDebug: true,
    quickDebugRequest: request
  })
}
</script>

<template>
  <div class="tw-p-4 tw-border-b tw-border-gray-700">
    <!-- URL输入区域 -->
    <div class="tw-flex tw-gap-2 tw-mb-3">
      <!-- 请求方法选择 -->
      <a-dropdown
        trigger="click"
        position="bl"
        v-model:popup-visible="popupVisible"
      >
        <div :class="['method-button', getCurrentMethodColor()]">
          {{ selectedMethod }}
        </div>
        <template #content>
          <div class="method-dropdown">
            <div
              v-for="method in httpMethods"
              :key="method.value"
              :class="['method-button', method.color]"
              @click="selectMethod(method.value)"
            >
              {{ method.value }}
            </div>
          </div>
        </template>
      </a-dropdown>

      <!-- URL输入框 -->
      <a-input
        v-model="requestUrl"
        placeholder="请输入请求路径"
        size="large"
        allow-clear
        class="menu-item tw-rounded-lg"
      >
        <template #prefix v-if="currentEnvironmentBaseUrl">
          <span class="tw-text-gray-500">{{ currentEnvironmentBaseUrl }}</span>
        </template>
      </a-input>

      <!-- 操作按钮 -->
      <div class="tw-flex tw-items-center tw-gap-2">
        <a-tooltip content="无需保存接口即可直接测试">
          <a-button
            type="primary"
            status="success"
            size="large"
            :loading="props.quickDebugLoading"
            @click="handleQuickDebug"
            class="tw-w-10"
          >
            <template #icon><icon-bug /></template>
          </a-button>
        </a-tooltip>
        
        <a-button-group>
          <a-button
            type="primary"
            size="large"
            :loading="props.sendingLoading"
            @click="handleSend"
          >
            <template #icon><icon-send /></template>
            调试
          </a-button>
          <a-button
            type="outline"
            size="large"
            :loading="props.savingLoading"
            @click="handleSave"
          >
            <template #icon><icon-save /></template>
            保存
          </a-button>
        </a-button-group>
      </div>
    </div>

    <!-- 接口信息区域 -->
    <div class="tw-flex tw-gap-2">
      <!-- 模块选择 -->
      <div class="tw-border tw-border-gray-600 tw-rounded-lg" style="width: 20%">
        <a-select
          v-model="selectedModule"
          placeholder="请选择模块"
          size="large"
          allow-clear
          :style="{ width: '100%' }"
        >
          <a-option
            v-for="module in processedModules"
            :key="module.id"
            :value="module.id"
          >
            <div class="tw-flex tw-items-center tw-gap-2" :style="{ paddingLeft: `${module.level * 16}px` }">
              <div
                v-if="module.children?.length"
                class="tw-w-4 tw-h-4 tw-flex tw-items-center tw-justify-center tw-cursor-pointer"
                @click="toggleModule(module.id, $event)"
              >
                <icon-right v-if="!expandedModules.includes(module.id)" class="!tw-w-3 !tw-h-3 !tw-text-[#6b7785]" />
                <icon-down v-else class="!tw-w-3 !tw-h-3 !tw-text-[#6b7785]" />
              </div>
              <span v-else class="tw-w-4"></span>
              {{ module.name }}
            </div>
          </a-option>
        </a-select>
      </div>

      <!-- 接口名称输入框 -->
      <a-input
        v-model="apiName"
        placeholder="请输入接口名称"
        size="large"
        allow-clear
        :style="{ width: '80%' }"
        class="menu-item tw-rounded-lg"
      />
    </div>
  </div>
</template>

<style lang="postcss" scoped>
/* 输入框menu-item样式 */
a-input.menu-item {
  box-shadow: inset 0 1px 0 0 rgba(148, 163, 184, 0.2) !important;
  background-color: rgba(17, 24, 39, 0.8) !important;
  border: 1px solid rgba(75, 85, 99, 0.4) !important;
}

/* 请求方法按钮样式 */
.method-button {
  @apply tw-flex tw-items-center tw-justify-center tw-rounded tw-text-white tw-font-medium tw-text-sm tw-cursor-pointer;
  width: 108px;
  height: 32px;
  font-size: 13px;
  letter-spacing: 0.5px;
  transition: all 0.2s ease-in-out;
}

.method-button:hover {
  transform: translateY(-1px);
  opacity: 1;
}

.method-dropdown {
  @apply tw-flex tw-flex-col tw-items-center;
  min-width: 82px;
}

.method-dropdown .method-button {
  height: 28px;
  padding: 0;
  width: 65px !important;
  margin: 2px 1px 2px 0 !important;
}

/* 输入框样式 */
:deep(.arco-input-wrapper) {
  @apply tw-bg-gray-900/60 tw-border-gray-700;
  
  input {
    @apply tw-text-gray-200;
    &::placeholder {
      @apply tw-text-gray-500;
    }
  }
}

/* 按钮样式 */
:deep(.arco-btn-outline) {
  @apply tw-border-gray-600 tw-text-gray-300;
  
  &:hover {
    @apply tw-border-blue-500 tw-text-blue-500;
  }
}

/* 下拉菜单样式 */
:global(.arco-dropdown-list) {
  @apply tw-bg-gray-800 tw-rounded-lg;
  padding: 2px 0 !important;
  width: 80px !important;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2) !important;
  border: 1px solid rgba(75, 85, 99, 0.4) !important;
}

.method-dropdown {
  @apply tw-flex tw-flex-col tw-items-center tw-justify-center;
  
  .method-button {
    margin: 2px 0;
    border-radius: 4px;
    text-align: center;
  }
}

/* 模块选择下拉框样式 */
:deep(.arco-select-view) {
  box-shadow: inset 0 1px 0 0 rgba(148, 163, 184, 0.2) !important;
  background-color: rgba(17, 24, 39, 0.8) !important;
  border: 1px solid rgba(75, 85, 99, 0.4) !important;
  @apply tw-rounded-lg;
}

:deep(.arco-select-view:hover) {
  background-color: rgba(17, 24, 39, 0.8) !important;
  border-color: rgba(75, 85, 99, 0.6) !important;
}

:deep(.arco-select-view-value) {
  @apply tw-text-gray-200;
}

:deep(.arco-select-view-value::placeholder) {
  @apply tw-text-gray-500;
}

:global(.arco-select-dropdown) {
  @apply tw-bg-gray-800 !important;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1) !important;
  border: none !important;
  padding: 4px !important;
  margin: 4px 0 !important;
}

:global(.arco-select-dropdown .arco-select-option) {
  @apply tw-p-0 !important;
  background: rgb(70, 84, 102, 0.4) !important;
  margin: 2px 0 !important;
  border-radius: 4px !important;
}

:global(.arco-select-dropdown .arco-select-option:hover) {
  background: rgb(47, 66, 114, 0.4) !important;
}

:global(.arco-select-dropdown .arco-select-option-active),
:global(.arco-select-dropdown .arco-select-option-selected) {
  background: rgb(47, 66, 114, 0.4) !important;
}

:global(.arco-select-dropdown .arco-select-option .arco-btn) {
  @apply tw-bg-transparent !important;
  border: none !important;
}

:global(.arco-select-dropdown .arco-select-option .arco-btn:hover) {
  @apply tw-bg-transparent !important;
}

:global(.arco-select-dropdown .arco-select-option .arco-btn .arco-icon) {
  @apply tw-text-[#6b7785] !important;
}

:global(.arco-select-dropdown .arco-select-option .arco-btn:hover .arco-icon) {
  @apply tw-text-[#86909c] !important;
}
</style>