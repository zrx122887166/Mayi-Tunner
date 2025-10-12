<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { FormInstance } from '@arco-design/web-vue'
import { Message } from '@arco-design/web-vue'
import { IconClose, IconUserGroup, IconPlus, IconMinus } from '@arco-design/web-vue/es/icon'
import { getProjects, createProject, updateProject, deleteProject, addProjectMember, removeProjectMember, getAvailableUsers, getProject, type Project, type CreateProjectParams, type UpdateProjectParams, type AvailableUser } from '@/api/project'

const loading = ref(false)
const projects = ref<Project[]>([])
const searchKeyword = ref('')
const visible = ref(false)
const formRef = ref<FormInstance>()

const pagination = ref({
  current: 1,
  pageSize: 20,  // 默认每页显示20条
  total: 0,
  showTotal: true,
  showJumper: true,
  showPageSize: true
})

const formData = reactive<CreateProjectParams>({
  name: '',
  description: ''
})

const rules = {
  name: [
    { required: true, message: '请输入项目名称' },
    { minLength: 2, message: '项目名称至少2个字符' }
  ],
  description: []
}

const handleSearch = (value: string) => {
  pagination.value.current = 1  // 重置页码
  fetchProjects(1, value)
}

const handlePageChange = (current: number) => {
  pagination.value.current = current
  fetchProjects(current, searchKeyword.value)
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  pagination.value.current = 1  // 重置到第一页
  fetchProjects(1, searchKeyword.value)
}

const handleCreateProject = () => {
  visible.value = true
}

const handleCancel = () => {
  visible.value = false
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true
    await createProject(formData)
    Message.success('创建项目成功')
    visible.value = false
    formRef.value?.resetFields()
    fetchProjects(pagination.value.current, searchKeyword.value)
  } catch (error: any) {
    console.error('创建项目错误:', error)
    Message.error(error?.message || '创建项目失败')
  } finally {
    loading.value = false
  }
}

const editVisible = ref(false)
const editRecord = ref<Project | null>(null)
const editFormRef = ref<FormInstance>()

const editFormData = reactive<UpdateProjectParams>({
  name: '',
  description: ''
})

const handleEdit = (record: Project) => {
  editRecord.value = record
  editFormData.name = record.name
  editFormData.description = record.description
  editVisible.value = true
}

const handleEditCancel = () => {
  editVisible.value = false
  editRecord.value = null
  editFormRef.value?.resetFields()
}

const handleEditSubmit = async () => {
  if (!editRecord.value) return
  
  try {
    await editFormRef.value?.validate()
    loading.value = true
    await updateProject(editRecord.value.id, editFormData)
    Message.success('更新项目成功')
    editVisible.value = false
    fetchProjects(pagination.value.current, searchKeyword.value)
  } catch (error: any) {
    console.error('更新项目错误:', error)
    Message.error(error?.message || '更新项目失败')
  } finally {
    loading.value = false
  }
}

const deleteVisible = ref(false)
const deleteRecord = ref<Project | null>(null)

const showDeleteConfirm = (record: Project) => {
  deleteRecord.value = record
  deleteVisible.value = true
}

const handleDeleteCancel = () => {
  deleteVisible.value = false
  deleteRecord.value = null
}

const handleDeleteConfirm = async () => {
  if (!deleteRecord.value) return
  
  try {
    loading.value = true
    await deleteProject(deleteRecord.value.id)
    Message.success('删除项目成功')
    fetchProjects(pagination.value.current, searchKeyword.value)
    deleteVisible.value = false
  } catch (error: any) {
    console.error('删除项目错误:', error)
    Message.error(error?.message || '删除项目失败')
  } finally {
    loading.value = false
  }
}

const handleDelete = (record: Project) => {
  showDeleteConfirm(record)
}

const fetchProjects = async (page: number = 1, search: string = '') => {
  loading.value = true
  try {
    const response = await getProjects(page, pagination.value.pageSize, search)
    console.log('API Response:', response) // 调试日志
    projects.value = response.data.results
    pagination.value.total = response.data.count
  } catch (error: any) {
    console.error('获取项目列表失败:', error)
    Message.error(error?.message || '获取项目列表失败')
  } finally {
    loading.value = false
  }
}

