<script setup lang="ts">
import { IconPlus, IconClose, IconDragDotVertical } from '@arco-design/web-vue/es/icon'
import type { CreateTestCaseData, TestCaseStep } from '@/api/testcase'
import { deleteTestCaseStep, addTestCaseSteps, updateTestCaseStepOrder } from '@/api/testcase'
import type { ApiInterface } from '@/api/interface'
import { Message } from '@arco-design/web-vue'
import draggable from 'vuedraggable'
import { ref, watch } from 'vue'
import ApiSelectDialog from './ApiSelectDialog.vue'

type Step = TestCaseStep

interface Props {
  steps: Step[]
  activeStep: Step | null
  testCaseId?: number
  readonly?: boolean
  testCase?: {
    name: string
    priority: 'P0' | 'P1' | 'P2' | 'P3'
    project: number
    description?: string
    group?: number
    tags?: number[]
    config?: {
      base_url: string
      variables: Record<string, any>
      parameters: Record<string, any>
      export: string[]
      verify: boolean
    }
  }
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
})
const emit = defineEmits(['add', 'select', 'delete', 'update:steps', 'save-test-case'])

const dropdownVisible = ref(false)
const apiSelectVisible = ref(false)
const isDragging = ref(false)
const draggedStep = ref<Step | null>(null)
const originalOrder = ref<number>(0)

const stepTypes = [
  { label: '引用接口', value: 'reference', icon: '↓' },
  { label: '自定义接口', value: 'custom_api', icon: '⚡' },
  // 以下功能暂未实现，先隐藏
  // { label: '自定义脚本', value: 'script', icon: '<>' },
  // { label: 'SQL控制器', value: 'sql', icon: '📊' },
  // { label: '等待控制器', value: 'wait', icon: '⏳' },
  // { label: '循环控制器', value: 'loop', icon: '🔄' },
  // { label: '条件控制器', value: 'condition', icon: '🔀' }
]

const handleAddStep = (type: string) => {
  if (!props.testCaseId) {
    // 如果测试用例未保存，触发保存事件，并在保存成功后继续添加步骤
    Message.info('正在自动保存用例基础信息...')
    emit('save-test-case', () => {
      // 保存成功后，延迟一点时间再次调用添加步骤函数
      setTimeout(() => {
        handleAddStep(type)
      }, 800) // 给足够的时间让testCaseId更新
    })
    return
  }

  if (type === 'reference') {
    apiSelectVisible.value = true
  } else if (type === 'custom_api') {
    const step: TestCaseStep = {
      id: 0,
      name: `自定义接口`,
      order: props.steps.length + 1,
      interface_info: {
        id: 0,
        name: '',
        method: 'GET',
        url: '',
        module: {
          id: 0,
          name: ''
        },
        project: {
          id: props.testCase?.project || 0,
          name: ''
        }
      },
      interface_data: {
        method: 'GET',
        url: '',
        body: {
          type: 'none',
          content: null
        },
        params: [],
        headers: [],
        variables: {},
        validators: [],
        extract: {},
        setup_hooks: [],
        teardown_hooks: []
      },
      config: {
        variables: {},
        validators: [],
        extract: {},
        setup_hooks: [],
        teardown_hooks: []
      },
      sync_fields: [
        'method',
        'url',
        'headers',
        'params',
        'body',
        'setup_hooks',
        'teardown_hooks',
        'variables',
        'validators',
        'extract'
      ],
      last_sync_time: null
    }
    // 更新整个步骤列表
    const updatedSteps = [...props.steps, step]
    emit('update:steps', updatedSteps)
    // 选中新添加的步骤
    emit('select', updatedSteps[updatedSteps.length - 1])
  } else {
    emit('add', type)
  }
  dropdownVisible.value = false
}

