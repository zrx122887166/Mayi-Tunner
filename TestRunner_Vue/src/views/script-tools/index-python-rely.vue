<template>
  <div class="container tw-h-full tw-flex tw-flex-col tw-gap-4 tw-p-4">
    <!-- 搜索框区域 -->
    <div class="search-container tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-px-6 tw-py-4 tw-flex tw-items-center tw-gap-4">
      <div class="search-input-wrapper">
        <el-input
          v-model="searchName"
          placeholder="根据工具名称查询"
          class="search-input"
          @input="handleInput"
          clearable
          :maxlength="50"
        />
      </div>
      <el-button type="primary" @click="openAddDialog" class="add-btn">新建依赖工具</el-button>
    </div>

    <!-- 主弹窗 -->
    <el-dialog
      v-model="dialogShow"
      :title="editToolId ? '编辑依赖工具' : '新建依赖工具'"
      width="80%"
      :before-close="beforeClose"
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
      class="custom-dialog"
    >
      <!-- 使用 el-form 包裹表单内容 -->
      <el-form
        ref="formRef"
        :model="projectForm"
        :rules="formRules"
        label-width="0"
        @submit.prevent="submit"
      >
        <div class="dialog-content">
          <!-- 基础信息部分 -->
          <div class="section basic-info">
            <div class="section-header">
              <div class="section-title">基础信息</div>
            </div>
            <div class="section-body">
              <div class="form-row">
                <div class="form-label">工具名称<span class="required-mark">*</span></div>
                <div class="form-field">
                  <el-form-item prop="name" class="tw-w-full">
                    <el-input 
                      v-model="projectForm.name" 
                      placeholder="请输入依赖工具名称" 
                      :maxlength="100"
                      class="custom-input"
                    />
                  </el-form-item>
                </div>
              </div>
              
              <div class="form-row">
                <div class="form-label">工具备注</div>
                <div class="form-field">
                  <el-form-item prop="remark" class="tw-w-full">
                    <el-input
                      type="textarea"
                      v-model="projectForm.remark"
                      placeholder="请输入依赖工具备注/使用说明"
                      rows="3"
                      :maxlength="500"
                      class="custom-textarea"
                    />
                  </el-form-item>
                </div>
              </div>
            </div>
          </div>

          <!-- Python脚本部分 -->
          <div class="section script-section">
            <div class="section-header">
              <div class="section-title">Python 脚本<span class="required-mark">*</span></div>
            </div>
            <div class="section-body">
              <div class="script-editor-wrapper">
                <el-form-item prop="pythonScript" class="tw-w-full">
                  <Coder
                    :lang="'python'"
                    :content="projectForm.pythonScript"
                    @updateScript="updateScript"
                    :height="'300px'"
                    class="custom-coder"
                  />
                </el-form-item>
              </div>
            </div>
          </div>
        </div>
      </el-form>
      
      <!-- 弹窗底部按钮 -->
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="close" class="cancel-btn">取消</el-button>
          <el-button type="primary" @click="submit" :loading="submitLoading" class="confirm-btn">确认</el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 工具列表 -->
    <div class="table-container tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-overflow-hidden tw-flex-grow">
      <el-table 
        :data="toolList" 
        style="width: 100%" 
        table-layout="auto" 
        class="tool-table"
        v-loading="loading"
        element-loading-text="加载中..."
        empty-text="暂无依赖工具数据"
      >
        <el-table-column label="工具名称" prop="name" min-width="180"></el-table-column>
        <el-table-column label="工具备注" prop="remark" min-width="200"></el-table-column>
        <el-table-column label="Python脚本" prop="pythonScript" min-width="300">
          <template #default="scope">
            <el-tooltip
              effect="dark"
              :content="scope.row.pythonScript"
              placement="top"
              v-if="scope.row.pythonScript && scope.row.pythonScript.length > 50"
            >
              <span class="script-preview">{{ scope.row.pythonScript.substring(0, 50) }}...</span>
            </el-tooltip>
            <span v-else>{{ scope.row.pythonScript || '无脚本' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="create_time" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button type="primary" @click="editTool(scope.row)" class="table-operation-btn edit-btn">编辑</el-button>
            <el-button type="danger" @click="deleteTool(scope.row)" class="table-operation-btn delete-btn">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 分页区域 -->
    <div class="tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-px-6 tw-py-4">
      <a-pagination
        v-model:current="pagination.current"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        show-total
        show-jumper
        show-page-size
        class="tw-flex tw-justify-end"
        @change="handlePageChange"
        @page-size-change="handlePageSizeChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, nextTick } from 'vue';
import request from '@/utils/request';
import Coder from '@/components/Coder';
import { ElMessage, ElMessageBox } from 'element-plus';
import { formatDateTime } from '@/utils/format';

// 分页配置
const pagination = ref({
  total: 0,
  current: 1,
  page_size: 10,
  showTotal: true,
  showJumper: true,
  showPageSize: true,
});

// 状态定义
const dialogShow = ref(false);
const searchName = ref('');
const editToolId = ref(null);
const loading = ref(false);
const submitLoading = ref(false);
const debounceTimer = ref(null);

// 表单引用
const formRef = ref(null);

// 表单数据
const projectForm = ref({
  name: '',
  remark: '',
  pythonScript: ''
});

// 表单验证规则
const formRules = reactive({
  name: [
    { required: true, message: '请输入工具名称', trigger: 'blur' },
    { max: 100, message: '工具名称不能超过100个字符', trigger: 'blur' }
  ],
  pythonScript: [
    { required: true, message: '请输入Python脚本', trigger: 'blur' }
  ],
  remark: [
    { max: 500, message: '工具备注不能超过500个字符', trigger: 'blur' }
  ]
});

const toolList = ref([]);

// 获取依赖工具列表
const getToolList = async () => {
  try {
    loading.value = true;
    const params = {
      page: pagination.value.current,
      size: pagination.value.page_size,
      name: searchName.value || ''
    };
    
    const response = await request.get('/tools/', { params });
    const responseData = response.data || response;
    
    if (responseData.results) {
      toolList.value = responseData.results;
      pagination.value.total = responseData.count || 0;
    } else if (Array.isArray(responseData)) {
      toolList.value = responseData;
      pagination.value.total = responseData.length;
    } else {
      toolList.value = [];
      pagination.value.total = 0;
    }
  } catch (error) {
    console.error('获取依赖工具列表失败:', error);
    ElMessage.error('获取依赖工具列表失败：' + (error.message || '网络错误'));
    toolList.value = [];
    pagination.value.total = 0;
  } finally {
    loading.value = false;
  }
};

// 打开新增对话框
const openAddDialog = () => {
  resetForm();
  editToolId.value = null;
  dialogShow.value = true;
  
  // 清除之前的验证状态
  nextTick(() => {
    if (formRef.value) {
      formRef.value.clearValidate();
    }
  });
};

// 编辑工具
const editTool = (item) => {
  dialogShow.value = true;
  editToolId.value = item.id;
  
  // 赋值表单数据
  projectForm.value = {
    name: item.name || '',
    remark: item.remark || '',
    pythonScript: item.pythonScript || ''
  };
  
  // 清除之前的验证状态
  nextTick(() => {
    if (formRef.value) {
      formRef.value.clearValidate();
    }
  });
};

// 更新脚本内容
const updateScript = (content) => {
  projectForm.value.pythonScript = content;
  // 触发验证
  if (formRef.value) {
    formRef.value.validateField('pythonScript');
  }
};

// 提交表单
const submit = async () => {
  if (!formRef.value) return;
  
  try {
    // 先验证表单
    const valid = await formRef.value.validate();
    if (!valid) {
      return;
    }
  } catch (error) {
    console.error('表单验证失败:', error);
    ElMessage.warning('请完善表单信息');
    return;
  }

  try {
    submitLoading.value = true;
    
    // 构造请求数据
    const requestData = {
      name: projectForm.value.name,
      remark: projectForm.value.remark,
      pythonScript: projectForm.value.pythonScript
    };

    let response;
    if (editToolId.value) {
      // 编辑操作
      response = await request.put(`/tools/${editToolId.value}/`, requestData);
      ElMessage.success('更新成功');
    } else {
      // 新增操作
      response = await request.post('/tools/', requestData);
      ElMessage.success('保存成功');
    }
    
    dialogShow.value = false;
    await getToolList();
    resetForm();
    
  } catch (error) {
    console.error('操作失败:', error);
    let errorMessage = '操作失败';
    if (error.response?.data?.error) {
      errorMessage = error.response.data.error;
    } else if (error.response?.data?.details) {
      errorMessage = JSON.stringify(error.response.data.details);
    } else {
      errorMessage = error.message || '网络错误';
    }
    ElMessage.error(errorMessage);
  } finally {
    submitLoading.value = false;
  }
};

// 删除工具
const deleteTool = async (item) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除工具 "${item.name}" 吗？此操作不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
        // 为取消按钮添加自定义类名
        cancelButtonClass: 'el-message-box__cancel-btn custom-cancel-btn'
      }
    );
    
    await request.delete(`/tools/${item.id}/`);
    ElMessage.success('删除成功');
    
    // 更新列表
    const index = toolList.value.findIndex(tool => tool.id === item.id);
    if (index !== -1) {
      toolList.value.splice(index, 1);
      pagination.value.total -= 1;
      
      // 处理分页
      if (toolList.value.length === 0 && pagination.value.current > 1) {
        pagination.value.current -= 1;
        getToolList();
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error);
      ElMessage.error('删除失败：' + (error.message || '网络错误'));
    }
  }
};