// 初始加载
fetchProjects(1)

// 添加成员管理相关的状态
const memberVisible = ref(false)
const memberRecord = ref<Project | null>(null)
const selectedMembers = ref<number[]>([])
const availableUsers = ref<AvailableUser[]>([])
const memberLoading = ref(false)
const memberSearchKeyword = ref('')
const memberPagination = ref({
  current: 1,
  pageSize: 10,
  total: 0
})

// 获取可用用户列表
const fetchAvailableUsers = async (projectId: number, page: number = 1, search: string = '') => {
  try {
    memberLoading.value = true
    const response = await getAvailableUsers(projectId, page, memberPagination.value.pageSize, search)
    availableUsers.value = response.data.results
    memberPagination.value.total = response.data.count
  } catch (error: any) {
    console.error('获取可用用户列表失败:', error)
    Message.error(error?.message || '获取可用用户列表失败')
  } finally {
    memberLoading.value = false
  }
}

// 修改成员管理相关的处理函数
const handleMemberManage = async (record: Project) => {
  memberRecord.value = record
  memberVisible.value = true  // 先显示弹窗
  memberSearchKeyword.value = ''  // 重置搜索关键词
  memberPagination.value.current = 1  // 重置页码
  
  try {
    memberLoading.value = true
    // 获取最新的项目详情
    const response = await getProject(record.id)
    memberRecord.value = response.data
    selectedMembers.value = response.data.members.map(member => member.id)
    // 获取可用用户列表
    await fetchAvailableUsers(record.id)
  } catch (error: any) {
    console.error('获取项目详情失败:', error)
    Message.error(error?.message || '获取项目详情失败')
  } finally {
    memberLoading.value = false
  }
}

const handleMemberSearch = (value: string) => {
  memberSearchKeyword.value = value
  memberPagination.value.current = 1  // 重置页码
  if (memberRecord.value) {
    fetchAvailableUsers(memberRecord.value.id, 1, value)
  }
}

const handleMemberPageChange = (page: number) => {
  memberPagination.value.current = page
  if (memberRecord.value) {
    fetchAvailableUsers(memberRecord.value.id, page, memberSearchKeyword.value)
  }
}

const handleMemberCancel = () => {
  memberVisible.value = false
  memberRecord.value = null
  selectedMembers.value = []
  availableUsers.value = []
}

const handleAddMember = async (userId: number) => {
  if (!memberRecord.value || isNaN(userId)) return
  
  try {
    memberLoading.value = true
    await addProjectMember(memberRecord.value.id, userId)
    Message.success('添加成员成功')
    // 重新获取项目详情以更新成员列表
    const response = await getProject(memberRecord.value.id)
    memberRecord.value = response.data
    selectedMembers.value = response.data.members.map(member => member.id)
    // 重新获取可用用户列表
    await fetchAvailableUsers(memberRecord.value.id, memberPagination.value.current, memberSearchKeyword.value)
  } catch (error: any) {
    console.error('添加成员错误:', error)
    Message.error(error?.message || '添加成员失败')
  } finally {
    memberLoading.value = false
  }
}

