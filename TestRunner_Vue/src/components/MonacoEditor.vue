<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { Message } from '@arco-design/web-vue'
import * as monaco from 'monaco-editor'

interface Props {
  modelValue?: string | Record<string, any> | null
  readonly?: boolean
  language?: string
  theme?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  readonly: false,
  language: 'json',
  theme: 'vs-dark'
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
    language: props.language,
    theme: props.theme,
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
    wordWrap: 'on',
    wrappingStrategy: 'advanced',
    scrollbar: {
      vertical: 'hidden',
      horizontal: 'hidden',
      useShadows: false,
      verticalScrollbarSize: 0,
      horizontalScrollbarSize: 0
    }
  })

  // 监听内容变化
  editor.onDidChangeModelContent(() => {
    try {
      const value = editor.getValue()
      if (props.language === 'json') {
        const jsonValue = value ? JSON.parse(value) : null
        emit('update:modelValue', jsonValue)
      } else {
        emit('update:modelValue', value)
      }
    } catch (error) {
      // 如果不是 JSON 或解析错误，直接发送原始值
      emit('update:modelValue', editor.getValue())
    }
  })

  // 监听内容变化时更新编辑器高度
  editor.onDidContentSizeChange(() => {
    const contentHeight = Math.min(400, editor.getContentHeight())
    editorContainer.value!.style.height = `${contentHeight}px`
    editor.layout()
  })
}

// 格式化值
const formatValue = (value: any): string => {
  if (value === null || value === undefined) {
    return ''
  }
  if (props.language === 'json') {
    if (typeof value === 'string') {
      try {
        return JSON.stringify(JSON.parse(value), null, 2)
      } catch {
        return value
      }
    }
    return JSON.stringify(value, null, 2)
  }
  return typeof value === 'string' ? value : String(value)
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

// 监听语言变化
watch(() => props.language, (newValue) => {
  if (editor) {
    monaco.editor.setModelLanguage(editor.getModel()!, newValue)
  }
})

// 组件挂载时初始化编辑器
onMounted(() => {
  initEditor()
})

// 组件卸载时销毁编辑器
onBeforeUnmount(() => {
  if (editor) {
    editor.dispose()
  }
})
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
  
  /* 隐藏滚动条 */
  .monaco-scrollable-element {
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
    
    .scrollbar {
      display: none !important;
    }
    
    &::-webkit-scrollbar {
      display: none !important;
    }
  }
}

:deep(.monaco-editor .monaco-scrollable-element .monaco-editor-background) {
  @apply tw-bg-gray-900/60;
}

:deep(.monaco-editor .monaco-scrollable-element .scrollbar) {
  @apply tw-bg-gray-800;
  
  .slider {
    @apply tw-bg-gray-600;
  }
}
</style>