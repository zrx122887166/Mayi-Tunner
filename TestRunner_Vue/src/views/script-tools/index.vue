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
      <el-button type="primary" @click="openAddDialog" class="add-btn">新建工具</el-button>
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
                      placeholder="请输入工具名称" 
                      :maxlength="100"
                      class="custom-input"
                    />
                  </el-form-item>
                </div>
              </div>
              
              <!-- 新增：工具分组名称输入框 -->
              <div class="form-row">
                <div class="form-label">工具分组名称<span class="required-mark">*</span></div>
                <div class="form-field">
                  <el-form-item prop="group_name" class="tw-w-full">
                    <el-input 
                      v-model="projectForm.group_name" 
                      placeholder="请输入工具分组名称" 
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
                      placeholder="请输入工具备注/使用说明"
                      rows="3"
                      :maxlength="500"
                      class="custom-textarea"
                    />
                  </el-form-item>
                </div>
              </div>
            </div>
          </div>

          <!-- 参数设置部分 -->
          <div class="section params-section">
            <div class="section-header">
              <div class="section-title">参数设置</div>
            </div>
            <div class="section-body">
              <!-- 参数设置开关 -->
              <div class="form-row switch-row">
                <div class="form-label">启用参数</div>
                <div class="form-field switch-field">
                  <el-switch v-model="projectForm.has_params" @change="handleParamChange" />
                </div>
              </div>
              
              <!-- 参数表格 -->
              <div v-if="projectForm.has_params" class="params-table-wrapper">
                <div class="table-container">
                  <table class="params-table">
                    <thead>
                      <tr>
                        <th class="param-header">参数展示名称<span class="required-mark">*</span></th>
                        <th class="param-header">参数名<span class="required-mark">*</span></th>
                        <th class="param-header">参数值</th>
                        <th class="param-header">默认值</th>
                        <th class="param-header">展示</th>
                        <th class="param-header operation-header">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(param, index) in projectForm.params" :key="index">
                        <td class="param-cell">
                          <el-form-item
                            :prop="`params[${index}].show_name`"
                            :rules="[
                              { required: projectForm.has_params, message: '请输入参数展示名称', trigger: 'blur' },
                              { max: 50, message: '参数展示名称不能超过50个字符', trigger: 'blur' }
                            ]"
                            class="tw-w-full param-form-item"
                          >
                            <el-input
                              v-model="param.show_name"
                              placeholder="用于展示在页面上的参数名称"
                              :maxlength="50"
                              class="table-input"
                            />
                          </el-form-item>
                        </td>
                        <td class="param-cell">
                          <el-form-item
                            :prop="`params[${index}].name`"
                            :rules="[
                              { required: projectForm.has_params, message: '请输入参数名', trigger: 'blur' },
                              { max: 50, message: '参数名不能超过50个字符', trigger: 'blur' }
                            ]"
                            class="tw-w-full param-form-item"
                          >
                            <el-input
                              v-model="param.name"
                              placeholder="程序使用需要的参数名"
                              :maxlength="50"
                              class="table-input"
                            />
                          </el-form-item>
                        </td>
                        <td class="param-cell">
                          <el-input
                            v-model="param.keys"
                            placeholder="多个值以;;隔开"
                            :maxlength="200"
                            class="table-input"
                          />
                        </td>
                        <td class="param-cell">
                          <el-input
                            v-model="param.default"
                            placeholder="可提供默认值给用户"
                            :maxlength="100"
                            class="table-input"
                          />
                        </td>
                        <td class="param-cell">
                          <div class="switch-cell">
                            <el-switch v-model="param.is_show" size="small" />
                          </div>
                        </td>
                        <td class="param-cell actions">
                          <div class="action-buttons">
                            <el-button
                              type="text"
                              @click="addParamItem(projectForm.params)"
                              class="action-btn add-btn"
                            >新增</el-button>
                            <el-button
                              type="text"
                              @click="removeParamItem(projectForm.params, index)"
                              v-if="projectForm.params.length > 1"
                              class="action-btn delete-btn"
                            >删除</el-button>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <!-- 修改：增加提示块的上边距，让它向下移动 -->
                <div class="param-tip tw-text-sm tw-text-gray-400 tw-mt-4 tw-ml-2">
                  <span class="required-mark">*</span> 启用参数时，参数展示名称和参数名为必填项
                </div>
              </div>
              
              <!-- 脚本依赖 -->
              <div class="form-row">
                <div class="form-label">脚本依赖</div>
                <div class="form-field">
                  <el-select
                    v-model="projectForm.selectedConnectPools"
                    multiple
                    placeholder="请选择脚本依赖"
                    collapse-tags
                    class="custom-select"
                    :popper-class="'script-deps-dropdown'"
                  >
                    <!-- 动态渲染选项 -->
                    <el-option
                      v-for="tool in scriptDepsOptions"
                      :key="tool.id"
                      :label="tool.name"
                      :value="tool.name"
                    />
                    <!-- 如果没有可用选项 -->
                    <el-option
                      v-if="scriptDepsOptions.length === 0"
                      :label="'无依赖脚本'"
                      :value="''"
                      disabled
                    />
                  </el-select>
                  <div v-if="scriptDepsOptions.length === 0" class="tw-text-gray-400 tw-text-sm tw-mt-2">
                    暂无可用依赖脚本，请先在脚本依赖管理页面创建
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 脚本提示部分 -->
          <div class="section tips-section">
            <div class="tip-content">
              <div class="tip-icon">
                <el-icon><InfoFilled /></el-icon>
              </div>
              <div class="tip-text">
                提示：建议使用本地 PyCharm 联调通过后，再进行复制。具体可参考【脚本工具案例】
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
    
    <!-- 新增工具分类弹窗 -->
    <el-dialog
      v-model="addSubTypeDialog"
      title="新建工具分类"
      width="40%"
      :close-on-click-modal="false"
      class="custom-dialog"
    >
      <div class="tw-bg-gray-900/90 tw-rounded-lg tw-p-6">
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
              class="tw-bg-gray-800/80 tw-text-gray-100 tw-border-gray-700"
            />
          </el-form-item>
          <el-form-item label="分类 icon" class="form-item" prop="icon">
            <el-input 
              v-model="addSubTypeForm.icon" 
              placeholder="例如：el-icon-folder"
              :maxlength="50"
              class="tw-bg-gray-800/80 tw-text-gray-100 tw-border-gray-700"
            />
          </el-form-item>
          <el-form-item class="form-item btn-group">
            <el-button @click="addSubTypeDialog = false" class="cancel-btn">取消</el-button>
            <el-button type="primary" @click="addSubType" :loading="subTypeLoading" class="confirm-btn">确定</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-dialog>
    
    <!-- 工具列表 -->
    <div class="table-container tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-overflow-hidden tw-flex-grow">
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
        <!-- 新增：工具分组名称列 -->
        <el-table-column label="工具分组" prop="group_name" min-width="180"></el-table-column>
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
import { addMenu } from '@/api/permission';
import Coder from '@/components/Coder';
import request from '@/utils/request';
import { ElMessageBox, ElMessage, ElForm } from 'element-plus';
import { formatDateTime } from '@/utils/format';
import { InfoFilled } from '@element-plus/icons-vue';

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
const addSubTypeDialog = ref(false);
const searchName = ref('');
const editToolId = ref(null);
const searchLoading = ref(false);
const tableLoading = ref(false);
const submitLoading = ref(false);
const subTypeLoading = ref(false);
const debounceTimer = ref(null);

