<template>
  <div class="code-editor-container">
    <codemirror
      v-model="script"
      placeholder="在此输入python脚本"
      :style="{ height: '500px', 'font-size': '14px' }" 
      :autofocus="true"
      :indent-with-tab="true"
      :tab-size="2"
      :extensions="extensions"
      :disabled="readOnly"
      @blur="updateScript"
      class="code-mirror-editor"
    />
  </div>
</template>

<script>
import { Codemirror } from 'vue-codemirror';
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark'; // 导入深色主题

export default {
  components: {
    Codemirror
  },
  props: {
    content: {
      type: String,
      default: ''
    },
    lang: {
      type: String,
      default: 'python'
    },
    readOnly: {
      type: Boolean,
      default: false
    },
    height: { // 添加高度属性
      type: String,
      default: '500px'
    }
  },
  data() {
    return {
      script: this.content,
      extensions: [python(), oneDark] // 应用深色主题
    };
  },
  watch: {
    content(newValue) {
      this.script = newValue;
    }
  },
  methods: {
    updateScript() {
      this.$emit('updateScript', this.script);
    }
  }
};
</script>

<style scoped>
.code-editor-container {
  width: 100%;
  max-width: 1800px;
  margin: 0 auto;
  padding: 16px;
  box-sizing: border-box;
}

::v-deep .code-mirror-editor {
  transition: all 0.3s ease;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

/* 深色主题样式 */
::v-deep .cm-editor {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 8px;
  overflow: hidden;
  background-color: rgba(15, 23, 42, 0.9) !important;
}

/* 行号区域样式 */
::v-deep .cm-gutters {
  background-color: rgba(30, 41, 59, 0.9) !important; /* 行号背景色 */
  border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #94a3b8 !important; /* 行号文本颜色 */
}

/* 行号文本样式 */
::v-deep .cm-lineNumbers {
  color: #94a3b8 !important;
}

/* 编辑器内容样式 */
::v-deep .cm-content {
  color: #e5e7eb !important;
  caret-color: #60a5fa !important;
}

/* 聚焦状态样式 */
::v-deep .cm-editor.cm-focused {
  border-color: rgba(59, 130, 246, 0.8) !important;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2) !important;
  outline: none;
}

/* 占位符样式 */
::v-deep .cm-placeholder {
  color: #9ca3af !important;
  font-style: italic;
}

/* 只读状态样式 */
::v-deep .cm-editor[disabled] {
  background-color: rgba(15, 23, 42, 0.7) !important;
  cursor: not-allowed;
  border-color: rgba(255, 255, 255, 0.05) !important;
}

/* 光标样式 */
::v-deep .cm-cursor {
  border-left-color: #60a5fa !important;
}

/* 选中文本样式 */
::v-deep .cm-selectionBackground {
  background-color: rgba(59, 130, 246, 0.3) !important;
}

/* 代码高亮样式 */
::v-deep .cm-keyword {
  color: #f472b6 !important; /* 粉色关键字 */
}

::v-deep .cm-string {
  color: #34d399 !important; /* 绿色字符串 */
}

::v-deep .cm-comment {
  color: #94a3b8 !important; /* 灰色注释 */
  font-style: italic !important;
}

::v-deep .cm-function {
  color: #60a5fa !important; /* 蓝色函数名 */
}

::v-deep .cm-number {
  color: #f59e0b !important; /* 橙色数字 */
}

::v-deep .cm-builtin {
  color: #818cf8 !important; /* 紫色内置函数 */
}

::v-deep .cm-variable {
  color: #e5e7eb !important; /* 白色变量名 */
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .code-editor-container {
    padding: 12px;
  }
  
  ::v-deep .cm-editor {
    font-size: 13px !important;
  }
}

@media (max-width: 768px) {
  .code-editor-container {
    padding: 8px;
  }
  
  ::v-deep .cm-editor {
    font-size: 12px !important;
  }
}
</style>