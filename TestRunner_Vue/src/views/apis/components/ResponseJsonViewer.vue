<script setup lang="ts">
import { ref, computed, watch, h } from 'vue'
import { IconCopy, IconClose, IconPlayArrow } from '@arco-design/web-vue/es/icon'
import { useClipboard } from '@vueuse/core'
import { Message } from '@arco-design/web-vue'
import jmespath from 'jmespath'

interface Props {
  visible: boolean
  responseData: any
  fieldType?: 'extract' | 'assert'
}

const props = defineProps<Props>()
const emit = defineEmits(['update:visible', 'select-path'])

// 复制功能
const { copy } = useClipboard()
const copyContent = async (content: string) => {
  await copy(content)
  Message.success('复制成功')
}

// 关闭抽屉
const closeDrawer = () => {
  emit('update:visible', false)
}

// 测试提取表达式相关
const testExpression = ref('')
const testResult = ref<{ success: boolean; value: any; error?: string } | null>(null)
const isTestAreaExpanded = ref(false)

// 格式化的JSON数据
const formattedData = computed(() => {
  try {
    if (!props.responseData) return null
    
    const content = props.responseData?.response?.content
    if (!content) return null
    
    return content
  } catch (error) {
    console.error('解析响应数据失败:', error)
    return null
  }
})

// 测试表达式
const runTest = () => {
  if (!testExpression.value) {
    Message.warning('请先输入提取表达式')
    return
  }
  
  if (!formattedData.value) {
    Message.warning('暂无响应数据')
    return
  }
  
  try {
    // 处理表达式
    let expression = testExpression.value
    let data = formattedData.value
    
    // 如果表达式以 body. 开头，则移除前缀
    if (expression.startsWith('body.')) {
      expression = expression.substring(5)
    }
    
    // 执行 JMESPath 查询
    const result = jmespath.search(data, expression)
    
    // 存储测试结果
    testResult.value = {
      success: true,
      value: result
    }
    
    // 根据不同模式显示不同的成功消息
    if (props.fieldType === 'extract') {
      Message.success('提取测试成功')
    } else if (props.fieldType === 'assert') {
      Message.success('断言表达式有效')
    }
  } catch (error: any) {
    testResult.value = {
      success: false,
      value: null,
      error: error.message || '表达式解析失败'
    }
    Message.error(`测试失败: ${error.message || '表达式解析失败'}`)
  }
}

// 格式化测试结果显示
const formatTestResult = (result: any) => {
  if (result === null) return 'null'
  if (result === undefined) return 'undefined'
  if (typeof result === 'string') return `"${result}"`
  if (typeof result === 'object') {
    try {
      return JSON.stringify(result, null, 2)
    } catch {
      return String(result)
    }
  }
  return String(result)
}

// 应用测试的表达式
const applyExpression = () => {
  if (testExpression.value && testResult.value?.success) {
    // 确保表达式包含 body. 前缀（如果需要）
    let expression = testExpression.value
    if (!expression.startsWith('body.')) {
      expression = `body.${expression}`
    }
    
    // 将结果转换为字符串
    let valueStr = testResult.value.value
    if (typeof valueStr === 'object' && valueStr !== null) {
      valueStr = JSON.stringify(valueStr)
    } else {
      valueStr = String(valueStr)
    }
    
    emit('select-path', expression, valueStr)
    
    if (props.fieldType === 'extract') {
      Message.success('已应用提取表达式')
    } else if (props.fieldType === 'assert') {
      Message.success('已应用断言表达式和预期值')
    }
    
    // 清空测试区域
    testExpression.value = ''
    testResult.value = null
    isTestAreaExpanded.value = false
  }
}

// 展开的节点路径
const expandedPaths = ref<string[]>([])

// 判断指定路径是否展开
const isExpanded = (path: string) => {
  return expandedPaths.value.includes(path)
}

// 切换节点展开状态
const toggleExpand = (path: string) => {
  const index = expandedPaths.value.indexOf(path)
  if (index === -1) {
    expandedPaths.value.push(path)
  } else {
    expandedPaths.value.splice(index, 1)
  }
}