// 新增：脚本依赖选项
const scriptDepsOptions = ref([]);

// 表单引用
const formRef = ref(null);
const subTypeFormRef = ref(null);

// 表单数据
const projectForm = ref({
  name: '',
  group_name: '', // 新增：工具分组名称
  remark: '',
  has_params: false,
  selectedConnectPools: [],
  params: [
    {
      show_name: '',
      name: '',
      keys: '',
      default: '',
      is_show: true
    }
  ],
  pythonScript: ''
});

// 新增分类表单
const addSubTypeForm = ref({
  name: '',
  icon: ''
});

// 表单验证规则
const formRules = reactive({
  name: [
    { required: true, message: '请输入工具名称', trigger: 'blur' },
    { max: 100, message: '工具名称不能超过100个字符', trigger: 'blur' }
  ],
  group_name: [ // 新增：分组名称验证规则
    { required: true, message: '请输入工具分组名称', trigger: 'blur' },
    { max: 100, message: '工具分组名称不能超过100个字符', trigger: 'blur' }
  ],
  pythonScript: [
    { required: true, message: '请输入Python脚本', trigger: 'blur' },
    { max: 500000, message: '脚本内容不能超过500000个字符', trigger: 'blur' }
  ],
  remark: [
    { max: 500, message: '工具备注不能超过500个字符', trigger: 'blur' }
  ]
});

