<template>
  <div class="execution-container tw-h-full tw-flex tw-flex-col tw-gap-4 tw-p-4">
    <!-- 警告信息 -->
    <el-alert
      v-if="showWarning"
      title="提示"
      message="请先选择一个工具再执行"
      type="warning"
      show-icon
      class="alert-warning"
      :closable="false"
    />

    <div class="content-wrapper">
      <!-- 左侧目录 -->
      <div 
        ref="sidebarRef"
        class="directory-sidebar"
        :style="{ width: sidebarWidth + 'px' }"
      >
        <div class="sidebar-header">
          <div class="sidebar-title">工具目录</div>
        </div>
        <div class="tool-list-wrapper">
          <el-scrollbar class="tool-scrollbar">
            <div class="tool-list">
              <div 
                v-for="tool in toolList"
                :key="tool.id"
                class="tool-item"
                :class="{ 'active': activeToolId === tool.id.toString() }"
                @click="handleToolClick(tool)"
              >
                <div class="tool-icon">
                  <el-icon><Document /></el-icon>
                </div>
                <div class="tool-info">
                  <div class="tool-name">{{ tool.name }}</div>
                </div>
              </div>
            </div>
          </el-scrollbar>
        </div>
      </div>
      
      <!-- 可拖拽调整宽度的分隔条 -->
      <div 
        class="resize-handle"
        @mousedown="startResize"
        @touchstart="startResize"
      >
        <div class="handle-line"></div>
      </div>

      <!-- 右侧内容 -->
      <div class="execution-content">
        <div v-if="currentTool" class="execution-detail">
          <!-- 工具标题区域 -->
          <div class="tool-header">
            <h1 class="tool-title">{{ currentTool.name }}</h1>
          </div>

          <!-- 参数设置部分 -->
          <div v-if="currentTool.has_params && currentTool.params && currentTool.params.length > 0" class="params-section">
            <div class="section-header">
              <div class="section-title">参数设置</div>
            </div>
            <div class="section-body">
              <!-- 参数表格 - 水平布局 -->
              <div class="params-table-wrapper">
                <div class="table-container">
                  <table class="params-table">
                    <tbody>
                      <tr v-for="(param, index) in currentTool.params" :key="index">
                        <td class="param-cell label-cell">
                          <div class="param-label">
                            {{ param.show_name }}
                            <span v-if="param.default" class="param-hint">(默认值: {{ param.default }})</span>
                          </div>
                        </td>
                        <td class="param-cell input-cell">
                          <template v-if="param.keys === ''">
                            <el-input
                              v-model="inputData[param.name]"
                              :placeholder="param.default ? `默认值: ${param.default}` : '请输入参数值'"
                              class="table-input"
                              :disabled="loading"
                              clearable
                            />
                          </template>
                          <template v-else>
                            <el-select
                              v-model="inputData[param.name]"
                              :placeholder="param.default ? `默认值: ${param.default}` : '请选择参数值'"
                              class="table-select"
                              :disabled="loading"
                              clearable
                            >
                              <el-option
                                v-for="option in param.keys.split(';;')"
                                :key="option"
                                :label="option"
                                :value="option"
                              />
                            </el-select>
                          </template>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          <!-- 执行按钮 -->
          <div class="action-section">
            <el-button 
              type="primary" 
              @click="executeScript" 
              :loading="loading"
              class="execute-btn"
              :disabled="!currentTool"
            >
              <el-icon class="mr-2"><VideoPlay /></el-icon>
              执行脚本
            </el-button>
          </div>

          <!-- 工具说明 -->
          <div v-if="currentTool.remark" class="remark-section">
            <div class="section-header">
              <div class="section-title">工具说明</div>
            </div>
            <div class="section-body">
              <div class="remark-content">
                {{ currentTool.remark }}
              </div>
            </div>
          </div>

          <!-- Python脚本部分 - 使用Coder组件 -->
          <div class="script-section">
            <div class="section-header">
              <div class="section-title">Python 脚本</div>
            </div>
            <div class="section-body">
              <div class="script-editor-wrapper">
                <div v-if="currentTool.pythonScript" class="custom-coder-wrapper">
                  <!-- 使用Coder组件，设置只读模式 -->
                  <Coder
                    :lang="'python'"
                    :content="currentTool.pythonScript"
                    :readonly="true"
                    class="custom-coder"
                  />
                </div>
                <div v-else class="no-script">
                  <el-empty description="暂无脚本代码" />
                </div>
              </div>
            </div>
          </div>

          <!-- 执行结果 -->
          <div v-if="executionResult" class="result-section">
            <div class="section-header">
              <div class="section-title">执行结果</div>
              <el-button 
                type="text" 
                @click="executionResult = null" 
                class="clear-result-btn"
              >
                清除结果
              </el-button>
            </div>
            <div class="section-body">
              <div class="result-content">
                <div class="result-header">
                  <div class="result-status" :class="executionResult.success ? 'success' : 'error'">
                    <el-icon v-if="executionResult.success" color="#67c23a"><Check /></el-icon>
                    <el-icon v-else color="#f56c6c"><Close /></el-icon>
                    <span>{{ executionResult.success ? '执行成功' : '执行失败' }}</span>
                  </div>
                  <div class="result-time">{{ formatDateTime(executionResult.timestamp) }}</div>
                </div>
                <div class="result-output">
                  <pre>{{ executionResult.output }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty-state">
          <el-empty description="请从左侧选择要执行的工具">
            <template #image>
              <el-icon size="80" color="var(--el-color-info-light-3)">
                <Document />
              </el-icon>
            </template>
          </el-empty>
        </div>
      </div>
    </div>

    <!-- 加载遮罩 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-content">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <div class="loading-text">脚本执行中...</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue';
import request from '@/utils/request';
import Coder from '@/components/Coder'; // 导入Coder组件
import { 
  ElMessage, 
  ElNotification 
} from 'element-plus';
import { 
  Document, 
  VideoPlay,
  Loading,
  Check,
  Close
} from '@element-plus/icons-vue';

// 状态定义
const toolList = ref([]);
const currentTool = ref(null);
const inputData = ref({});
const loading = ref(false);
const showWarning = ref(false);
const activeToolId = ref('');
const executionResult = ref(null);
const sidebarWidth = ref(240);
const sidebarRef = ref(null);
let isResizing = false;

// 计算属性
const currentToolName = computed(() => {
  return currentTool.value ? currentTool.value.name : '工具目录';
});

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return '未知时间';
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).replace(/\//g, '-');
  } catch (error) {
    return dateStr;
  }
};