// 选择一个路径
const selectPath = (path: string, data: any) => {
  // 将路径格式转换为JMESPath格式 (例如 body.data.users[0].name)
  let jmesPath = path;
  
  // 如果需要添加前缀，可以在这里处理
  if (!path.startsWith('body')) {
    jmesPath = `body.${path}`;
  }
  
  // 准备值
  let value = data;
  if (typeof value === 'string') {
    // 对于字符串，去掉JSON.stringify添加的引号
    value = value;
  } else if (typeof value === 'object' && value !== null) {
    // 对于对象和数组，转换为JSON字符串
    value = JSON.stringify(value);
  } else {
    // 其他类型转为字符串
    value = String(value);
  }
  
  // 设置到测试表达式输入框
  testExpression.value = path
  isTestAreaExpanded.value = true
  
  // 自动运行测试
  runTest()
}

// 定义不同数据类型的样式
const getValueClass = (value: any) => {
  if (value === null) return 'tw-text-gray-500'
  if (typeof value === 'number') return 'tw-text-blue-400'
  if (typeof value === 'boolean') return 'tw-text-purple-400'
  if (typeof value === 'string') return 'tw-text-green-400'
  return 'tw-text-gray-300'
}

// 格式化值，处理长字符串
const formatValue = (value: any) => {
  if (typeof value === 'string') {
    // 不再截断字符串，完整显示
    return JSON.stringify(value);
  }
  return JSON.stringify(value);
}