// 重置表单
const resetForm = () => {
  projectForm.value = {
    name: '',
    remark: '',
    pythonScript: ''
  };
  
  if (formRef.value) {
    formRef.value.resetFields();
  }
};

// 关闭弹窗
const close = () => {
  dialogShow.value = false;
};

// 弹窗关闭前回调
const beforeClose = (done) => {
  done();
};

// 弹窗关闭后处理
const handleDialogClosed = () => {
  resetForm();
};

// 搜索相关
const handleInput = (val) => {
  if (debounceTimer.value) {
    clearTimeout(debounceTimer.value);
  }
  debounceTimer.value = setTimeout(() => {
    searchTools();
  }, 500);
};

const searchTools = () => {
  pagination.value.current = 1;
  getToolList();
};

// 分页相关
const handlePageChange = (current) => {
  pagination.value.current = current;
  getToolList();
};

const handlePageSizeChange = (size) => {
  pagination.value.page_size = size;
  pagination.value.current = 1;
  getToolList();
};

// 页面挂载时获取列表
onMounted(() => {
  getToolList();
});
</script>

<style scoped>
.container {
  height: 100%;
  box-sizing: border-box;
}

/* 搜索框区域 */
.search-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input-wrapper {
  width: 280px;
}

.search-input {
  width: 100%;
}

