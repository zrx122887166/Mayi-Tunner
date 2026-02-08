<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, shallowRef } from 'vue'
import { Message } from '@arco-design/web-vue'
import type { Function } from '../../../api/function'
import { testFunction } from '../../../api/function'
import * as monaco from 'monaco-editor'

const props = defineProps<{
  mode: 'create' | 'edit'
  loading?: boolean
  initialValues?: Function
}>()

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'submit', values: Partial<Function>): void
}>()

const form = ref({
  name: props.initialValues?.name || '',
  code: props.initialValues?.code || '',
  description: props.initialValues?.description || ''
})

const testArgs = ref('{}')
const testLoading = ref(false)
const testResult = ref('')

// 代码编辑器相关
const codeEditorContainer = ref<HTMLElement>()
const codeEditor = shallowRef<monaco.editor.IStandaloneCodeEditor>()

// 测试参数编辑器相关
const argsEditorContainer = ref<HTMLElement>()
const argsEditor = shallowRef<monaco.editor.IStandaloneCodeEditor>()

// 初始化代码编辑器
const initCodeEditor = () => {
  if (!codeEditorContainer.value || codeEditor.value) return

  codeEditor.value = monaco.editor.create(codeEditorContainer.value, {
    value: form.value.code,
    language: 'python',
    theme: 'vs-dark',
    automaticLayout: true,
    minimap: { enabled: true },
    scrollBeyondLastLine: false,
    fontSize: 14,
    tabSize: 4,
    renderLineHighlight: 'all',
    roundedSelection: false,
    occurrencesHighlight: 'off',
    cursorBlinking: 'smooth',
    cursorSmoothCaretAnimation: 'on',
    smoothScrolling: true,
    mouseWheelZoom: true,
    padding: { top: 10, bottom: 10 }
  })

  // 监听内容变化
  codeEditor.value.onDidChangeModelContent(() => {
    form.value.code = codeEditor.value?.getValue() || ''
  })
}

// 初始化测试参数编辑器
const initArgsEditor = () => {
  if (!argsEditorContainer.value || argsEditor.value) return

  argsEditor.value = monaco.editor.create(argsEditorContainer.value, {
    value: testArgs.value,
    language: 'json',
    theme: 'vs-dark',
    automaticLayout: true,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    fontSize: 14,
    tabSize: 2,
    renderLineHighlight: 'all',
    roundedSelection: false,
    occurrencesHighlight: 'off',
    cursorBlinking: 'smooth',
    cursorSmoothCaretAnimation: 'on',
    smoothScrolling: true,
    mouseWheelZoom: true,
    padding: { top: 10, bottom: 10 }
  })

  // 监听内容变化
  argsEditor.value.onDidChangeModelContent(() => {
    testArgs.value = argsEditor.value?.getValue() || '{}'
  })
}

onMounted(() => {
  initCodeEditor()
  initArgsEditor()
})

onUnmounted(() => {
  if (codeEditor.value) {
    codeEditor.value.dispose()
  }
  if (argsEditor.value) {
    argsEditor.value.dispose()
  }
})

const handleSubmit = () => {
  if (!form.value.name.trim()) {
    Message.warning('请输入函数名称')
    return
  }
  if (!form.value.code.trim()) {
    Message.warning('请输入函数代码')
    return
  }
  emit('submit', form.value)
}

