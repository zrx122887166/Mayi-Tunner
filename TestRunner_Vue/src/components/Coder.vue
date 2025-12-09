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

export default {
  // 注册组件
  components: {
    Codemirror
  },
  // 定义 props
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
    }
  },
  // 定义数据
  data() {
    return {
      script: this.content,
      extensions: [python()]
    };
  },
  // 监听 props 变化
  watch: {
    content(newValue) {
      this.script = newValue;
    }
  },
  // 定义方法
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

/* 编辑器主体样式 */
::v-deep .cm-editor {
  width: 100%;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

/* 聚焦状态样式 */
::v-deep .cm-editor.cm-focused {
  border-color: #42b983; /* Vue 绿色作为焦点色 */
  box-shadow: 0 0 0 2px rgba(66, 185, 131, 0.2);
  outline: none;
}

/* 占位符样式 */
::v-deep .cm-placeholder {
  color: #9e9e9e;
  font-style: italic;
}

/* 只读状态样式 */
::v-deep .cm-editor[disabled] {
  background-color: #f5f5f5;
  cursor: not-allowed;
  border-color: #e0e0e0;
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