.add-btn {
  flex-shrink: 0;
}

/* 弹窗内容样式 - 统一背景色 */
.dialog-content {
  background-color: #121826;
  border-radius: 8px;
  padding: 20px;
}

.section {
  margin-bottom: 24px;
}

.section:last-child {
  margin-bottom: 0;
}

.section-header {
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
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

/* 表单行样式 */
.form-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 20px;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-label {
  width: 120px;
  flex-shrink: 0;
  font-size: 14px;
  color: #9ca3af;
  padding-top: 8px;
}

/* 必填标识样式 */
.required-mark {
  color: #f56c6c;
  margin-left: 4px;
  font-size: 14px;
}

.form-field {
  flex: 1;
}

/* 输入框样式 */
.custom-input,
.custom-textarea {
  width: 100%;
}

/* 脚本编辑器样式 */
.script-section {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  padding: 16px;
}

.script-editor-wrapper {
  margin-top: 12px;
}

/* 弹窗底部按钮 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.cancel-btn {
  background-color: rgba(55, 65, 81, 0.6);
  border-color: rgba(75, 85, 99, 0.6);
  color: #d1d5db;
  min-width: 80px;
  transition: all 0.2s ease;
}

.cancel-btn:hover {
  background-color: rgba(75, 85, 99, 0.8);
  border-color: rgba(107, 114, 128, 0.8);
  color: #fff;
}

.confirm-btn {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.9) 0%, rgba(79, 70, 229, 0.9) 100%);
  border-color: transparent;
  min-width: 80px;
  transition: all 0.2s ease;
}

.confirm-btn:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 1) 0%, rgba(79, 70, 229, 1) 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* 工具列表样式 */
.table-container {
  width: 100%;
  overflow: hidden;
}

.tool-table {
  width: 100%;
  margin: 0;
}

.table-operation-btn {
  margin-right: 8px;
}

/* 脚本预览样式 */
.script-preview {
  color: #60a5fa;
  cursor: pointer;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

/* 分页样式 */
.custom-pagination {
  justify-content: flex-end;
}

/* 深度选择器样式 */
:deep(.el-dialog) {
  background-color: #121826;
  border: none;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);
}

:deep(.el-dialog__header) {
  padding: 20px 20px 10px;
  margin: 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

:deep(.el-dialog__title) {
  color: #f3f4f6;
  font-weight: 600;
  font-size: 18px;
}

:deep(.el-dialog__headerbtn) {
  top: 20px;
  right: 20px;
}

:deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #9ca3af;
  font-size: 18px;
}

:deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: #f3f4f6;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

/* 搜索框样式调整 */
:deep(.search-input .el-input__wrapper) {
  background-color: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  box-shadow: none;
  transition: all 0.2s ease;
}

:deep(.search-input .el-input__wrapper:hover) {
  border-color: rgba(59, 130, 246, 0.4);
  background-color: rgba(30, 41, 59, 0.8);
}

:deep(.search-input .el-input__wrapper.is-focus) {
  border-color: rgba(59, 130, 246, 0.8);
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2);
  background-color: rgba(30, 41, 59, 0.9);
}