const handleRemoveMember = async (userId: number) => {
  if (!memberRecord.value) return
  
  try {
    memberLoading.value = true
    await removeProjectMember(memberRecord.value.id, userId)
    Message.success('移除成员成功')
    // 重新获取项目详情以更新成员列表
    const response = await getProject(memberRecord.value.id)
    memberRecord.value = response.data
    selectedMembers.value = response.data.members.map(member => member.id)
    // 重新获取可用用户列表
    await fetchAvailableUsers(memberRecord.value.id)
  } catch (error: any) {
    console.error('移除成员错误:', error)
    Message.error(error?.message || '移除成员失败')
  } finally {
    memberLoading.value = false
  }
}
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-gap-4 tw-p-4">
    <!-- 搜索区域 -->
    <div class="tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-p-6 tw-flex tw-justify-between tw-items-center">
      <a-input-search
        v-model="searchKeyword"
        placeholder="搜索项目名称"
        class="tw-w-64"
        allow-clear
        @search="handleSearch"
        @press-enter="handleSearch(searchKeyword)"
        @clear="handleSearch('')"
        aria-label="搜索项目"
      />
      <a-button type="primary" class="custom-add-button" @click="handleCreateProject">
        新增项目
      </a-button>
    </div>

    <!-- 表格区域 -->
    <div class="tw-flex-1 tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-overflow-hidden tw-flex tw-items-center tw-justify-center">
      <div v-if="!projects.length && !loading" class="tw-flex tw-flex-col tw-items-center tw-justify-center tw-p-8 tw-text-center">
        <div class="tw-text-8xl tw-mb-6 tw-text-gray-600">
          <icon-plus class="tw-opacity-50" />
        </div>
        <h2 class="tw-text-2xl tw-font-medium tw-mb-2 tw-text-gray-300">还没有项目</h2>
        <p class="tw-text-gray-500 tw-mb-8 tw-text-center tw-max-w-md">
          项目是进行接口测试的基本单位，您需要先创建一个项目才能开始使用接口测试功能
        </p>
        <a-button type="primary" size="large" class="custom-add-button" @click="handleCreateProject">
          创建您的第一个项目
        </a-button>
      </div>

      <div v-else class="tw-w-full tw-h-full">
        <a-spin :loading="loading" dot class="tw-h-full">
          <a-table
            :data="projects"
            :loading="loading"
            :pagination="false"
            :scroll="{ y: 'calc(100vh - 320px)' }"
            class="custom-table"
            aria-label="项目列表"
          >
            <template #columns>
              <a-table-column title="ID" data-index="id" :width="70" />
              <a-table-column title="项目名称" data-index="name" />
              <a-table-column title="描述" data-index="description" />
              <a-table-column title="创建者" data-index="creator">
                <template #cell="{ record }">
                  {{ record.creator.username }}
                </template>
              </a-table-column>
              <a-table-column title="成员数" data-index="members" align="center">
                <template #cell="{ record }">
                  {{ record.members.length }}
                </template>
              </a-table-column>
              <a-table-column title="创建时间" data-index="created_at" />
              <a-table-column title="更新时间" data-index="updated_at" />
              <a-table-column title="操作" align="center" :width="240">
                <template #cell="{ record }">
                  <div class="tw-flex tw-justify-center tw-gap-2">
                    <a-button type="primary" size="small" class="btn-member" @click="handleMemberManage(record)" aria-label="成员管理">
                      <template #icon>
                        <icon-user-group />
                      </template>
                      成员
                    </a-button>
                    <a-button type="primary" size="small" class="btn-edit" @click="handleEdit(record)" aria-label="编辑项目">
                      编辑
                    </a-button>
                    <a-button type="primary" size="small" class="btn-delete" @click="handleDelete(record)" aria-label="删除">
                      删除
                    </a-button>
                  </div>
                </template>
              </a-table-column>
            </template>
          </a-table>
        </a-spin>
      </div>
    </div>

    <!-- 分页区域 -->
    <div class="tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-p-6">
      <a-pagination
        v-model:current="pagination.current"
        v-model:pageSize="pagination.pageSize"
        :total="pagination.total"
        show-total
        show-jumper
        show-page-size
        class="tw-flex tw-justify-end"
        @change="handlePageChange"
        @page-size-change="handlePageSizeChange"
        aria-label="分页导航"
      />
    </div>

    <!-- 创建项目卡片 -->
    <div v-if="visible" class="tw-fixed tw-inset-0 tw-z-50 tw-flex tw-items-center tw-justify-center">
      <div class="tw-fixed tw-inset-0 tw-bg-black/60 tw-backdrop-blur-sm" @click="handleCancel"></div>
      <a-card 
        :bordered="false"
        class="tw-w-[500px] tw-z-10 !tw-bg-gray-800 !tw-border-gray-700"
      >
        <template #title>
          <div class="tw-flex tw-justify-between tw-items-center">
            <span class="tw-text-gray-100">新增项目</span>
            <a-button type="text" @click="handleCancel">
              <template #icon>
                <icon-close />
              </template>
            </a-button>
          </div>
        </template>
        <a-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          layout="vertical"
          autocomplete="off"
        >
          <a-form-item field="name" label="项目名称" validate-trigger="blur">
            <a-input
              v-model="formData.name"
              placeholder="请输入项目名称"
              allow-clear
              aria-label="项目名称输入框"
              autocomplete="off"
            />
          </a-form-item>
          <a-form-item field="description" label="项目描述" validate-trigger="blur">
            <a-textarea
              v-model="formData.description"
              placeholder="请输入项目描述"
              allow-clear
              aria-label="项目描述输入框"
            />
          </a-form-item>
          <div class="tw-flex tw-justify-end tw-gap-2 tw-mt-6">
            <a-button @click="handleCancel" class="tw-w-24" aria-label="取消">取消</a-button>
            <a-button type="primary" :loading="loading" @click="handleSubmit" class="tw-w-24" aria-label="确定">
              确定
            </a-button>
          </div>
        </a-form>
      </a-card>
    </div>

    <!-- 编辑项目卡片 -->
    <div v-if="editVisible" class="tw-fixed tw-inset-0 tw-z-50 tw-flex tw-items-center tw-justify-center">
      <div class="tw-fixed tw-inset-0 tw-bg-black/60 tw-backdrop-blur-sm" @click="handleEditCancel"></div>
      <a-card 
        :bordered="false"
        class="tw-w-[500px] tw-z-10 !tw-bg-gray-800 !tw-border-gray-700"
      >
        <template #title>
          <div class="tw-flex tw-justify-between tw-items-center">
            <span class="tw-text-gray-100">编辑项目</span>
            <a-button type="text" @click="handleEditCancel">
              <template #icon>
                <icon-close />
              </template>
            </a-button>
          </div>
        </template>
        <a-form
          ref="editFormRef"
          :model="editFormData"
          :rules="rules"
          layout="vertical"
        >
          <a-form-item field="name" label="项目名称" validate-trigger="blur">
            <a-input
              v-model="editFormData.name"
              placeholder="请输入项目名称"
              allow-clear
              aria-label="项目名称输入框"
            />
          </a-form-item>
          <a-form-item field="description" label="项目描述" validate-trigger="blur">
            <a-textarea
              v-model="editFormData.description"
              placeholder="请输入项目描述"
              allow-clear
              aria-label="项目描述输入框"
            />
          </a-form-item>
          <div class="tw-flex tw-justify-end tw-gap-2 tw-mt-6">
            <a-button @click="handleEditCancel" class="tw-w-24" aria-label="取消">取消</a-button>
            <a-button type="primary" :loading="loading" @click="handleEditSubmit" class="tw-w-24" aria-label="确定">
              确定
            </a-button>
          </div>
        </a-form>
      </a-card>
    </div>

    <!-- 删除确认卡片 -->
    <div v-if="deleteVisible" class="tw-fixed tw-inset-0 tw-z-50 tw-flex tw-items-center tw-justify-center">
      <div class="tw-fixed tw-inset-0 tw-bg-black/60 tw-backdrop-blur-sm" @click="handleDeleteCancel"></div>
      <a-card 
        :bordered="false"
        class="tw-w-[400px] tw-z-10 !tw-bg-gray-800 !tw-border-gray-700"
      >
        <template #title>
          <div class="tw-flex tw-justify-between tw-items-center">
            <span class="tw-text-gray-100">确认删除</span>
            <a-button type="text" @click="handleDeleteCancel">
              <template #icon>
                <icon-close />
              </template>
            </a-button>
          </div>
        </template>
        <div class="tw-text-gray-300 tw-mb-6">
          确定要删除项目 "{{ deleteRecord?.name }}" 吗？此操作不可恢复。
        </div>
        <div class="tw-flex tw-justify-end tw-gap-2">
          <a-button @click="handleDeleteCancel" class="tw-w-24" aria-label="取消">取消</a-button>
          <a-button type="primary" status="danger" :loading="loading" @click="handleDeleteConfirm" class="tw-w-24" aria-label="确定删除">
            确定删除
          </a-button>
        </div>
      </a-card>
    </div>

    <!-- 成员管理对话框 -->
    <div v-if="memberVisible" class="tw-fixed tw-inset-0 tw-z-50 tw-flex tw-items-center tw-justify-center">
      <div class="tw-fixed tw-inset-0 tw-bg-black/60 tw-backdrop-blur-sm" @click="handleMemberCancel"></div>
      <a-card 
        :bordered="false"
        class="tw-w-[900px] tw-z-10 !tw-bg-gray-800 !tw-border-gray-700"
      >
        <template #title>
          <div class="tw-flex tw-justify-between tw-items-center">
            <span class="tw-text-gray-100">成员管理 - {{ memberRecord?.name }}</span>
            <a-button type="text" @click="handleMemberCancel">
              <template #icon>
                <icon-close />
              </template>
            </a-button>
          </div>
        </template>
        
        <a-spin :loading="memberLoading" dot class="tw-w-full">
          <div class="tw-flex tw-gap-4">
            <!-- 左侧：可添加的成员列表 -->
            <div class="tw-flex-1 tw-bg-gray-700/50 tw-rounded-lg tw-p-4">
              <div class="tw-flex tw-flex-col tw-h-[400px]">
                <div class="tw-text-gray-300 tw-mb-3">可添加成员</div>
                <a-input-search
                  v-model="memberSearchKeyword"
                  placeholder="搜索用户"
                  allow-clear
                  class="tw-mb-3"
                  @search="handleMemberSearch"
                  @press-enter="handleMemberSearch(memberSearchKeyword)"
                  @clear="handleMemberSearch('')"
                />
                <div class="tw-flex-1 tw-overflow-y-auto tw-bg-gray-800/50 tw-rounded-lg tw-p-3">
                  <div class="tw-space-y-2">
                    <div
                      v-for="user in availableUsers"
                      :key="user.id"
                      class="tw-flex tw-items-center tw-justify-between tw-p-2 tw-rounded-lg tw-bg-gray-700/50 hover:tw-bg-gray-600/50 tw-transition-colors tw-cursor-pointer"
                      @click="handleAddMember(user.id)"
                    >
                      <div class="tw-flex tw-flex-col">
                        <span class="tw-text-gray-200">{{ user.username }}</span>
                        <span class="tw-text-xs tw-text-gray-400">{{ user.email || '未设置邮箱' }}</span>
                      </div>
                      <a-button type="outline" size="mini" status="success">
                        <template #icon>
                          <icon-plus />
                        </template>
                        添加
                      </a-button>
                    </div>
                  </div>
                </div>
                <a-pagination
                  v-model:current="memberPagination.current"
                  :total="memberPagination.total"
                  :page-size="memberPagination.pageSize"
                  size="small"
                  class="tw-mt-3"
                  @change="handleMemberPageChange"
                />
              </div>
            </div>

            <!-- 右侧：已添加的成员列表 -->
            <div class="tw-flex-1 tw-bg-gray-700/50 tw-rounded-lg tw-p-4">
              <div class="tw-flex tw-flex-col tw-h-[400px]">
                <div class="tw-text-gray-300 tw-mb-3">已添加成员</div>
                <div class="tw-flex-1 tw-overflow-y-auto tw-bg-gray-800/50 tw-rounded-lg tw-p-3">
                  <div class="tw-space-y-2">
                    <div
                      v-for="member in [...(memberRecord?.members || [])].reverse()"
                      :key="member.id"
                      class="tw-flex tw-items-center tw-justify-between tw-p-2 tw-rounded-lg tw-bg-gray-700/50"
                    >
                      <div class="tw-flex tw-flex-col">
                        <span class="tw-text-gray-200">{{ member.username }}</span>
                        <span class="tw-text-xs tw-text-gray-400">{{ member.email || '未设置邮箱' }}</span>
                      </div>
                      <a-button 
                        v-if="member.id !== memberRecord?.creator.id"
                        type="outline" 
                        size="mini" 
                        status="danger"
                        @click="handleRemoveMember(member.id)"
                      >
                        <template #icon>
                          <icon-minus />
                        </template>
                        移除
                      </a-button>
                      <span 
                        v-else 
                        class="tw-text-xs tw-text-blue-400 tw-px-2 tw-py-1 tw-bg-blue-400/10 tw-rounded"
                      >
                        创建者
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </a-spin>
      </a-card>
    </div>
  </div>
