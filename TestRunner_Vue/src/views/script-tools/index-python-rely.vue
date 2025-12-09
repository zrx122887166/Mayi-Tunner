<template>
  <div class="script-rely-container">
    <!-- 搜索和操作区 -->
    <div class="operation-bar">
      <el-input
        v-model="searchName"
        placeholder="根据工具名称查询"
        style="width: 200px; margin-right: 10px;"
        @input="handleInput"
        clearable
        :maxlength="50"
      />
      <el-button @click="searchTools" class="search-btn" :loading="searchLoading">查询</el-button>
      <el-button type="primary" @click="dialogShow = true" class="add-btn">新建</el-button>
    </div>
    
    <!-- 主弹窗 -->
    <el-dialog
      v-model="dialogShow"
      :title="editToolId ? '编辑依赖工具' : '新建依赖工具'"
      width="70%"
      :before-close="beforeClose"
      :z-index="1000"
      :close-on-click-modal="false"
      class="custom-dialog"
    >
      <el-form
        :model="projectForm"
        :rules="formRules"
        ref="formRef"
        label-width="120px"
        status-icon
        class="form-container"
      >
        <!-- 工具名称 -->
        <el-form-item label="工具名称" class="form-item" prop="name">
          <el-input v-model="projectForm.name" placeholder="请输入工具名称" :maxlength="100" show-word-limit />
        </el-form-item>
        
        <!-- 工具备注 -->
        <el-form-item label="工具备注" class="form-item" prop="remark">
          <el-input
            type="textarea"
            v-model="projectForm.remark"
            placeholder="请输入工具备注/使用说明"
            :maxlength="500"
            show-word-limit
            rows="3"
          />
        </el-form-item>
        
        <!-- Python 脚本 -->
        <el-form-item label="Python 脚本" class="form-item" prop="pythonScript">
          <el-input
            type="textarea"
            v-model="projectForm.pythonScript"
            placeholder="请输入 Python 脚本"
            :rows="15"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="close">取消</el-button>
          <el-button type="primary" @click="submit" :loading="submitLoading">确认</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 工具列表 -->
    <el-table 
      :data="toolList" 
      style="width: 100%" 
      table-layout="auto"
      class="tool-table"
      v-loading="loading"
      element-loading-text="加载中..."
      empty-text="暂无依赖工具数据"
    >
      <el-table-column label="工具名称" prop="name" width="200"></el-table-column>
      <el-table-column label="工具备注" prop="remark"></el-table-column>
      <el-table-column label="Python脚本" prop="pythonScript" width="300">
        <template #default="scope">
          <el-tooltip
            effect="dark"
            :content="scope.row.pythonScript"
            placement="top"
            v-if="scope.row.pythonScript && scope.row.pythonScript.length > 50"
          >
            <span>{{ scope.row.pythonScript.substring(0, 50) }}...</span>
          </el-tooltip>
          <span v-else>{{ scope.row.pythonScript || '无脚本' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" prop="create_time" width="180">
        <template #default="scope">
          {{ formatDateTime(scope.row.create_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button type="primary" size="small" @click="editTool(scope.row)" class="table-operation-btn edit-btn">编辑</el-button>
          <el-button type="danger" size="small" @click="deleteTool(scope.row)" class="table-operation-btn delete-btn">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[5, 10, 20]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        :disabled="loading"
      >
      </el-pagination>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, nextTick } from 'vue';
import request from '@/utils/request';
import { ElMessage, ElMessageBox } from 'element-plus';

// 状态定义
const dialogShow = ref(false);
const loading = ref(false);
const searchLoading = ref(false);
const submitLoading = ref(false);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const searchName = ref('');
const editToolId = ref(null);
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
      page: currentPage.value,
      size: pageSize.value,
      name: searchName.value || ''
    };
    
    console.log('📡 请求参数:', params);
    
    const response = await request.get('/tools/', { params });
    console.log('✅ 获取工具列表响应:', response);
    
    // 根据实际响应结构调整
    let responseData = response;
    if (response && typeof response === 'object') {
      // 如果响应有data字段，使用data
      if ('data' in response) {
        responseData = response.data;
      }
      
      // 处理不同的响应结构
      if (responseData.results) {
        toolList.value = responseData.results;
        total.value = responseData.count || 0;
      } else if (Array.isArray(responseData)) {
        toolList.value = responseData;
        total.value = responseData.length;
      } else {
        console.warn('响应数据格式异常:', responseData);
        toolList.value = [];
        total.value = 0;
      }
    }
    
    console.log('📊 最终工具列表:', toolList.value);
    
  } catch (error) {
    console.error('❌ 获取依赖工具列表失败:', error);
    console.error('错误详情:', error.response);
    ElMessage.error('获取依赖工具列表失败：' + (error.message || '网络错误'));
    toolList.value = [];
  } finally {
    loading.value = false;
  }
};

// 编辑工具
const editTool = (item) => {
  console.log('编辑工具:', item);
  dialogShow.value = true;
  editToolId.value = item.id;
  
  // 直接赋值，确保字段名正确
  projectForm.value = {
    name: item.name || '',
    remark: item.remark || '',
    pythonScript: item.pythonScript || item.pythonScript || ''  // 兼容两种字段名
  };
  
  console.log('设置的表单数据:', projectForm.value);
};

// 提交表单
const submit = async () => {
  if (!formRef.value) return;
  
  try {
    await formRef.value.validate();
  } catch (error) {
    console.error('表单验证失败:', error);
    ElMessage.error('请完善表单信息');
    return;
  }

  try {
    submitLoading.value = true;
    
    // 构造请求数据 - 根据后端期望的字段名
    const requestData = {
      name: projectForm.value.name,
      remark: projectForm.value.remark,
      pythonScript: projectForm.value.pythonScript
    };
    
    console.log('📤 提交数据:', requestData);
    console.log('编辑ID:', editToolId.value);

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
    
    console.log('✅ 提交响应:', response);
    
    dialogShow.value = false;
    await getToolList(); // 提交成功刷新列表
    resetForm();
    
  } catch (error) {
    console.error('❌ 请求出错:', error);
    console.error('错误响应:', error.response);
    
    let errorMessage = '操作失败';
    if (error.response?.data) {
      if (typeof error.response.data === 'string') {
        errorMessage = error.response.data;
      } else if (error.response.data.error) {
        errorMessage = error.response.data.error;
      } else if (error.response.data.details) {
        errorMessage = JSON.stringify(error.response.data.details);
      }
    } else {
      errorMessage = error.message || '网络错误';
    }
    
    ElMessage.error(errorMessage);
  } finally {
    submitLoading.value = false;
  }
};

// 删除工具 - 完全重写的版本
const deleteTool = async (item) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除工具 "${item.name}" 吗？此操作不可恢复！`, 
      '警告', 
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    console.log('删除工具ID:', item.id);
    
    try {
      // 使用更底层的请求方式
      const response = await request.delete(`/tools/${item.id}/`);
      console.log('删除响应:', response);
      
      // 204状态码表示成功，直接显示成功消息
      ElMessage.success('删除成功');
      
      // 立即更新本地数据，避免重新请求
      const index = toolList.value.findIndex(tool => tool.id === item.id);
      if (index !== -1) {
        toolList.value.splice(index, 1);
        total.value -= 1;
        
        // 如果删除后当前页没有数据且不是第一页，跳转到上一页
        if (toolList.value.length === 0 && currentPage.value > 1) {
          currentPage.value -= 1;
          await getToolList(); // 重新加载上一页数据
        }
      } else {
        // 如果本地没找到，重新加载列表
        await getToolList();
      }
      
    } catch (deleteError) {
      console.log('删除请求详情:', deleteError);
      
      // 检查是否是204状态码
      if (deleteError.response && deleteError.response.status === 204) {
        // 204状态码实际上是成功的
        ElMessage.success('删除成功');
        
        // 更新本地数据
        const index = toolList.value.findIndex(tool => tool.id === item.id);
        if (index !== -1) {
          toolList.value.splice(index, 1);
          total.value -= 1;
          
          if (toolList.value.length === 0 && currentPage.value > 1) {
            currentPage.value -= 1;
            await getToolList();
          }
        } else {
          await getToolList();
        }
      } else {
        // 真正的错误
        throw deleteError;
      }
    }
    
  } catch (error) {
    // 处理取消操作
    if (error.name === 'CancelError') {
      console.log('用户取消了删除操作');
      return;
    }
    
    // 处理其他错误
    console.error('删除失败:', error);
    
    let errorMessage = '删除失败';
    if (error.response) {
      if (error.response.data) {
        if (typeof error.response.data === 'string') {
          errorMessage = error.response.data;
        } else if (error.response.data.error) {
          errorMessage = error.response.data.error;
        } else if (error.response.data.details) {
          errorMessage = JSON.stringify(error.response.data.details);
        }
      } else {
        errorMessage = `HTTP错误: ${error.response.status}`;
      }
    } else {
      errorMessage = error.message || '网络错误';
    }
    
    ElMessage.error(errorMessage);
  }
};

// 其他方法保持不变
const beforeClose = (done) => {
  resetForm();
  done();
};

const close = () => {
  dialogShow.value = false;
  resetForm();
};

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields();
  }
  projectForm.value = {
    name: '',
    remark: '',
    pythonScript: ''
  };
  editToolId.value = null;
};

const handleSizeChange = (newSize) => {
  pageSize.value = newSize;
  currentPage.value = 1;
  getToolList();
};

const handleCurrentChange = (newPage) => {
  currentPage.value = newPage;
  getToolList();
};

const searchTools = () => {
  currentPage.value = 1;
  getToolList();
};

// 处理搜索输入防抖
const handleInput = (val) => {
  if (debounceTimer.value) {
    clearTimeout(debounceTimer.value);
  }
  debounceTimer.value = setTimeout(() => {
    if (!val) {
      currentPage.value = 1;
      getToolList();
    }
  }, 500);
};

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return dateString; // 如果解析失败，返回原字符串
    }
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).replace(/\//g, '-');
  } catch (error) {
    console.error('日期格式化错误:', error);
    return dateString;
  }
};

onMounted(() => {
  console.log('组件挂载，开始获取工具列表...');
  getToolList();
});

// 暴露变量和方法
defineExpose({
  dialogShow,
  toolList,
  currentPage,
  pageSize,
  total,
  searchName,
  editToolId,
  projectForm,
  loading,
  getToolList,
  editTool,
  submit,
  deleteTool,
  close,
  handleSizeChange,
  handleCurrentChange,
  searchTools,
  handleInput
});
</script>

<style scoped>
.script-rely-container {
  padding: 20px;
  background-color: rgba(31, 41, 55, 0.5);
  min-height: calc(100vh - 60px);
}

.operation-bar {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  border-radius: 8px;
  background-color: rgba(55, 65, 81, 0.5);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.search-btn {
  margin-right: 10px;
  background: linear-gradient(to right, #4f46e5, #7c3aed);
  border: none;
  color: #fff;
  border-radius: 8px;
  padding: 0 20px;
  height: 36px;
  transition: all 0.3s ease;
}

.search-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
}

.add-btn {
  margin-left: auto;
  background: linear-gradient(to right, #3b82f6, #1d4ed8);
  border: none;
  color: #fff;
  padding: 0 24px;
  height: 36px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);
}

.add-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
  background: linear-gradient(to right, #2563eb, #60a5fa);
}

.add-btn:active {
  transform: translateY(1px);
  box-shadow: 0 1px 3px rgba(59, 130, 246, 0.3);
}

.tool-table {
  margin-top: 20px;
  border: 1px solid rgba(148, 163, 184, 0.1);
  border-radius: 8px;
  overflow: hidden;
  background-color: rgba(55, 65, 81, 0.5);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.pagination-container {
  text-align: right;
  margin-top: 20px;
  padding: 10px 0;
  background-color: rgba(55, 65, 81, 0.5);
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.form-container {
  margin-top: 10px;
}

.form-item {
  margin-bottom: 15px;
}

.dialog-footer {
  text-align: right;
}

/* 表格样式优化 */
:deep(.el-table .cell) {
  word-break: break-word;
}

/* 长文本显示优化 */
:deep(.el-tooltip__trigger) {
  cursor: pointer;
  color: #60a5fa;
}

/* 表格操作按钮样式 */
.table-operation-btn {
  margin-right: 8px;
}

.edit-btn {
  background: linear-gradient(to right, #728bb4, #2563eb) !important;
  border: none !important;
}

.edit-btn:hover {
  background: linear-gradient(to right, #6181c2, #2563eb) !important;
}

.delete-btn {
  background: linear-gradient(to right, #4549ed, #ff6464) !important;
  border: none !important;
}

.delete-btn:hover {
  background: linear-gradient(to right, #ff6464, #4549ed) !important;
}
</style>

<style>
/* 全局样式覆盖 - 与A代码保持一致 */
.custom-dialog .el-dialog {
  background-color: rgba(30, 41, 59, 0.95) !important;
  border: none !important;
  border-radius: 8px !important;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5) !important;
}

.custom-dialog .el-dialog__header {
  background-color: rgba(30, 41, 59, 0.8) !important;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2) !important;
  padding: 15px 20px !important;
  border-radius: 8px 8px 0 0 !important;
}

.custom-dialog .el-dialog__title {
  color: #e2e8f0 !important;
  font-weight: 600 !important;
}

.custom-dialog .el-dialog__headerbtn {
  top: 15px !important;
}

.custom-dialog .el-dialog__headerbtn .el-dialog__close {
  color: #94a3b8 !important;
}

.custom-dialog .el-dialog__headerbtn:hover .el-dialog__close {
  color: #e2e8f0 !important;
}

.custom-dialog .el-dialog__body {
  background-color: rgba(30, 41, 59, 0.8) !important;
  color: #e2e8f0 !important;
  padding: 20px !important;
}

.custom-dialog .el-form-item__label {
  color: #94a3b8 !important;
}

.custom-dialog .el-input__wrapper {
  background-color: rgba(30, 41, 59, 0.6) !important;
  border-color: rgba(148, 163, 184, 0.2) !important;
  box-shadow: none !important;
}

.custom-dialog .el-input__wrapper:hover {
  border-color: #60a5fa !important;
}

.custom-dialog .el-input__wrapper.is-focus {
  border-color: #60a5fa !important;
  box-shadow: 0 0 0 1px #60a5fa !important;
}

.custom-dialog .el-input__inner {
  color: #e2e8f0 !important;
}

.custom-dialog .el-textarea__inner {
  background-color: rgba(30, 41, 59, 0.6) !important;
  border-color: rgba(148, 163, 184, 0.2) !important;
  color: #e2e8f0 !important;
  box-shadow: none !important;
}

.custom-dialog .el-textarea__inner:hover {
  border-color: #60a5fa !important;
}

.custom-dialog .el-textarea__inner:focus {
  border-color: #60a5fa !important;
  box-shadow: 0 0 0 1px #60a5fa !important;
}

/* 字数统计样式 */
.custom-dialog .el-input__count {
  background: transparent !important;
  color: #94a3b8 !important;
}

.custom-dialog .el-textarea .el-input__count {
  background: transparent !important;
  color: #94a3b8 !important;
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

.el-button--danger {
  background: linear-gradient(to right, #4549ed, #ff6464) !important;
  border: none !important;
  color: #fff !important;
}

.el-button--danger:hover {
  background: linear-gradient(to right, #ff6464, #4549ed) !important;
}

/* 分页样式统一 */
.el-pagination {
  --el-pagination-bg-color: transparent !important;
  --el-pagination-text-color: #94a3b8 !important;
  --el-pagination-border-color: rgba(148, 163, 184, 0.1) !important;
  --el-pagination-hover-color: #60a5fa !important;
}

.el-pagination .btn-prev,
.el-pagination .btn-next,
.el-pagination .number {
  background-color: rgba(30, 41, 59, 0.5) !important;
  color: #94a3b8 !important;
  border: 1px solid rgba(148, 163, 184, 0.1) !important;
}

.el-pagination .btn-prev:hover,
.el-pagination .btn-next:hover,
.el-pagination .number:hover {
  color: #60a5fa !important;
  background-color: rgba(59, 130, 246, 0.1) !important;
}

.el-pagination .number.active {
  background-color: rgba(59, 130, 246, 0.2) !important;
  color: #60a5fa !important;
  border-color: rgba(59, 130, 246, 0.3) !important;
}

.el-pagination .el-input__wrapper {
  background-color: rgba(30, 41, 59, 0.5) !important;
  border-color: rgba(148, 163, 184, 0.1) !important;
  color: #e2e8f0 !important;
}

.el-pagination .el-input__inner {
  color: #e2e8f0 !important;
}

.el-pagination .el-pagination__total {
  color: #94a3b8 !important;
}

.el-pagination .el-pagination__sizes .el-input .el-input__inner {
  color: #e2e8f0 !important;
}

.el-pagination .el-pagination__jump {
  color: #94a3b8 !important;
}

/* 表格样式统一 */
.el-table {
  --el-table-border-color: rgba(148, 163, 184, 0.1) !important;
  --el-table-bg-color: transparent !important;
  --el-table-tr-bg-color: transparent !important;
  --el-table-text-color: #e2e8f0 !important;
  --el-table-header-text-color: #94a3b8 !important;
  --el-table-row-hover-bg-color: rgba(59, 130, 246, 0.1) !important;
  --el-table-current-row-bg-color: rgba(59, 130, 246, 0.2) !important;
}

.el-table th {
  background-color: rgba(30, 41, 59, 0.8) !important;
  color: #94a3b8 !important;
  font-weight: 600 !important;
}

.el-table tr {
  background-color: transparent !important;
}

.el-table td {
  background-color: rgba(30, 41, 59, 0.4) !important;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1) !important;
}

.el-table tr:hover > td {
  background-color: rgba(59, 130, 246, 0.1) !important;
}

.el-table .el-table__empty-block {
  background-color: transparent !important;
}

.el-table .el-table__empty-text {
  color: #94a3b8 !important;
}

/* 搜索框样式统一 */
.el-input__wrapper {
  background-color: rgba(30, 41, 59, 0.5) !important;
  border-color: rgba(148, 163, 184, 0.1) !important;
  box-shadow: none !important;
}

.el-input__wrapper:hover {
  border-color: #60a5fa !important;
}

.el-input__wrapper.is-focus {
  border-color: #60a5fa !important;
  box-shadow: 0 0 0 1px #60a5fa !important;
}

.el-input__inner {
  color: #e2e8f0 !important;
}

.el-input__suffix {
  color: #94a3b8 !important;
}

/* 加载样式 */
.el-loading-mask {
  background-color: rgba(15, 23, 42, 0.7) !important;
}

.el-loading-spinner .path {
  stroke: #60a5fa !important;
}

.el-loading-text {
  color: #94a3b8 !important;
}
</style>