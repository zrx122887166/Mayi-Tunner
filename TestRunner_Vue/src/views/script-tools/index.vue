<template>
  <div class="container">
    <!-- 搜索框区域 -->
    <div class="search-container">
      <el-input
        v-model="searchName"
        placeholder="根据工具名称查询"
        class="search-input"
        @input="handleInput"
        clearable
        :maxlength="50"
      />
      <el-button @click="searchTools" class="search-btn" :loading="searchLoading">
        <el-icon v-if="searchLoading" class="el-icon-loading" />
        查询
      </el-button>
      <el-button type="primary" @click="openAddDialog" class="add-btn">新建</el-button>
    </div>

    <!-- 主弹窗 -->
    <el-dialog
      v-model="dialogShow"
      :title="editToolId ? '编辑工具' : '新建工具'"
      width="80%"
      :before-close="beforeClose"
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
      class="custom-dialog"
    >
      <!-- 表单部分 -->
      <el-form
        :model="projectForm"
        :rules="formRules"
        ref="formRef"
        label-width="120px"
        status-icon
        class="main-form"
      >
        <!-- 工具名称 -->
        <el-form-item label="工具名称" class="form-item" prop="name">
          <el-input 
            v-model="projectForm.name" 
            placeholder="请输入工具名称" 
            :maxlength="100"
            show-word-limit
          />
        </el-form-item>
        
        <!-- 工具备注 -->
        <el-form-item label="工具备注" class="form-item" prop="remark">
          <el-input
            type="textarea"
            v-model="projectForm.remark"
            placeholder="请输入工具备注/使用说明"
            rows="3"
            :maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <!-- 参数设置 -->
        <el-form-item label="参数设置" class="form-item">
          <el-switch v-model="projectForm.has_params" @change="handleParamChange" />
        </el-form-item>
        
        <!-- 连接池选择 -->
        <el-form-item label="脚本依赖" class="form-item">
          <el-select
            v-model="projectForm.selectedConnectPools"
            multiple
            placeholder="脚本依赖选择"
            collapse-tags
          >
            <el-option label="ConnectInfoPool" value="ConnectInfoPool"></el-option>
            <el-option label="MbMysqlRedisConnectPool" value="MbMysqlRedisConnectPool"></el-option>
          </el-select>
        </el-form-item>
        
        <!-- 参数表格 -->
        <div v-if="projectForm.has_params" class="params-table-container">
          <el-form-item>
            <el-table :data="projectForm.params" style="width: 100%" table-layout="auto">
              <!-- 参数展示名称 -->
              <el-table-column label="参数展示名称" min-width="150">
                <template #default="scope">
                  <el-input
                    v-model="scope.row.show_name"
                    placeholder="用于展示在页面上的参数名称"
                    :maxlength="50"
                  />
                </template>
              </el-table-column>
              
              <!-- 参数名 -->
              <el-table-column label="参数名" min-width="120">
                <template #default="scope">
                  <el-input
                    v-model="scope.row.name"
                    placeholder="程序使用需要的参数名"
                    :maxlength="50"
                  />
                </template>
              </el-table-column>
              
              <!-- 参数值 -->
              <el-table-column label="参数值" min-width="180">
                <template #default="scope">
                  <el-input
                    v-model="scope.row.keys"
                    placeholder="多个值以;;隔开"
                    :maxlength="200"
                  />
                </template>
              </el-table-column>
              
              <!-- 默认值 -->
              <el-table-column label="默认值" min-width="120">
                <template #default="scope">
                  <el-input
                    v-model="scope.row.default"
                    placeholder="可提供默认值给用户"
                    :maxlength="100"
                  />
                </template>
              </el-table-column>
              
              <!-- 展示 -->
              <el-table-column label="展示" width="100">
                <template #default="scope">
                  <el-switch v-model="scope.row.is_show" />
                </template>
              </el-table-column>
              
              <!-- 操作 -->
              <el-table-column label="操作" width="160" align="center">
                <template #default="scope">
                  <el-button
                    type="text"
                    @click="addParamItem(projectForm.params)"
                    class="table-btn"
                  >新增</el-button>
                  <el-button
                    type="text"
                    text-color="#ff4d4f"
                    @click="removeParamItem(projectForm.params, scope.$index)"
                    v-if="projectForm.params.length > 1"
                    class="table-btn"
                  >删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-form-item>
        </div>
        
        <!-- 脚本工具提示 -->
        <div class="script-tips-container">
          <div class="tips">
            提示：建议使用本地 PyCharm 联调通过后，再进行复制。具体可参考【脚本工具案例】
            <el-tooltip
              class="box-item"
              effect="dark"
              placement="top-start"
            >
              <template #content>
                <pre>{{ scriptExample }}</pre>
              </template>
              <el-icon class="iconfont icon-tishi" />
            </el-tooltip>
          </div>
        </div>
        
        <!-- 脚本编辑区域 -->
        <el-form-item label="Python 脚本" class="form-item script-editor" prop="scripts">
          <Coder
            :lang="'python'"
            :content="projectForm.scripts"
            @updateScript="updateScript"
          />
        </el-form-item>
      </el-form>
      
      <!-- 弹窗底部按钮 -->
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="close">取消</el-button>
          <el-button type="primary" @click="submit" :loading="submitLoading">确认</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 新增工具分类弹窗 -->
    <el-dialog
      v-model="addSubTypeDialog"
      title="新建工具分类"
      width="40%"
      :close-on-click-modal="false"
      class="custom-dialog"
    >
      <el-form 
        :model="addSubTypeForm" 
        :rules="subTypeRules"
        ref="subTypeFormRef"
        label-width="120px" 
        class="subtype-form"
      >
        <el-form-item label="分类名称" class="form-item" prop="name">
          <el-input 
            v-model="addSubTypeForm.name" 
            :maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="分类 icon" class="form-item" prop="icon">
          <el-input 
            v-model="addSubTypeForm.icon" 
            placeholder="例如：el-icon-folder"
            :maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item class="form-item btn-group">
          <el-button type="primary" @click="addSubType" :loading="subTypeLoading">确定</el-button>
          <el-button @click="addSubTypeDialog = false">取消</el-button>
        </el-form-item>
      </el-form>
    </el-dialog>
    
    <!-- 工具列表 -->
    <div class="table-container">
      <el-table 
        :data="toolList" 
        style="width: 100%" 
        table-layout="auto" 
        class="tool-table"
        v-loading="tableLoading"
        element-loading-text="加载中..."
        empty-text="暂无工具数据"
      >
        <el-table-column label="工具名称" prop="name" min-width="180"></el-table-column>
        <el-table-column label="工具备注" prop="remark" min-width="200"></el-table-column>
        <el-table-column label="创建人" prop="creator" width="120"></el-table-column>
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
    
    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="currentPage"
        :page-sizes="[5, 10, 20, 50]"
        :page-size="pageSize"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        :disabled="tableLoading"
      >
      </el-pagination>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, nextTick } from 'vue';