</template>

<style lang="postcss" scoped>
.custom-table {
  @apply tw-h-full;
}

.custom-table :deep(.arco-table) {
  background-color: transparent !important;
}

.custom-table :deep(.arco-table-container) {
  background-color: transparent !important;
  border: none !important;
}

.custom-table :deep(.arco-table-body) {
  background-color: transparent !important;
}

/* 隐藏所有滚动条但保留滚动功能 */
.custom-table :deep(*::-webkit-scrollbar) {
  width: 0 !important;
  height: 0 !important;
  display: none !important;
}

/* Firefox */
.custom-table :deep(*) {
  scrollbar-width: none !important;
}

/* IE 和 Edge */
.custom-table :deep(*) {
  -ms-overflow-style: none !important;
}

/* Arco Design 特定的滚动条组件 */
.custom-table :deep(.arco-scrollbar__bar) {
  opacity: 0 !important;
  display: none !important;
}

.custom-table :deep(.arco-table-header) {
  background-color: rgba(30, 41, 59, 0.5) !important;
  position: sticky;
  top: 0;
  z-index: 2;
}

.custom-table :deep(.arco-table-content) {
  background-color: transparent !important;
}

.custom-table :deep(.arco-spin) {
  @apply tw-h-full tw-flex tw-flex-col;
}