const handleApiSelect = async (selectedInterfaces: ApiInterface[]) => {
  try {
    const testCaseData: CreateTestCaseData = {
      name: props.testCase?.name || '未命名用例',
      priority: props.testCase?.priority || 'P3',
      project: props.testCase?.project || 0,
      description: props.testCase?.description || '',
      group: props.testCase?.group,
      tags: props.testCase?.tags || [],
      config: props.testCase?.config || {
        base_url: '',
        variables: {},
        parameters: {},
        export: [],
        verify: true
      },
      steps_info: selectedInterfaces.map((api, index) => ({
        name: api.name,
        order: props.steps.length + index + 1,
        interface_id: api.id!,
        interface_data: {
          method: api.method,
          url: api.url,
          headers: api.headers || [],
          params: api.params || [],
          body: api.body || { type: 'none', content: null },
          validators: api.validators || [],
          extract: api.extract || {},
          // 确保 setup_hooks 和 teardown_hooks 是字符串数组
          setup_hooks: (api.setup_hooks || []).map((hook: any) =>
            typeof hook === 'string' ? hook : JSON.stringify(hook)
          ),
          teardown_hooks: (api.teardown_hooks || []).map((hook: any) =>
            typeof hook === 'string' ? hook : JSON.stringify(hook)
          ),
          variables: api.variables || {}
        }
      }))
    }

    const response = await addTestCaseSteps(props.testCaseId!, testCaseData)
    Message.success('添加步骤成功')

    // 更新步骤列表
    emit('update:steps', response.data.steps)

    // 选中最后一个步骤
    if (response.data.steps.length > 0) {
      emit('select', response.data.steps[response.data.steps.length - 1])
    }

    // 关闭弹窗
    apiSelectVisible.value = false
  } catch (error) {
    console.error('Failed to add steps:', error)
    Message.error('添加步骤失败')
  }
}

const handleSelectStep = (step: Step) => {
  // 直接触发选择事件，让父组件处理选择逻辑
  emit('select', step)
}

const handleDeleteStep = async (step: Step, event: Event) => {
  event.stopPropagation()

  // 如果用例未保存或者是自定义接口，直接从列表中删除
  if (!props.testCaseId || !step.id) {
    const updatedSteps = props.steps.filter(s => s !== step)
    // 重新计算步骤顺序
    updatedSteps.forEach((s, index) => {
      s.order = index + 1
    })
    emit('update:steps', updatedSteps)
    // 如果删除的是当前选中的步骤，清空选中状态
    if (props.activeStep === step) {
      emit('select', null)
    }
    return
  }

  // 对于已保存的用例和步骤，调用删除API
  try {
    await deleteTestCaseStep(props.testCaseId, step.id)
    Message.success('步骤删除成功')
    // 更新步骤列表
    const updatedSteps = props.steps.filter(s => s.id !== step.id)
    // 重新计算步骤顺序
    updatedSteps.forEach((s, index) => {
      s.order = index + 1
    })
    emit('update:steps', updatedSteps)
    // 如果删除的是当前选中的步骤，清空选中状态
    if (props.activeStep?.id === step.id) {
      emit('select', null)
    }
  } catch (error) {
    Message.error('步骤删除失败')
  }
}

const handleDragStart = (evt: any) => {
  isDragging.value = true
  const draggedIndex = evt.oldIndex
  draggedStep.value = props.steps[draggedIndex]
  originalOrder.value = draggedStep.value?.order || draggedIndex + 1
}

const handleDragEnd = async (evt: any) => {
  isDragging.value = false
  
  // 如果没有拖动或没有测试用例ID，只在本地更新顺序
  if (!draggedStep.value || !props.testCaseId || !draggedStep.value.id) {
    // 重新计算步骤顺序
    props.steps.forEach((step, index) => {
      step.order = index + 1
    })
    draggedStep.value = null
    return
  }

  // 获取新的顺序位置
  const newIndex = evt.newIndex
  const newOrder = newIndex + 1

  // 如果顺序没有变化，不需要调用API
  if (originalOrder.value === newOrder) {
    draggedStep.value = null
    return
  }

  try {
    // 调用API更新步骤顺序
    await updateTestCaseStepOrder(props.testCaseId, {
      step_id: draggedStep.value.id,
      order: newOrder
    })
    
    // 本地更新步骤顺序
    props.steps.forEach((step, index) => {
      step.order = index + 1
    })
    
    Message.success('步骤顺序已更新')
  } catch (error) {
    console.error('Failed to update step order:', error)
    Message.error('更新步骤顺序失败')
    
    // 失败时恢复原顺序
    const currentIndex = props.steps.findIndex(s => s.id === draggedStep.value?.id)
    if (currentIndex !== -1 && originalOrder.value) {
      const targetIndex = originalOrder.value - 1
      const [movedStep] = props.steps.splice(currentIndex, 1)
      props.steps.splice(targetIndex, 0, movedStep)
      
      // 重新计算顺序
      props.steps.forEach((step, index) => {
        step.order = index + 1
      })
      
      emit('update:steps', [...props.steps])
    }
  } finally {
    draggedStep.value = null
    originalOrder.value = 0
  }
}