const handleTest = async () => {
  if (!form.value.code.trim()) {
    Message.warning('请先输入函数代码')
    return
  }

  let parsedArgs
  try {
    parsedArgs = JSON.parse(testArgs.value)
  } catch (error) {
    Message.error('测试参数格式不正确，请输入有效的JSON')
    return
  }

  try {
    testLoading.value = true
    const response = await testFunction({
      code: form.value.code,
      test_args: parsedArgs
    })
    
    testResult.value = response.result || '测试结果为空'
    Message.success('测试运行成功')
  } catch (error: any) {
    console.error('测试运行失败:', error)
    testResult.value = error.response?.data?.message || '测试运行失败'
    Message.error(error.response?.data?.message || '测试运行失败')
  } finally {
    testLoading.value = false
  }
}
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-bg-gray-900 tw-rounded-lg tw-overflow-hidden">
    <!-- 头部区域 -->
    <div class="tw-px-6 tw-py-4 tw-border-b tw-border-gray-800">
      <div class="tw-flex tw-justify-between tw-items-center">
        <h2 class="tw-text-xl tw-font-semibold tw-text-gray-100">
          {{ mode === 'create' ? '新建函数' : '编辑函数' }}
        </h2>
        <div class="tw-flex tw-gap-2">
          <a-button @click="emit('cancel')" class="!tw-bg-gray-800 !tw-border-gray-700 !tw-text-gray-300">
            取消
          </a-button>
          <a-button
            type="primary"
            :loading="loading"
            @click="handleSubmit"
            class="!tw-bg-blue-500 !tw-border-blue-500 hover:!tw-bg-blue-600 hover:!tw-border-blue-600"
          >
            {{ mode === 'create' ? '创建' : '保存' }}
          </a-button>
        </div>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="tw-flex-1 tw-min-h-0 tw-overflow-y-auto">
      <div class="tw-p-6">
        <a-form :model="form" layout="vertical">
          <!-- 基本信息 -->
          <div class="tw-grid tw-grid-cols-2 tw-gap-4 tw-mb-6">
            <a-form-item field="name" label="函数名称" class="!tw-mb-0">
              <a-input
                v-model="form.name"
                placeholder="请输入函数名称"
                class="!tw-bg-gray-800/60 !tw-border-gray-700"
              />
            </a-form-item>
            <a-form-item field="description" label="函数描述" class="!tw-mb-0">
              <a-input
                v-model="form.description"
                placeholder="请输入函数描述"
                class="!tw-bg-gray-800/60 !tw-border-gray-700"
              />
            </a-form-item>
          </div>

          <!-- 代码编辑器 -->
          <a-form-item field="code" label="函数代码" class="!tw-mb-6">
            <div ref="codeEditorContainer" class="tw-h-[400px] tw-w-full tw-border tw-border-gray-700 tw-rounded" />
          </a-form-item>

          <!-- 测试区域 -->
          <div class="tw-bg-gray-800/40 tw-rounded-lg tw-p-4">
            <div class="tw-flex tw-justify-between tw-items-center tw-mb-4">
              <h3 class="tw-text-base tw-font-medium tw-text-gray-200">函数测试</h3>
              <a-button
                type="primary"
                size="small"
                :loading="testLoading"
                @click="handleTest"
                class="!tw-bg-purple-500 !tw-border-purple-500 hover:!tw-bg-purple-600 hover:!tw-border-purple-600"
              >
                运行测试
              </a-button>
            </div>
            
            <div class="tw-mb-4">
              <div class="tw-text-sm tw-text-gray-400 tw-mb-2">测试参数 (JSON格式)</div>
              <div ref="argsEditorContainer" class="tw-h-[100px] tw-w-full tw-border tw-border-gray-700 tw-rounded" />
            </div>

            <div v-if="testResult">
              <div class="tw-text-sm tw-text-gray-400 tw-mb-2">测试结果</div>
              <a-textarea
                v-model="testResult"
                :style="{ height: '150px' }"
                readonly
                class="!tw-bg-gray-800/60 !tw-border-gray-700"
              />
            </div>
          </div>
        </a-form>
      </div>
    </div>
  </div>
</template>

<style lang="postcss" scoped>
:deep(.arco-form-item-label) {
  > label {
    @apply tw-text-gray-300;
  }
}

:deep(.arco-form-item-content) {
  @apply tw-h-full;
}

:deep(.arco-textarea),
:deep(.arco-input) {
  @apply tw-text-gray-200;
  
  &::placeholder {
    @apply tw-text-gray-500;
  }
}

:deep(.arco-btn) {
  @apply tw-rounded-lg;
}

/* 滚动条样式 */
.tw-overflow-y-auto {
  &::-webkit-scrollbar {
    @apply tw-w-2;
  }
  
  &::-webkit-scrollbar-track {
    @apply tw-bg-transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    @apply tw-bg-gray-700 tw-rounded-full;
    
    &:hover {
      @apply tw-bg-gray-600;
    }
  }
}
</style> 