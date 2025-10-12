<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useUserStore } from '@/stores/user'
import type { TableRowSelection, FormInstance } from '@arco-design/web-vue'
import { Message } from '@arco-design/web-vue'
import { IconUser, IconLock, IconEmail, IconPhone, IconClose } from '@arco-design/web-vue/es/icon'
import { getUsers, createUser, deleteUser, updateUser, type CreateUserParams, type UpdateUserParams } from '@/api/user'

interface User {
  id: number
  username: string
  email: string
  phone: string
  is_active: boolean
  is_staff: boolean
  date_joined: string
  avatar: string | null
}

interface PaginatedResponse<T> {
  count: number
  results: T[]
}

const userStore = useUserStore()
const loading = ref(false)
const users = ref<User[]>([])
const searchKeyword = ref('')
const selectedKeys = ref<(string | number)[]>([])
const visible = ref(false)
const formRef = ref<FormInstance>()

const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0
})

const formData = reactive<CreateUserParams>({
  username: '',
  password: '',
  email: '',
  phone: '',
  avatar: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名' },
    { minLength: 3, message: '用户名至少3个字符' }
  ],
  password: [
    { required: true, message: '请输入密码' },
    { minLength: 6, message: '密码至少6个字符' }
  ],
  email: [
    { type: 'email' as const, message: '请输入正确的邮箱格式' }
  ],
  phone: [
    { match: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式' }
  ]
}

const rowSelection = {
  type: 'checkbox',
  showCheckedAll: true,
  selectedRowKeys: selectedKeys.value,
  onRowSelect: (rowKeys: (string | number)[]) => {
    selectedKeys.value = rowKeys
  }
} as TableRowSelection

const handleSearch = (value: string) => {
  pagination.value.current = 1  // 重置页码
  fetchUsers(1, value)
}

const handlePageChange = (current: number) => {
  pagination.value.current = current
  fetchUsers(current, searchKeyword.value)
}

const handleAddUser = () => {
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
    await createUser(formData)
    Message.success('创建用户成功')
    visible.value = false
    formRef.value?.resetFields()
    fetchUsers(pagination.value.current, searchKeyword.value)
  } catch (error: any) {
    // 处理验证错误
    if (error?.message && typeof error.message === 'object') {
      // 显示第一个错误消息
      const firstError = Object.values(error.message)[0]
      if (Array.isArray(firstError)) {
        Message.error(firstError[0])
      }
    } else {
      console.error('创建用户错误:', error)
      Message.error(error?.message || '创建用户失败')
    }
  } finally {
    loading.value = false
  }
}

const editVisible = ref(false)
const editRecord = ref<User | null>(null)
const editFormRef = ref<FormInstance>()

const editFormData = reactive<UpdateUserParams>({
  username: '',
  password: '',
  email: '',
  phone: '',
  avatar: '',
  is_active: true,
  is_staff: false
})

const editRules = {
  email: [
    { type: 'email' as const, message: '请输入正确的邮箱格式' }
  ],
  phone: [
    { match: /^1[3-9]\d{9}$/, message: '请输入正确的手机号格式' }
  ]
}

const handleEdit = (record: User) => {
  editRecord.value = record
  editFormData.username = record.username
  editFormData.email = record.email || ''
  editFormData.phone = record.phone || ''
  editFormData.avatar = record.avatar || ''
  editFormData.is_active = record.is_active
  editFormData.is_staff = record.is_staff
  editVisible.value = true
}

const handleEditCancel = () => {
  editVisible.value = false
  editRecord.value = null
  editFormRef.value?.resetFields()
  // 重置密码字段
  editFormData.password = ''
}

const handleEditSubmit = async () => {
  if (!editRecord.value) return
  
  try {
    await editFormRef.value?.validate()
    loading.value = true

    // 仅在密码不为空时才发送密码
    const updateData: UpdateUserParams = { ...editFormData }
    if (!updateData.password) {
      delete updateData.password
    }

    await updateUser(editRecord.value.id, updateData)
    Message.success('更新用户成功')
    editVisible.value = false
    // 重新加载当前页数据
    fetchUsers(pagination.value.current, searchKeyword.value)
  } catch (error: any) {
    if (error?.message && typeof error.message === 'object') {
      const firstError = Object.values(error.message)[0]
      if (Array.isArray(firstError)) {
        Message.error(firstError[0])
      }
    } else {
      console.error('更新用户错误:', error)
      Message.error(error?.message || '更新用户失败')
    }
  } finally {
    loading.value = false
  }
}