import { addMenu } from '@/api/permission';
import Coder from '@/components/Coder';
import request from '@/utils/request';
import { ElMessageBox, ElMessage, ElForm } from 'element-plus';

// 状态定义
const dialogShow = ref(false);
const addSubTypeDialog = ref(false);
const searchName = ref('');
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const editToolId = ref(null);
const searchLoading = ref(false);
const submitLoading = ref(false);
const tableLoading = ref(false);
const subTypeLoading = ref(false);

// 防抖定时器
const debounceTimer = ref(null);

// 表单引用
const formRef = ref(null);
const subTypeFormRef = ref(null);

// 表单数据
const projectForm = ref({
  name: '',
  sub_type: null,
  component: '',
  path: '',
  remark: '',
  desc: '',
  has_params: false,
  params: [],
  dependency_modules: [],
  scripts: '',  // 用于存储脚本内容
  selectedConnectPools: []
});

// 表单验证规则
const formRules = reactive({
  name: [
    { required: true, message: '请输入工具名称', trigger: 'blur' },
    { max: 100, message: '工具名称不能超过100个字符', trigger: 'blur' }
  ],
  scripts: [
    { required: true, message: '请输入Python脚本', trigger: 'blur' }
  ]
});

// 分类表单验证规则
const subTypeRules = reactive({
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { max: 50, message: '分类名称不能超过50个字符', trigger: 'blur' }
  ],
  icon: [
    { required: true, message: '请输入分类图标', trigger: 'blur' },
    { max: 50, message: '图标名称不能超过50个字符', trigger: 'blur' }
  ]
});

