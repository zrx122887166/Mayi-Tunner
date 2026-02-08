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
          <!-- 修改这里：添加渐变色文字 -->
          <div class="sidebar-subtitle">
            共 <span class="colorful-text">{{ toolList.length }}</span> 个可用工具
          </div>
        </div>
        <div class="tool-list-wrapper">
          <el-scrollbar class="tool-scrollbar">
            <div class="tool-list">
              <!-- 分组列表 -->
              <div v-for="(group, groupIndex) in toolGroups" :key="groupIndex" class="tool-group">
                <!-- 分组标题 -->
                <div 
                  class="group-header"
                  @click="toggleGroup(groupIndex)"
                >
                  <div class="group-icon-wrapper">
                    <div class="group-icon-bg tw-bg-blue-500/10">
                      <el-icon v-if="group.expanded"><ArrowDown /></el-icon>
                      <el-icon v-else><ArrowRight /></el-icon>
                    </div>
                  </div>
                  <div class="group-info">
                    <div class="group-name">{{ group.name }}</div>
                    <div class="group-count">{{ group.tools.length }} 个工具</div>
                  </div>
                </div>
                
                <!-- 分组下的工具列表 -->
                <div v-if="group.expanded" class="group-tools">
                  <div 
                    v-for="tool in group.tools"
                    :key="tool.id"
                    class="tool-item"
                    :class="{ 'active': activeToolId === tool.id.toString() }"
                    @click="handleToolClick(tool)"
                  >
                    <div class="tool-icon-wrapper">
                      <div class="tool-icon-bg tw-bg-purple-500/10">
                        <el-icon><Document /></el-icon>
                      </div>
                    </div>
                    <div class="tool-info">
                      <div class="tool-name">{{ tool.name }}</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 无分组工具 -->
              <div v-if="ungroupedTools.length > 0" class="tool-group">
                <div 
                  class="group-header"
                  @click="toggleUngrouped"
                >
                  <div class="group-icon-wrapper">
                    <div class="group-icon-bg tw-bg-gray-500/10">
                      <el-icon v-if="showUngrouped"><ArrowDown /></el-icon>
                      <el-icon v-else><ArrowRight /></el-icon>
                    </div>
                  </div>
                  <div class="group-info">
                    <div class="group-name">未分组</div>
                    <div class="group-count">{{ ungroupedTools.length }} 个工具</div>
                  </div>
                </div>
                
                <div v-if="showUngrouped" class="group-tools">
                  <div 
                    v-for="tool in ungroupedTools"
                    :key="tool.id"
                    class="tool-item"
                    :class="{ 'active': activeToolId === tool.id.toString() }"
                    @click="handleToolClick(tool)"
                  >
                    <div class="tool-icon-wrapper">
                      <div class="tool-icon-bg tw-bg-purple-500/10">
                        <el-icon><Document /></el-icon>
                      </div>
                    </div>
                    <div class="tool-info">
                      <div class="tool-name">{{ tool.name }}</div>
                      <div class="tool-description">{{ tool.description || '暂无描述' }}</div>
                    </div>
                  </div>
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
          <div v-if="currentTool.has_params && filteredParams.length > 0" class="params-section">
            <div class="section-header">
              <div class="section-title">参数设置</div>
            </div>
            <div class="section-body">
              <div class="params-table-wrapper">
                <div class="table-container">
                  <table class="params-table">
                    <tbody>
                      <tr v-for="(param, index) in filteredParams" :key="index">
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

          <!-- Python脚本部分 -->
          <div class="script-section">
            <div class="section-header">
              <div class="section-title">Python 脚本</div>
            </div>
            <div class="section-body">
              <div class="script-editor-wrapper">
                <div v-if="currentTool.pythonScript" class="custom-coder-wrapper">
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
import { ref, computed, onMounted } from 'vue';
import request from '@/utils/request';
import Coder from '@/components/Coder';
import { 
  ElMessage, 
  ElNotification 
} from 'element-plus';
import { 
  Document, 
  VideoPlay,
  Loading,
  Check,
  Close,
  ArrowRight,
  ArrowDown
} from '@element-plus/icons-vue';