const deleteVisible = ref(false)
const deleteRecord = ref<User | null>(null)

const showDeleteConfirm = (record: User) => {
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
    await deleteUser(deleteRecord.value.id)
    Message.success('删除用户成功')
    // 重新加载当前页数据
    fetchUsers(pagination.value.current, searchKeyword.value)
    deleteVisible.value = false
  } catch (error: any) {
    console.error('删除用户错误:', error)
    Message.error(error?.message || '删除用户失败')
  } finally {
    loading.value = false
  }
}

const handleDelete = (record: User) => {
  showDeleteConfirm(record)
}

const fetchUsers = async (page: number = 1, keyword: string = '') => {
  loading.value = true
  try {
    const response = await getUsers(page, pagination.value.pageSize, keyword)
    const data = response.data as PaginatedResponse<User>
    users.value = data.results
    pagination.value.total = data.count
  } catch (error) {
    console.error('获取用户列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 初始加载
fetchUsers(1)
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-gap-4 tw-p-4">
    <!-- 搜索区域 -->
    <div class="tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-px-6 tw-py-5 tw-flex tw-justify-between tw-items-center">
      <a-input-search
        v-model="searchKeyword"
        placeholder="搜索用户名/邮箱"
        class="tw-w-64"
        allow-clear
        @search="handleSearch"
        @press-enter="handleSearch(searchKeyword)"
        @clear="handleSearch('')"
        aria-label="搜索用户"
      />
      <a-button type="primary" @click="handleAddUser">
        新增用户
      </a-button>
    </div>

    <!-- 表格区域 -->
    <div class="tw-flex-1 tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-overflow-hidden tw-flex tw-flex-col">
      <div class="tw-px-6 tw-py-5 tw-flex-1">
        <a-spin :loading="loading" dot>
          <a-table
            :data="users"
            :loading="false"
            :pagination="false"
            :row-selection="rowSelection"
            :scroll="{ y: 'calc(100vh - 340px)' }"
            class="custom-table"
            aria-label="用户列表"
          >
            <template #columns>
              <a-table-column title="用户名" data-index="username" />
              <a-table-column title="邮箱" data-index="email" />
              <a-table-column title="手机号" data-index="phone" />
              <a-table-column title="管理员" data-index="is_staff">
                <template #cell="{ record }">
                  <a-tag :color="record.is_staff ? 'gold' : 'gray'">
                    {{ record.is_staff ? '是' : '否' }}
                  </a-tag>
                </template>
              </a-table-column>
              <a-table-column title="状态" data-index="is_active">
                <template #cell="{ record }">
                  <a-tag :color="record.is_active ? 'green' : 'red'">
                    {{ record.is_active ? '启用' : '禁用' }}
                  </a-tag>
                </template>
              </a-table-column>
              <a-table-column title="创建时间" data-index="date_joined" />
              <a-table-column title="操作" align="center">
                <template #cell="{ record }">
                  <div class="tw-flex tw-justify-center tw-gap-2">
                    <a-button type="primary" size="small" class="btn-edit" @click="handleEdit(record)" aria-label="编辑用户">
                      编辑
                    </a-button>
                    <a-button type="primary" size="small" class="btn-delete" @click="handleDelete(record)" aria-label="删除用户">
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
    <div class="tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-px-6 tw-py-5">
      <a-pagination
        v-model:current="pagination.current"
        v-model:pageSize="pagination.pageSize"
        :total="pagination.total"
        show-total
        show-jumper
        show-page-size
        class="tw-flex tw-justify-end"
        @change="handlePageChange"
        aria-label="分页导航"
      />
    </div>

    <!-- 新增用户卡片 -->
    <div v-if="visible" class="tw-fixed tw-inset-0 tw-z-50 tw-flex tw-items-center tw-justify-center">
      <div class="tw-fixed tw-inset-0 tw-bg-black/60 tw-backdrop-blur-sm" @click="handleCancel"></div>
      <a-card 
        :bordered="false"
        class="tw-w-[500px] tw-z-10 !tw-bg-gray-800 !tw-border-gray-700"
      >
        <template #title>
          <div class="tw-flex tw-justify-between tw-items-center">
            <span class="tw-text-gray-100">新增用户</span>
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
          <a-form-item field="username" label="用户名" validate-trigger="blur">
            <a-input
              v-model="formData.username"
              placeholder="请输入用户名"
              allow-clear
              aria-label="用户名输入框"
              autocomplete="off"
            >
              <template #prefix>
                <icon-user />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item field="password" label="密码" validate-trigger="blur">
            <a-input-password
              v-model="formData.password"
              placeholder="请输入密码"
              allow-clear
              aria-label="密码输入框"
              autocomplete="new-password"
            >
              <template #prefix>
                <icon-lock />
              </template>
            </a-input-password>
          </a-form-item>
          <a-form-item field="email" label="邮箱" validate-trigger="blur">
            <a-input
              v-model="formData.email"
              placeholder="请输入邮箱"
              allow-clear
              aria-label="邮箱输入框"
              autocomplete="off"
            >
              <template #prefix>
                <icon-email />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item field="phone" label="手机号" validate-trigger="blur">
            <a-input
              v-model="formData.phone"
              placeholder="请输入手机号"
              allow-clear
              aria-label="手机号输入框"
              autocomplete="off"
            >
              <template #prefix>
                <icon-phone />
              </template>
            </a-input>
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
          确定要删除用户 "{{ deleteRecord?.username }}" 吗？此操作不可恢复。
        </div>
        <div class="tw-flex tw-justify-end tw-gap-2">
          <a-button @click="handleDeleteCancel" class="tw-w-24" aria-label="取消">取消</a-button>
          <a-button type="primary" status="danger" :loading="loading" @click="handleDeleteConfirm" class="tw-w-24" aria-label="确定删除">
            确定删除
          </a-button>
        </div>
      </a-card>
    </div>

    <!-- 编辑用户卡片 -->
    <div v-if="editVisible" class="tw-fixed tw-inset-0 tw-z-50 tw-flex tw-items-center tw-justify-center">
      <div class="tw-fixed tw-inset-0 tw-bg-black/60 tw-backdrop-blur-sm" @click="handleEditCancel"></div>
      <a-card 
        :bordered="false"
        class="tw-w-[500px] tw-z-10 !tw-bg-gray-800 !tw-border-gray-700"
      >
        <template #title>
          <div class="tw-flex tw-justify-between tw-items-center">
            <span class="tw-text-gray-100">编辑用户</span>
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
          :rules="editRules"
          layout="vertical"
        >
          <a-form-item field="username" label="用户名" validate-trigger="blur">
            <a-input
              v-model="editFormData.username"
              placeholder="请输入用户名"
              allow-clear
              aria-label="用户名输入框"
              disabled
            >
              <template #prefix>
                <icon-user />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item v-if="userStore.userInfo?.is_staff" field="password" label="新密码（可选）" validate-trigger="blur">
            <a-input-password
              v-model="editFormData.password"
              placeholder="留空则不修改密码"
              allow-clear
              aria-label="新密码输入框"
              autocomplete="new-password"
            >
              <template #prefix>
                <icon-lock />
              </template>
            </a-input-password>
          </a-form-item>
          <a-form-item field="email" label="邮箱" validate-trigger="blur">
            <a-input
              v-model="editFormData.email"
              placeholder="请输入邮箱"
              allow-clear
              aria-label="邮箱输入框"
            >
              <template #prefix>
                <icon-email />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item field="phone" label="手机号" validate-trigger="blur">
            <a-input
              v-model="editFormData.phone"
              placeholder="请输入手机号"
              allow-clear
              aria-label="手机号输入框"
            >
              <template #prefix>
                <icon-phone />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item field="is_active" label="状态">
            <a-switch
              v-model="editFormData.is_active"
              :checked-value="true"
              :unchecked-value="false"
              checked-text="启用"
              unchecked-text="禁用"
            />
        </a-form-item>
        <a-form-item v-if="userStore.userInfo?.is_staff" field="is_staff" label="管理员">
          <a-switch
            v-model="editFormData.is_staff"
            :checked-value="true"
            :unchecked-value="false"
            checked-text="是"
            unchecked-text="否"
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
  </div>
</template>

<style scoped>
.custom-table :deep(.arco-table) {
  background-color: transparent !important;
}

.custom-table :deep(.arco-table-container) {
  background-color: transparent !important;
  border: none !important;
}

.custom-table :deep(.arco-table-header) {
  background-color: transparent !important;
}

.custom-table :deep(.arco-table-body) {
  background-color: transparent !important;
}

.custom-table :deep(.arco-table-th) {
  background-color: rgba(30, 41, 59, 0.5) !important;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1) !important;
  color: #e2e8f0 !important;
  font-weight: 500 !important;
}

.custom-table :deep(.arco-table-td) {
  background-color: transparent !important;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1) !important;
  color: #cbd5e1 !important;
}

.custom-table :deep(.arco-table-tr) {
  background-color: transparent !important;
}

.custom-table :deep(.arco-table-tr:hover) {
  background-color: rgba(30, 41, 59, 0.5) !important;
}

.custom-table :deep(.arco-table-tr-checked) {
  background-color: rgba(59, 130, 246, 0.1) !important;
}

.custom-table :deep(.arco-table-tr-checked:hover) {
  background-color: rgba(59, 130, 246, 0.2) !important;
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

/* 添加 Spin 样式 */
:deep(.arco-spin) {
  .arco-spin-mask {
    background-color: rgba(15, 23, 42, 0.6) !important;
  }
  .arco-spin-dot-list {
    .arco-spin-dot-item {
      background-color: #60a5fa !important;
    }
  }
}

/* 弹窗整体样式 */
:deep(.arco-modal-mask) {
  background-color: rgba(15, 23, 42, 0.8) !important;
  backdrop-filter: blur(8px) !important;
}

:deep(.arco-modal) {
  padding: 0 !important;
  border-radius: 12px !important;
  background-color: rgb(31, 41, 55) !important;
  border: 1px solid rgba(148, 163, 184, 0.1) !important;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25) !important;
  overflow: hidden !important;
}

:deep(.arco-modal-container) {
  background-color: rgb(31, 41, 55) !important;
}

:deep(.arco-modal-header) {
  padding: 20px 24px !important;
  background-color: rgb(31, 41, 55) !important;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1) !important;
}

