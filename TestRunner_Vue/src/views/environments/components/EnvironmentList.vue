<script setup lang="ts">
import { computed } from 'vue'
import type { Environment } from '../../../api/environment'
import {
  IconPlus,
  IconStorage,
  IconLink,
  IconSearch,
  IconSettings
} from '@arco-design/web-vue/es/icon'

interface Props {
  environments: Environment[]
  selectedEnvironment: Environment | null
  loading: boolean
  searchKeyword: string
  showGlobalHeaders?: boolean
  showDatabaseConfig?: boolean
}

interface Emits {
  (e: 'update:searchKeyword', value: string): void
  (e: 'select', environment: Environment): void
  (e: 'create'): void
  (e: 'selectGlobalHeaders'): void
  (e: 'selectDatabaseConfig'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const filteredEnvironments = computed(() => {
  if (!props.searchKeyword) return props.environments
  const keyword = props.searchKeyword.toLowerCase()
  return props.environments.filter(env => 
    env.name.toLowerCase().includes(keyword) || 
    env.description?.toLowerCase().includes(keyword) ||
    env.base_url.toLowerCase().includes(keyword)
  )
})
</script>

<template>
  <div class="tw-h-full tw-overflow-hidden env-list-container">
    <!-- 环境列表卡片 -->
    <a-card class="tw-h-full !tw-bg-[#1D2433] !tw-border-gray-800 !tw-rounded-lg !tw-w-full env-card">
      <!-- 卡片标题区域 -->
      <template #title>
        <div class="tw-flex tw-justify-between tw-items-center tw-py-2">
          <div class="tw-flex tw-items-center tw-gap-2">
            <icon-storage class="tw-text-blue-500" />
            <span class="tw-text-gray-100 tw-font-medium">环境列表</span>
          </div>
          <a-button type="outline" size="small" @click="emit('create')">
            <template #icon><icon-plus /></template>
            新建
          </a-button>
        </div>
      </template>
      
      <div class="card-content">
        <!-- 搜索框 -->
        <div class="search-container">
          <a-input-search
            :model-value="searchKeyword"
            @update:model-value="(val: string) => emit('update:searchKeyword', val)"
            placeholder="搜索环境..."
            allow-clear
            class="tw-w-full"
          >
            <template #prefix>
              <icon-search />
            </template>
          </a-input-search>
        </div>
        
        <!-- 列表内容区域 -->
        <a-spin :loading="loading" dot class="list-spin">
          <div class="content-container custom-scrollbar">
            <!-- 全局请求头卡片 -->
            <div
              class="tw-mb-4 tw-cursor-pointer tw-transition-all tw-w-full card-item"
              @click="emit('selectGlobalHeaders')"
            >
              <div
                class="tw-bg-gray-800 tw-rounded-lg tw-overflow-hidden tw-shadow-sm tw-transition-all tw-border tw-border-gray-700 hover:tw-border-teal-500 tw-w-full"
                :class="{ 'tw-border-teal-500 tw-shadow-md': showGlobalHeaders }"
              >
                <div class="tw-p-4 tw-flex tw-items-center tw-gap-4">
                  <div class="tw-w-10 tw-h-10 tw-rounded-lg tw-bg-teal-500/10 tw-flex tw-items-center tw-justify-center tw-flex-shrink-0">
                    <icon-settings class="tw-text-teal-500 tw-text-xl" />
                  </div>
                  <div class="tw-flex-1 tw-min-w-0 tw-overflow-hidden">
                    <div class="tw-font-medium tw-text-gray-100 tw-truncate tw-max-w-full">全局请求头</div>
                    <div class="tw-mt-1 tw-text-xs tw-text-gray-400 tw-truncate tw-max-w-full">
                      项目级别的全局请求头设置
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 数据库配置卡片 -->
            <div
              class="tw-mb-4 tw-cursor-pointer tw-transition-all tw-w-full card-item"
              @click="emit('selectDatabaseConfig')"
            >
              <div
                class="tw-bg-gray-800 tw-rounded-lg tw-overflow-hidden tw-shadow-sm tw-transition-all tw-border tw-border-gray-700 hover:tw-border-purple-500 tw-w-full"
                :class="{ 'tw-border-purple-500 tw-shadow-md': showDatabaseConfig }"
              >
                <div class="tw-p-4 tw-flex tw-items-center tw-gap-4">
                  <div class="tw-w-10 tw-h-10 tw-rounded-lg tw-bg-purple-500/10 tw-flex tw-items-center tw-justify-center tw-flex-shrink-0">
                    <icon-storage class="tw-text-purple-500 tw-text-xl" />
                  </div>
                  <div class="tw-flex-1 tw-min-w-0 tw-overflow-hidden">
                    <div class="tw-font-medium tw-text-gray-100 tw-truncate tw-max-w-full">数据库配置</div>
                    <div class="tw-mt-1 tw-text-xs tw-text-gray-400 tw-truncate tw-max-w-full">
                      项目级别的数据库连接配置
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 环境列表卡片 -->
            <div
              v-for="env in filteredEnvironments"
              :key="env.id"
              class="tw-mb-4 tw-cursor-pointer tw-transition-all tw-w-full card-item"
              @click="emit('select', env)"
            >
              <div 
                class="tw-bg-gray-800 tw-rounded-lg tw-overflow-hidden tw-shadow-sm tw-transition-all tw-border tw-border-gray-700 hover:tw-border-blue-500 tw-w-full"
                :class="{ 'tw-border-blue-500 tw-shadow-md': selectedEnvironment?.id === env.id }"
              >
                <div class="tw-p-4 tw-flex tw-items-center tw-gap-4">
                  <div class="tw-w-10 tw-h-10 tw-rounded-lg tw-bg-blue-500/10 tw-flex tw-items-center tw-justify-center tw-flex-shrink-0">
                    <icon-storage class="tw-text-blue-500 tw-text-xl" />
                  </div>
                  <div class="tw-flex-1 tw-min-w-0 tw-overflow-hidden">
                    <div class="tw-flex tw-items-center tw-justify-between tw-gap-2 tw-w-full">
                      <div class="tw-font-medium tw-text-gray-100 tw-truncate tw-max-w-[80%]" :title="env.name">{{ env.name }}</div>
                      <a-tag
                        :color="env.is_active ? 'green' : 'red'"
                        size="small"
                        class="tw-flex-shrink-0"
                      >{{ env.is_active ? '启用' : '禁用' }}</a-tag>
                    </div>
                    <div class="tw-mt-1 tw-flex tw-items-center tw-gap-2 tw-text-xs tw-text-gray-400 tw-w-full">
                      <icon-link class="tw-text-gray-500 tw-flex-shrink-0" />
                      <span class="tw-truncate tw-max-w-[280px] tw-inline-block" :title="env.base_url">{{ env.base_url }}</span>
                    </div>
                  </div>
                </div>
                <div v-if="env.description" class="tw-px-4 tw-pb-3 tw-text-xs tw-text-gray-500 tw-truncate tw-max-w-full" :title="env.description">
                  {{ env.description }}
                </div>
              </div>
            </div>
            
            <!-- 无环境时的空状态 -->
            <div
              v-if="filteredEnvironments.length === 0 && !loading"
              class="tw-text-center tw-py-6 tw-text-gray-500"
            >
              {{ searchKeyword ? '没有找到匹配的环境' : '暂无环境，请点击"新建"按钮创建' }}
            </div>
          </div>
        </a-spin>
      </div>
    </a-card>
  </div>
</template>

<style lang="postcss" scoped>
.env-list-container {
  display: flex;
  flex-direction: column;
}

:deep(.arco-spin) {
  .arco-spin-mask {
    background-color: transparent !important;
  }
}

.env-card {
  display: flex;
  flex-direction: column;
}

.env-card :deep(.arco-card-header) {
  flex-shrink: 0;
  border-bottom: 1px solid rgba(55, 65, 81, 0.5);
}

.env-card :deep(.arco-card-body) {
  padding: 0 !important;
  margin: 0 !important;
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.card-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
  overflow: hidden;
}

.search-container {
  margin-bottom: 16px;
  flex-shrink: 0;
}

.list-spin {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.content-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  width: 100%;
  padding-right: 4px;
  /* 隐藏滚动条但保留滚动功能 */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
  &::-webkit-scrollbar {
    display: none; /* Chrome, Safari, Opera*/
  }
}

/* 调整卡片内的内容对齐方式 */
.card-item {
  width: 100%;
  padding: 0;
}

.card-item > div {
  width: 100%;
}

/* 确保所有内容容器内部元素都有一致的填充 */
.tw-p-4 {
  padding: 1rem;
}

/* 自定义滚动条样式 */
.custom-scrollbar {
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
  
  &::-webkit-scrollbar {
    display: none; /* Chrome, Safari, Opera*/
  }
}

/* 强制所有文本内容截断 */
:deep(.tw-truncate) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

/* 限制基础URL宽度 */
.tw-truncate.tw-max-w-\[280px\] {
  max-width: 280px; /* URL显示宽度 */
}
</style> 