// 其他数据
const emit = defineEmits(['submit', 'close', 'getSubTypes']);
const projectTypes = ref([]);
const can_add = ref(true);
const modules = ref([]);
const addSubTypeForm = ref({ name: '', icon: '' });
const toolList = ref([]);

// 脚本示例常量
const scriptExample = `import argparse


if __name__ == '__main__':
    # 如果是脚本需要进行参数设置
    parser = argparse.ArgumentParser(description="参数设置")
    parser.add_argument('-u', '--user_main_id', default='118315336')
    parser.add_argument('-l', '--level', default='1')
    parser.add_argument('-e', '--environment', default='pre')
    parser.add_argument('-r', '--member_redis_db', default="3")
    args = parser.parse_args()
    test = ChangeMemberLevel(usermainId=int(args.user_main_id),
                             level=int(args.level),
                             environment=args.environment,
                             member_redis_db=int(args.member_redis_db))
    test.ch_member_level()`;

// 方法定义
const beforeClose = (done) => {
  emit('close');
  resetForm();
  dialogShow.value = false;
  done();
};

const handleDialogClosed = () => {
  // 弹窗关闭后的回调
  resetForm();
};

const submit = async () => {
  // 表单验证
  if (!formRef.value) return;
  
  try {
    const valid = await formRef.value.validate();
    if (!valid) return;
  } catch (error) {
    console.error('表单验证失败:', error);
    return;
  }

  try {
    submitLoading.value = true;
    
    // 准备提交数据 - 修复字段映射
    const submitData = {
      name: projectForm.value.name,
      remark: projectForm.value.remark,
      scripts: projectForm.value.scripts,
      params: projectForm.value.params,
      selectedConnectPools: projectForm.value.selectedConnectPools
    };

    console.log('提交的数据:', submitData);

    let apiUrl;
    let method;
    
    if (editToolId.value) {
      // 编辑操作
      apiUrl = `/pythontool/${editToolId.value}/`;
      method = 'put';
    } else {
      // 新增操作
      apiUrl = '/pythontool/';
      method = 'post';
    }

    const response = await request[method](apiUrl, submitData);
    console.log('提交响应:', response);

    // 根据实际响应结构判断成功
    if (response && (response.id || response.message)) {
      ElMessage.success(editToolId.value ? '更新成功' : '保存成功');
      
      // 立即关闭弹窗
      dialogShow.value = false;
      
      // 重置表单
      resetForm();
      
      // 刷新列表 - 使用 nextTick 确保 DOM 更新完成
      nextTick(() => {
        getToolList();
      });
    } else {
      ElMessage.error(editToolId.value ? '更新失败' : '保存失败');
    }
  } catch (error) {
    console.error('提交出错:', error);
    const errorMsg = error.response?.data?.error || error.response?.data?.message || error.message || (editToolId.value ? '更新失败' : '保存失败');
    ElMessage.error(errorMsg);
  } finally {
    submitLoading.value = false;
  }
};

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields();
  }
  projectForm.value = {
    name: '',
    sub_type: null,
    component: '',
    path: '',
    remark: '',
    desc: '',
    has_params: false,
    params: [],
    dependency_modules: [],
    scripts: '',
    selectedConnectPools: []
  };
  editToolId.value = null;
};

const close = () => {
  dialogShow.value = false;
  resetForm();
};

const addSubType = async () => {
  // 表单验证
  if (!subTypeFormRef.value) return;
  const valid = await subTypeFormRef.value.validate();
  if (!valid) return;

  try {
    subTypeLoading.value = true;
    await addMenu(addSubTypeForm.value);
    addSubTypeDialog.value = false;
    emit('getSubTypes');
    ElMessage.success('添加分类成功');
    addSubTypeForm.value = { name: '', icon: '' };
  } catch (error) {
    console.error('添加分类失败:', error);
    ElMessage.error('添加分类失败');
  } finally {
    subTypeLoading.value = false;
  }
};

const handleParamChange = () => {
  if (projectForm.value.has_params && projectForm.value.params.length === 0) {
    addParamItem(projectForm.value.params);
  }
};

const addParamItem = (array) => {
  array.push({
    show_name: '',
    name: '',
    keys: '',
    is_show: true,
    default: ''
  });
};

const removeParamItem = (array, index) => {
  array.splice(index, 1);
};

const updateScript = (val) => {
  projectForm.value.scripts = val;
};

