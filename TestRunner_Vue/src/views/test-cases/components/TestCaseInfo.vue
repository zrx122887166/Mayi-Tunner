<script setup lang="ts">
import { 
  IconEdit, 
  IconFire,
  IconApps,
  IconTags,
  IconFolder,
} from '@arco-design/web-vue/es/icon'
import type { TestCase } from '@/api/testcase'

interface Props {
  testCase: TestCase
}

defineProps<Props>()
</script>

<template>
  <div class="tw-space-y-4">
    <!-- 基本信息 -->
    <div class="tw-flex tw-items-center tw-gap-6">
      <div class="tw-flex tw-items-center tw-gap-2">
        <icon-edit class="tw-text-gray-400" />
        <span class="tw-text-xl tw-font-medium">{{ testCase.name }}</span>
      </div>
      <a-tag :color="testCase.priority === 'P0' ? 'red' : testCase.priority === 'P1' ? 'orange' : testCase.priority === 'P2' ? 'blue' : 'green'">
        <template #icon>
          <icon-fire />
        </template>
        {{ testCase.priority }}
      </a-tag>
    </div>

    <!-- 描述信息 -->
    <div v-if="testCase.description" class="tw-text-gray-400">
      {{ testCase.description }}
    </div>

    <!-- 分组和标签信息 -->
    <div class="tw-flex tw-items-center tw-gap-6">
      <div v-if="testCase.group_info" class="tw-flex tw-items-center tw-gap-2 tw-text-gray-400">
        <icon-folder />
        <span>{{ testCase.group_info.name }}</span>
      </div>
      <div v-if="testCase.module_info" class="tw-flex tw-items-center tw-gap-2 tw-text-gray-400">
        <icon-apps />
        <span>{{ testCase.module_info.name }}</span>
      </div>
      <div v-if="testCase.tags_info?.length" class="tw-flex tw-items-center tw-gap-2">
        <icon-tags class="tw-text-gray-400" />
        <a-space>
          <a-tag
            v-for="tag in testCase.tags_info"
            :key="tag.id"
            :color="tag.color"
          >
            {{ tag.name }}
          </a-tag>
        </a-space>
      </div>
    </div>

    <!-- 创建和更新信息 -->
    <div class="tw-flex tw-items-center tw-gap-6 tw-text-sm tw-text-gray-400">
      <span>创建人：{{ testCase.created_by.username }}</span>
      <span>创建时间：{{ new Date(testCase.created_time).toLocaleString() }}</span>
      <span>更新时间：{{ new Date(testCase.updated_time).toLocaleString() }}</span>
    </div>
  </div>
</template>