<template>
  <div class="tool-directory-container">
    <!-- 警告信息 -->
    <el-alert
      v-if="showWarning"
      title="提示"
      message="请先选择一个工具再执行"
      type="warning"
      show-icon
      class="alert-warning"
    />

    <div class="tool-content">
      <!-- 左侧目录 -->
      <div class="directory-menu">
        <el-menu 
          :disabled="loading"
          :default-active="activeToolId"
          class="tool-menu"
        >
          <el-menu-item
            v-for="tool in toolList"
            :key="tool.id"
            :index="tool.id.toString()"
            @click="handleToolClick(tool)"
          >
            {{ tool.name }}
          </el-menu-item>
        </el-menu>
      </div>

      <!-- 右侧内容 -->
      <div class="tool-detail">
        <div v-if="currentTool" class="tool-detail-content">
          <h2 class="tool-title">{{ currentTool.name }}</h2>

          <!-- 接口输入区域 - 水平布局，包含参数和执行按钮 -->
          <div class="input-section">
            <div class="param-and-button-container">
              <div class="param-row">
                <div v-for="param in currentTool.params" :key="param.name" class="param-item">
                  <span class="param-label">{{ param.show_name }}:</span>
                  <template v-if="param.keys === ''">
                    <el-input
                      v-model="inputData[param.name]"
                      placeholder="请输入"
                      class="param-input"
                      :disabled="loading"
                    />
                  </template>
                  <template v-else>
                    <el-select
                      v-model="inputData[param.name]"
                      placeholder="请选择"
                      class="param-select"
                      :disabled="loading"
                    >
                      <el-option
                        v-for="option in param.keys.split(';;')"
                        :key="option"
                        :label="option"
                        :value="option"
                      />
                    </el-select>
                  </template>
                </div>
              </div>
              
              <div class="execute-btn-container">
                <el-button 
                  type="primary" 
                  @click="executeScript" 
                  :disabled="loading"
                  class="execute-btn"
                >
                  执行
                </el-button>
              </div>
            </div>
          </div>

          <!-- 工具说明 -->
          <div class="tool-remark">
            <h3 class="section-title">工具使用说明：</h3>
            <p>{{ currentTool.remark || '无说明' }}</p>
          </div>

          <!-- 脚本预览 -->
          <div class="script-preview">
            <h3 class="section-title">脚本预览</h3>
            <div class="code-container">
              <pre v-if="formattedScript"><code class="language-python">{{ formattedScript }}</code></pre>
              <div v-else class="no-script-tip">暂无脚本代码</div>
            </div>
          </div>
        </div>

        <div v-else class="empty-tip">
          请从左侧目录选择工具
        </div>
      </div>
    </div>
    <el-loading :visible="loading" text="请求中..." fullscreen></el-loading>
  </div>
</template>

<script setup>
// 脚本部分保持不变
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import request from '@/utils/request';
import hljs from 'highlight.js/lib/core';
import python from 'highlight.js/lib/languages/python';
import 'highlight.js/styles/github.css';
import { ElMessageBox, ElMessage } from 'element-plus';

// 注册Python语言
hljs.registerLanguage('python', python);

// 状态定义
const toolList = ref([]);
const currentTool = ref(null);
const formattedScript = ref('');
const inputData = ref({});
const loading = ref(false);
const showWarning = ref(false);
const activeToolId = ref('');

// 计算属性
const currentToolName = computed(() => {
  return currentTool.value ? currentTool.value.name : '工具目录';
});

// 格式化并高亮代码
const formatAndHighlightCode = (code) => {
  if (!code) return '';
  
  try {
    // 使用highlight.js进行语法高亮
    const highlighted = hljs.highlight(code, { language: 'python' });
    return highlighted.value;
  } catch (error) {
    console.error('代码高亮失败:', error);
    // 如果高亮失败，返回原始代码
    return code;
  }
};

// 获取工具列表
const fetchTools = async () => {
  try {
    loading.value = true;
    const baseApi = import.meta.env.VUE_APP_BASE_API || 'http://localhost:8000';
    
    const url = `${baseApi}/api/pythontool/?size=100`;
    console.log('获取工具列表URL:', url);
    
    const response = await request.get(url);
    console.log('工具列表响应:', response);
    
    let responseData = response;
    if (response && typeof response === 'object' && 'data' in response) {
      responseData = response.data;
    }
    
    console.log('处理后的工具列表数据:', responseData);
    
    if (responseData && responseData.results) {
      toolList.value = responseData.results;
      console.log('设置工具列表:', toolList.value);
    } else {
      console.warn('工具列表数据格式异常:', responseData);
      toolList.value = [];
    }
  } catch (error) {
    console.error('获取工具列表失败:', error);
    ElMessage.error('获取工具列表失败：' + (error.message || '网络错误'));
  } finally {
    loading.value = false;
  }
};