const getToolList = async () => {
  // 如果正在加载中，直接返回
  if (tableLoading.value) return;
  
  try {
    tableLoading.value = true;
    const baseApi = import.meta.env.VUE_APP_BASE_API || 'http://localhost:8000';
    
    // 确保URL格式正确，避免301重定向
    let url = `${baseApi}/api/pythontool/`; // 确保以斜杠结尾
    
    // 构建查询参数
    const params = new URLSearchParams();
    params.append('page', currentPage.value);
    params.append('size', pageSize.value);
    
    if (searchName.value) {
      params.append('name', searchName.value);
    }
    
    const queryString = params.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
    
    console.log('请求URL:', url);
    
    const response = await request.get(url);
    console.log('完整响应:', response);
    
    // 处理响应数据
    let responseData = response;
    
    // 检查 response 是否有 data 属性
    if (response && typeof response === 'object' && 'data' in response) {
      responseData = response.data;
    }
    
    console.log('处理后的响应数据:', responseData);
    
    // 安全地获取数据
    if (responseData && responseData.results) {
      toolList.value = responseData.results;
      total.value = responseData.count || 0;
    } else if (Array.isArray(responseData)) {
      // 如果直接返回数组
      toolList.value = responseData;
      total.value = responseData.length;
    } else {
      console.warn('未识别的响应格式:', responseData);
      toolList.value = [];
      total.value = 0;
    }
  } catch (error) {
    console.error('获取工具列表失败:', error);
    console.error('错误详情:', error.response);
    ElMessage.error('获取工具列表失败: ' + (error.message || '网络错误'));
  } finally {
    tableLoading.value = false;
  }
};

const editTool = async (item) => {
  console.log('编辑工具数据:', item);
  
  try {
    // 先获取最新的工具详情
    const baseApi = import.meta.env.VUE_APP_BASE_API || 'http://localhost:8000';
    const detailUrl = `${baseApi}/api/pythontool/${item.id}/`;
    
    const response = await request.get(detailUrl);
    const toolDetail = response.data || response;
    
    console.log('工具详情:', toolDetail);
    
    dialogShow.value = true;
    
    // 使用 nextTick 确保 DOM 更新完成后再设置表单数据
    nextTick(() => {
      // 修复字段映射
      projectForm.value = {
        name: toolDetail.name || '',
        remark: toolDetail.remark || '',
        scripts: toolDetail.pythonScript || '', // 注意这里改为 pythonScript
        has_params: toolDetail.has_params || false,
        selectedConnectPools: toolDetail.connect_pools || [], // 注意这里改为 connect_pools
        params: toolDetail.params || [],
        // 其他字段保持默认值
        sub_type: null,
        component: '',
        path: '',
        desc: '',
        dependency_modules: []
      };
      editToolId.value = item.id;

      if (projectForm.value.has_params && projectForm.value.params.length === 0) {
        addParamItem(projectForm.value.params);
      }
    });
  } catch (error) {
    console.error('获取工具详情失败:', error);
    ElMessage.error('获取工具详情失败');
  }
};

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
    
    const baseApi = import.meta.env.VUE_APP_BASE_API || 'http://localhost:8000';
    const deleteUrl = `${baseApi}/api/pythontool/${item.id}/`;
    
    // 发送删除请求，不关心响应内容
    await request.delete(deleteUrl);
    
    // 总是显示成功并刷新列表
    ElMessage.success('删除成功');
    
    // 强制刷新列表
    await getToolList();
    
  } catch (error) {
    if (error.name !== 'CancelError') {
      console.error('删除出错:', error);
      ElMessage.error('删除失败');
    }
  }
};

// 打开新增对话框
const openAddDialog = () => {
  resetForm();
  dialogShow.value = true;
};

// 处理搜索输入 - 修复防抖逻辑
const handleInput = (val) => {
  // 清除之前的定时器
  if (debounceTimer.value) {
    clearTimeout(debounceTimer.value);
  }
  
  // 设置新的定时器
  debounceTimer.value = setTimeout(() => {
    // 输入为空时自动搜索
    if (!val) {
      currentPage.value = 1;
      getToolList();
    }
  }, 500);
};

const handleSizeChange = (newSize) => {
  pageSize.value = newSize;
  currentPage.value = 1; // 重置到第一页
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

// 格式化日期时间
const formatDateTime = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).replace(/\//g, '-');
};

// 生命周期
onMounted(() => {
  getToolList();
});