.custom-table :deep(.arco-spin-children) {
  @apply tw-h-full tw-flex tw-flex-col;
}

/* 分页样式 */
:deep(.arco-pagination) {
  .arco-pagination-item {
    border-radius: 6px !important;
    color: #94a3b8 !important;
    background-color: transparent !important;
    
    &:hover {
      color: #60a5fa !important;
      background-color: rgba(59, 130, 246, 0.1) !important;
    }
    
    &.arco-pagination-item-active {
      background-color: rgba(59, 130, 246, 0.2) !important;
      color: #60a5fa !important;
    }
  }

  .arco-pagination-jumper {
    .arco-input {
      border-radius: 6px !important;
      background-color: rgba(30, 41, 59, 0.5) !important;
      border-color: rgba(148, 163, 184, 0.1) !important;
      color: #e2e8f0 !important;

      &:hover, &:focus {
        border-color: #60a5fa !important;
      }
    }
  }

  .arco-pagination-total {
    color: #94a3b8 !important;
  }
}

/* 搜索框样式 */
:deep(.arco-input-wrapper) {
  background-color: rgba(30, 41, 59, 0.5) !important;
  border-color: rgba(148, 163, 184, 0.1) !important;

  &:hover, &:focus-within {
    border-color: #60a5fa !important;
  }

  .arco-input {
    color: #e2e8f0 !important;
  }

  .arco-input-prefix, .arco-input-suffix {
    color: #94a3b8 !important;
  }
}

/* 按钮样式 */
:deep(.btn-edit) {
  background: linear-gradient(to right, #728bb4, #2563eb) !important;
  border: none !important;
  
  &:hover {
    background: linear-gradient(to right, #6181c2, #2563eb) !important;
  }
}

:deep(.btn-delete) {
  background: linear-gradient(to right, #4549ed, #ff6464) !important;
  border: none !important;
  
  &:hover {
    background: linear-gradient(to right, #ff6464, #4549ed) !important;
  }
}

:deep(.btn-member) {
  background: linear-gradient(to right, #5a53a8, #3f39ab) !important;
  border: none !important;
  color: #ffffff !important;
  
  &:hover {
    background: linear-gradient(to right, #4338ca, #4f46e5) !important;
  }
}

.custom-add-button {
  background: linear-gradient(to right, #3b82f6 ,#1d4ed8);
  border: none;
  padding: 0 24px;
  height: 36px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    background: linear-gradient(to right, #2563eb, #60a5fa);
  }

  &:active {
    transform: translateY(1px);
    box-shadow: 0 1px 3px rgba(59, 130, 246, 0.3);
  }
}
</style> 