// 获取工具列表
const fetchTools = async () => {
  try {
    loading.value = true;
    const response = await request.get('/pythontool/', {
      params: { 
        size: 100,
        ordering: '-create_time'
      }
    });
    
    const responseData = response.data || response;
    
    if (responseData.results) {
      toolList.value = responseData.results;
    } else if (Array.isArray(responseData)) {
      toolList.value = responseData;
    } else {
      toolList.value = [];
    }
  } catch (error) {
    console.error('获取工具列表失败:', error);
    ElMessage.error('获取工具列表失败：' + (error.message || '网络错误'));
    toolList.value = [];
  } finally {
    loading.value = false;
  }
};

// 处理工具点击
const handleToolClick = async (tool) => {
  try {
    loading.value = true;
    
    const response = await request.get(`/pythontool/${tool.id}/`);
    const toolDetail = response.data || response;
    
    if (toolDetail) {
      currentTool.value = toolDetail;
      activeToolId.value = tool.id.toString();
      
      // 初始化输入数据
      inputData.value = {};
      if (toolDetail.params && toolDetail.params.length) {
        toolDetail.params.forEach(param => {
          inputData.value[param.name] = param.default || '';
        });
      }
      
      // 清除之前的执行结果
      executionResult.value = null;
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
    
    const dataToSend = {
      id: currentTool.value.id,
      ...inputData.value
    };
    
    const response = await request.post('/python_run/', dataToSend);
    const responseData = response.data || response;
    
    // 保存执行结果
    executionResult.value = {
      success: true,
      output: responseData.output || '无输出',
      timestamp: new Date().toISOString()
    };
    
    ElNotification.success({
      title: '执行成功',
      message: '脚本执行完成,页面底部查看执行结果',
      duration: 3000
    });
    
  } catch (error) {
    console.error('执行脚本失败:', error);
    
    // 保存错误结果
    executionResult.value = {
      success: false,
      output: error.response?.data?.error || error.response?.data?.detail?.stderr || error.message || '执行失败',
      timestamp: new Date().toISOString()
    };
    
    ElNotification.error({
      title: '执行失败',
      message: '脚本执行过程中出现错误',
      duration: 5000
    });
  } finally {
    loading.value = false;
  }
};

// 开始调整宽度
const startResize = (e) => {
  e.preventDefault();
  isResizing = true;
  
  const startX = e.clientX || e.touches[0].clientX;
  const startWidth = sidebarWidth.value;
  
  const handleMouseMove = (moveEvent) => {
    if (!isResizing) return;
    
    const currentX = moveEvent.clientX || moveEvent.touches[0].clientX;
    const diff = currentX - startX;
    const newWidth = Math.max(200, Math.min(400, startWidth + diff));
    
    sidebarWidth.value = newWidth;
  };
  
  const handleMouseUp = () => {
    isResizing = false;
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('touchmove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
    document.removeEventListener('touchend', handleMouseUp);
  };
  
  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('touchmove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
  document.addEventListener('touchend', handleMouseUp);
};

onMounted(() => {
  fetchTools();
});
</script>

<style scoped>
.execution-container {
  height: 100%;
  box-sizing: border-box;
}

/* 警告信息 */
.alert-warning {
  margin-bottom: 0;
  border-radius: 6px;
  border: none;
  background-color: rgba(245, 158, 11, 0.1);
}

.alert-warning :deep(.el-alert__title) {
  color: #f59e0b;
}

.alert-warning :deep(.el-alert__description) {
  color: #9ca3af;
}

/* 内容包装器 */
.content-wrapper {
  display: flex;
  height: calc(100vh - 160px);
  background-color: #121826;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  position: relative;
}

/* 左侧目录 */
.directory-sidebar {
  width: 240px;
  flex-shrink: 0;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  background-color: rgba(30, 41, 59, 0.3);
  display: flex;
  flex-direction: column;
  position: relative;
  user-select: none;
  resize: horizontal;
  min-width: 200px;
  max-width: 400px;
}

/* 可拖拽调整宽度的分隔条 */
.resize-handle {
  position: relative;
  width: 8px;
  background-color: transparent;
  cursor: col-resize;
  flex-shrink: 0;
  z-index: 10;
  margin-left: -4px;
}

.resize-handle:hover .handle-line,
.resize-handle:active .handle-line {
  background-color: rgba(59, 130, 246, 0.8);
}

.handle-line {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.15);
  transition: background-color 0.2s ease;
}

.resize-handle:hover::after,
.resize-handle:active::after {
  opacity: 1;
}

.resize-handle::after {
  content: '';
  position: absolute;
  top: 0;
  left: -4px;
  right: -4px;
  bottom: 0;
  background-color: rgba(59, 130, 246, 0.05);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.sidebar-header {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-title {
  font-size: 16px;
  font-weight: 600;
  color: #e5e7eb;
  position: relative;
  padding-left: 12px;
}

.sidebar-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  background-color: #409eff;
  border-radius: 2px;
}

.tool-list-wrapper {
  flex: 1;
  overflow: hidden;
}

.tool-scrollbar {
  height: 100%;
}

.tool-list {
  padding: 8px;
}

/* 工具项 - 简化样式 */
.tool-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  margin-bottom: 6px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  height: 48px;
}

.tool-item:hover {
  background-color: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.2);
}

.tool-item.active {
  background-color: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.4);
}