// 暴露变量和方法
defineExpose({
  dialogShow,
  addSubTypeDialog,
  projectForm,
  toolList,
  currentPage,
  pageSize,
  total,
  searchName,
  editToolId,
  addSubTypeForm,
  projectTypes,
  can_add,
  modules,
  beforeClose,
  submit,
  close,
  addSubType,
  handleParamChange,
  addParamItem,
  removeParamItem,
  updateScript,
  getToolList,
  editTool,
  deleteTool,
  handleSizeChange,
  handleCurrentChange,
  searchTools,
  handleInput
});
</script>

<style scoped>
/* 全局样式重置 */
.container {
  width: 100%;
  padding: 0;
  margin: 0;
  box-sizing: border-box;
  background-color: rgba(31, 41, 55, 0.5);
  min-height: 100vh;
}

/* 搜索区域样式 */
.search-container {
  display: flex;
  align-items: center;
  margin: 20px;
  gap: 10px;
  flex-wrap: wrap;
  background-color: rgba(55, 65, 81, 0.5);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.search-input {
  width: 280px;
  min-width: 200px;
  flex: 1;
  max-width: 400px;
}

.search-btn {
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
  background: linear-gradient(to right, #3b82f6, #1d4ed8);
  border: none;
  color: #fff;
  margin-left: auto;
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

/* 表单样式 */
.main-form, .subtype-form {
  margin: 20px;
}

.form-item {
  margin-bottom: 18px;
}

/* 参数表格样式 */
.params-table-container {
  margin: 15px 0;
  padding: 10px;
  border-radius: 4px;
  border: 1px solid rgba(148, 163, 184, 0.1);
  background-color: rgba(30, 41, 59, 0.3);
}

/* 表格按钮样式 */
.table-btn {
  margin: 0 auto;
  display: inline-flex;
  align-items: center;
  height: 100%;
}

/* 脚本提示区域 */
.script-tips-container {
  margin: 15px 0;
  padding: 12px;
  background-color: rgba(30, 41, 59, 0.3);
  border-radius: 4px;
  font-size: 14px;
  color: #94a3b8;
}

.tips {
  line-height: 1.6;
  color: #94a3b8;
}

/* 脚本编辑区域 */
.script-editor {
  margin-top: 20px;
}

/* 工具列表表格样式 */
.table-container {
  margin: 20px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.1);
  overflow: hidden;
  background-color: rgba(55, 65, 81, 0.5);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.tool-table {
  border-bottom: none;
}

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

/* 分页样式 */
.pagination-container {
  text-align: right;
  margin: 20px;
  padding: 10px 0;
  background-color: rgba(55, 65, 81, 0.5);
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* 弹窗底部按钮 */
.dialog-footer {
  text-align: right;
}

/* 分类弹窗按钮组 */
.btn-group {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}
</style>

<style>
/* 全局样式覆盖 */
.custom-dialog .el-dialog {
  background-color: rgba(30, 41, 59, 0.95) !important;
  border: none !important; /* 去掉白色边框 */
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

/* 脚本依赖选择器样式 */
.custom-dialog .el-select .el-input__wrapper {
  background-color: rgba(30, 41, 59, 0.6) !important;
  border-color: rgba(148, 163, 184, 0.2) !important;
}

.custom-dialog .el-select .el-input__inner {
  color: #e2e8f0 !important;
}

/* 下拉选择器样式 */
.custom-dialog .el-select-dropdown {
  background-color: rgba(30, 41, 59, 0.95) !important;
  border: 1px solid rgba(148, 163, 184, 0.2) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4) !important;
}

.custom-dialog .el-select-dropdown__item {
  color: #e2e8f0 !important;
  background-color: transparent !important;
}

.custom-dialog .el-select-dropdown__item:hover {
  background-color: rgba(59, 130, 246, 0.2) !important;
}

.custom-dialog .el-select-dropdown__item.selected {
  background-color: rgba(59, 130, 246, 0.3) !important;
  color: #60a5fa !important;
}

/* 多选标签样式 */
.custom-dialog .el-select__tags .el-tag {
  background-color: rgba(59, 130, 246, 0.2) !important;
  border-color: rgba(59, 130, 246, 0.4) !important;
  color: #60a5fa !important;
}

.custom-dialog .el-select__tags .el-tag .el-icon-close {
  color: #60a5fa !important;
}

.custom-dialog .el-select__tags .el-tag .el-icon-close:hover {
  background-color: rgba(239, 68, 68, 0.2) !important;
  color: #ef4444 !important;
}

/* 字数统计样式 - 修复计数颜色 */
.custom-dialog .el-input__count {
  background: transparent !important;
  color: #94a3b8 !important;
}

.custom-dialog .el-textarea .el-input__count {
  background: transparent !important;
  color: #94a3b8 !important;
}

.custom-dialog .el-table {
  background-color: transparent !important;
  color: #e2e8f0 !important;
}

.custom-dialog .el-table th {
  background-color: rgba(30, 41, 59, 0.8) !important;
  color: #94a3b8 !important;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2) !important;
}

.custom-dialog .el-table tr {
  background-color: transparent !important;
}

.custom-dialog .el-table td {
  background-color: rgba(30, 41, 59, 0.4) !important;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1) !important;
  color: #e2e8f0 !important;
}

.custom-dialog .el-table tr:hover > td {
  background-color: rgba(59, 130, 246, 0.1) !important;
}

.custom-dialog .el-switch__core {
  background-color: rgba(148, 163, 184, 0.3) !important;
  border-color: rgba(148, 163, 184, 0.3) !important;
}

.custom-dialog .el-switch.is-checked .el-switch__core {
  background-color: #10b981 !important;
  border-color: #10b981 !important;
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

/* 分页样式统一 - 修复分页按钮背景色 */
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

/* Coder 组件样式调整 - 修复代码编辑器行号框 */
.coder-container .el-textarea__inner {
  background-color: rgba(30, 41, 59, 0.6) !important;
  border-color: rgba(148, 163, 184, 0.2) !important;
  color: #e2e8f0 !important;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace !important;
}

/* 修复代码编辑器行号框背景色 */
.coder-container .code-line-numbers {
  background-color: rgba(30, 41, 59, 0.8) !important;
  color: #94a3b8 !important;
  border-right: 1px solid rgba(148, 163, 184, 0.2) !important;
}

/* 代码高亮样式 */
.coder-container .hljs {
  background: rgba(30, 41, 59, 0.6) !important;
  color: #e2e8f0 !important;
}

.coder-container .hljs-keyword {
  color: #60a5fa !important;
}

.coder-container .hljs-string {
  color: #34d399 !important;
}

.coder-container .hljs-comment {
  color: #94a3b8 !important;
}

.coder-container .hljs-function {
  color: #f472b6 !important;
}

.coder-container .hljs-number {
  color: #f59e0b !important;
}

/* 脚本依赖选择器样式修复 */
.custom-dialog .el-select-dropdown {
  background-color: rgba(30, 41, 59, 0.95) !important;
  border: 1px solid rgba(148, 163, 184, 0.2) !important;
}

.custom-dialog .el-select-dropdown__item {
  color: #e2e8f0 !important;
  background-color: transparent !important;
}

.custom-dialog .el-select-dropdown__item:hover {
  background-color: rgba(59, 130, 246, 0.2) !important;
}

.custom-dialog .el-select-dropdown__item.selected {
  background-color: rgba(59, 130, 246, 0.3) !important;
  color: #60a5fa !important;
}

/* 修复多选标签样式 */
.custom-dialog .el-select__tags .el-tag {
  background-color: rgba(59, 130, 246, 0.2) !important;
  border-color: rgba(59, 130, 246, 0.4) !important;
  color: #60a5fa !important;
}

.custom-dialog .el-select__tags .el-tag .el-icon-close {
  color: #60a5fa !important;
}

.custom-dialog .el-select__tags .el-tag .el-icon-close:hover {
  background-color: rgba(239, 68, 68, 0.2) !important;
  color: #ef4444 !important;
}

/* 修复文本输入框计数颜色 */
.custom-dialog .el-input__count {
  background: transparent !important;
  color: #94a3b8 !important;
}

.custom-dialog .el-textarea .el-input__count {
  background: transparent !important;
  color: #94a3b8 !important;
}

/* 修复分页按钮背景色 */
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

/* 修复代码编辑器行号框背景色 */
.coder-container .code-line-numbers {
  background-color: rgba(30, 41, 59, 0.8) !important;
  color: #94a3b8 !important;
  border-right: 1px solid rgba(148, 163, 184, 0.2) !important;
}
</style>