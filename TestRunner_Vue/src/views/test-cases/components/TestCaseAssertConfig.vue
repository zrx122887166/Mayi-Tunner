<script setup lang="ts">
import { ref, watch, onMounted, inject } from 'vue'
import { IconDelete, IconPlus, IconCode } from '@arco-design/web-vue/es/icon'
import { Message } from '@arco-design/web-vue'
import ResponseJsonViewer from '@/views/apis/components/ResponseJsonViewer.vue'
import type { ApiValidator } from '@/api/interface'

interface Props {
  validators?: Array<Record<keyof ApiValidator, [string, string]>>
}

const props = withDefaults(defineProps<Props>(), {
  validators: () => []
})

// 获取响应数据
const apiResponse = inject('apiResponse', ref(null))

// 抽屉控制
const drawerVisible = ref(false)
const currentEditingIndex = ref(-1)

interface AssertRule {
  type: keyof ApiValidator
  expression: string
  expected: string
  description: string
  enabled: boolean
}

// 数据类型选项（用于 type_match 断言）
const dataTypes = [
  { label: '整数', value: 'int' },
  { label: '浮点数', value: 'float' },
  { label: '字符串', value: 'str' },
  { label: '布尔值', value: 'bool' },
  { label: '列表', value: 'list' },
  { label: '字典', value: 'dict' },
  { label: '对象', value: 'object' },
  { label: '数组', value: 'array' },
  { label: '空值', value: 'None' }
]

const validatorTypes = [
  // 基础比较断言
  { label: '等于', value: 'eq', category: '基础比较' },
  { label: '不等于', value: 'ne', category: '基础比较' },
  { label: '大于', value: 'gt', category: '基础比较' },
  { label: '大于等于', value: 'ge', category: '基础比较' },
  { label: '小于', value: 'lt', category: '基础比较' },
  { label: '小于等于', value: 'le', category: '基础比较' },
  
  // 字符串相关断言
  { label: '包含', value: 'contains', category: '字符串' },
  { label: '被包含', value: 'contained_by', category: '字符串' },
  { label: '以...开头', value: 'startswith', category: '字符串' },
  { label: '以...结尾', value: 'endswith', category: '字符串' },
  { label: '正则匹配', value: 'regex_match', category: '字符串' },
  { label: '字符串等于', value: 'str_eq', category: '字符串' },
  
  // 长度相关断言
  { label: '长度等于', value: 'length_equal', category: '长度' },
  { label: '长度大于', value: 'length_greater_than', category: '长度' },
  { label: '长度小于', value: 'length_less_than', category: '长度' },
  { label: '长度大于等于', value: 'length_greater_or_equals', category: '长度' },
  { label: '长度小于等于', value: 'length_less_or_equals', category: '长度' },
  
  // 其他断言
  { label: '类型匹配', value: 'type_match', category: '其他' }
] as const

const assertRules = ref<AssertRule[]>([
  { type: 'eq', expression: '', expected: '', description: '', enabled: true }
])

// 初始化断言规则
const initAssertRules = () => {
  if (props.validators && props.validators.length > 0) {
    assertRules.value = props.validators.map(validator => {
      const [type, [expression, expected]] = Object.entries(validator)[0] as [keyof ApiValidator, [string, string]]
      return {
        type,
        expression,
        expected,
        description: '',
        enabled: true
      }
    })
  } else {
    assertRules.value = [{ type: 'eq', expression: '', expected: '', description: '', enabled: true }]
  }
}

// 监听 validators 变化
watch(() => props.validators, (newValidators) => {
  if (newValidators && newValidators.length > 0) {
    assertRules.value = newValidators.map(validator => {
      const [type, [expression, expected]] = Object.entries(validator)[0] as [keyof ApiValidator, [string, string]]
      return {
        type,
        expression,
        expected,
        description: '',
        enabled: true
      }
    })
  } else {
    assertRules.value = [{ type: 'eq', expression: '', expected: '', description: '', enabled: true }]
  }
})