:deep(.arco-modal-title-text) {
  color: #e2e8f0 !important;
}

:deep(.arco-modal-body) {
  background-color: rgb(31, 41, 55) !important;
}

:deep(.arco-modal-title) {
  font-size: 18px !important;
  font-weight: 600 !important;
  color: #e2e8f0 !important;
  background-color: rgb(31, 41, 55) !important;
}

:deep(.arco-modal-content) {
  padding: 24px !important;
  background-color: rgb(31, 41, 55) !important;
}

:deep(.arco-modal-wrapper) {
  background-color: rgb(31, 41, 55) !important;
}

:deep(.arco-form) {
  background-color: rgb(31, 41, 55) !important;
}

:deep(.arco-form-item) {
  background-color: rgb(31, 41, 55) !important;
}

:deep(.arco-form-item-wrapper) {
  background-color: rgb(31, 41, 55) !important;
}

:deep(.arco-form-item-label) {
  padding-bottom: 8px !important;
  color: #e2e8f0 !important;
  font-weight: 500 !important;
  background-color: rgb(31, 41, 55) !important;
}

:deep(.arco-input-wrapper),
:deep(.arco-input-password) {
  height: 40px !important;
  background-color: rgba(30, 41, 59, 0.5) !important;
  border-color: rgba(148, 163, 184, 0.1) !important;
  border-radius: 8px !important;
  transition: all 0.2s ease-in-out !important;

  &:hover {
    border-color: #60a5fa !important;
    background-color: rgba(30, 41, 59, 0.7) !important;
  }

  &:focus-within {
    border-color: #3b82f6 !important;
    background-color: rgba(30, 41, 59, 0.7) !important;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
  }

  .arco-input {
    color: #e2e8f0 !important;
    
    &::placeholder {
      color: #64748b !important;
    }
  }

  .arco-input-prefix {
    margin-right: 10px !important;
    color: #60a5fa !important;
  }

  .arco-input-suffix {
    color: #94a3b8 !important;
  }
}