// 递归渲染JSON节点
const renderJsonNode = (data: any, path: string = '', isRoot: boolean = true): any => {
  if (data === null || data === undefined) {
    return h('div', { class: 'tw-flex tw-items-center' }, [
      h('span', { class: 'tw-text-gray-500' }, 'null'),
      !isRoot && h('span', {
        class: 'tw-ml-2 tw-text-xs tw-text-gray-500 hover:tw-text-blue-400 tw-cursor-pointer tw-px-1 tw-py-0.5 tw-bg-blue-500/10 tw-rounded',
        onClick: () => selectPath(path, data)
      }, props.fieldType === 'extract' ? '选择' : '断言')
    ])
  }
  
  if (typeof data !== 'object') {
    // 计算内容是否需要换行
    const content = formatValue(data);
    const needsWrapping = content.length > 40; // 大致估计一行的字符数

    return h('div', { class: 'tw-flex tw-items-center tw-flex-wrap' }, [
      h('span', { 
        class: `${getValueClass(data)} tw-break-all ${needsWrapping ? 'tw-max-w-[calc(100%-70px)]' : ''}`,
      }, content),
      !isRoot && h('span', {
        class: 'tw-ml-2 tw-text-xs tw-text-gray-500 hover:tw-text-blue-400 tw-cursor-pointer tw-px-1 tw-py-0.5 tw-bg-blue-500/10 tw-rounded tw-whitespace-nowrap tw-flex-shrink-0',
        onClick: () => selectPath(path, data)
      }, props.fieldType === 'extract' ? '选择' : '断言')
    ])
  }
  
  if (Array.isArray(data)) {
    if (data.length === 0) {
      return h('div', { class: 'tw-flex tw-items-center' }, [
        h('span', { class: 'tw-text-gray-500 tw-flex-shrink-0' }, '[]'),
        !isRoot && h('span', {
          class: 'tw-ml-2 tw-text-xs tw-text-gray-500 hover:tw-text-blue-400 tw-cursor-pointer tw-px-1 tw-py-0.5 tw-bg-blue-500/10 tw-rounded tw-flex-shrink-0',
          onClick: () => selectPath(path, data)
        }, props.fieldType === 'extract' ? '选择' : '断言')
      ])
    }
    
    const isNodeExpanded = isExpanded(path)
    
    // 计算数组标题是否需要预留空间
    const arrayTitle = `Array[${data.length}]`;
    const needsArrayTitleWrapping = arrayTitle.length > 20;
    
    return h('div', { class: 'tw-flex tw-flex-col tw-max-w-full' }, [
      h('div', { 
        class: 'tw-flex tw-items-center tw-cursor-pointer hover:tw-text-blue-400 tw-flex-wrap',
        onClick: () => toggleExpand(path)
      }, [
        h('span', { class: 'tw-mr-1 tw-flex-shrink-0' }, isNodeExpanded ? '▼' : '▶'),
        h('span', { 
          class: `tw-text-gray-300 tw-break-all ${needsArrayTitleWrapping ? 'tw-max-w-[calc(100%-90px)]' : ''}`
        }, arrayTitle),
        !isRoot && h('span', {
          class: 'tw-ml-2 tw-text-xs tw-text-gray-500 hover:tw-text-blue-400 tw-cursor-pointer tw-px-1 tw-py-0.5 tw-bg-blue-500/10 tw-rounded tw-flex-shrink-0',
          onClick: (e: Event) => { e.stopPropagation(); selectPath(path, data) }
        }, props.fieldType === 'extract' ? '提取' : '选择断言')
      ]),
      
      isNodeExpanded && h('div', { class: 'tw-pl-4 tw-border-l tw-border-gray-700 tw-ml-2 tw-max-w-full' }, 
        data.map((item: any, index: number) => h('div', { 
          key: index, 
          class: 'tw-flex tw-items-start tw-py-1 tw-max-w-full tw-flex-wrap' 
        }, [
          h('span', { class: 'tw-text-gray-400 tw-mr-1 tw-flex-shrink-0 tw-whitespace-nowrap' }, `${index}:`),
          h('div', { 
            class: `tw-flex-1 tw-min-w-0 ${index > 999 ? 'tw-max-w-[calc(100%-30px)]' : ''}`
          }, [
          renderJsonNode(item, `${path}[${index}]`, false)
          ])
        ]))
      )
    ])
  }
  
  // 处理对象
  const keys = Object.keys(data)
  if (keys.length === 0) {
    return h('div', { class: 'tw-flex tw-items-center' }, [
      h('span', { class: 'tw-text-gray-500 tw-flex-shrink-0' }, '{}'),
      !isRoot && h('span', {
        class: 'tw-ml-2 tw-text-xs tw-text-gray-500 hover:tw-text-blue-400 tw-cursor-pointer tw-px-1 tw-py-0.5 tw-bg-blue-500/10 tw-rounded tw-flex-shrink-0',
        onClick: () => selectPath(path, data)
      }, props.fieldType === 'extract' ? '提取' : '选择断言')
    ])
  }
  
  const isNodeExpanded = isExpanded(path)
  
  // 计算对象标题是否需要预留空间
  const objectTitle = `Object {${keys.length}}`;
  const needsObjectTitleWrapping = objectTitle.length > 20;
  
  return h('div', { class: 'tw-flex tw-flex-col tw-max-w-full' }, [
    h('div', {
      class: 'tw-flex tw-items-center tw-cursor-pointer hover:tw-text-blue-400 tw-flex-wrap',
      onClick: () => toggleExpand(path)
    }, [
      h('span', { class: 'tw-mr-1 tw-flex-shrink-0' }, isNodeExpanded ? '▼' : '▶'),
      h('span', { 
        class: `tw-text-gray-300 tw-break-all ${needsObjectTitleWrapping ? 'tw-max-w-[calc(100%-90px)]' : ''}`
      }, objectTitle),
      !isRoot && h('span', {
        class: 'tw-ml-2 tw-text-xs tw-text-gray-500 hover:tw-text-blue-400 tw-cursor-pointer tw-px-1 tw-py-0.5 tw-bg-blue-500/10 tw-rounded tw-flex-shrink-0',
        onClick: (e: Event) => { e.stopPropagation(); selectPath(path, data) }
      }, props.fieldType === 'extract' ? '提取' : '选择断言')
    ]),
    
    isNodeExpanded && h('div', { class: 'tw-pl-4 tw-border-l tw-border-gray-700 tw-ml-2 tw-max-w-full' },
      keys.map(key => h('div', { 
        key, 
        class: 'tw-flex tw-items-start tw-py-1 tw-max-w-full tw-flex-wrap' 
      }, [
        h('div', { class: 'tw-flex tw-items-center tw-mr-1 tw-flex-shrink-0' }, [
          h('span', { class: 'tw-text-gray-400 tw-mr-1 tw-whitespace-nowrap' }, `${key}:`)
        ]),
        h('div', { 
          class: `tw-flex tw-items-start tw-flex-1 tw-min-w-0 ${key.length > 15 ? 'tw-max-w-[calc(100%-30px)]' : ''}`
        }, [
          renderJsonNode(data[key], path ? `${path}.${key}` : key, false)
        ])
      ]))
    )
  ])
}