const getInterfaceName = (step: Step) => {
  return step.interface_info?.name || '未选择接口'
}

const getMethodColor = (method?: string) => {
  switch(method?.toUpperCase()) {
    case 'GET': return 'tw-text-green-500'
    case 'POST': return 'tw-text-blue-500'
    case 'PUT': return 'tw-text-yellow-500'
    case 'DELETE': return 'tw-text-red-500'
    default: return 'tw-text-gray-500'
  }
}

const getStepStatus = (step: Step) => {
  if (!step.interface_info?.id) return { type: 'warning', text: '未配置接口' }
  if (!step.interface_data?.extract || Object.keys(step.interface_data.extract).length === 0) return { type: 'warning', text: '未配置提取' }
  if (!step.interface_data?.validators?.length) return { type: 'warning', text: '未配置断言' }
  return { type: 'success', text: '配置完成' }
}

// 处理长URL的省略显示
const formatUrl = (url?: string): string => {
  if (!url) return '未设置URL'

  // 特殊处理查询参数丰富的URL
  if (url.includes('?')) {
    const [path, query] = url.split('?')

    // 保留路径，但缩短它
    let displayPath = path
    if (path.length > 12) {
      const pathParts = path.split('/').filter(Boolean)
      if (pathParts.length > 1) {
        displayPath = `/${pathParts[0]}/.../${pathParts[pathParts.length - 1]}`
      } else if (pathParts.length === 1) {
        displayPath = `/${pathParts[0].substring(0, 5)}...`
      } else {
        displayPath = '/...'
      }
    }

    // 显示查询参数的开始部分
    return `${displayPath}?${query.substring(0, 8)}...`
  }

  // 对于没有查询参数的URL
  if (url.length > 20) {
    const pathParts = url.split('/').filter(Boolean)
    if (pathParts.length > 1) {
      return `/${pathParts[0]}/.../${pathParts[pathParts.length - 1]}`
    } else if (pathParts.length === 1) {
      return `/${pathParts[0].substring(0, 8)}...`
    }
  }

  return url
}
</script>

