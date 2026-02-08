<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconFolder, IconPlus, IconEdit, IconDelete, IconRight, IconDown } from '@arco-design/web-vue/es/icon'
import { groupApi } from '@/api/group'
import type { Group } from '@/types/testcase'

interface Props {
  modelValue: number | null
  readonly?: boolean
  projectId: number
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue'])

const groupList = ref<Group[]>([])
const groupLoading = ref(false)
const createGroupVisible = ref(false)
const createGroupLoading = ref(false)
const isEditGroupMode = ref(false)
const editingGroupId = ref<number | null>(null)
const expandedGroups = ref<number[]>([])

const newGroup = reactive({
  name: '',
  parent: null as number | null,
  project: props.projectId
})

// 加载分组树
const loadGroupTree = async () => {
  try {
    groupLoading.value = true
    const res = await groupApi.getGroupTree(props.projectId)
    // 根据创建时间排序，新的在后面
    const sortGroups = (groups: Group[]) => {
      groups.sort((a, b) => {
        const timeA = new Date(a.created_time).getTime()
        const timeB = new Date(b.created_time).getTime()
        return timeA - timeB
      })
      groups.forEach(group => {
        if (group.children?.length) {
          sortGroups(group.children)
        }
      })
      return groups
    }
    groupList.value = sortGroups(res)
  } catch (error) {
    console.error('Failed to load group tree:', error)
    Message.error('加载分组列表失败')
    groupList.value = []
  } finally {
    groupLoading.value = false
  }
}

// 处理分组展开/收起
const toggleGroup = (groupId: number, event: Event) => {
  event.preventDefault()
  event.stopPropagation()
  const index = expandedGroups.value.indexOf(groupId)
  if (index === -1) {
    expandedGroups.value.push(groupId)
  } else {
    expandedGroups.value.splice(index, 1)
  }
}

// 创建分组
const handleCreateGroup = () => {
  newGroup.name = ''
  newGroup.parent = null
  newGroup.project = props.projectId
  createGroupVisible.value = true
}

// 编辑分组
const handleEditGroup = (group: Group, event: Event) => {
  event.stopPropagation()
  isEditGroupMode.value = true
  editingGroupId.value = group.id
  newGroup.name = group.name
  newGroup.parent = group.parent
  newGroup.project = props.projectId
  createGroupVisible.value = true
}

// 删除分组
const handleDeleteGroup = async (groupId: number, event: Event) => {
  event.stopPropagation()
  try {
    await groupApi.deleteGroup(groupId)
    Message.success('删除成功')
    loadGroupTree()
  } catch (error) {
    console.error('Failed to delete group:', error)
    Message.error('删除分组失败')
  }
}

// 修改创建分组确认函数
const handleCreateGroupConfirm = async () => {
  if (!newGroup.name.trim()) {
    Message.error('请输入分组名称')
    return false
  }

  try {
    createGroupLoading.value = true
    if (isEditGroupMode.value && editingGroupId.value) {
      // 编辑分组
      await groupApi.updateGroup(editingGroupId.value, {
        name: newGroup.name.trim(),
        parent: newGroup.parent,
        project: props.projectId
      })
      Message.success('更新成功')
    } else {
      // 创建分组
      await groupApi.createGroup({
        name: newGroup.name.trim(),
        parent: newGroup.parent,
        project: props.projectId
      })
      Message.success('创建成功')
    }
    createGroupVisible.value = false
    resetGroupForm()
    loadGroupTree()
    return true
  } catch (error) {
    console.error('Failed to handle group:', error)
    Message.error(isEditGroupMode.value ? '更新分组失败' : '创建分组失败')
    return false
  } finally {
    createGroupLoading.value = false
  }
}

// 重置分组表单
const resetGroupForm = () => {
  newGroup.name = ''
  newGroup.parent = null
  newGroup.project = props.projectId
  isEditGroupMode.value = false
  editingGroupId.value = null
}

onMounted(() => {
  loadGroupTree()
})
</script>

<template>
  <div class="tw-flex tw-items-center">
    <a-select
      :model-value="modelValue"
      @update:model-value="val => emit('update:modelValue', val)"
      placeholder="选择分组"
      class="!tw-w-60"
      :disabled="readonly"
      :loading="groupLoading"
      allow-clear
    >
      <template #prefix>
        <icon-folder />
      </template>
      <template #empty>
        <div class="tw-flex tw-flex-col tw-min-h-[80px]">
          <div class="tw-flex tw-items-center tw-justify-center tw-py-2">
            <div v-if="groupLoading">
              <a-spin />
            </div>
            <div v-else class="tw-text-gray-400">
              暂无分组
            </div>
          </div>
          <div class="tw-bg-[var(--color-bg-popup)] tw-border-t tw-border-[var(--color-neutral-3)] tw-py-2 tw-px-3 tw-flex tw-justify-center">
            <a-button type="primary" size="mini" @click="handleCreateGroup" :disabled="readonly">
              <template #icon>
                <icon-plus />
              </template>
              新建分组
            </a-button>
          </div>
        </div>
      </template>
      <template v-for="group in groupList" :key="group.id">
        <a-option :value="group.id" :label="group.name">
          <div class="tw-grid tw-grid-cols-[1fr_48px] tw-items-center tw-w-full">
            <div class="tw-flex tw-items-center tw-gap-2 tw-min-w-0">
              <div
                v-if="group.children?.length"
                class="tw-w-4 tw-h-4 tw-flex tw-items-center tw-justify-center tw-cursor-pointer"
                @click="toggleGroup(group.id, $event)"
              >
                <icon-right v-if="!expandedGroups.includes(group.id)" class="!tw-w-3 !tw-h-3 !tw-text-[#6b7785]" />
                <icon-down v-else class="!tw-w-3 !tw-h-3 !tw-text-[#6b7785]" />
              </div>
              <span v-else class="tw-w-4"></span>
              <icon-folder class="tw-text-blue-500 tw-flex-shrink-0" />
              <span class="tw-truncate">{{ group.name }}</span>
            </div>
            <div class="tw-flex tw-items-center tw-justify-end tw-ml-2">
              <icon-edit
                class="tw-text-xs tw-text-[var(--color-text-3)] hover:tw-text-[var(--color-text-1)] tw-cursor-pointer tw-mr-2"
                @click="handleEditGroup(group, $event)"
              />
              <icon-delete
                class="tw-text-xs tw-text-[var(--color-text-3)] hover:tw-text-[var(--color-danger)] tw-cursor-pointer"
                @click="handleDeleteGroup(group.id, $event)"
              />
            </div>
          </div>
        </a-option>
        <template v-if="group.children?.length && expandedGroups.includes(group.id)">
          <template v-for="child in group.children" :key="child.id">
            <a-option
              :value="child.id"
              :label="child.name"
            >
              <div class="tw-grid tw-grid-cols-[1fr_48px] tw-items-center tw-w-full">
                <div class="tw-flex tw-items-center tw-gap-2 tw-pl-4 tw-min-w-0">
                  <div
                    v-if="child.children?.length"
                    class="tw-w-4 tw-h-4 tw-flex tw-items-center tw-justify-center tw-cursor-pointer"
                    @click="toggleGroup(child.id, $event)"
                  >
                    <icon-right v-if="!expandedGroups.includes(child.id)" class="!tw-w-3 !tw-h-3 !tw-text-[#6b7785]" />
                    <icon-down v-else class="!tw-w-3 !tw-h-3 !tw-text-[#6b7785]" />
                  </div>
                  <span v-else class="tw-w-4"></span>
                  <icon-folder class="tw-text-blue-400 tw-flex-shrink-0" />
                  <span class="tw-truncate">{{ child.name }}</span>
                </div>
                <div class="tw-flex tw-items-center tw-justify-end tw-ml-2">
                  <icon-edit
                    class="tw-text-xs tw-text-[var(--color-text-3)] hover:tw-text-[var(--color-text-1)] tw-cursor-pointer tw-mr-2"
                    @click="handleEditGroup(child, $event)"
                  />
                  <icon-delete
                    class="tw-text-xs tw-text-[var(--color-text-3)] hover:tw-text-[var(--color-danger)] tw-cursor-pointer"
                    @click="handleDeleteGroup(child.id, $event)"
                  />
                </div>
              </div>
            </a-option>
            <template v-if="child.children?.length && expandedGroups.includes(child.id)">
              <a-option
                v-for="grandChild in child.children"
                :key="grandChild.id"
                :value="grandChild.id"
                :label="grandChild.name"
              >
                <div class="tw-grid tw-grid-cols-[1fr_48px] tw-items-center tw-w-full">
                  <div class="tw-flex tw-items-center tw-gap-2 tw-pl-8 tw-min-w-0">
                    <span class="tw-w-4"></span>
                    <icon-folder class="tw-text-blue-300 tw-flex-shrink-0" />
                    <span class="tw-truncate">{{ grandChild.name }}</span>
                  </div>
                  <div class="tw-flex tw-items-center tw-justify-end tw-ml-2">
                    <icon-edit
                      class="tw-text-xs tw-text-[var(--color-text-3)] hover:tw-text-[var(--color-text-1)] tw-cursor-pointer tw-mr-2"
                      @click="handleEditGroup(grandChild, $event)"
                    />
                    <icon-delete
                      class="tw-text-xs tw-text-[var(--color-text-3)] hover:tw-text-[var(--color-danger)] tw-cursor-pointer"
                      @click="handleDeleteGroup(grandChild.id, $event)"
                    />
                  </div>
                </div>
              </a-option>
            </template>
          </template>
        </template>
      </template>
      <template #footer>
        <div class="tw-sticky tw-bottom-0 tw-bg-[var(--color-bg-popup)] tw-border-t tw-border-[var(--color-neutral-3)] tw-py-2 tw-px-3 tw-flex tw-justify-center">
          <a-button type="primary" size="mini" @click="handleCreateGroup" :disabled="readonly">
            <template #icon>
              <icon-plus />
            </template>
            新建分组
          </a-button>
        </div>
      </template>
    </a-select>