:deep(.arco-form-item-message) {
  margin-top: 6px !important;
  color: #ef4444 !important;
}

:deep(.arco-btn) {
  height: 40px !important;
  font-weight: 500 !important;
  border-radius: 8px !important;
  transition: all 0.2s ease-in-out !important;

  &:not(.arco-btn-primary):not(.btn-edit):not(.btn-delete) {
    color: #e2e8f0 !important;
    border-color: rgba(148, 163, 184, 0.1) !important;
    background-color: transparent !important;

    &:hover {
      color: #60a5fa !important;
      border-color: #60a5fa !important;
      background-color: rgba(59, 130, 246, 0.1) !important;
    }
  }

  &.arco-btn-primary:not(.btn-edit):not(.btn-delete):not([status="danger"]) {
    background: linear-gradient(to right, #7b93b9, #2563eb) !important;
    border: none !important;
    color: #ffffff !important;
    
    &:hover {
      background: linear-gradient(to right, #111c35, #1d4ed8) !important;
    }
  }
}

:deep(.arco-modal-close-btn) {
  color: #94a3b8 !important;
  
  &:hover {
    color: #e2e8f0 !important;
    background-color: rgba(148, 163, 184, 0.1) !important;
  }
}

/* Drawer 样式 */
:deep(.arco-drawer) {
  background-color: rgb(31, 41, 55) !important;
}

:deep(.arco-drawer-header) {
  background-color: rgb(31, 41, 55) !important;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1) !important;
}

:deep(.arco-drawer-title) {
  color: #e2e8f0 !important;
}

:deep(.arco-drawer-body) {
  background-color: rgb(31, 41, 55) !important;
}

:deep(.arco-drawer-mask) {
  background-color: rgba(15, 23, 42, 0.8) !important;
  backdrop-filter: blur(8px) !important;
}

:deep(.arco-drawer-close-btn) {
  color: #94a3b8 !important;
  
  &:hover {
    color: #e2e8f0 !important;
    background-color: rgba(148, 163, 184, 0.1) !important;
  }
}

/* Card 样式 */
:deep(.arco-card) {
  border-radius: 12px !important;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25) !important;
}