<template>
  <div class="tw-h-full">
    <div class="tw-flex tw-justify-between tw-items-center tw-mb-4">
      <div class="tw-flex tw-items-center">
        <a-tag>{{ steps.length }}个步骤</a-tag>
      </div>
    </div>
    <div class="tw-space-y-3 tw-max-h-[calc(100vh-20rem)] tw-overflow-y-auto hide-scrollbar">
      <template v-if="steps.length">
        <draggable
          :list="steps"
          :animation="150"
          item-key="name"
          handle=".drag-handle"
          class="tw-space-y-3"
          :disabled="readonly"
          @update:modelValue="(steps: Step[]) => $emit('update:steps', steps)"
          @start="handleDragStart"
          @end="handleDragEnd"
        >
          <template #item="{ element: step, index }">
            <div
              class="tw-rounded-lg tw-cursor-pointer tw-transition-all tw-border group"
              :class="[
                activeStep?.id === step.id || (activeStep?.order === step.order && !step.id)
                  ? 'tw-bg-blue-500/20 tw-border-blue-500/50'
                  : 'tw-bg-gray-800/50 hover:tw-bg-gray-800 tw-border-gray-700'
              ]"
              @click="handleSelectStep(step)"
            >
              <div class="tw-p-4 tw-flex tw-items-center tw-gap-3">
                <icon-drag-dot-vertical
                  class="drag-handle tw-text-gray-500 tw-flex-shrink-0"
                  :class="readonly ? 'tw-cursor-not-allowed tw-opacity-50' : 'tw-cursor-move'"
                />
                <span class="tw-w-7 tw-h-7 tw-flex tw-items-center tw-justify-center tw-bg-blue-500 tw-rounded-lg tw-text-white tw-flex-shrink-0">
                  {{ index + 1 }}
                </span>
                <div class="tw-flex-1 tw-min-w-0 tw-overflow-hidden">
                  <div class="tw-flex tw-items-center tw-justify-between tw-mb-2">
                    <span class="tw-text-gray-300 tw-font-medium">{{ step.name }}</span>
                  </div>
                  <div class="tw-flex tw-items-center tw-gap-2 tw-text-sm">
                    <span :class="[getMethodColor(step.interface_info?.method), 'tw-flex-shrink-0']">
                      {{ step.interface_info?.method || 'METHOD' }}
                    </span>
                    <span
                      class="tw-text-gray-400 tw-truncate tw-max-w-[calc(100%-4rem)]"
                      :title="step.interface_info?.url || '未设置URL'"
                    >
                      {{ formatUrl(step.interface_info?.url) }}
                    </span>
                  </div>
                  <div class="tw-flex tw-flex-wrap tw-gap-2 tw-mt-2">
                    <a-tag size="small" color="arcoblue" :class="{'!tw-opacity-30': !Object.keys(step.interface_data?.variables || {}).length}">
                      {{ Object.keys(step.interface_data?.variables || {}).length }}个变量
                    </a-tag>
                    <a-tag size="small" color="orange" :class="{'!tw-opacity-30': !Object.keys(step.interface_data?.extract || {}).length}">
                      {{ Object.keys(step.interface_data?.extract || {}).length }}个提取
                    </a-tag>
                    <a-tag size="small" color="green" :class="{'!tw-opacity-30': !step.interface_data?.validators?.length}">
                      {{ step.interface_data?.validators?.length || 0 }}个断言
                    </a-tag>
                  </div>
                </div>
                <icon-close
                  class="tw-text-gray-400 hover:tw-text-red-500 tw-transition-all tw-cursor-pointer tw-text-lg tw-flex-shrink-0"
                  :style="{ fontSize: '18px' }"
                  @click="handleDeleteStep(step, $event)"
                />
              </div>
            </div>
          </template>
        </draggable>
      </template>
      <a-trigger
        trigger="hover"
        position="bottom"
        :popup-visible="dropdownVisible"
        @popup-visible-change="visible => dropdownVisible = visible"
        class="add-step-trigger"
        :popup-translate="[0, 8]"
      >
        <div
          class="tw-rounded-lg tw-cursor-pointer tw-transition-all tw-border tw-border-dashed tw-border-gray-700 hover:tw-border-blue-500 tw-bg-gray-800/50 hover:tw-bg-gray-800"
        >
          <div class="tw-p-4 tw-flex tw-items-center tw-justify-center tw-gap-2 tw-text-gray-400 hover:tw-text-blue-500">
            <icon-plus />
            <span>添加步骤</span>
          </div>
        </div>
        <template #content>
          <a-menu class="!tw-bg-[rgb(55,65,81)] !tw-border-gray-700 tw-min-w-[180px]">
            <a-menu-item
              v-for="type in stepTypes"
              :key="type.value"
              @click="handleAddStep(type.value)"
            >
              <div class="tw-flex tw-items-center tw-h-full tw-w-full">
                <span class="tw-w-5 tw-h-5 tw-flex tw-items-center tw-justify-center tw-bg-[rgb(45,55,71)] tw-rounded-lg tw-text-sm tw-ml-2">{{ type.icon }}</span>
                <span class="tw-text-sm tw-flex-1 tw-text-center">{{ type.label }}</span>
                <span class="tw-w-5"></span>
              </div>
            </a-menu-item>
          </a-menu>
        </template>
      </a-trigger>
    </div>
  </div>

  <ApiSelectDialog
    v-model:visible="apiSelectVisible"
    :test-case-id="testCaseId"
    :test-case="testCase"
    @select="handleApiSelect"
  />
</template>

<style scoped>
.hide-scrollbar {
  scrollbar-width: none;  /* Firefox */
  -ms-overflow-style: none;  /* IE and Edge */
  overflow-x: hidden;  /* 防止水平滚动 */
}

.hide-scrollbar::-webkit-scrollbar {
  display: none;  /* Chrome, Safari and Opera */
}

:deep(.arco-menu-item) {
  @apply tw-text-gray-300 hover:tw-text-blue-500 hover:tw-bg-[rgb(45,55,71)];
  height: 32px !important;
  line-height: 32px !important;
  padding: 0 !important;
  margin: 2px 0 !important;
}

:deep(.arco-menu) {
  padding: 6px !important;
}

:deep(.arco-menu-item:first-child) {
  margin-top: 0 !important;
}

:deep(.arco-menu-item:last-child) {
  margin-bottom: 0 !important;
}

:deep(.arco-menu-selected) {
  @apply !tw-bg-[rgb(45,55,71)] !tw-text-blue-500;
}

.add-step-trigger {
  :deep(.arco-trigger-popup) {
    margin-bottom: 8px !important;
  }
}
</style>