// 状态定义
const toolList = ref([]);
const currentTool = ref(null);
const inputData = ref({});
const loading = ref(false);
const showWarning = ref(false);
const activeToolId = ref('');
const executionResult = ref(null);
const sidebarWidth = ref(280);
const sidebarRef = ref(null);
let isResizing = false;

// 分组相关状态
const toolGroups = ref([]);
const ungroupedTools = ref([]);
const showUngrouped = ref(false);

// 核心修改：计算属性过滤is_show为true的参数
const filteredParams = computed(() => {
  if (!currentTool.value || !currentTool.value.params) return [];
  return currentTool.value.params.filter(param => param.is_show !== false);
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

// 分组工具数据
const groupTools = () => {
  const groupsMap = {};
  
  toolList.value.forEach(tool => {
    const groupName = tool.group_name || '';
    if (groupName) {
      if (!groupsMap[groupName]) {
        groupsMap[groupName] = [];
      }
      groupsMap[groupName].push(tool);
    } else {
      ungroupedTools.value.push(tool);
    }
  });
  
  toolGroups.value = Object.keys(groupsMap).map(groupName => ({
    name: groupName,
    tools: groupsMap[groupName],
    expanded: false
  }));
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
    
    ungroupedTools.value = [];
    groupTools();
    
  } catch (error) {
    console.error('获取工具列表失败:', error);
    ElMessage.error('获取工具列表失败：' + (error.message || '网络错误'));
    toolList.value = [];
  } finally {
    loading.value = false;
  }
};

// 切换分组展开/折叠状态
const toggleGroup = (index) => {
  toolGroups.value[index].expanded = !toolGroups.value[index].expanded;
};

// 切换未分组展开/折叠状态
const toggleUngrouped = () => {
  showUngrouped.value = !showUngrouped.value;
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
      
      inputData.value = {};
      if (toolDetail.params && toolDetail.params.length) {
        toolDetail.params.forEach(param => {
          if (param.is_show !== false) {
            inputData.value[param.name] = param.default || '';
          }
        });
      }
      
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
    const newWidth = Math.max(240, Math.min(400, startWidth + diff));
    
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
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
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
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
  position: relative;
}

/* 左侧目录 */
.directory-sidebar {
  width: 280px;
  flex-shrink: 0;
  background-color: #1D2433;
  display: flex;
  flex-direction: column;
  position: relative;
  user-select: none;
  resize: horizontal;
  min-width: 240px;
  max-width: 400px;
  border-right: 1px solid rgba(255, 255, 255, 0.05);
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

/* 侧边栏头部 */
.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-title {
  font-size: 18px;
  font-weight: 600;
  color: #F3F4F6;
  margin-bottom: 4px;
}

.sidebar-subtitle {
  font-size: 14px;
  color: #9CA3AF;
  font-weight: 400;
}

/* 渐变色文字样式 */
.colorful-text {
  background: linear-gradient(135deg, #60A5FA 0%, #8B5CF6 50%, #EC4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 600;
  position: relative;
  display: inline-block;
}

/* 添加发光效果 */
.colorful-text::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #60A5FA 0%, #8B5CF6 50%, #EC4899 100%);
  filter: blur(8px);
  opacity: 0.3;
  z-index: -1;
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
  padding: 12px;
}

/* 分组样式 */
.tool-group {
  margin-bottom: 8px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.05);
  background-color: rgba(30, 41, 59, 0.3);
}

/* 分组头部 */
.group-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  background-color: rgba(15, 23, 42, 0.5);
  border-bottom: 1px solid transparent;
}

.group-header:hover {
  background-color: rgba(59, 130, 246, 0.1);
}