:deep(.arco-card-header) {
  border-bottom: 1px solid rgba(148, 163, 184, 0.1) !important;
}

:deep(.arco-form-item-label) {
  > label {
    color: #e2e8f0 !important;
  }
}

:deep(.arco-btn-text) {
  color: #94a3b8 !important;
  
  &:hover {
    color: #e2e8f0 !important;
    background-color: rgba(148, 163, 184, 0.1) !important;
  }
}

/* 动画效果 */
.tw-fixed {
  animation: modalFade 0.3s ease-out;
}

@keyframes modalFade {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 删除确认弹窗深色主题 */
:deep(.dark-modal) {
  .arco-modal {
    background-color: rgb(31, 41, 55) !important;
    border: 1px solid rgba(148, 163, 184, 0.1) !important;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25) !important;
  }

  .arco-modal-header {
    background-color: rgb(31, 41, 55) !important;
    border-bottom: 1px solid rgba(148, 163, 184, 0.1) !important;
  }

  .arco-modal-title {
    color: #e2e8f0 !important;
  }

  .arco-modal-body {
    background-color: rgb(31, 41, 55) !important;
    color: #e2e8f0 !important;
  }

  .arco-btn-secondary {
    color: #e2e8f0 !important;
    background-color: transparent !important;
    border-color: rgba(148, 163, 184, 0.1) !important;

    &:hover {
      color: #60a5fa !important;
      border-color: #60a5fa !important;
      background-color: rgba(59, 130, 246, 0.1) !important;
    }
  }

  .arco-btn-primary {
    background: linear-gradient(to right, #ef4444, #dc2626) !important;
    border: none !important;
    
    &:hover {
      background: linear-gradient(to right, #dc2626, #b91c1c) !important;
    }
  }
}

/* 关闭按钮样式 */
:deep(.arco-card-header) .arco-btn-text {
  width: 32px !important;
  height: 32px !important;
  min-width: 32px !important;
  min-height: 32px !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  border-radius: 8px !important;
  
  .arco-icon {
    font-size: 16px !important;
  }
  
  &:hover {
    color: #e2e8f0 !important;
    background-color: rgba(148, 163, 184, 0.1) !important;
  }
}

/* 表单样式 */
:deep(.arco-form-item-label) {
  padding-bottom: 8px !important;
  color: #e2e8f0 !important;
  font-weight: 500 !important;
  background-color: rgb(31, 41, 55) !important;
}

:deep(.arco-input-wrapper),
:deep(.arco-textarea-wrapper) {
  height: 40px !important;
  background-color: rgba(30, 41, 59, 0.5) !important;
  border-color: rgba(148, 163, 184, 0.1) !important;
  border-radius: 8px !important;
  transition: all 0.2s ease-in-out !important;
  
  &:hover {
    border-color: #60a5fa !important;
    background-color: rgba(30, 41, 59, 0.7) !important;
  }

  &:focus-within {
    border-color: #3b82f6 !important;
    background-color: rgba(30, 41, 59, 0.7) !important;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
  }

  .arco-input, .arco-textarea {
    color: #e2e8f0 !important;
    
    &::placeholder {
      color: #64748b !important;
    }
  }
}

:deep(.arco-textarea-wrapper) {
  height: auto !important;
}

:deep(.arco-form-item-message) {
  margin-top: 6px !important;
  color: #ef4444 !important;
}

/* 按钮基础样式 */
:deep(.arco-btn) {
  height: 40px !important;
  font-weight: 500 !important;
  border-radius: 8px !important;
  transition: all 0.2s ease-in-out !important;

  &:not(.arco-btn-primary):not(.btn-edit):not(.btn-delete) {
    color: #e2e8f0 !important;
    border-color: rgba(148, 163, 184, 0.1) !important;
    background-color: transparent !important;

    &:hover {
      color: #60a5fa !important;
      border-color: #60a5fa !important;
      background-color: rgba(59, 130, 246, 0.1) !important;
    }
  }

  &.arco-btn-primary:not(.btn-edit):not(.btn-delete):not([status="danger"]) {
  background: linear-gradient(to right, #3b82f6 ,#1d4ed8);
  border: none;
  padding: 0 24px;
  height: 36px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);
}

.custom-add-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
  background: linear-gradient(to right, #2563eb, #60a5fa);
}

.custom-add-button:active {
  transform: translateY(1px);
  box-shadow: 0 1px 3px rgba(59, 130, 246, 0.3);
}
}

/* 表格操作按钮样式 */
:deep(.btn-edit) {
  background: linear-gradient(to right, #728bb4, #2563eb) !important;
  border: none !important;
  color: #ffffff !important;
  
  &:hover {
    background: linear-gradient(to right, #2f4675, #1d4ed8) !important;
  }
}

:deep(.btn-delete) {
  background: linear-gradient(to right, #4549ed, #ff6464) !important;
  border: none !important;
  
  &:hover {
    background: linear-gradient(to right, #ff6464, #4549ed) !important;
  }
}

/* 确保危险按钮样式优先级 */
:deep(.arco-btn-primary[status="danger"]) {
  background: linear-gradient(to right, #ef4444, #dc2626) !important;
  border: none !important;
  color: #ffffff !important;
  
  &:hover {
    background: linear-gradient(to right, #dc2626, #b91c1c) !important;
  }
}

/* Switch 组件样式 */
:deep(.arco-switch) {
  background-color: rgba(148, 163, 184, 0.2) !important;
  border-color: rgba(148, 163, 184, 0.1) !important;

  &.arco-switch-checked {
    background-color: #2563eb !important;
    border-color: #2563eb !important;
  }

  .arco-switch-handle {
    background-color: #e2e8f0 !important;
  }

  .arco-switch-text {
    color: #e2e8f0 !important;
  }
}
</style> 