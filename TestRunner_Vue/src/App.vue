<script setup lang="ts">
import { onMounted } from 'vue'
import { useProjectStore } from './stores/project'
import { useUserStore } from './stores/user'

const projectStore = useProjectStore()
const userStore = useUserStore()

onMounted(async () => {
  // 设置深色主题
  document.body.setAttribute('arco-theme', 'dark')
  
  // 检查用户是否已登录
  const token = localStorage.getItem('token')
  if (token) {
    // 初始化用户信息
    await userStore.initUserInfo()
    
    // 预加载项目列表
    try {
      await projectStore.fetchProjects()
    } catch (error) {
      console.error('初始化项目列表失败:', error)
    }
  }
})
</script>

<template>
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<style>
:root {
  color-scheme: dark;
}

body {
  margin: 0;
  padding: 0;
  background-color: rgb(17, 24, 39);
  color: rgb(243, 244, 246);
}

#app {
  min-height: 100vh;
  background-color: rgb(17, 24, 39);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Arco Design 深色主题覆盖 */
:root[arco-theme="dark"] {
  --color-bg-1: rgb(17, 24, 39);
  --color-bg-2: rgb(31, 41, 55);
  --color-bg-3: rgb(55, 65, 81);
  --color-bg-4: rgb(75, 85, 99);
  --color-bg-5: rgb(107, 114, 128);
  --color-text-1: rgb(243, 244, 246);
  --color-text-2: rgb(229, 231, 235);
  --color-text-3: rgb(209, 213, 219);
  --color-text-4: rgb(156, 163, 175);
  --color-border: rgba(75, 85, 99, 0.3);
  --color-fill-1: rgba(17, 24, 39, 0.5);
  --color-fill-2: rgba(31, 41, 55, 0.5);
  --color-fill-3: rgba(55, 65, 81, 0.5);
  --color-fill-4: rgba(75, 85, 99, 0.5);
}

/* 表格样式覆盖 */
.arco-table {
  --color-bg-2: rgb(31, 41, 55) !important;
  --color-neutral-2: rgb(31, 41, 55) !important;
  --color-neutral-3: rgb(55, 65, 81) !important;
  background-color: rgb(31, 41, 55) !important;
  color: rgb(243, 244, 246) !important;
}

.arco-table-th {
  background-color: rgb(31, 41, 55) !important;
  border-bottom: 1px solid rgba(75, 85, 99, 0.2) !important;
}

.arco-table-td {
  background-color: transparent !important;
  border-bottom: 1px solid rgba(75, 85, 99, 0.1) !important;
}

.arco-table-tr:hover .arco-table-td {
  background-color: rgba(55, 65, 81, 0.3) !important;
}

/* 卡片样式覆盖 */
.arco-card {
  background-color: rgb(31, 41, 55) !important;
  border: 1px solid rgba(75, 85, 99, 0.2) !important;
}
</style>