.group-icon-wrapper {
  margin-right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.group-icon-bg {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.group-icon-bg .el-icon {
  font-size: 16px;
  color: #60A5FA;
}

.group-info {
  flex: 1;
  overflow: hidden;
}

.group-name {
  font-weight: 500;
  color: #E5E7EB;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.group-count {
  font-size: 12px;
  color: #94A3B8;
  font-weight: 400;
}

/* 分组下的工具列表 */
.group-tools {
  background-color: rgba(15, 23, 42, 0.2);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding: 4px 8px;
}

/* 工具项 */
.tool-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  margin: 2px 0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  background-color: transparent;
}

.tool-item:hover {
  background-color: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.2);
}

.tool-item.active {
  background-color: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.3);
}

.tool-icon-wrapper {
  margin-right: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tool-icon-bg {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.tool-icon-bg .el-icon {
  font-size: 18px;
  color: #A78BFA;
}

.tool-item.active .tool-icon-bg {
  background-color: rgba(139, 92, 246, 0.2);
}

.tool-item.active .tool-icon-bg .el-icon {
  color: #8B5CF6;
}

.tool-info {
  flex: 1;
  overflow: hidden;
  min-width: 0;
}

.tool-name {
  font-weight: 500;
  color: #E5E7EB;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.tool-description {
  font-size: 12px;
  color: #94A3B8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 400;
}

.tool-item.active .tool-name {
  color: #8B5CF6;
  font-weight: 600;
}

/* 右侧内容 */
.execution-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
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
  font-size: 24px;
  font-weight: 600;
  color: #F3F4F6;
  margin: 0;
  line-height: 1.3;
}

/* 通用部分样式 */
.section {
  margin-bottom: 24px;
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
  font-size: 18px;
  font-weight: 600;
  color: #F3F4F6;
  position: relative;
  padding-left: 16px;
  line-height: 1.4;
}

.section-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 20px;
  background: linear-gradient(135deg, #60A5FA 0%, #8B5CF6 100%);
  border-radius: 2px;
}

.section-body {
  padding: 0 8px;
}

/* 参数设置部分 */
.params-table-wrapper {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  overflow: hidden;
  border-width: 1px;
  background-color: rgba(30, 41, 59, 0.3);
}

.table-container {
  overflow-x: auto;
}

.params-table {
  width: 100%;
  border-collapse: collapse;
  background-color: transparent;
  min-width: 600px;
}

.params-table thead {
  display: none;
}

.param-cell {
  padding: 8px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  background-color: transparent;
  vertical-align: middle;
  height: 36px;
}

.param-cell:last-child {
  border-right: none;
}

.param-cell.label-cell {
  width: 35%;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  background-color: rgba(30, 41, 59, 0.2);
  padding-left: 16px;
}

.param-cell.input-cell {
  width: 65%;
  padding-right: 16px;
}

.param-label {
  color: #F3F4F6;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  flex-direction: column;
  line-height: 1.4;
}

.param-hint {
  color: #94A3B8;
  font-size: 12px;
  margin-top: 4px;
  font-weight: 400;
}

.table-input,
.table-select {
  width: 100%;
}

/* 执行按钮部分 */
.action-section {
  margin: 28px 0 24px 0;
  text-align: center;
}

.execute-btn {
  background: linear-gradient(135deg, rgba(96, 165, 250, 0.9) 0%, rgba(139, 92, 246, 0.9) 100%);
  border-color: transparent;
  padding: 14px 40px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 10px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(96, 165, 250, 0.2);
}

.execute-btn:hover {
  background: linear-gradient(135deg, rgba(96, 165, 250, 1) 0%, rgba(139, 92, 246, 1) 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(96, 165, 250, 0.3);
}

.execute-btn:disabled {
  background: rgba(148, 163, 184, 0.3);
  transform: none;
  box-shadow: none;
  cursor: not-allowed;
}

/* 工具说明部分 */
.remark-section {
  margin-top: 20px;
  margin-bottom: 20px;
}

.remark-content {
  color: #D1D5DB;
  line-height: 1.6;
  padding: 12px 16px;
  background-color: rgba(30, 41, 59, 0.4);
  border-radius: 8px;
  border-left: 3px solid rgba(139, 92, 246, 0.6);
  font-size: 14px;
  font-weight: 400;
  white-space: pre-wrap;
  min-height: 10px;
}

/* Python脚本部分 */
.script-section {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 20px;
  margin-top: 24px;
  background-color: rgba(30, 41, 59, 0.3);
}

.script-editor-wrapper {
  margin-top: 16px;
}

.custom-coder-wrapper {
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.no-script {
  padding: 60px 20px;
  text-align: center;
}

/* 执行结果部分 */
.result-section {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 20px;
  margin-top: 28px;
  background-color: rgba(30, 41, 59, 0.3);
}

.clear-result-btn {
  color: #94A3B8;
  font-weight: 500;
  transition: color 0.2s ease;
}

.clear-result-btn:hover {
  color: #F3F4F6;
}

.result-content {
  background-color: rgba(15, 23, 42, 0.4);
  border-radius: 8px;
  overflow: hidden;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background-color: rgba(30, 41, 59, 0.6);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.result-status {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 16px;
}

.result-status.success {
  color: #34D399;
}

.result-status.error {
  color: #F87171;
}

.result-time {
  color: #94A3B8;
  font-size: 14px;
  font-weight: 400;
}

.result-output {
  padding: 20px;
  max-height: 400px;
  overflow-y: auto;
}

.result-output pre {
  margin: 0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #E5E7EB;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-weight: 400;
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
  background-color: rgba(15, 23, 42, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(4px);
}

.loading-content {
  text-align: center;
  color: #F3F4F6;
}

.loading-icon {
  font-size: 56px;
  color: #60A5FA;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 18px;
  color: #D1D5DB;
  font-weight: 500;
}

/* 深度选择器样式 */
:deep(.el-scrollbar) {
  height: 100%;
}

:deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
}

:deep(.el-alert) {
  border-radius: 8px !important;
  border: none !important;
}

:deep(.el-alert--warning) {
  background-color: rgba(245, 158, 11, 0.1) !important;
}

:deep(.el-alert--warning .el-alert__title) {
  color: #F59E0B !important;
  font-weight: 600;
}

:deep(.el-alert--warning .el-alert__description) {
  color: #9CA3AF !important;
  font-weight: 400;
}

/* 输入框样式 */
:deep(.table-input .el-input__wrapper) {
  background-color: rgba(17, 24, 39, 0.9) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #F3F4F6 !important;
  border-radius: 6px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
  transition: all 0.2s ease !important;
  padding: 6px 10px !important;
  height: 24px !important;
}

:deep(.table-input .el-input__wrapper:hover) {
  border-color: rgba(96, 165, 250, 0.5) !important;
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.1) !important;
}

:deep(.table-input .el-input__wrapper.is-focus) {
  border-color: rgba(96, 165, 250, 0.8) !important;
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2) !important;
}

:deep(.table-input .el-input__inner) {
  color: #F3F4F6 !important;
  background-color: transparent !important;
  font-size: 14px !important;
  font-weight: 400 !important;
  height: 24px !important;
  line-height: 24px !important;
}

/* 输入框placeholder颜色 */
:deep(.table-input .el-input__inner::placeholder) {
  color: #9CA3AF !important;
  font-weight: 400 !important;
}

/* 选择器样式 */
:deep(.table-select .el-select__wrapper) {
  background-color: rgba(17, 24, 39, 0.9) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #F3F4F6 !important;
  border-radius: 6px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
  transition: all 0.2s ease !important;
  padding: 6px 10px !important;
  height: 36px !important;
}

:deep(.table-select .el-select__wrapper:hover) {
  border-color: rgba(96, 165, 250, 0.5) !important;
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.1) !important;
}

:deep(.table-select .el-select__wrapper.is-focused) {
  border-color: rgba(96, 165, 250, 0.8) !important;
  box-shadow: 0 0 0 3px rgba(96, 165, 250, 0.2) !important;
}

/* 选择框placeholder颜色 */
:deep(.table-select .el-select__placeholder) {
  color: #9CA3AF !important;
  font-weight: 400 !important;
}

:deep(.table-select .el-input__inner::placeholder) {
  color: #9CA3AF !important;
  font-weight: 400 !important;
}

/* 空状态样式 */
:deep(.el-empty) {
  --el-empty-fill-color: #9CA3AF;
}

:deep(.el-empty__description) {
  color: #9CA3AF;
  font-weight: 400;
  font-size: 15px;
}

/* 按钮样式 */
:deep(.el-button) {
  transition: all 0.3s ease;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .content-wrapper {
    flex-direction: column;
    height: auto;
  }
  
  .directory-sidebar {
    width: 100% !important;
    height: 300px;
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    max-width: none;
  }
  
  .resize-handle {
    display: none;
  }
  
  .execution-content {
    height: calc(100vh - 460px);
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
  background-color: #1D2433 !important;
  border: 1px solid rgba(96, 165, 250, 0.3) !important;
  color: #F3F4F6 !important;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4) !important;
  border-radius: 8px !important;
  --el-select-dropdown-bg-color: #1D2433 !important;
}

.el-select-dropdown__item {
  color: #F3F4F6 !important;
  background-color: transparent !important;
  font-size: 14px !important;
  font-weight: 400 !important;
  padding: 8px 16px !important;
  transition: all 0.2s ease !important;
  height: 36px !important;
  line-height: 20px !important;
}

.el-select-dropdown__item:hover {
  background-color: rgba(96, 165, 250, 0.15) !important;
}

.el-select-dropdown__item.selected {
  background-color: rgba(96, 165, 250, 0.2) !important;
  color: #FFFFFF !important;
  font-weight: 500 !important;
}

.el-select-dropdown__item.hover {
  background-color: rgba(96, 165, 250, 0.1) !important;
}

/* 修改下拉框输入框中选中的文本颜色为白色 */
.el-select .el-select__selected-item {
  color: #FFFFFF !important;
  font-weight: 500 !important;
}

.el-select .el-input__wrapper .el-select__selected-item {
  color: #FFFFFF !important;
  font-weight: 500 !important;
}

/* 修改下拉框placeholder颜色 */
.el-select .el-select__placeholder {
  color: #afa29c !important;
  font-weight: 400 !important;
}

/* 修改多选模式下选中的标签文字颜色 */
.el-select .el-tag .el-tag__content {
  color: #E5E7EB !important;
  font-weight: 500 !important;
}

/* 覆盖element-plus的变量，确保输入框中的文本颜色为白色 */
:root {
  --el-text-color-regular: #F3F4F6 !important;
  --el-input-text-color: #F3F4F6 !important;
  --el-font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif !important;
}

.el-input .el-input__inner,
.el-select .el-input__inner,
.el-select .el-select__selected-item {
  color: #FFFFFF !important;
  font-weight: 500 !important;
}

/* 通知样式 */
.el-notification {
  background-color: #1D2433 !important;
  border: 1px solid rgba(96, 165, 250, 0.3) !important;
  color: #F3F4F6 !important;
  border-radius: 8px !important;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4) !important;
}

.el-notification__title {
  color: #F3F4F6 !important;
  font-weight: 600 !important;
}

.el-notification__content {
  color: #9CA3AF !important;
  font-weight: 400 !important;
}

.el-notification--success .el-notification__icon {
  color: #34D399 !important;
}

.el-notification--error .el-notification__icon {
  color: #F87171 !important;
}

/* Coder组件样式 */
:deep(.custom-coder .code-editor) {
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 6px !important;
  overflow: hidden !important;
}

:deep(.custom-coder .CodeMirror) {
  background-color: rgba(17, 24, 39, 0.9) !important;
  color: #F3F4F6 !important;
  height: 320px !important;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
}

:deep(.custom-coder .CodeMirror-gutters) {
  background-color: rgba(30, 41, 59, 0.95) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}

:deep(.custom-coder .CodeMirror-linenumber) {
  color: #94A3B8 !important;
  background-color: transparent !important;
  font-weight: 400 !important;
}

/* 滚动条全局样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.3);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background-color: rgba(96, 165, 250, 0.4);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background-color: rgba(96, 165, 250, 0.6);
}
</style>