.tool-icon {
  margin-right: 10px;
  color: #94a3b8;
}

.tool-item.active .tool-icon {
  color: #409eff;
}

.tool-info {
  flex: 1;
  overflow: hidden;
}

.tool-name {
  font-weight: 500;
  color: #e5e7eb;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tool-item.active .tool-name {
  color: #409eff;
}

/* 右侧内容 */
.execution-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #121826;
  min-width: 0;
}

.execution-detail {
  max-width: 1200px;
  margin: 0 auto;
}

/* 工具标题区域 */
.tool-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.tool-title {
  font-size: 22px;
  font-weight: 600;
  color: #e5e7eb;
  margin: 0;
}

/* 通用部分样式 */
.section {
  margin-bottom: 20px;
}

.section-header {
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #e5e7eb;
  position: relative;
  padding-left: 12px;
}

.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  background-color: #409eff;
  border-radius: 2px;
}

.section-body {
  padding: 0 8px;
}

/* 参数设置部分 - 水平布局，去掉表头，边框更窄 */
.params-table-wrapper {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  overflow: hidden;
  border-width: 1px;
}

.table-container {
  overflow-x: auto;
}

.params-table {
  width: 100%;
  border-collapse: collapse;
  background-color: rgba(30, 41, 59, 0.3);
  min-width: 600px;
}

