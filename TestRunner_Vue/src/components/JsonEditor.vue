<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import * as monaco from 'monaco-editor'

interface Props {
  modelValue?: string | Record<string, any> | null
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  readonly: false
})

const emit = defineEmits(['update:modelValue'])

// 编辑器容器引用
const editorContainer = ref<HTMLElement>()

// 编辑器实例
let editor: monaco.editor.IStandaloneCodeEditor

// 初始化编辑器
const initEditor = () => {
  if (!editorContainer.value) return

  // 创建编辑器实例
  editor = monaco.editor.create(editorContainer.value, {
    value: formatValue(props.modelValue),
    language: 'json',
    theme: 'vs-dark',
    automaticLayout: true,
    minimap: {
      enabled: false
    },
    scrollBeyondLastLine: false,
    fontSize: 14,
    tabSize: 2,
    readOnly: props.readonly,
    lineNumbers: 'on',
    roundedSelection: true,
    scrollbar: {
      vertical: 'visible',
      horizontal: 'visible',
      useShadows: false,
      verticalScrollbarSize: 8,
      horizontalScrollbarSize: 8
    }
  })

  // 监听内容变化
  editor.onDidChangeModelContent(() => {
    try {
      const value = editor.getValue()
      const jsonValue = value ? JSON.parse(value) : null
      emit('update:modelValue', jsonValue)
    } catch (error) {
      // JSON 解析错误时不更新值
    }
  })
}

// 格式化值
const formatValue = (value: any): string => {
  if (value === null || value === undefined) {
    return ''
  }
  if (typeof value === 'string') {
    try {
      return JSON.stringify(JSON.parse(value), null, 2)
    } catch {
      return value
    }
  }
  return JSON.stringify(value, null, 2)
}

// 监听值变化
watch(() => props.modelValue, (newValue) => {
  if (editor && editor.getValue() !== formatValue(newValue)) {
    editor.setValue(formatValue(newValue))
  }
})

// 监听只读状态变化
watch(() => props.readonly, (newValue) => {
  if (editor) {
    editor.updateOptions({ readOnly: newValue })
  }
})

// 组件挂载时初始化编辑器
onMounted(() => {
  initEditor()
})

// 组件卸载时销毁编辑器
const onBeforeUnmount = () => {
  if (editor) {
    editor.dispose()
  }
}
</script>

<template>
  <div ref="editorContainer" class="tw-w-full tw-h-full tw-rounded-lg tw-overflow-hidden" />
</template>

<style lang="postcss" scoped>
:deep(.monaco-editor) {
  .margin,
  .monaco-editor-background {
    @apply tw-bg-gray-900/60;
  }
}
</style> 