:deep(.search-input .el-input__inner) {
  color: #e5e7eb;
  background-color: transparent !important;
}

:deep(.search-input .el-input__clear) {
  color: #9ca3af;
}

:deep(.search-input .el-input__clear:hover) {
  color: #e5e7eb;
}

/* 工具名称输入框 - 移除背景色 */
:deep(.custom-input .el-input__wrapper) {
  background-color: transparent !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #e5e7eb !important;
  border-radius: 4px !important;
  box-shadow: none !important;
  transition: all 0.2s ease !important;
}

:deep(.custom-input .el-input__wrapper:hover) {
  border-color: rgba(59, 130, 246, 0.4) !important;
  background-color: transparent !important;
}

:deep(.custom-input .el-input__wrapper.is-focus) {
  border-color: rgba(59, 130, 246, 0.8) !important;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2) !important;
  background-color: transparent !important;
}

:deep(.custom-input .el-input__inner) {
  color: #e5e7eb !important;
  background-color: transparent !important;
}

/* 工具备注输入框样式 */
:deep(.custom-textarea .el-textarea__wrapper) {
  background-color: rgba(30, 41, 59, 0.6) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #e5e7eb !important;
  border-radius: 4px !important;
  box-shadow: none !important;
  transition: all 0.2s ease !important;
}

:deep(.custom-textarea .el-textarea__wrapper:hover) {
  border-color: rgba(59, 130, 246, 0.4) !important;
  background-color: rgba(30, 41, 59, 0.8) !important;
}

:deep(.custom-textarea .el-textarea__wrapper.is-focus) {
  border-color: rgba(59, 130, 246, 0.8) !important;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2) !important;
  background-color: rgba(30, 41, 59, 0.9) !important;
}

:deep(.custom-textarea .el-textarea__inner) {
  color: #e5e7eb !important;
  background-color: transparent !important;
}

/* 去掉工具备注输入框右下角的字数统计标识 */
:deep(.custom-textarea .el-input__count),
:deep(.custom-textarea .el-textarea__count) {
  display: none !important;
}

/* 整体页面优化 */
:deep(.el-table) {
  --el-table-bg-color: rgba(30, 41, 59, 0.3);
  --el-table-header-bg-color: rgba(30, 41, 59, 0.8) !important;
  --el-table-text-color: #e5e7eb;
  --el-table-border-color: rgba(255, 255, 255, 0.08);
  --el-table-row-hover-bg-color: rgba(59, 130, 246, 0.05);
}

:deep(.el-table th) {
  background-color: rgba(30, 41, 59, 0.8) !important;
  color: #94a3b8 !important;
  font-weight: 500;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
}

:deep(.el-table tr) {
  background-color: transparent !important;
}

:deep(.el-table td) {
  background-color: transparent !important;
  color: #d1d5db !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
}

:deep(.el-table tr:hover td) {
  background-color: rgba(59, 130, 246, 0.05) !important;
}

/* 表单验证样式 */
:deep(.el-form-item__error) {
  color: #f56c6c;
  font-size: 12px;
  line-height: 1;
  padding-top: 4px;
  position: absolute;
  top: 100%;
  left: 0;
}

/* 必填字段验证提示样式 */
:deep(.el-form-item.is-error .custom-input .el-input__wrapper),
:deep(.el-form-item.is-error .custom-textarea .el-textarea__wrapper) {
  border-color: #f56c6c !important;
}

:deep(.el-form-item.is-error .custom-input .el-input__wrapper.is-focus),
:deep(.el-form-item.is-error .custom-textarea .el-textarea__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgba(245, 108, 108, 0.2) !important;
}

/* 工具提示样式 */
:deep(.el-tooltip__popper) {
  background-color: #121826 !important;
  border: 1px solid rgba(59, 130, 246, 0.3) !important;
  color: #e5e7eb !important;
  max-width: 600px !important;
  word-break: break-all !important;
}

:deep(.el-tooltip__popper .popper__arrow) {
  border-color: #121826 transparent transparent transparent !important;
}

:deep(.el-tooltip__popper .popper__arrow::before) {
  border-color: #121826 transparent transparent transparent !important;
}