.params-table thead {
  display: none;
}

.param-cell {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  background-color: rgba(30, 41, 59, 0.2);
  vertical-align: middle;
}

.param-cell:last-child {
  border-right: none;
}

/* 标签单元格和输入单元格设置不同宽度 */
.param-cell.label-cell {
  width: 30%;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  background-color: rgba(30, 41, 59, 0.3);
  padding-left: 16px;
}

.param-cell.input-cell {
  width: 70%;
  padding-right: 16px;
}

.param-label {
  color: #e5e7eb;
  font-size: 14px;
  display: flex;
  flex-direction: column;
}

.param-hint {
  color: #94a3b8;
  font-size: 12px;
  margin-top: 4px;
}

.table-input,
.table-select {
  width: 100%;
}

/* 执行按钮部分 - 增加与参数的距离 */
.action-section {
  margin: 32px 0 24px 0;
  text-align: center;
}

.execute-btn {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.9) 0%, rgba(79, 70, 229, 0.9) 100%);
  border-color: transparent;
  padding: 12px 32px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.execute-btn:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 1) 0%, rgba(79, 70, 229, 1) 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
}

.execute-btn:disabled {
  background: rgba(148, 163, 184, 0.3);
  transform: none;
  box-shadow: none;
  cursor: not-allowed;
}

/* 工具说明部分 - 往下移动一点，边框更窄 */
.remark-section {
  margin-top: 1px;
  margin-bottom: 20px;
}

.remark-content {
  color: #94a3b8;
  line-height: 1.6;
  padding: 10px;
  background-color: rgba(30, 41, 59, 0.3);
  border-radius: 6px;
  border-left: 2px solid rgba(59, 130, 246, 0.6);
  font-size: 14px;
}

/* Python脚本部分 */
.script-section {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  padding: 16px;
  margin-top: 20px;
}

.script-editor-wrapper {
  margin-top: 12px;
}

.custom-coder-wrapper {
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.no-script {
  padding: 60px 20px;
  text-align: center;
}

/* 执行结果部分 */
.result-section {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  padding: 16px;
  margin-top: 24px;
}

.clear-result-btn {
  color: #94a3b8;
}

.clear-result-btn:hover {
  color: #e5e7eb;
}

.result-content {
  background-color: rgba(30, 41, 59, 0.3);
  border-radius: 6px;
  overflow: hidden;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background-color: rgba(30, 41, 59, 0.5);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.result-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.result-status.success {
  color: #67c23a;
}

.result-status.error {
  color: #f56c6c;
}

.result-time {
  color: #94a3b8;
  font-size: 14px;
}

.result-output {
  padding: 20px;
  max-height: 300px;
  overflow-y: auto;
}

.result-output pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.5;
  color: #e5e7eb;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 空状态 */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
  text-align: center;
}

/* 加载遮罩 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(15, 23, 42, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.loading-content {
  text-align: center;
  color: #e5e7eb;
}

.loading-icon {
  font-size: 48px;
  color: #409eff;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 16px;
  color: #94a3b8;
}

/* 深度选择器样式 */
:deep(.el-scrollbar) {
  height: 100%;
}

:deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}

:deep(.el-alert) {
  border-radius: 6px !important;
  border: none !important;
}

:deep(.el-alert--warning) {
  background-color: rgba(245, 158, 11, 0.1) !important;
}

:deep(.el-alert--warning .el-alert__title) {
  color: #f59e0b !important;
}

:deep(.el-alert--warning .el-alert__description) {
  color: #9ca3b8 !important;
}

/* 输入框样式 */
:deep(.table-input .el-input__wrapper) {
  background-color: rgba(15, 23, 42, 0.8) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #e5e7eb !important;
  border-radius: 4px !important;
  box-shadow: none !important;
  transition: all 0.2s ease !important;
}

:deep(.table-input .el-input__wrapper:hover) {
  border-color: rgba(59, 130, 246, 0.4) !important;
}

:deep(.table-input .el-input__wrapper.is-focus) {
  border-color: rgba(59, 130, 246, 0.8) !important;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2) !important;
}

:deep(.table-input .el-input__inner) {
  color: #e5e7eb !important;
  background-color: transparent !important;
}

/* 输入框placeholder颜色 */
:deep(.table-input .el-input__inner::placeholder) {
  color: #9ca3af !important;
}