// 添加断言规则
const addRow = () => {
  assertRules.value.push({ type: 'eq', expression: '', expected: '', description: '', enabled: true })
}

// 删除断言规则
const removeRow = (index: number) => {
  assertRules.value.splice(index, 1)
  if (assertRules.value.length === 0) {
    assertRules.value.push({ type: 'eq', expression: '', expected: '', description: '', enabled: true })
  }
}

// 处理从响应中选择路径
const handleSelectPath = (path: string, value: string) => {
  if (currentEditingIndex.value >= 0 && currentEditingIndex.value < assertRules.value.length) {
    // 设置表达式
    assertRules.value[currentEditingIndex.value].expression = path
    
    // 设置预期结果，如果结果为空
    if (!assertRules.value[currentEditingIndex.value].expected.trim()) {
      // 使用当前值作为预期结果
      assertRules.value[currentEditingIndex.value].expected = value
    }
    
    Message.success('已设置断言表达式')
  }
}

// 打开响应查看器
const openResponseViewer = (index: number) => {
  currentEditingIndex.value = index
  drawerVisible.value = true
}

// 获取断言规则列表
const getAssertRules = () => {
  return assertRules.value
    .filter(rule => rule.enabled && rule.expression && rule.expected)
    .map(rule => ({
      [rule.type]: [rule.expression, rule.expected]
    }))
}

// 组件挂载时初始化数据
onMounted(() => {
  initAssertRules()
})

// 导出方法供父组件调用
defineExpose({
  getAssertRules
})
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-p-4 tw-space-y-2">
    <div class="tw-flex-1 tw-min-h-0 tw-overflow-y-auto tw-pr-2">
      <div class="tw-space-y-2">
        <div
          v-for="(rule, index) in assertRules"
          :key="index"
          class="tw-flex tw-items-center tw-gap-2 tw-w-full"
        >
          <a-checkbox v-model="rule.enabled" class="tw-flex-shrink-0" />
          
          <div class="tw-flex tw-flex-1 tw-gap-2">
            <div class="tw-flex tw-relative tw-w-3/5">
              <a-input
                v-model="rule.expression"
                placeholder="断言表达式 (例如: body.data.code)"
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
              <a-select
                v-model="rule.type"
                class="tw-w-2/5"
                placeholder="断言类型"
              >
                <a-optgroup
                  v-for="category in ['基础比较', '字符串', '长度', '其他']"
                  :key="category"
                  :label="category"
                >
                  <a-option
                    v-for="type in validatorTypes.filter(t => t.category === category)"
                    :key="type.value"
                    :value="type.value"
                  >
                    {{ type.label }}
                  </a-option>
                </a-optgroup>
              </a-select>
              
              <!-- 根据断言类型显示不同的输入控件 -->
              <a-select
                v-if="rule.type === 'type_match'"
                v-model="rule.expected"
                placeholder="选择类型"
                allow-clear
                class="tw-w-3/5"
              >
                <a-option
                  v-for="type in dataTypes"
                  :key="type.value"
                  :value="type.value"
                >
                  {{ type.label }}
                </a-option>
              </a-select>
              
              <a-input
                v-else
                v-model="rule.expected"
                placeholder="预期结果"
                allow-clear
                class="tw-w-3/5"
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
        添加断言规则
      </a-button>
    </div>
    
    <!-- 响应JSON查看器 -->
    <ResponseJsonViewer
      v-model:visible="drawerVisible"
      :response-data="apiResponse"
      field-type="assert"
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

:deep(.arco-select-view) {
  @apply tw-bg-gray-900/60 tw-border-gray-700;
}

:deep(.arco-select-view-value) {
  @apply tw-text-gray-200;
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

:deep(.arco-select-dropdown) {
  @apply tw-bg-gray-800 tw-border-gray-700;

  .arco-select-option {
    @apply tw-text-gray-300;

    &:hover {
      @apply tw-bg-gray-700;
    }

    &.arco-select-option-active {
      @apply tw-bg-blue-500/20 tw-text-blue-500;
    }
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