/* 删除确认弹窗取消按钮样式 */
:deep(.el-message-box__cancel-btn),
:deep(.custom-cancel-btn) {
  background-color: rgba(55, 65, 81, 0.6) !important;
  border-color: rgba(75, 85, 99, 0.6) !important;
  color: #d1d5db !important;
  min-width: 80px !important;
  transition: all 0.2s ease !important;
}

:deep(.el-message-box__cancel-btn:hover),
:deep(.custom-cancel-btn:hover) {
  background-color: rgba(75, 85, 99, 0.8) !important;
  border-color: rgba(107, 114, 128, 0.8) !important;
  color: #fff !important;
}
</style>

<style>
/* 全局样式 - 与创建脚本工具保持一致 */
.el-loading-mask {
  background-color: rgba(15, 23, 42, 0.7) !important;
}

.el-loading-spinner .path {
  stroke: #60a5fa !important;
}

.el-loading-text {
  color: #94a3b8 !important;
}

/* 弹窗背景样式 */
.el-overlay {
  background-color: rgba(0, 0, 0, 0.6) !important;
  backdrop-filter: blur(2px) !important;
}

/* 消息提示框样式 */
.el-message {
  --el-message-bg-color: rgba(30, 41, 59, 0.9) !important;
  --el-message-text-color: #e5e7eb !important;
  border-color: rgba(59, 130, 246, 0.3) !important;
  backdrop-filter: blur(10px) !important;
}

.el-message--success {
  --el-message-bg-color: rgba(22, 163, 74, 0.9) !important;
  border-color: rgba(34, 197, 94, 0.3) !important;
}

.el-message--error {
  --el-message-bg-color: rgba(220, 38, 38, 0.9) !important;
  border-color: rgba(248, 113, 113, 0.3) !important;
}

.el-message--warning {
  --el-message-bg-color: rgba(234, 179, 8, 0.9) !important;
  border-color: rgba(250, 204, 21, 0.3) !important;
}

/* 确认对话框样式 */
.el-message-box {
  background-color: #121826 !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 8px !important;
}

.el-message-box__title {
  color: #f3f4f6 !important;
}

.el-message-box__content {
  color: #d1d5db !important;
}

.el-message-box__headerbtn .el-message-box__close {
  color: #9ca3af !important;
}

.el-message-box__headerbtn:hover .el-message-box__close {
  color: #f3f4f6 !important;
}

/* 全局样式 - 确保删除确认弹窗取消按钮样式统一 */
.el-message-box__cancel-btn {
  background-color: rgba(55, 65, 81, 0.6) !important;
  border-color: rgba(75, 85, 99, 0.6) !important;
  color: #d1d5db !important;
  min-width: 80px !important;
  transition: all 0.2s ease !important;
}

.el-message-box__cancel-btn:hover {
  background-color: rgba(75, 85, 99, 0.8) !important;
  border-color: rgba(107, 114, 128, 0.8) !important;
  color: #fff !important;
}

/* Coder组件样式 - 从A代码复制过来 */
.custom-coder .code-editor {
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 4px !important;
  overflow: hidden !important;
}

.custom-coder .CodeMirror {
  background-color: rgba(15, 23, 42, 0.9) !important;
  color: #e5e7eb !important;
  height: 300px !important;
}

.custom-coder .CodeMirror-gutters {
  background-color: rgba(15, 23, 42, 0.95) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
}

.custom-coder .CodeMirror-linenumber {
  color: #94a3b8 !important;
  background-color: transparent !important;
}

/* 分页组件样式优化 - 与创建脚本工具相同 */
.a-pagination .ant-pagination-item {
  background-color: rgba(30, 41, 59, 0.6) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
}

.a-pagination .ant-pagination-item a {
  color: #d1d5db !important;
}

.a-pagination .ant-pagination-item:hover {
  border-color: rgba(59, 130, 246, 0.4) !important;
  background-color: rgba(30, 41, 59, 0.8) !important;
}

.a-pagination .ant-pagination-item-active {
  background-color: rgba(59, 130, 246, 0.2) !important;
  border-color: rgba(59, 130, 246, 0.6) !important;
}

.a-pagination .ant-pagination-item-active a {
  color: #60a5fa !important;
}

.a-pagination .ant-pagination-prev .ant-pagination-item-link,
.a-pagination .ant-pagination-next .ant-pagination-item-link {
  background-color: rgba(30, 41, 59, 0.6) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: #d1d5db !important;
}

.a-pagination .ant-pagination-options .ant-select-selector {
  background-color: rgba(30, 41, 59, 0.6) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  color: #d1d5db !important;
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