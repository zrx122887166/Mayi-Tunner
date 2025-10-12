<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { useProjectStore } from '../../stores/project'
import {
  IconHome,
  IconMenuFold,
  IconMenuUnfold,
  IconApps,
  IconStorage,
  IconCode,
  IconList,
  IconUser,
  IconFile
} from '@arco-design/web-vue/es/icon'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()
const isCollapsed = ref(false)

// 计算是否有项目
const hasProjects = computed(() => projectStore.projects.length > 0)

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 处理菜单点击，检查是否有项目
const handleMenuClick = (routeName: string) => {
  // 如果是项目管理页面或者首页，直接跳转
  if (routeName === 'projects' || routeName === 'dashboard') {
    router.push({ name: routeName })
    return
  }
  
  // 获取项目列表（如果还未获取）
  if (projectStore.projects.length === 0) {
    projectStore.fetchProjects().then(() => {
      // 检查是否有项目
      if (projectStore.projects.length === 0) {
        Message.warning('请先新建项目')
        router.push({ name: 'projects' })
      } else {
        router.push({ name: routeName })
      }
    }).catch(() => {
      Message.error('获取项目列表失败')
    })
  } else if (!hasProjects.value) {
    // 如果已经确认没有项目
    Message.warning('请先新建项目')
    router.push({ name: 'projects' })
  } else {
    // 已有项目，允许跳转
    router.push({ name: routeName })
  }
}

defineExpose({
  isCollapsed
})
</script>