// 处理工具点击
const handleToolClick = async (tool) => {
  try {
    loading.value = true;
    const baseApi = import.meta.env.VUE_APP_BASE_API || 'http://localhost:8000';
    
    const url = `${baseApi}/api/pythontool/${tool.id}/`;
    console.log('获取工具详情URL:', url);
    
    const response = await request.get(url);
    console.log('工具详情响应:', response);
    
    let toolDetail = response;
    if (response && typeof response === 'object' && 'data' in response) {
      toolDetail = response.data;
    }
    
    console.log('处理后的工具详情:', toolDetail);
    
    if (toolDetail) {
      currentTool.value = toolDetail;
      activeToolId.value = tool.id.toString();
      
      // 直接使用pythonScript字段，确保字段名正确
      const scriptCode = toolDetail.pythonScript || '';
      console.log('获取到的脚本代码:', scriptCode);
      
      // 格式化并高亮代码
      formattedScript.value = scriptCode;
      
      // 初始化输入数据
      inputData.value = {};
      if (toolDetail.params && toolDetail.params.length) {
        toolDetail.params.forEach(param => {
          inputData.value[param.name] = param.default || '';
        });
      }
      
      console.log('设置当前工具:', currentTool.value);
      console.log('设置输入数据:', inputData.value);

      // 延迟执行代码高亮，确保DOM已更新
      nextTick(() => {
        // 手动高亮所有代码块
        document.querySelectorAll('pre code').forEach((block) => {
          hljs.highlightElement(block);
        });
      });
    } else {
      ElMessage.error('获取工具详情失败：数据格式异常');
    }
  } catch (error) {
    console.error('获取工具详情失败:', error);
    ElMessage.error('获取工具详情失败：' + (error.message || '服务器错误'));
  } finally {
    loading.value = false;
  }
};

// 执行脚本
const executeScript = async () => {
  if (!currentTool.value) {
    showWarning.value = true;
    setTimeout(() => showWarning.value = false, 3000);
    return;
  }

  try {
    loading.value = true;
    const baseApi = import.meta.env.VUE_APP_BASE_API || 'http://localhost:8000';
    
    const url = `${baseApi}/api/python_run/`;
    
    const dataToSend = {
      id: currentTool.value.id,
      ...inputData.value
    };
    
    console.log('执行脚本URL:', url);
    console.log('执行脚本数据:', dataToSend);
    
    const response = await request.post(url, dataToSend);
    console.log('执行脚本响应:', response);
    
    let responseData = response;
    if (response && typeof response === 'object' && 'data' in response) {
      responseData = response.data;
    }
    
    console.log('处理后的执行结果:', responseData);

    if (responseData && responseData.message === '执行成功') {
      ElMessageBox.alert(
        `执行成功！\n输出结果：\n${responseData.output}`, 
        '提示', 
        { type: 'success' }
      );
    } else {
      const errorMsg = responseData?.error || responseData?.detail?.stderr || '未知错误';
      ElMessageBox.alert(
        `执行失败：${errorMsg}`, 
        '提示', 
        { type: 'error' }
      );
    }
  } catch (error) {
    console.error('执行脚本失败:', error);
    ElMessageBox.alert(
      `请求失败：${error.response?.data?.error || error.message || '网络错误'}`, 
      '提示', 
      { type: 'error' }
    );
  } finally {
    loading.value = false;
  }
};

// 监听formattedScript变化，重新高亮
watch(formattedScript, () => {
  nextTick(() => {
    document.querySelectorAll('pre code').forEach((block) => {
      hljs.highlightElement(block);
    });
  });
});

onMounted(() => {
  console.log('组件挂载，开始获取工具列表...');
  fetchTools();
  
  // 延迟执行代码高亮
  setTimeout(() => {
    document.querySelectorAll('pre code').forEach((block) => {
      hljs.highlightElement(block);
    });
  }, 500);
});
</script>

<style scoped>
/* 全局样式重置 */
.tool-directory-container {
  width: 100%;
  padding: 0;
  margin: 0;
  box-sizing: border-box;
  background-color: rgba(31, 41, 55, 0.5);
  min-height: 100vh;
  padding: 20px;
}

/* 面包屑导航样式 */
.breadcrumb {
  margin-bottom: 20px;
  background-color: rgba(55, 65, 81, 0.5);
  padding: 15px 20px;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.breadcrumb :deep(.el-breadcrumb__item) {
  color: #94a3b8;
}

.breadcrumb :deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: #e2e8f0;
}

.breadcrumb :deep(.el-breadcrumb__inner) {
  color: #94a3b8;
}

.breadcrumb :deep(.el-breadcrumb__inner:hover) {
  color: #60a5fa;
}

