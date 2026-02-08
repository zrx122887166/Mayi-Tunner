<script setup lang="ts">
import { ref, watch, onMounted, inject } from 'vue'
import { IconDelete, IconPlus, IconCode } from '@arco-design/web-vue/es/icon'
import { Message } from '@arco-design/web-vue'
import ResponseJsonViewer from '@/views/apis/components/ResponseJsonViewer.vue'

interface Props {
  extract?: Record<string, string>
}

const props = withDefaults(defineProps<Props>(), {
  extract: () => ({})
})

const emit = defineEmits(['update:extract'])

// 获取响应数据
const apiResponse = inject<any>('apiResponse', ref(null))

// 抽屉控制
const drawerVisible = ref(false)
const currentEditingIndex = ref(-1)

interface ExtractRule {
  variable: string
  expression: string
  description: string
  enabled: boolean
}

const extractRules = ref<ExtractRule[]>([{ variable: '', expression: '', description: '', enabled: true }])

// 初始化提取规则
const initExtractRules = () => {
  if (props.extract && Object.keys(props.extract).length > 0) {
    extractRules.value = Object.entries(props.extract).map(([variable, expression]) => ({
      variable,
      expression,
      description: '',
      enabled: true
    }))
  } else {
    extractRules.value = [{ variable: '', expression: '', description: '', enabled: true }]
  }
}

// 监听 extract 变化
watch(() => props.extract, (newExtract) => {
  if (newExtract && Object.keys(newExtract).length > 0) {
    extractRules.value = Object.entries(newExtract).map(([variable, expression]) => ({
      variable,
      expression,
      description: '',
      enabled: true
    }))
  } else {
    extractRules.value = [{ variable: '', expression: '', description: '', enabled: true }]
  }
})

// 添加提取规则
const addRow = () => {
  extractRules.value.push({ variable: '', expression: '', description: '', enabled: true })
}

// 删除提取规则
const removeRow = (index: number) => {
  extractRules.value.splice(index, 1)
  if (extractRules.value.length === 0) {
    extractRules.value.push({ variable: '', expression: '', description: '', enabled: true })
  }
}

// 处理从响应中选择路径
const handleSelectPath = (path: string, value: string) => {
  if (currentEditingIndex.value >= 0 && currentEditingIndex.value < extractRules.value.length) {
    // 设置表达式
    extractRules.value[currentEditingIndex.value].expression = path
    // 设置变量名（如果变量名为空）
    if (!extractRules.value[currentEditingIndex.value].variable.trim()) {
      // 基于路径生成变量名
      const pathParts = path.split('.')
      let varName = pathParts[pathParts.length - 1]
      // 处理数组索引，例如 users[0] -> users_0
      varName = varName.replace(/\[(\d+)\]/g, '_$1')
      extractRules.value[currentEditingIndex.value].variable = varName
    }
    Message.success('已设置提取表达式')
  }
}

// 打开响应查看器
const openResponseViewer = (index: number) => {
  currentEditingIndex.value = index
  drawerVisible.value = true
}

// 获取提取规则列表
const getExtractRules = () => {
  const rules: Record<string, string> = {}
  extractRules.value
    .filter(rule => rule.enabled && rule.variable && rule.expression)
    .forEach(rule => {
      rules[rule.variable] = rule.expression
    })
  return rules
}

// 组件挂载时初始化数据
onMounted(() => {
  initExtractRules()
})

// 导出方法供父组件调用
defineExpose({
  getExtractRules
})
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-p-4 tw-space-y-2">
    <div class="tw-flex-1 tw-min-h-0 tw-overflow-y-auto tw-pr-2">
      <div class="tw-space-y-2">
        <div
          v-for="(rule, index) in extractRules"
          :key="index"
          class="tw-flex tw-items-center tw-gap-2 tw-w-full"
        >
          <a-checkbox v-model="rule.enabled" class="tw-flex-shrink-0" />
          
          <div class="tw-flex tw-flex-1 tw-gap-2">
            <div class="tw-flex tw-relative tw-w-3/5">
              <a-input
                v-model="rule.expression"
                placeholder="提取表达式 (例如: body.data.results[?name=='测试用例执行'].id | [0])"
                allow-clear
                class="tw-w-full"
              />
              <a-button
                type="text"
                class="tw-absolute tw-right-0 tw-top-0 tw-bottom-0 tw-text-gray-400 hover:tw-text-blue-500"
                @click="openResponseViewer(index)"
                :disabled="!apiResponse"
              >
                <template #icon><icon-code /></template>
              </a-button>
            </div>
            
            <div class="tw-flex tw-gap-2 tw-w-2/5">
              <a-input
                v-model="rule.variable"
                placeholder="变量名"
                allow-clear
                class="tw-w-full"
              />
              
              <a-input
                v-model="rule.description"
                placeholder="描述"
                allow-clear
                class="tw-hidden"
              />
            </div>
          </div>
          
          <a-button
            type="text"
            status="danger"
            @click="removeRow(index)"
            class="tw-flex-shrink-0"
          >
            <template #icon><icon-delete /></template>
          </a-button>
        </div>
      </div>
    </div>
    <div>
      <a-button type="outline" @click="addRow">
        <template #icon><icon-plus /></template>
        添加提取规则
      </a-button>
    </div>
    
    <!-- 响应JSON查看器 -->
    <ResponseJsonViewer
      v-model:visible="drawerVisible"
      :response-data="apiResponse"
      field-type="extract"
      @select-path="handleSelectPath"
    />
  </div>
</template>

<style lang="postcss" scoped>
:deep(.arco-input-wrapper) {
  @apply tw-bg-gray-900/60 tw-border-gray-700;
  
  input {
    @apply tw-text-gray-200 tw-bg-transparent;
    &::placeholder {
      @apply tw-text-gray-500;
    }
  }
}

:deep(.arco-checkbox) {
  @apply tw-text-gray-400;
}

:deep(.arco-btn-outline) {
  @apply tw-border-gray-600 tw-text-gray-300;
  
  &:hover {
    @apply tw-border-blue-500 tw-text-blue-500;
  }
}

:deep(.arco-btn-text) {
  @apply tw-text-gray-400;
  
  &:hover {
    @apply tw-text-blue-500 tw-bg-blue-500/10;
  }
  
  &.arco-btn-status-danger {
    &:hover {
      @apply tw-text-red-500 tw-bg-red-500/10;
    }
  }
}
</style>