<template>
  <div class="sidebar-container tw-flex" :class="{ 'tw-w-16': isCollapsed, 'tw-w-48': !isCollapsed }">
    <div class="tw-bg-gray-700 tw-rounded-lg tw-shadow-dark tw-w-full tw-flex tw-flex-col">
      <div class="tw-flex-1">
        <!-- 首页菜单项 -->
        <div 
          class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all"
          :class="{ 
            'tw-bg-gray-800/90': route.name === 'dashboard',
            'tw-bg-gray-800/40': route.name !== 'dashboard',
            'tw-px-4 tw-py-2.5': !isCollapsed,
            'tw-p-2.5 tw-justify-center': isCollapsed
          }"
          @click="handleMenuClick('dashboard')"
        >
          <IconHome class="tw-text-blue-500 tw-w-5 tw-h-5" />
          <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">首页</div>
        </div>

        <!-- 项目管理菜单项 -->
        <div 
          class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all"
          :class="{ 
            'tw-bg-gray-800/90': route.name === 'projects',
            'tw-bg-gray-800/40': route.name !== 'projects',
            'tw-px-4 tw-py-2.5': !isCollapsed,
            'tw-p-2.5 tw-justify-center': isCollapsed
          }"
          @click="handleMenuClick('projects')"
        >
          <IconApps class="tw-text-blue-500 tw-w-5 tw-h-5" />
          <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">项目管理</div>
        </div>

        <!-- 环境管理菜单项 -->
        <div 
          class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all"
          :class="{ 
            'tw-bg-gray-800/90': route.name === 'environments',
            'tw-bg-gray-800/40': route.name !== 'environments',
            'tw-px-4 tw-py-2.5': !isCollapsed,
            'tw-p-2.5 tw-justify-center': isCollapsed
          }"
          @click="handleMenuClick('environments')"
        >
          <IconStorage class="tw-text-blue-500 tw-w-5 tw-h-5" />
          <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">环境管理</div>
        </div>

        <!-- 函数管理菜单项 -->
        <div 
          class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all"
          :class="{ 
            'tw-bg-gray-800/90': route.name === 'functions',
            'tw-bg-gray-800/40': route.name !== 'functions',
            'tw-px-4 tw-py-2.5': !isCollapsed,
            'tw-p-2.5 tw-justify-center': isCollapsed
          }"
          @click="handleMenuClick('functions')"
        >
          <IconCode class="tw-text-blue-500 tw-w-5 tw-h-5" />
          <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">函数管理</div>
        </div>

        <!-- 接口管理菜单项 -->
        <div
          class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all"
          :class="{
            'tw-bg-gray-800/90': route.name === 'apis',
            'tw-bg-gray-800/40': route.name !== 'apis',
            'tw-px-4 tw-py-2.5': !isCollapsed,
            'tw-p-2.5 tw-justify-center': isCollapsed
          }"
          @click="handleMenuClick('apis')"
        >
          <IconCode class="tw-text-blue-500 tw-w-5 tw-h-5" />
          <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">接口管理</div>
        </div>

        <!-- 用例管理菜单项 -->
        <div
          class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all"
          :class="{
            'tw-bg-gray-800/90': route.name === 'test-cases',
            'tw-bg-gray-800/40': route.name !== 'test-cases',
            'tw-px-4 tw-py-2.5': !isCollapsed,
            'tw-p-2.5 tw-justify-center': isCollapsed
          }"
          @click="handleMenuClick('test-cases')"
        >
          <IconList class="tw-text-blue-500 tw-w-5 tw-h-5" />
          <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">用例管理</div>
        </div>

        <!-- 测试任务集菜单项 -->
        <div
          class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all"
          :class="{
            'tw-bg-gray-800/90': route.name === 'testtasks',
            'tw-bg-gray-800/40': route.name !== 'testtasks',
            'tw-px-4 tw-py-2.5': !isCollapsed,
            'tw-p-2.5 tw-justify-center': isCollapsed
          }"
          @click="handleMenuClick('testtasks')"
        >
          <IconList class="tw-text-blue-500 tw-w-5 tw-h-5" />
          <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">测试任务</div>
        </div>

        <!-- 测试报告菜单项 -->
        <div
          class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all"
          :class="{
            'tw-bg-gray-800/90': route.name === 'test-reports',
            'tw-bg-gray-800/40': route.name !== 'test-reports',
            'tw-px-4 tw-py-2.5': !isCollapsed,
            'tw-p-2.5 tw-justify-center': isCollapsed
          }"
          @click="handleMenuClick('test-reports')"
        >
          <IconFile class="tw-text-blue-500 tw-w-5 tw-h-5" />
          <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">测试报告</div>
        </div>

        <!-- 同步配置菜单项 -->
        <div
          class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all"
          :class="{
            'tw-bg-gray-800/90': route.name === 'sync-config',
            'tw-bg-gray-800/40': route.name !== 'sync-config',
            'tw-px-4 tw-py-2.5': !isCollapsed,
            'tw-p-2.5 tw-justify-center': isCollapsed
          }"
          @click="handleMenuClick('sync-config')"
        >
          <IconStorage class="tw-text-blue-500 tw-w-5 tw-h-5" />
          <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">同步配置</div>
        </div>

        <!-- 用户管理菜单项 -->
        <div
          class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all"
          :class="{
            'tw-bg-gray-800/90': route.name === 'user-management',
            'tw-bg-gray-800/40': route.name !== 'user-management',
            'tw-px-4 tw-py-2.5': !isCollapsed,
            'tw-p-2.5 tw-justify-center': isCollapsed
          }"
          @click="handleMenuClick('user-management')"
        >
          <IconUser class="tw-text-blue-500 tw-w-5 tw-h-5" />
          <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">用户管理</div>
        </div>
      </div>

      <!-- 收起按钮 -->
      <div class="tw-p-4 tw-border-t tw-border-gray-600/30">
        <div
          class="tw-cursor-pointer tw-flex tw-items-center tw-justify-center tw-gap-2 tw-py-2 tw-px-3 tw-rounded-lg tw-transition-all hover:tw-bg-gray-600/30"
          :class="{ 'tw-bg-gray-800/50': isCollapsed }"
          @click="toggleCollapse"
        >
          <component
            :is="isCollapsed ? IconMenuUnfold : IconMenuFold"
            class="tw-text-gray-400"
            :class="{ 'tw-rotate-180': isCollapsed }"
          />
          <span v-if="!isCollapsed" class="tw-text-sm tw-text-gray-400 tw-font-medium">收起菜单</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar-container {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

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
</style>