/* 选择器样式 */
:deep(.table-select .el-select__wrapper) {
  background-color: rgba(15, 23, 42, 0.8) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #e5e7eb !important;
  border-radius: 4px !important;
  box-shadow: none !important;
  transition: all 0.2s ease !important;
}

:deep(.table-select .el-select__wrapper:hover) {
  border-color: rgba(59, 130, 246, 0.4) !important;
}

:deep(.table-select .el-select__wrapper.is-focused) {
  border-color: rgba(59, 130, 246, 0.8) !important;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2) !important;
}

/* 选择框placeholder颜色 */
:deep(.table-select .el-select__placeholder) {
  color: #9ca3af !important;
}

:deep(.table-select .el-input__inner::placeholder) {
  color: #9ca3af !important;
}

/* 空状态样式 */
:deep(.el-empty) {
  --el-empty-fill-color: #94a3b8;
}

:deep(.el-empty__description) {
  color: #94a3b8;
}

/* 按钮样式 */
:deep(.el-button) {
  transition: all 0.3s ease;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .content-wrapper {
    flex-direction: column;
    height: auto;
  }
  
  .directory-sidebar {
    width: 100% !important;
    height: 250px;
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    max-width: none;
  }
  
  .resize-handle {
    display: none;
  }
  
  .execution-content {
    height: calc(100vh - 410px);
  }
}

@media (max-width: 768px) {
  .params-table {
    min-width: 500px;
  }
  
  .param-cell.label-cell {
    width: 40%;
  }
  
  .param-cell.input-cell {
    width: 60%;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .execute-btn {
    width: 100%;
  }
}
</style>

<style>
/* 全局样式 - 确保下拉菜单深色主题 */
.el-select-dropdown {
  background-color: #121826 !important;
  border: 1px solid rgba(59, 130, 246, 0.3) !important;
  color: #e5e7eb !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
  --el-select-dropdown-bg-color: #121826 !important;
}

.el-select-dropdown__item {
  color: #e5e7eb !important;
  background-color: transparent !important;
}

.el-select-dropdown__item:hover {
  background-color: rgba(59, 130, 246, 0.15) !important;
}

.el-select-dropdown__item.selected {
  background-color: rgba(59, 130, 246, 0.2) !important;
  color: #ffffff !important;
}

.el-select-dropdown__item.hover {
  background-color: rgba(59, 130, 246, 0.1) !important;
}

/* 修改下拉框输入框中选中的文本颜色为白色 */
.el-select .el-select__selected-item {
  color: #ffffff !important;
}

.el-select .el-input__wrapper .el-select__selected-item {
  color: #ffffff !important;
}

/* 修改下拉框placeholder颜色 */
.el-select .el-select__placeholder {
  color: #9ca3af !important;
}

/* 修改多选模式下选中的标签文字颜色 */
.el-select .el-tag .el-tag__content {
  color: #e5e7eb !important;
}

/* 覆盖element-plus的变量，确保输入框中的文本颜色为白色 */
:root {
  --el-text-color-regular: #e5e7eb !important;
  --el-input-text-color: #e5e7eb !important;
}

.el-input .el-input__inner,
.el-select .el-input__inner,
.el-select .el-select__selected-item {
  color: #ffffff !important;
}

/* 通知样式 */
.el-notification {
  background-color: #121826 !important;
  border: 1px solid rgba(59, 130, 246, 0.3) !important;
  color: #e5e7eb !important;
}

.el-notification__title {
  color: #e5e7eb !important;
}

.el-notification__content {
  color: #94a3b8 !important;
}

.el-notification--success .el-notification__icon {
  color: #67c23a !important;
}

.el-notification--error .el-notification__icon {
  color: #f56c6c !important;
}

/* Coder组件样式 - 从A代码复制过来 */
:deep(.custom-coder .code-editor) {
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 4px !important;
  overflow: hidden !important;
}

:deep(.custom-coder .CodeMirror) {
  background-color: rgba(15, 23, 42, 0.9) !important;
  color: #e5e7eb !important;
  height: 300px !important;
}

:deep(.custom-coder .CodeMirror-gutters) {
  background-color: rgba(15, 23, 42, 0.95) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
}

:deep(.custom-coder .CodeMirror-linenumber) {
  color: #94a3b8 !important;
  background-color: transparent !important;
}

/* 滚动条全局样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.3);
}

::-webkit-scrollbar-thumb {
  background-color: rgba(59, 130, 246, 0.4);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background-color: rgba(59, 130, 246, 0.6);
}
</style>