    <!-- 创建分组对话框 -->
    <a-modal
      v-model:visible="createGroupVisible"
      :title="isEditGroupMode ? '编辑分组' : '创建分组'"
      @cancel="() => { createGroupVisible = false; resetGroupForm() }"
      @before-ok="handleCreateGroupConfirm"
      :ok-loading="createGroupLoading"
      :mask-style="{ backgroundColor: 'rgba(0, 0, 0, 0.65)' }"
    >
      <div class="tw-space-y-4">
        <div class="tw-flex tw-items-center tw-gap-4">
          <span class="tw-w-20 tw-text-right">分组名称：</span>
          <a-input
            v-model="newGroup.name"
            placeholder="请输入分组名称"
            class="!tw-flex-1"
            allow-clear
          />
        </div>
        <div class="tw-flex tw-items-center tw-gap-4">
          <span class="tw-w-20 tw-text-right">父分组：</span>
          <a-select
            v-model="newGroup.parent"
            placeholder="请选择父分组"
            class="!tw-flex-1"
            allow-clear
            :loading="groupLoading"
          >
            <template #empty>
              <div v-if="groupLoading" class="tw-flex tw-items-center tw-justify-center tw-py-2">
                <a-spin />
              </div>
              <div v-else class="tw-text-gray-400 tw-text-center tw-py-2">
                暂无分组
              </div>
            </template>
            <template v-for="group in groupList" :key="group.id">
              <a-option :value="group.id" :label="group.name">
                <div class="tw-flex tw-items-center tw-gap-2">
                  <div
                    v-if="group.children?.length"
                    class="tw-w-4 tw-h-4 tw-flex tw-items-center tw-justify-center tw-cursor-pointer"
                    @click="toggleGroup(group.id, $event)"
                  >
                    <icon-right v-if="!expandedGroups.includes(group.id)" class="!tw-w-3 !tw-h-3 !tw-text-[#6b7785]" />
                    <icon-down v-else class="!tw-w-3 !tw-h-3 !tw-text-[#6b7785]" />
                  </div>
                  <span v-else class="tw-w-4"></span>
                  <icon-folder class="tw-text-blue-500 tw-flex-shrink-0" />
                  <span class="tw-truncate">{{ group.name }}</span>
                </div>
              </a-option>
              <template v-if="group.children?.length && expandedGroups.includes(group.id)">
                <a-option
                  v-for="child in group.children"
                  :key="child.id"
                  :value="child.id"
                  :label="child.name"
                >
                  <div class="tw-flex tw-items-center tw-gap-2 tw-pl-4">
                    <div
                      v-if="child.children?.length"
                      class="tw-w-4 tw-h-4 tw-flex tw-items-center tw-justify-center tw-cursor-pointer"
                      @click="toggleGroup(child.id, $event)"
                    >
                      <icon-right v-if="!expandedGroups.includes(child.id)" class="!tw-w-3 !tw-h-3 !tw-text-[#6b7785]" />
                      <icon-down v-else class="!tw-w-3 !tw-h-3 !tw-text-[#6b7785]" />
                    </div>
                    <span v-else class="tw-w-4"></span>
                    <icon-folder class="tw-text-blue-400 tw-flex-shrink-0" />
                    <span class="tw-truncate">{{ child.name }}</span>
                  </div>
                </a-option>
                <template v-if="child.children?.length && expandedGroups.includes(child.id)">
                  <a-option
                    v-for="grandChild in child.children"
                    :key="grandChild.id"
                    :value="grandChild.id"
                    :label="grandChild.name"
                  >
                    <div class="tw-flex tw-items-center tw-gap-2 tw-pl-8">
                      <span class="tw-w-4"></span>
                      <icon-folder class="tw-text-blue-300 tw-flex-shrink-0" />
                      <span class="tw-truncate">{{ grandChild.name }}</span>
                    </div>
                  </a-option>
                </template>
              </template>
            </template>
          </a-select>
        </div>
      </div>
    </a-modal>
  </div>
</template> 