// 分类表单验证规则
const subTypeRules = reactive({
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { max: 50, message: '分类名称不能超过50个字符', trigger: 'blur' }
  ],
  icon: [
    { required: true, message: '请输入分类icon', trigger: 'blur' },
    { max: 50, message: '分类icon不能超过50个字符', trigger: 'blur' }
  ]
});

const toolList = ref([]);

// 新增：获取脚本依赖选项列表
const fetchScriptDepsOptions = async () => {
  try {
    const response = await request.get('/tools/', {
      params: {
        size: 100, // 获取所有，不分页
        ordering: 'name'
      }
    });
    
    const responseData = response.data || response;
    
    if (responseData.results) {
      scriptDepsOptions.value = responseData.results.map(tool => ({
        id: tool.id,
        name: tool.name || '未命名工具'
      }));
    } else if (Array.isArray(responseData)) {
      scriptDepsOptions.value = responseData.map(tool => ({
        id: tool.id,
        name: tool.name || '未命名工具'
      }));
    } else {
      scriptDepsOptions.value = [];
    }
    
    console.log('加载脚本依赖选项成功:', scriptDepsOptions.value);
  } catch (error) {
    console.error('获取脚本依赖选项失败:', error);
    scriptDepsOptions.value = [];
    // 不显示错误提示，避免干扰用户
  }
};

// 获取工具列表
const getToolList = async () => {
  try {
    tableLoading.value = true;
    const params = {
      page: pagination.value.current,
      size: pagination.value.page_size,
      name: searchName.value || ''
    };
    
    const response = await request.get('/pythontool/', { params });
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
    console.error('获取工具列表失败:', error);
    ElMessage.error('获取工具列表失败：' + (error.message || '网络错误'));
    toolList.value = [];
    pagination.value.total = 0;
  } finally {
    tableLoading.value = false;
  }
};

