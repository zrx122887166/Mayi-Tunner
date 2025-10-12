<script setup lang="ts">
import { onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { useProjectStore } from '../stores/project'
import { useEnvironmentStore } from '../stores/environment'
import TopNavbar from './components/TopNavbar.vue'
import UserMenu from './components/UserMenu.vue'
import Sidebar from './components/Sidebar.vue'

const userStore = useUserStore()
const projectStore = useProjectStore()
const environmentStore = useEnvironmentStore()

onMounted(async () => {
  await userStore.initUserInfo()
  projectStore.initFromStorage()
  environmentStore.initFromStorage()
  await projectStore.fetchProjects()
  if (projectStore.currentProjectId) {
    await environmentStore.fetchEnvironments(Number(projectStore.currentProjectId))
  }
})
</script>

<template>
  <div class="tw-h-screen tw-flex tw-flex-col tw-bg-gray-900 tw-overflow-hidden tw-text-gray-100">
    <!-- 顶部导航 -->
    <TopNavbar>
      <template #right>
        <UserMenu />
      </template>
    </TopNavbar>

    <!-- 主要内容区域 -->
    <div class="tw-flex tw-flex-1 tw-mx-3 tw-mb-3 tw-gap-3 tw-overflow-hidden">
      <!-- 左侧菜单 -->
      <Sidebar />

      <!-- 内容区域 -->
      <div class="tw-flex-1 tw-flex tw-overflow-hidden">
        <div class="tw-bg-gray-700 tw-rounded-lg tw-shadow-dark tw-w-full tw-flex tw-flex-col tw-overflow-hidden">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" class="tw-flex-1 tw-overflow-auto" />
            </transition>
          </router-view>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>