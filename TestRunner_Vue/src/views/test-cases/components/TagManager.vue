<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconTag, IconPlus, IconEdit, IconDelete } from '@arco-design/web-vue/es/icon'
import { tagApi } from '@/api/testcase'
import type { Tag, TagStatistics } from '@/types/testcase'

interface Props {
  modelValue: number[]
  readonly?: boolean
  projectId: number
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue'])

const tagLoading = ref(false)
const tagList = ref<Tag[]>([])
const tagStats = ref<TagStatistics[]>([])
const tagSearchValue = ref('')
const createTagVisible = ref(false)
const createTagLoading = ref(false)
const isEditMode = ref(false)
const editingTagId = ref<number | null>(null)

const newTag = reactive({
  name: '',
  color: '#1890ff'
})

const resetTagForm = () => {
  newTag.name = ''
  newTag.color = '#1890ff'
  isEditMode.value = false
  editingTagId.value = null
}

// 创建标签
const handleCreateTag = () => {
  resetTagForm()
  createTagVisible.value = true
}

// 编辑标签
const handleEditTag = (tag: Tag, event: Event) => {
  event.stopPropagation()
  isEditMode.value = true
  editingTagId.value = tag.id
  newTag.name = tag.name
  newTag.color = tag.color
  createTagVisible.value = true
}

// 删除标签
const handleDeleteTag = async (tagId: number, event: Event) => {
  event.stopPropagation()
  try {
    await tagApi.deleteTag(tagId)
    Message.success('删除成功')
    loadTags()
    loadTagStats()
  } catch (error) {
    console.error('Failed to delete tag:', error)
    Message.error('删除标签失败')
  }
}

const handleCreateTagConfirm = async () => {
  if (!newTag.name.trim()) {
    Message.error('请输入标签名称')
    return false
  }

  try {
    createTagLoading.value = true
    if (isEditMode.value && editingTagId.value) {
      // 编辑标签
      await tagApi.updateTag(editingTagId.value, {
        name: newTag.name.trim(),
        color: newTag.color,
        project: props.projectId
      })
      Message.success('更新成功')
    } else {
      // 创建标签
      await tagApi.createTag({
        name: newTag.name.trim(),
        color: newTag.color,
        project: props.projectId
      })
      Message.success('创建成功')
    }
    createTagVisible.value = false
    resetTagForm()
    loadTags()
    loadTagStats()
    return true
  } catch (error) {
    console.error('Failed to handle tag:', error)
    Message.error(isEditMode.value ? '更新标签失败' : '创建标签失败')
    return false
  } finally {
    createTagLoading.value = false
  }
}

// 加载标签列表
const loadTags = async (search?: string) => {
  try {
    tagLoading.value = true
    const res = await tagApi.getTags({
      project_id: props.projectId,
      search,
      ordering: 'name'
    })
    tagList.value = res.results
  } catch (error) {
    console.error('Failed to load tags:', error)
    Message.error('加载标签列表失败')
  } finally {
    tagLoading.value = false
  }
}

// 加载标签使用统计
const loadTagStats = async () => {
  try {
    const stats = await tagApi.getTagStatistics(props.projectId)
    tagStats.value = stats
  } catch (error) {
    console.error('Failed to load tag statistics:', error)
  }
}

// 处理标签搜索
const handleTagSearch = (value: string) => {
  tagSearchValue.value = value
  loadTags(value)
}

onMounted(() => {
  loadTags()
  loadTagStats()
})
</script>

<template>
  <div class="tw-flex tw-items-center">
    <a-select
      :model-value="modelValue"
      @update:model-value="val => emit('update:modelValue', val)"
      placeholder="选择标签"
      class="!tw-w-60"
      :disabled="readonly"
      :loading="tagLoading"
      multiple
      allow-search
      allow-clear
      @search="handleTagSearch"
      :popup-max-height="false"
    >
      <template #prefix>
        <icon-tag />
      </template>
      <template #empty>
        <div class="tw-flex tw-flex-col tw-min-h-[80px]">
          <div class="tw-flex tw-items-center tw-justify-center tw-py-2">
            <div v-if="tagLoading">
              <a-spin />
            </div>
            <div v-else class="tw-text-gray-400">
              {{ tagSearchValue ? '未找到相关标签' : '暂无标签' }}
            </div>
          </div>
          <div class="tw-bg-[var(--color-bg-popup)] tw-border-t tw-border-[var(--color-neutral-3)] tw-py-2 tw-px-3 tw-flex tw-justify-center">
            <a-button type="primary" size="mini" @click="handleCreateTag" :disabled="readonly">
              <template #icon>
                <icon-plus />
              </template>
              新建标签
            </a-button>
          </div>
        </div>
      </template>
      <a-option
        v-for="tag in tagList"
        :key="tag.id"
        :value="tag.id"
        :label="tag.name"
        class="!tw-bg-transparent hover:!tw-bg-[var(--color-fill-2)]"
      >
        <div class="tw-grid tw-grid-cols-[1fr_48px] tw-items-center tw-w-full">
          <div class="tw-flex tw-items-center tw-min-w-0">
            <div
              class="tw-w-3 tw-h-3 tw-rounded-full tw-flex-shrink-0 tw-mr-2"
              :style="{ backgroundColor: tag.color }"
            />
            <span class="tw-truncate">{{ tag.name }}</span>
            <span v-if="tagStats.find(s => s.id === tag.id)" class="tw-text-gray-400 tw-text-xs tw-flex-shrink-0 tw-ml-1">
              ({{ tagStats.find(s => s.id === tag.id)?.usage_count || 0 }})
            </span>
          </div>
          <div class="tw-flex tw-items-center tw-justify-end tw-ml-2">
            <icon-edit
              class="tw-text-xs tw-text-[var(--color-text-3)] hover:tw-text-[var(--color-text-1)] tw-cursor-pointer tw-mr-2"
              @click="handleEditTag(tag, $event)"
            />
            <icon-delete
              class="tw-text-xs tw-text-[var(--color-text-3)] hover:tw-text-[var(--color-danger)] tw-cursor-pointer"
              @click="handleDeleteTag(tag.id, $event)"
            />
          </div>
        </div>
      </a-option>
      <template #footer>
        <div class="tw-sticky tw-bottom-0 tw-bg-[var(--color-bg-popup)] tw-border-t tw-border-[var(--color-neutral-3)] tw-py-2 tw-px-3 tw-flex tw-justify-center">
          <a-button type="primary" size="mini" @click="handleCreateTag" :disabled="readonly">
            <template #icon>
              <icon-plus />
            </template>
            新建标签
          </a-button>
        </div>
      </template>
    </a-select>

    <!-- 标签对话框 -->
    <a-modal
      v-model:visible="createTagVisible"
      :title="isEditMode ? '编辑标签' : '创建标签'"
      @cancel="() => { createTagVisible = false; resetTagForm() }"
      @before-ok="handleCreateTagConfirm"
      :ok-loading="createTagLoading"
      :mask-style="{ backgroundColor: 'rgba(0, 0, 0, 0.65)' }"
    >
      <div class="tw-space-y-4">
        <div class="tw-flex tw-items-center tw-gap-4">
          <span class="tw-w-20 tw-text-right">标签名称：</span>
          <a-input
            v-model="newTag.name"
            placeholder="请输入标签名称"
            class="!tw-flex-1"
            allow-clear
          />
        </div>
        <div class="tw-flex tw-items-center tw-gap-4">
          <span class="tw-w-20 tw-text-right">标签颜色：</span>
          <a-color-picker
            v-model="newTag.color"
            :default-value="newTag.color"
            class="!tw-flex-1"
          />
        </div>
      </div>
    </a-modal>
  </div>
</template> 