// 编辑工具
const editTool = (item) => {
  dialogShow.value = true;
  editToolId.value = item.id;
  
  // 赋值表单数据
  projectForm.value = {
    name: item.name || '',
    group_name: item.group_name || '', // 新增：赋值分组名称
    remark: item.remark || '',
    has_params: item.has_params || false,
    selectedConnectPools: item.connect_pools || [],
    params: item.params && item.params.length ? [...item.params] : [
      {
        show_name: '',
        name: '',
        keys: '',
        default: '',
        is_show: true
      }
    ],
    pythonScript: item.pythonScript || ''
  };
  
  // 清除之前的验证状态
  nextTick(() => {
    if (formRef.value) {
      formRef.value.clearValidate();
    }
  });
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

// 自定义参数验证方法
const validateParams = () => {
  // 如果禁用参数，直接返回成功
  if (!projectForm.value.has_params) return true;
  
  // 启用参数时，校验每个参数项的必填字段
  const params = projectForm.value.params || [];
  let isValid = true;
  
  params.forEach((param, index) => {
    // 验证参数展示名称
    if (!param.show_name || param.show_name.trim() === '') {
      ElMessage.error(`第${index + 1}行：请输入参数展示名称`);
      isValid = false;
    }
    
    // 验证参数名
    if (!param.name || param.name.trim() === '') {
      ElMessage.error(`第${index + 1}行：请输入参数名`);
      isValid = false;
    }
  });
  
  return isValid;
};

// 提交表单
const submit = async () => {
  if (!formRef.value) return;
  
  try {
    // 先验证基础表单
    const valid = await formRef.value.validate();
    if (!valid) {
      return;
    }
    
    // 验证参数项（新增核心逻辑）
    if (!validateParams()) {
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
      group_name: projectForm.value.group_name,
      remark: projectForm.value.remark,
      has_params: projectForm.value.has_params,
      connect_pools: projectForm.value.selectedConnectPools,
      pythonScript: projectForm.value.pythonScript
    };
    
    // 只有启用参数时才添加params字段
    if (projectForm.value.has_params) {
      // 过滤空参数项（可选）
      const validParams = projectForm.value.params.filter(param => 
        param.show_name && param.name
      );
      requestData.params = validParams.length > 0 ? validParams : [
        {
          show_name: '',
          name: '',
          keys: '',
          default: '',
          is_show: true
        }
      ];
    } else {
      // 禁用参数时，明确设置params为空数组
      requestData.params = [];
    }

    let response;
    if (editToolId.value) {
      // 编辑操作
      response = await request.put(`/pythontool/${editToolId.value}/`, requestData);
      ElMessage.success('更新成功');
    } else {
      // 新增操作
      response = await request.post('/pythontool/', requestData);
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

// 添加参数项
const addParamItem = (params) => {
  params.push({
    show_name: '',
    name: '',
    keys: '',
    default: '',
    is_show: true
  });
};

// 移除参数项
const removeParamItem = (params, index) => {
  params.splice(index, 1);
};

// 参数开关变化
const handleParamChange = (val) => {
  if (val) {
    // 启用参数时，初始化参数项（如果为空）
    if (!projectForm.value.params || projectForm.value.params.length === 0) {
      projectForm.value.params = [
        {
          show_name: '',
          name: '',
          keys: '',
          default: '',
          is_show: true
        }
      ];
    }
    // 触发表单验证
    nextTick(() => {
      if (formRef.value) {
        projectForm.value.params.forEach((_, index) => {
          formRef.value.validateField(`params[${index}].show_name`);
          formRef.value.validateField(`params[${index}].name`);
        });
      }
    });
  } else {
    // 禁用参数时，清空参数数据
    projectForm.value.params = [
      {
        show_name: '',
        name: '',
        keys: '',
        default: '',
        is_show: true
      }
    ];
    // 清除参数项的验证状态
    nextTick(() => {
      if (formRef.value) {
        projectForm.value.params.forEach((_, index) => {
          formRef.value.clearValidate(`params[${index}].show_name`);
          formRef.value.clearValidate(`params[${index}].name`);
        });
      }
    });
  }
};

// 更新脚本内容
const updateScript = (content) => {
  projectForm.value.pythonScript = content;
  // 触发验证
  if (formRef.value) {
    formRef.value.validateField('pythonScript');
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
    
    await request.delete(`/pythontool/${item.id}/`);
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

// 添加分类
const addSubType = async () => {
  if (!subTypeFormRef.value) return;
  
  try {
    await subTypeFormRef.value.validate();
  } catch (error) {
    console.error('分类表单验证失败:', error);
    ElMessage.error('请完善分类信息');
    return;
  }
  
  try {
    subTypeLoading.value = true;
    await addMenu(addSubTypeForm.value);
    ElMessage.success('分类添加成功');
    addSubTypeDialog.value = false;
    addSubTypeForm.value = { name: '', icon: '' };
  } catch (error) {
    console.error('添加分类失败:', error);
    ElMessage.error('添加分类失败：' + (error.message || '网络错误'));
  } finally {
    subTypeLoading.value = false;
  }
};

// 重置表单
const resetForm = () => {
  projectForm.value = {
    name: '',
    group_name: '', // 新增：重置分组名称
    remark: '',
    has_params: false,
    selectedConnectPools: [],
    params: [
      {
        show_name: '',
        name: '',
        keys: '',
        default: '',
        is_show: true
      }
    ],
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

// 页面挂载时获取列表和脚本依赖选项
onMounted(() => {
  getToolList();
  fetchScriptDepsOptions();
});
</script>

<style scoped>
/* 原有样式保持不变，新增以下样式 */
.param-tip {
  margin-top: 8px;
  margin-left: 16px;
  font-size: 12px;
  color: #94a3b8;
}

/* 增强必填标记样式 */
:deep(.param-header .required-mark) {
  color: #f56c6c;
  margin-left: 4px;
  font-size: 12px;
}

/* 参数项验证错误样式 */
:deep(.el-form-item.is-error .table-input .el-input__wrapper) {
  border-color: #f56c6c !important;
}

:deep(.el-form-item.is-error .table-input .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgba(245, 108, 108, 0.2) !important;
}

/* 其他原有样式... */
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

/* 启用参数行 - 水平对齐优化 */
.switch-row {
  align-items: center !important;
  min-height: 40px;
}

.switch-field {
  display: flex;
  align-items: center;
  height: 40px;
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

/* 启用参数标签取消顶部内边距，保证水平对齐 */
.switch-row .form-label {
  padding-top: 0 !important;
}

.form-field {
  flex: 1;
}

/* 输入框样式 */
.custom-input,
.custom-textarea,
.custom-select {
  width: 100%;
}

/* 工具备注输入框 - 增加边框展示 */
.custom-textarea {
  border: 1px solid rgba(59, 130, 246, 0.4) !important;
  border-radius: 6px !important;
}

/* 参数表格样式 */
.params-table-wrapper {
  margin-top: 16px;
  margin-bottom: 24px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  overflow: hidden;
}

.table-container {
  overflow-x: auto;
}

.params-table {
  width: 100%;
  border-collapse: collapse;
  background-color: rgba(30, 41, 59, 0.3);
}

.param-header {
  background-color: rgba(30, 41, 59, 0.8) !important;
  color: #94a3b8;
  font-weight: 500;
  text-align: left;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  white-space: nowrap;
  vertical-align: middle;
}

/* 修复问题2：操作列头单独样式 */
.operation-header {
  text-align: center !important;
}

.param-cell {
  padding: 20px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  background-color: rgba(30, 41, 59, 0.2);
  vertical-align: middle;
}

.param-cell:last-child {
  border-right: none;
}

/* 修复问题2：操作列样式优化 */
.param-cell.actions {
  min-width: 140px;
  text-align: center;
  padding: 0;
}

.table-input {
  width: 100%;
}

.switch-cell {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  min-height: 32px;
}

/* 修复问题2：操作按钮容器样式 */
.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 14px 16px;
  box-sizing: border-box;
}

.action-btn {
  padding: 4px 8px;
  font-size: 12px;
}

.action-btn.add-btn {
  color: #409eff;
}

.action-btn.delete-btn {
  color: #f56c6c;
}

/* 提示信息样式 */
.tips-section {
  background-color: rgba(59, 130, 246, 0.05);
  border-radius: 6px;
  padding: 14px 16px;
  border-left: 4px solid rgba(59, 130, 246, 0.6);
  margin-bottom: 24px;
}

.tip-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.tip-icon {
  color: #409eff;
  font-size: 18px;
  padding-top: 2px;
}

.tip-text {
  flex: 1;
  color: #9ca3af;
  font-size: 14px;
  line-height: 1.5;
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

.custom-coder {
  border-radius: 4px;
  overflow: hidden;
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

/* 表格输入框样式 */
:deep(.table-input .el-input__wrapper) {
  background-color: rgba(15, 23, 42, 0.8) !important;
  border: 1px solid rgba(255, 255, 255, 0.05) !important;
}

:deep(.table-input .el-input__wrapper:hover) {
  border-color: rgba(59, 130, 246, 0.3) !important;
}

:deep(.table-input .el-input__wrapper.is-focus) {
  border-color: rgba(59, 130, 246, 0.6) !important;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.1) !important;
}

/* 去掉工具备注输入框右下角的字数统计标识 */
:deep(.custom-textarea .el-input__count),
:deep(.custom-textarea .el-textarea__count) {
  display: none !important;
}

/* 选择器样式 - 脚本依赖下拉框黑色背景 */
:deep(.custom-select .el-select__wrapper) {
  background-color: rgba(30, 41, 59, 0.6) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #e5e7eb !important;
  border-radius: 4px !important;
  box-shadow: none !important;
  transition: all 0.2s ease !important;
  min-height: 32px !important;
}

:deep(.custom-select .el-select__wrapper:hover) {
  border-color: rgba(59, 130, 246, 0.4) !important;
  background-color: rgba(30, 41, 59, 0.8) !important;
}

:deep(.custom-select .el-select__wrapper.is-focused) {
  border-color: rgba(59, 130, 246, 0.8) !important;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2) !important;
  background-color: rgba(30, 41, 59, 0.9) !important;
}

/* 移除选中标签的白色背景 */
:deep(.custom-select .el-select__tags) {
  background-color: transparent !important;
  padding: 2px 4px !important;
}

:deep(.custom-select .el-select__tags .el-tag) {
  background-color: rgba(30, 41, 59, 0.9) !important;
  border: 1px solid rgba(59, 130, 246, 0.4) !important;
  color: #e5e7eb !important;
  margin: 2px 4px 2px 0 !important;
  padding: 0 8px !important;
  height: 24px !important;
  line-height: 24px !important;
  border-radius: 4px !important;
}

/* 特别修改 .el-tag__content 的样式 */
:deep(.custom-select .el-select__tags .el-tag .el-tag__content) {
  color: #e5e7eb !important;
  background-color: transparent !important;
}

:deep(.custom-select .el-select__tags .el-tag .el-tag__close) {
  color: #9ca3af !important;
  margin-left: 4px !important;
  background-color: transparent !important;
}

:deep(.custom-select .el-select__tags .el-tag .el-tag__close:hover) {
  color: #e5e7eb !important;
  background-color: transparent !important;
}

/* 修复多选时输入框的背景色 */
:deep(.custom-select .el-select__input) {
  background-color: transparent !important;
  color: #e5e7eb !important;
}

/* 开关样式 */
:deep(.el-switch__core) {
  background-color: rgba(75, 85, 99, 0.6) !important;
  border-color: rgba(75, 85, 99, 0.6) !important;
  transition: all 0.2s ease;
}

:deep(.el-switch.is-checked .el-switch__core) {
  background-color: rgba(59, 130, 246, 0.8) !important;
  border-color: rgba(59, 130, 246, 0.8) !important;
}

/* Coder组件样式 */
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

/* 脚本编辑器验证样式 */
:deep(.el-form-item.is-error .custom-coder .code-editor) {
  border-color: #f56c6c !important;
}

/* 分页组件样式优化 */
:deep(.a-pagination .ant-pagination-item) {
  background-color: rgba(30, 41, 59, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

:deep(.a-pagination .ant-pagination-item a) {
  color: #d1d5db;
}

:deep(.a-pagination .ant-pagination-item:hover) {
  border-color: rgba(59, 130, 246, 0.4);
  background-color: rgba(30, 41, 59, 0.8);
}

:deep(.a-pagination .ant-pagination-item-active) {
  background-color: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.6);
}

:deep(.a-pagination .ant-pagination-item-active a) {
  color: #60a5fa;
}

:deep(.a-pagination .ant-pagination-prev .ant-pagination-item-link),
:deep(.a-pagination .ant-pagination-next .ant-pagination-item-link) {
  background-color: rgba(30, 41, 59, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
  color: #d1d5db;
}

:deep(.a-pagination .ant-pagination-options .ant-select-selector) {
  background-color: rgba(30, 41, 59, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
  color: #d1d5db;
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

/* 修复问题1：参数表格中el-form-item样式调整，确保垂直居中 */
:deep(.param-form-item) {
  margin-bottom: 0 !important;
  height: 100% !important;
  display: flex !important;
  align-items: center !important;
}

:deep(.param-form-item .el-form-item__content) {
  display: flex !important;
  align-items: center !important;
  height: 100% !important;
  margin-left: 0 !important;
  width: 100% !important;
}

:deep(.param-form-item .el-form-item__content .el-input) {
  width: 100% !important;
}

/* 修复问题1：确保表格单元格中的所有内容垂直居中 */
:deep(.param-cell) {
  vertical-align: middle !important;
}

:deep(.param-cell .el-input) {
  vertical-align: middle !important;
}

/* 修复问题2：脚本依赖选择器placeholder颜色 */
:deep(.custom-select .el-select__placeholder) {
  color: #9ca3af !important;
  font-weight: 400 !important;
}

:deep(.custom-select .el-select__input::placeholder) {
  color: #9ca3af !important;
  font-weight: 400 !important;
}
</style>

<style>
/* 脚本依赖下拉框全局样式 */
.script-deps-dropdown.el-select-dropdown {
  background-color: #121826 !important;
  border: 1px solid rgba(59, 130, 246, 0.3) !important;
  color: #e5e7eb !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
  --el-select-dropdown-bg-color: #121826 !important;
}

.script-deps-dropdown .el-select-dropdown__empty {
  background-color: #121826 !important;
  color: #9ca3af !important;
}

/* 下拉框选项文字水平居中展示 */
.script-deps-dropdown .el-select-dropdown__item {
  color: #e5e7eb !important;
  transition: all 0.2s ease !important;
  padding: 8px 16px !important;
  background-color: transparent !important;
  text-align: center !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.script-deps-dropdown .el-select-dropdown__item:hover {
  background-color: rgba(59, 130, 246, 0.15) !important;
  color: #93c5fd !important;
}

/* 移除选中枚举值在下拉列表中的背景色 */
.script-deps-dropdown .el-select-dropdown__item.selected {
  background-color: rgba(15, 23, 42, 0.8) !important;
  color: #60a5fa !important;
  font-weight: 500 !important;
  border-radius: 4px !important;
}

.script-deps-dropdown .el-select-dropdown__item.hover {
  background-color: rgba(59, 130, 246, 0.1) !important;
}

.script-deps-dropdown .el-select-dropdown__item.is-disabled {
  color: #6b7280 !important;
}

.script-deps-dropdown .el-select-dropdown__item.is-disabled:hover {
  background-color: transparent !important;
}

/* 针对多选标签的全局样式覆盖 */
.el-tag {
  --el-tag-bg-color: rgba(30, 41, 59, 0.9) !important;
  --el-tag-border-color: rgba(59, 130, 246, 0.4) !important;
  --el-tag-text-color: #e5e7eb !important;
  --el-tag-hover-color: #e5e7eb !important;
}

.el-tag.el-tag--info {
  background-color: rgba(30, 41, 59, 0.9) !important;
  border-color: rgba(59, 130, 246, 0.4) !important;
  color: #e5e7eb !important;
}

.el-tag.el-tag--info .el-tag__content {
  color: #e5e7eb !important;
}

/* 滚动条样式 */
.script-deps-dropdown .el-select-dropdown__wrap {
  scrollbar-width: thin !important;
  scrollbar-color: rgba(59, 130, 246, 0.3) #121826 !important;
}

.script-deps-dropdown .el-select-dropdown__wrap::-webkit-scrollbar {
  width: 6px !important;
}

.script-deps-dropdown .el-select-dropdown__wrap::-webkit-scrollbar-track {
  background: #121826 !important;
}

.script-deps-dropdown .el-select-dropdown__wrap::-webkit-scrollbar-thumb {
  background-color: rgba(59, 130, 246, 0.3) !important;
  border-radius: 3px !important;
}

.script-deps-dropdown .el-select-dropdown__wrap::-webkit-scrollbar-thumb:hover {
  background-color: rgba(59, 130, 246, 0.5) !important;
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

/* 全局修复：确保所有选择器placeholder为浅灰色 */
.el-select .el-select__placeholder {
  color: #9ca3af !important;
  font-weight: 400 !important;
}

.el-select .el-input__inner::placeholder {
  color: #9ca3af !important;
  font-weight: 400 !important;
}
</style>