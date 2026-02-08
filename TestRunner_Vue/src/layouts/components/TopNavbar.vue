<script setup lang="ts">
import { useProjectStore } from '../../stores/project'
import { useEnvironmentStore } from '../../stores/environment'
import testrunnerIcon from '../../assets/testrunnerarco.svg'

const projectStore = useProjectStore()
const environmentStore = useEnvironmentStore()

const handleDropdownVisibleChange = (visible: boolean) => {
  if (visible) {
    projectStore.fetchProjects()
  }
}

const handleEnvironmentDropdownVisibleChange = (visible: boolean) => {
  if (visible && projectStore.currentProjectId) {
    environmentStore.fetchEnvironments(Number(projectStore.currentProjectId))
  }
}
</script>

<template>
  <div class="tw-h-14 tw-bg-gray-700 tw-rounded-lg tw-shadow-dark tw-m-3 tw-flex tw-justify-between tw-items-center">
    <div class="tw-flex tw-items-center">
      <div class="tw-text-lg tw-font-bold tw-flex tw-items-center tw-gap-2 tw-text-gray-100 tw-px-4">
        <img :src="testrunnerIcon" alt="TestRunner" class="tw-w-8 tw-h-8" />
        <span>蚂蚁自动化测试平台</span>
      </div>

      <div class="tw-h-14 tw-flex tw-items-center tw-border-l tw-border-gray-600/30">
        <!-- 项目选择器 -->
        <a-select
          v-model="projectStore.currentProjectId"
          :loading="projectStore.loading"
          :style="{ width: '192px' }"
          placeholder="选择项目"
          @change="(value: any) => projectStore.setCurrentProject(value)"
          @popup-visible-change="handleDropdownVisibleChange"
          allow-clear
          class="tw-ml-8 menu-item tw-rounded-lg"
        >
          <template #label="{ data }">
            <div class="tw-flex tw-items-center tw-gap-2 tw-pl-2">
              <div v-if="data?.label" class="tw-w-5 tw-h-5 tw-rounded-md tw-bg-gradient-to-r tw-from-blue-500 tw-to-indigo-500 tw-flex tw-items-center tw-justify-center tw-text-white tw-font-medium tw-flex-shrink-0">
                {{ data.label[0]?.toUpperCase() }}
              </div>
              <span class="tw-truncate tw-text-gray-300 tw-pl-1" :title="data?.label">{{ data?.label || '选择项目' }}</span>
            </div>
          </template>
          <a-option
            v-for="project in projectStore.projects"
            :key="project.id"
            :value="project.id.toString()"
            :label="project.name"
          >
            <div class="tw-flex tw-items-center tw-gap-2 tw-pl-2">
              <div class="tw-w-5 tw-h-5 tw-rounded-md tw-bg-gradient-to-r tw-from-blue-500 tw-to-indigo-500 tw-flex tw-items-center tw-justify-center tw-text-white tw-font-medium tw-flex-shrink-0">
                {{ project.name[0]?.toUpperCase() }}
              </div>
              <span class="tw-truncate tw-text-gray-300 tw-pl-1" :title="project.name">{{ project.name }}</span>
            </div>
          </a-option>
        </a-select>

        <!-- 环境选择器 -->
        <a-select
          v-model="environmentStore.currentEnvironmentId"
          :loading="environmentStore.loading"
          :style="{ width: '192px' }"
          placeholder="选择环境"
          @change="environmentStore.setCurrentEnvironment"
          @popup-visible-change="handleEnvironmentDropdownVisibleChange"
          allow-clear
          class="tw-ml-4 menu-item tw-rounded-lg"
        >
          <template #label="{ data }">
            <div class="tw-flex tw-items-center tw-gap-2 tw-pl-2">
              <div v-if="data?.label" class="tw-w-5 tw-h-5 tw-rounded-md tw-bg-gradient-to-r tw-from-blue-500 tw-to-indigo-600 tw-flex tw-items-center tw-justify-center tw-text-white tw-font-medium tw-flex-shrink-0">
                {{ data.label[0]?.toUpperCase() }}
              </div>
              <span class="tw-truncate tw-text-gray-300 tw-pl-1" :title="data?.label">{{ data?.label || '选择环境' }}</span>
            </div>
          </template>
          <a-option
            v-for="env in environmentStore.environments"
            :key="env.id"
            :value="env.id.toString()"
            :label="env.name"
          >
            <div class="tw-flex tw-items-center tw-gap-2 tw-pl-2">
              <div class="tw-w-5 tw-h-5 tw-rounded-md tw-bg-gradient-to-r tw-from-blue-500 tw-to-indigo-600 tw-flex tw-items-center tw-justify-center tw-text-white tw-font-medium tw-flex-shrink-0">
                {{ env.name[0]?.toUpperCase() }}
              </div>
              <span class="tw-truncate tw-text-gray-300 tw-pl-1" :title="env.name">{{ env.name }}</span>
            </div>
          </a-option>
        </a-select>
      </div>
    </div>
    <slot name="right"></slot>
  </div>
</template>

<style scoped>
.menu-item {
  box-shadow: inset 0 1px 0 0 rgba(148, 163, 184, 0.1) !important;
  transition: all 0.2s ease-in-out !important;
  background-color: rgba(31, 41, 55, 0.4) !important;
}

.menu-item:hover {
  background-color: rgba(31, 41, 55, 0.8) !important;
  transform: translateY(-1px) !important;
  box-shadow: inset 0 1px 0 0 rgba(148, 163, 184, 0.1),
              0 2px 4px rgba(0, 0, 0, 0.1) !important;
}

:deep(.arco-select.menu-item) {
  background: rgba(31, 41, 55, 0.8) !important;
  border: none !important;
  border-radius: 0.5rem !important;
  height: 40px !important;
  box-shadow: inset 0 1px 0 0 rgba(148, 163, 184, 0.1) !important;
  transition: all 0.2s ease-in-out !important;
}

:deep(.arco-select.menu-item:hover) {
  background: rgba(31, 41, 55, 0.95) !important;
  transform: translateY(-1px) !important;
  box-shadow: inset 0 1px 0 0 rgba(148, 163, 184, 0.1),
              0 2px 4px rgba(0, 0, 0, 0.1) !important;
}

:deep(.arco-select-view) {
  background: transparent !important;
  border: none !important;
  padding: 0 12px !important;
  height: 40px !important;
}

:deep(.arco-select-view-value) {
  color: rgb(209, 213, 219) !important;
}

:deep(.arco-select-dropdown-option-content) {
  padding-left: 8px !important;
}
</style>