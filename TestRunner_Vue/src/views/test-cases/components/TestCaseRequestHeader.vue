<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { IconSend, IconSave, IconRight, IconDown, IconQuestionCircle } from '@arco-design/web-vue/es/icon'
import { Message } from '@arco-design/web-vue'
import { useEnvironmentStore } from '@/stores/environment'
import type { ApiInterface } from '@/api/interface'



interface Props {
  modules?: ApiModule[]
  modelValue: {
    method: string
    url: string
    name: string
    module: number | null
    interface?: ApiInterface | null
  }
  savingLoading?: boolean
  sendingLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modules: () => [],
  savingLoading: false,
  sendingLoading: false
})

const emit = defineEmits([
  'update:modelValue', 
  'send', 
  'save',
  'save-step'
])

// 获取环境store
const environmentStore = useEnvironmentStore()

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

// 处理后的模块列表
const processedModules = computed(() => {
  return processModules(props.modules)
})

// 接口名称
const apiName = computed({
  get: () => props.modelValue.name || '',
  set: (value) => {
    emit('update:modelValue', {
      ...props.modelValue,
      name: value
    })
  }
})

// 选择的模块
const selectedModule = computed({
  get: () => props.modelValue.module || undefined,
  set: (value) => {
    emit('update:modelValue', {
      ...props.modelValue,
      module: value || null
    })
  }
})

// 请求URL
const requestUrl = computed({
  get: () => props.modelValue.url || '',
  set: (value) => {
    emit('update:modelValue', {
      ...props.modelValue,
      url: value
    })
  }
})

// 当前选中的请求方法
const selectedMethod = ref('GET')

// 监听 modelValue 中的 method 变化
watch(() => props.modelValue.method, (newMethod) => {
  if (newMethod && newMethod !== selectedMethod.value) {
    selectedMethod.value = newMethod
  }
}, { immediate: true })

// 监听 selectedMethod 变化，同步更新到 modelValue
watch(selectedMethod, (newMethod) => {
  if (newMethod !== props.modelValue.method) {
    emit('update:modelValue', {
      ...props.modelValue,
      method: newMethod
    })
  }
})

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

// 发送请求
const handleSend = () => {
  if (!requestUrl.value) {
    Message.warning('请输入请求路径')
    return
  }
  emit('send', {
    method: selectedMethod.value,
    url: requestUrl.value,
    name: apiName.value,
    module: selectedModule.value
  })
}

// 保存用例
const handleSave = () => {
  if (!selectedModule.value) {
    Message.warning('请选择模块')
    return
  }
  if (!apiName.value) {
    Message.warning('请输入步骤名称')
    return
  }
  if (!requestUrl.value) {
    Message.warning('请输入请求路径')
    return
  }
  emit('save', {
    method: selectedMethod.value,
    url: requestUrl.value,
    name: apiName.value,
    module: selectedModule.value
  })
}