/* 警告信息样式 */
.alert-warning {
  margin-bottom: 20px;
  border-radius: 8px;
  border: none;
  background-color: rgba(251, 191, 36, 0.1);
}

.alert-warning :deep(.el-alert__title) {
  color: #fbbf24;
}

.alert-warning :deep(.el-alert__description) {
  color: #94a3b8;
}

/* 主内容区域 */
.tool-content {
  display: flex;
  margin-top: 20px;
  gap: 20px;
  height: calc(100vh - 200px);
}

/* 左侧目录样式 */
.directory-menu {
  width: 260px;
  border: 1px solid rgba(148, 163, 184, 0.1);
  border-radius: 8px;
  height: 100%;
  overflow-y: auto;
  background-color: rgba(55, 65, 81, 0.5);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.tool-menu {
  border-right: none;
  background-color: transparent;
}

.tool-menu :deep(.el-menu-item) {
  color: #94a3b8;
  background-color: transparent;
  height: 45px;
  line-height: 45px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

.tool-menu :deep(.el-menu-item:hover) {
  background-color: rgba(59, 130, 246, 0.1);
  color: #60a5fa;
}

.tool-menu :deep(.el-menu-item.is-active) {
  background-color: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border-left: 3px solid #60a5fa;
}

/* 右侧内容区域 */
.tool-detail {
  flex: 1;
  padding: 0;
  background-color: rgba(55, 65, 81, 0.5);
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
}

.tool-detail-content {
  background-color: transparent;
  border-radius: 8px;
  padding: 20px;
  color: #e2e8f0;
}

.tool-title {
  margin: 0 0 20px 0;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  color: #e2e8f0;
  font-size: 20px;
  font-weight: 600;
}

/* 输入区域样式 - 水平布局，包含参数和执行按钮 */
.input-section {
  margin: 20px 0;
  padding: 20px;
  background-color: rgba(30, 41, 59, 0.3);
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.param-and-button-container {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.param-row {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
  flex: 1;
  min-width: 300px;
}

.param-item {
  display: flex;
  align-items: center;
  flex: 0 0 auto;
  margin-bottom: 0;
}

.param-label {
  min-width: auto;
  color: #94a3b8;
  font-weight: 500;
  margin-right: 8px;
  white-space: nowrap;
}

.param-input, .param-select {
  width: 180px;
}

.execute-btn-container {
  display: flex;
  align-items: center;
  margin-left: auto;
}

.execute-btn {
  background: linear-gradient(to right, #3b82f6, #1d4ed8);
  border: none;
  color: #fff;
  border-radius: 8px;
  padding: 0 20px;
  height: 36px;
  transition: all 0.3s ease;
}

.execute-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
  background: linear-gradient(to right, #2563eb, #60a5fa);
}

.execute-btn:disabled {
  background: rgba(148, 163, 184, 0.3);
  transform: none;
  box-shadow: none;
  cursor: not-allowed;
}

/* 工具说明样式 */
.tool-remark {
  background: rgba(30, 41, 59, 0.3);
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
  color: #94a3b8;
  line-height: 1.6;
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.section-title {
  font-size: 16px;
  color: #e2e8f0;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  font-weight: 600;
}

/* 脚本预览样式 */
.script-preview {
  margin: 20px 0;
}

.code-container {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.script-preview pre {
  margin: 0;
  padding: 20px;
  overflow-x: auto;
  line-height: 1.5;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  color: #e2e8f0;
  background: transparent;
}

.no-script-tip {
  padding: 40px 20px;
  text-align: center;
  color: #94a3b8;
  background: transparent;
}

.empty-tip {
  text-align: center;
  color: #94a3b8;
  padding: 80px 0;
  background-color: transparent;
  border-radius: 8px;
  font-size: 16px;
}

/* 确保代码高亮样式正确 */
:deep(.hljs) {
  background: transparent !important;
  color: #e2e8f0 !important;
}

/* 输入框和选择框样式覆盖 */
:deep(.el-input__wrapper) {
  background-color: rgba(30, 41, 59, 0.6) !important;
  border-color: rgba(148, 163, 184, 0.2) !important;
  box-shadow: none !important;
  color: #e2e8f0 !important;
}

:deep(.el-input__wrapper:hover) {
  border-color: #60a5fa !important;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #60a5fa !important;
  box-shadow: 0 0 0 1px #60a5fa !important;
}

:deep(.el-input__inner) {
  color: #e2e8f0 !important;
}

:deep(.el-input__suffix) {
  color: #94a3b8 !important;
}

:deep(.el-select .el-input__wrapper) {
  background-color: rgba(30, 41, 59, 0.6) !important;
  border-color: rgba(148, 163, 184, 0.2) !important;
}

:deep(.el-select .el-input__inner) {
  color: #e2e8f0 !important;
}

/* 下拉选择器样式 - 调整为深色背景 */
:deep(.el-select-dropdown) {
  background-color: rgba(30, 41, 59, 0.95) !important;
  border: 1px solid rgba(148, 163, 184, 0.2) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
}

:deep(.el-select-dropdown__item) {
  color: #e2e8f0 !important;
  background-color: transparent !important;
}

:deep(.el-select-dropdown__item:hover) {
  background-color: rgba(59, 130, 246, 0.2) !important;
}

:deep(.el-select-dropdown__item.selected) {
  background-color: rgba(59, 130, 246, 0.3) !important;
  color: #60a5fa !important;
}

:deep(.el-select-dropdown__item.hover) {
  background-color: rgba(59, 130, 246, 0.15) !important;
}

:deep(.el-select-dropdown__empty) {
  color: #94a3b8 !important;
  padding: 10px 0;
}

/* 加载样式 */
:deep(.el-loading-mask) {
  background-color: rgba(15, 23, 42, 0.7) !important;
}

:deep(.el-loading-spinner .path) {
  stroke: #60a5fa !important;
}

:deep(.el-loading-text) {
  color: #94a3b8 !important;
}

/* 代码高亮样式调整 */
:deep(.hljs-keyword) {
  color: #60a5fa !important;
}

:deep(.hljs-string) {
  color: #34d399 !important;
}

:deep(.hljs-comment) {
  color: #94a3b8 !important;
}

:deep(.hljs-function) {
  color: #f472b6 !important;
}

:deep(.hljs-number) {
  color: #f59e0b !important;
}

/* 响应式设计 - 当屏幕宽度不足时自动换行 */
@media (max-width: 1200px) {
  .param-row {
    gap: 15px;
  }
  
  .param-input, .param-select {
    width: 160px;
  }
}

@media (max-width: 992px) {
  .param-row {
    gap: 12px;
  }
  
  .param-input, .param-select {
    width: 140px;
  }
}

@media (max-width: 768px) {
  .param-and-button-container {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .execute-btn-container {
    margin-left: 0;
    margin-top: 15px;
    align-self: flex-end;
  }
  
  .param-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    min-width: 100%;
  }
  
  .param-item {
    width: 100%;
  }
  
  .param-input, .param-select {
    width: 100%;
  }
}
</style>

<style>
/* 全局样式覆盖 - 与主题保持一致 */
/* 警告框样式 */
.el-alert {
  border-radius: 8px !important;
  border: none !important;
}

.el-alert--warning {
  background-color: rgba(251, 191, 36, 0.1) !important;
}

.el-alert--warning .el-alert__title {
  color: #fbbf24 !important;
}

.el-alert--warning .el-alert__description {
  color: #94a3b8 !important;
}

/* 菜单样式 */
.el-menu {
  background-color: transparent !important;
  border: none !important;
}

.el-menu-item {
  color: #94a3b8 !important;
  background-color: transparent !important;
}

.el-menu-item:hover {
  background-color: rgba(59, 130, 246, 0.1) !important;
  color: #60a5fa !important;
}

.el-menu-item.is-active {
  background-color: rgba(59, 130, 246, 0.2) !important;
  color: #60a5fa !important;
}

/* 按钮样式统一 */
.el-button--primary {
  background: linear-gradient(to right, #3b82f6, #1d4ed8) !important;
  border: none !important;
  color: #fff !important;
}

.el-button--primary:hover {
  background: linear-gradient(to right, #2563eb, #60a5fa) !important;
}

.el-button--primary:disabled {
  background: rgba(148, 163, 184, 0.3) !important;
  color: #94a3b8 !important;
  cursor: not-allowed !important;
}

/* 面包屑样式 */
.el-breadcrumb__item {
  color: #94a3b8 !important;
}

.el-breadcrumb__inner {
  color: #94a3b8 !important;
}

.el-breadcrumb__inner:hover {
  color: #60a5fa !important;
}

.el-breadcrumb__item:last-child .el-breadcrumb__inner {
  color: #e2e8f0 !important;
}

/* 下拉选择器箭头颜色 */
.el-select .el-input .el-select__caret {
  color: #94a3b8 !important;
}

.el-select .el-input .el-select__caret:hover {
  color: #60a5fa !important;
}

/* 确保下拉菜单完全融入深色主题 */
.el-select-dropdown__wrap {
  background-color: transparent !important;
}

.el-select-dropdown__item {
  color: #e2e8f0 !important;
}

.el-select-dropdown__item:hover {
  background-color: rgba(59, 130, 246, 0.2) !important;
}

.el-select-dropdown__item.selected {
  color: #60a5fa !important;
  background-color: rgba(59, 130, 246, 0.3) !important;
}
</style>