// 展开所有节点
const expandAllNodes = (data: any, basePath: string = '') => {
  if (!data || typeof data !== 'object') return
  
  // 添加当前路径到展开列表
  if (basePath) {
    expandedPaths.value.push(basePath)
  }
  
  // 如果是数组，递归展开每个元素
  if (Array.isArray(data)) {
    data.forEach((item, index) => {
      const path = basePath ? `${basePath}[${index}]` : `[${index}]`
      expandAllNodes(item, path)
    })
  } 
  // 如果是对象，递归展开每个属性
  else if (data && typeof data === 'object') {
    Object.keys(data).forEach(key => {
      const path = basePath ? `${basePath}.${key}` : key
      expandAllNodes(data[key], path)
    })
  }
}

// 监听数据变化时自动展开所有节点
watch(() => props.responseData, (newData) => {
  // 重置展开状态
  expandedPaths.value = ['']
  
  // 如果有数据，展开所有节点
  if (newData?.response?.content) {
    expandAllNodes(newData.response.content, '')
  }
}, { immediate: true })

// 监听抽屉关闭时清空测试数据
watch(() => props.visible, (visible) => {
  if (!visible) {
    testExpression.value = ''
    testResult.value = null
    isTestAreaExpanded.value = false
  }
})
</script>

<template>
  <a-drawer
    :visible="visible"
    :width="700"
    :footer="false"
    @cancel="closeDrawer"
    unmountOnClose
    placement="right"
    :mask-closable="true"
  >
    <template #title>
      <div class="tw-flex tw-justify-between tw-items-center">
        <span>响应数据 - {{ fieldType === 'extract' ? '提取器' : '断言' }}</span>
        <a-button type="text" @click="closeDrawer">
          <template #icon><icon-close /></template>
        </a-button>
      </div>
    </template>
    
    <div class="tw-p-4 tw-h-full tw-overflow-auto">
      <!-- 测试区域 (用于提取和断言) -->
      <div class="tw-mb-4">
        <div v-if="isTestAreaExpanded" class="tw-mt-3 tw-space-y-3">
          <div class="tw-flex tw-gap-2">
            <a-input
              v-model="testExpression"
              :placeholder="fieldType === 'extract' ? '输入提取表达式进行测试 (例如: data.results[0].id)' : '输入断言表达式进行测试 (例如: body.data.code)'"
              allow-clear
              class="tw-flex-1"
              @press-enter="runTest"
            />
            <a-button type="primary" @click="runTest">
              <template #icon><icon-play-arrow /></template>
              测试
            </a-button>
          </div>
          
          <!-- 测试结果展示 -->
          <div v-if="testResult">
            <div v-if="testResult.success" class="tw-bg-green-500/10 tw-border tw-border-green-500/30 tw-rounded-md tw-p-3">
              <div class="tw-flex tw-items-center tw-justify-between tw-mb-2">
                <span class="tw-text-green-400 tw-text-sm">✓ {{ fieldType === 'extract' ? '提取成功' : '表达式有效' }}</span>
                <a-button
                  size="mini"
                  type="primary"
                  status="success"
                  @click="applyExpression"
                >
                  {{ fieldType === 'extract' ? '应用此表达式' : '应用到断言' }}
                </a-button>
              </div>
              <div class="tw-bg-gray-900/50 tw-rounded tw-p-2 tw-max-h-32 tw-overflow-auto">
                <pre class="tw-text-gray-300 tw-text-xs tw-font-mono tw-whitespace-pre-wrap">{{ formatTestResult(testResult.value) }}</pre>
              </div>
            </div>
            <div v-else class="tw-bg-red-500/10 tw-border tw-border-red-500/30 tw-rounded-md tw-p-3">
              <div class="tw-text-red-400 tw-text-sm tw-mb-1">✗ {{ fieldType === 'extract' ? '提取失败' : '表达式无效' }}</div>
              <div class="tw-text-red-300 tw-text-xs">{{ testResult.error }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 响应数据展示 -->
      <div v-if="formattedData" class="tw-bg-gray-900/50 tw-rounded-lg tw-shadow-inner tw-p-4 tw-relative tw-overflow-auto">
        <div
          class="tw-absolute tw-right-2 tw-top-2 tw-cursor-pointer copy-button tw-text-gray-400 hover:tw-text-blue-400"
          @click="copyContent(JSON.stringify(formattedData, null, 2))"
          title="复制"
        >
          <icon-copy />
        </div>
        
        <div class="tw-font-mono tw-text-sm tw-break-all">
          <div class="tw-mt-4">
            <div v-if="formattedData" class="tw-overflow-x-auto content-container">
              <component :is="renderJsonNode(formattedData, '')" />
            </div>
            <div v-else class="tw-text-gray-500">
              无数据
            </div>
          </div>
        </div>
      </div>
      <a-empty v-else description="暂无响应数据" />
      
      <div class="tw-mt-4 tw-bg-gray-900/30 tw-rounded-lg tw-p-4">
        <h3 class="tw-font-medium tw-text-gray-300 tw-mb-2">使用说明</h3>
        <ul class="tw-text-sm tw-text-gray-400 tw-list-disc tw-pl-4">
          <li class="tw-mb-1">点击对象或数组前的箭头可以展开/折叠节点</li>
          <li class="tw-mb-1">点击值后面的"{{ fieldType === 'extract' ? '选择' : '断言' }}"按钮可以选择该路径进行测试</li>
          <li class="tw-mb-1">使用测试区域可以调试{{ fieldType === 'extract' ? '提取' : '断言' }}表达式，测试成功后可应用到{{ fieldType === 'extract' ? '提取规则' : '断言配置' }}中</li>
          <li class="tw-mb-1">选择的路径会自动转换为JMESPath表达式</li>
          <li>路径格式示例: <code class="tw-bg-gray-800 tw-px-1 tw-py-0.5 tw-rounded">body.data.users[0].name</code></li>
        </ul>
      </div>
    </div>
  </a-drawer>
</template>

<style lang="postcss" scoped>
:deep(.arco-drawer) {
  @apply tw-bg-gray-800;
}

:deep(.arco-drawer-header) {
  @apply tw-border-gray-700 tw-bg-gray-800 tw-text-gray-300;
}

:deep(.arco-drawer-body) {
  @apply tw-bg-gray-800 tw-text-gray-300;
}

:deep(.arco-empty-description) {
  @apply tw-text-gray-500;
}

:deep(.arco-input-wrapper) {
  @apply tw-bg-gray-900/60 tw-border-gray-700;
  
  input {
    @apply tw-text-gray-200 tw-bg-transparent;
    &::placeholder {
      @apply tw-text-gray-500;
    }
  }
}

:deep(.arco-btn-primary) {
  @apply tw-bg-blue-600 tw-border-blue-600;
  
  &:hover {
    @apply tw-bg-blue-700 tw-border-blue-700;
  }
}

:deep(.arco-btn-primary.arco-btn-status-success) {
  @apply tw-bg-green-600 tw-border-green-600;
  
  &:hover {
    @apply tw-bg-green-700 tw-border-green-700;
  }
}

.tw-font-mono {
  word-break: break-all;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

/* 优化内容容器样式 */
.tw-overflow-x-auto {
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
  overflow-x: auto;
  max-width: 100%;
  display: block;
  padding-right: 8px; /* 为滚动条预留空间 */
}

/* 添加内容容器样式 */
.content-container {
  max-height: 500px;
  overflow-y: auto;
}

.tw-overflow-x-auto::-webkit-scrollbar {
  height: 6px;
  width: 6px;
}

.tw-overflow-x-auto::-webkit-scrollbar-track {
  background: transparent;
}

.tw-overflow-x-auto::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.tw-overflow-x-auto::-webkit-scrollbar-thumb:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

code {
  font-family: monospace;
}

pre {
  margin: 0;
  font-family: 'Monaco', 'Courier New', monospace;
}
</style>