// 保存步骤
const handleSaveStep = () => {
  if (!selectedModule.value) {
    Message.warning('请选择模块')
    return
  }
  if (!apiName.value) {
    Message.warning('请输入步骤名称')
    return
  }
  if (!requestUrl.value) {
    Message.warning('请输入请求路径')
    return
  }
  
  emit('save-step', {
    method: selectedMethod.value,
    url: requestUrl.value,
    name: apiName.value,
    module: selectedModule.value
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
        class="menu-item tw-rounded-lg tw-flex-1"
      >
        <template #prefix v-if="currentEnvironmentBaseUrl">
          <span class="tw-text-gray-500">{{ currentEnvironmentBaseUrl }}</span>
        </template>
      </a-input>

      <!-- 操作按钮 -->
      <a-button-group>
        <a-button
          type="outline"
          size="large"
          :loading="props.sendingLoading"
          @click="handleSend"
          status="success"
          class="btn-debug"
        >
          <template #icon><icon-send /></template>
          运行调试
          <a-tooltip content="点击将自动保存接口并添加为用例的引用步骤，然后运行调试">
            <icon-question-circle class="tw-ml-1 tw-text-xs tw-opacity-70" />
          </a-tooltip>
        </a-button>
        <a-button
          type="outline"
          size="large"
          :loading="props.savingLoading"
          @click="handleSaveStep"
          status="success"
        >
          <template #icon><icon-save /></template>
          保存步骤
        </a-button>
        <a-button
          type="outline"
          size="large"
          :loading="props.savingLoading"
          @click="handleSave"
        >
          <template #icon><icon-save /></template>
          保存接口
        </a-button>
      </a-button-group>
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
        placeholder="请输入步骤名称"
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
.menu-item {
  box-shadow: inset 0 1px 0 0 rgba(148, 163, 184, 0.2) !important;
  background-color: rgba(17, 24, 39, 0.8) !important;
  border: 1px solid rgba(75, 85, 99, 0.4) !important;
}

/* 请求方法按钮样式 */
.method-button {
  @apply tw-flex tw-items-center tw-justify-center tw-rounded tw-text-white tw-font-medium tw-text-sm tw-cursor-pointer;
  width: 82px;
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

:deep(.arco-input-prefix) {
  margin-right: 4px;
  padding-right: 8px;
  border-right: 1px solid rgba(75, 85, 99, 0.4);
}

/* 按钮样式 */
:deep(.arco-btn-outline) {
  @apply tw-border-gray-600 tw-text-gray-300;
  
  &:hover {
    @apply tw-border-blue-500 tw-text-blue-500;
  }
}

/* 运行调试按钮样式 */
:deep(.btn-debug) {
  @apply tw-text-[#10B981] tw-border-[#10B981]/30 !important;
  background-color: rgba(16, 185, 129, 0.05) !important;
  
  &:hover {
    @apply tw-text-[#10B981] tw-border-[#10B981]/50 !important;
    background-color: rgba(16, 185, 129, 0.1) !important;
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

/* 模块选择下拉框样式 */
:deep(.arco-select) {
  @apply tw-bg-gray-900/60;
  
  .arco-select-view {
    box-shadow: inset 0 1px 0 0 rgba(148, 163, 184, 0.2) !important;
    background-color: rgba(17, 24, 39, 0.8) !important;
    border: 1px solid rgba(75, 85, 99, 0.4) !important;
    @apply tw-rounded-lg;

    &:hover {
      border-color: rgba(75, 85, 99, 0.6) !important;
    }
  }

  .arco-select-view-value {
    @apply tw-text-gray-200;
  }

  input {
    @apply tw-text-gray-200 tw-bg-transparent;
    &::placeholder {
      @apply tw-text-gray-500;
    }
  }
}

:deep(.arco-select-dropdown) {
  @apply tw-bg-gray-800 tw-border-gray-700 tw-rounded-lg;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1) !important;
  border: 1px solid rgba(75, 85, 99, 0.4) !important;
  padding: 4px !important;
  margin: 4px 0 !important;

  .arco-select-option {
    @apply tw-text-gray-300 tw-rounded-lg tw-px-2 tw-py-1 tw-my-1;

    &:hover {
      @apply tw-bg-gray-700;
    }

    &.arco-select-option-active,
    &.arco-select-option-selected {
      @apply tw-bg-blue-500/20 tw-text-blue-500;
    }
  }
}

/* 模块树形结构样式 */
:deep(.arco-select-dropdown .arco-select-option) {
  @apply tw-p-0 !important;
  background: transparent !important;
  margin: 2px 0 !important;
  border-radius: 4px !important;

  &:hover {
    background: rgb(47, 66, 114, 0.4) !important;
  }

  &.arco-select-option-active,
  &.arco-select-option-selected {
    background: rgb(47, 66, 114, 0.4) !important;
  }
}

:deep(.arco-select-dropdown .arco-select-option .arco-btn) {
  @apply tw-bg-transparent !important;
  border: none !important;

  &:hover {
    @apply tw-bg-transparent !important;
  }

  .arco-icon {
    @apply tw-text-[#6b7785] !important;

    &:hover {
      @apply tw-text-[#86909c] !important;
    }
  }
}
</style> 