<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
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
  IconFile,
  IconCaretDown,
  IconRight,
} from '@arco-design/web-vue/es/icon'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()
const isCollapsed = ref(false)
const scriptToolsExpanded = ref(false)

// 计算是否有项目
const hasProjects = computed(() => projectStore.projects.length > 0)

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 处理菜单点击，检查是否有项目
const handleMenuClick = (routeName: string) => {
  // 如果是项目管理页面或者首页，直接跳转
  if (routeName === 'projects' || routeName === 'dashboard') {
    // 从脚本工具子菜单切换到其他菜单时，收起脚本工具菜单
    if (isScriptSubmenuActive()) {
      scriptToolsExpanded.value = false
    }
    router.push({ name: routeName })
    return
  }
  
  // 如果是其他非脚本工具相关的一级菜单，收起脚本工具菜单
  if (!['script-create', 'script-tools', 'script-deps'].includes(routeName)) {
    scriptToolsExpanded.value = false
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

// 监听路由变化，自动展开脚本工具菜单
watch(() => route.name, (newRouteName) => {
  // 如果当前路由是脚本工具相关页面，自动展开脚本工具菜单
  if (newRouteName === 'script-create' || newRouteName === 'script-tools' || newRouteName === 'script-deps') {
    scriptToolsExpanded.value = true
  } else {
    // 当路由切换到非脚本工具相关页面时，自动收起脚本工具菜单
    // 但不要立即收起，给用户一点响应时间
    setTimeout(() => {
      scriptToolsExpanded.value = false
    }, 100)
  }
}, { immediate: true })

// 添加一个函数来检查当前路由是否匹配菜单
const isActive = (menuRouteName: string | string[]) => {
  if (Array.isArray(menuRouteName)) {
    return menuRouteName.includes(route.name as string)
  }
  return route.name === menuRouteName
}

// 修改：判断是否为脚本工具子菜单
const isScriptSubmenuActive = () => {
  return route.name === 'script-create' || route.name === 'script-tools' || route.name === 'script-deps'
}

// 检查是否为脚本工具相关页面
const isScriptRelatedPage = () => {
  return isScriptSubmenuActive()
}

defineExpose({
  isCollapsed
})
</script>

<template>
  <div class="sidebar-container" :class="{ 'tw-w-16': isCollapsed, 'tw-w-48': !isCollapsed }">
    <div class="tw-bg-gray-700 tw-rounded-lg tw-shadow-dark tw-w-full tw-h-full tw-overflow-hidden">
      <!-- 整个侧边栏都可滚动，包括底部按钮 -->
      <div class="tw-h-full tw-overflow-y-auto">
        <div class="tw-flex tw-flex-col tw-min-h-full">
          <!-- 菜单区域 -->
          <div class="tw-flex-1 tw-pb-4">
            <!-- 首页菜单项 -->
            <div 
              class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all hover:tw-bg-gray-800/80"
              :class="{ 
                'menu-item-active': isActive('dashboard'),
                'tw-bg-gray-800/40': !isActive('dashboard'),
                'tw-px-4 tw-py-2.5': !isCollapsed,
                'tw-p-2.5 tw-justify-center': isCollapsed
              }"
              @click="handleMenuClick('dashboard')"
            >
              <IconHome class="tw-text-blue-400 tw-w-5 tw-h-5" />
              <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">首页</div>
            </div>

            <!-- 项目管理菜单项 -->
            <div 
              class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all hover:tw-bg-gray-800/80"
              :class="{ 
                'menu-item-active': isActive('projects'),
                'tw-bg-gray-800/40': !isActive('projects'),
                'tw-px-4 tw-py-2.5': !isCollapsed,
                'tw-p-2.5 tw-justify-center': isCollapsed
              }"
              @click="handleMenuClick('projects')"
            >
              <IconApps class="tw-text-blue-400 tw-w-5 tw-h-5" />
              <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">项目管理</div>
            </div>

            <!-- 环境管理菜单项 -->
            <div 
              class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all hover:tw-bg-gray-800/80"
              :class="{ 
                'menu-item-active': isActive('environments'),
                'tw-bg-gray-800/40': !isActive('environments'),
                'tw-px-4 tw-py-2.5': !isCollapsed,
                'tw-p-2.5 tw-justify-center': isCollapsed
              }"
              @click="handleMenuClick('environments')"
            >
              <IconStorage class="tw-text-blue-400 tw-w-5 tw-h-5" />
              <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">环境管理</div>
            </div>

            <!-- 函数管理菜单项 -->
            <div 
              class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all hover:tw-bg-gray-800/80"
              :class="{ 
                'menu-item-active': isActive('functions'),
                'tw-bg-gray-800/40': !isActive('functions'),
                'tw-px-4 tw-py-2.5': !isCollapsed,
                'tw-p-2.5 tw-justify-center': isCollapsed
              }"
              @click="handleMenuClick('functions')"
            >
              <IconCode class="tw-text-blue-400 tw-w-5 tw-h-5" />
              <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">函数管理</div>
            </div>

            <!-- 接口管理菜单项 -->
            <div
              class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all hover:tw-bg-gray-800/80"
              :class="{
                'menu-item-active': isActive('apis'),
                'tw-bg-gray-800/40': !isActive('apis'),
                'tw-px-4 tw-py-2.5': !isCollapsed,
                'tw-p-2.5 tw-justify-center': isCollapsed
              }"
              @click="handleMenuClick('apis')"
            >
              <IconCode class="tw-text-blue-400 tw-w-5 tw-h-5" />
              <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">接口管理</div>
            </div>

            <!-- 用例管理菜单项 -->
            <div
              class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all hover:tw-bg-gray-800/80"
              :class="{
                'menu-item-active': isActive('test-cases'),
                'tw-bg-gray-800/40': !isActive('test-cases'),
                'tw-px-4 tw-py-2.5': !isCollapsed,
                'tw-p-2.5 tw-justify-center': isCollapsed
              }"
              @click="handleMenuClick('test-cases')"
            >
              <IconList class="tw-text-blue-400 tw-w-5 tw-h-5" />
              <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">用例管理</div>
            </div>

            <!-- 测试任务集菜单项 -->
            <div
              class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all hover:tw-bg-gray-800/80"
              :class="{
                'menu-item-active': isActive('testtasks'),
                'tw-bg-gray-800/40': !isActive('testtasks'),
                'tw-px-4 tw-py-2.5': !isCollapsed,
                'tw-p-2.5 tw-justify-center': isCollapsed
              }"
              @click="handleMenuClick('testtasks')"
            >
              <IconList class="tw-text-blue-400 tw-w-5 tw-h-5" />
              <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">测试任务</div>
            </div>

            <!-- 测试报告菜单项 -->
            <div
              class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all hover:tw-bg-gray-800/80"
              :class="{
                'menu-item-active': isActive('test-reports'),
                'tw-bg-gray-800/40': !isActive('test-reports'),
                'tw-px-4 tw-py-2.5': !isCollapsed,
                'tw-p-2.5 tw-justify-center': isCollapsed
              }"
              @click="handleMenuClick('test-reports')"
            >
              <IconFile class="tw-text-blue-400 tw-w-5 tw-h-5" />
              <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">测试报告</div>
            </div>

            <!-- 同步配置菜单项 -->
            <div
              class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all hover:tw-bg-gray-800/80"
              :class="{
                'menu-item-active': isActive('sync-config'),
                'tw-bg-gray-800/40': !isActive('sync-config'),
                'tw-px-4 tw-py-2.5': !isCollapsed,
                'tw-p-2.5 tw-justify-center': isCollapsed
              }"
              @click="handleMenuClick('sync-config')"
            >
              <IconStorage class="tw-text-blue-400 tw-w-5 tw-h-5" />
              <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">同步配置</div>
            </div>

            <!-- 用户管理菜单项 -->
            <div
              class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all hover:tw-bg-gray-800/80"
              :class="{
                'menu-item-active': isActive('user-management'),
                'tw-bg-gray-800/40': !isActive('user-management'),
                'tw-px-4 tw-py-2.5': !isCollapsed,
                'tw-p-2.5 tw-justify-center': isCollapsed
              }"
              @click="handleMenuClick('user-management')"
            >
              <IconUser class="tw-text-blue-400 tw-w-5 tw-h-5" />
              <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">用户管理</div>
            </div>

            <!-- 脚本工具父菜单 -->
            <!-- 修改：当子菜单被选中时，父菜单不高亮 -->
            <div 
              class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-2 tw-transition-all hover:tw-bg-gray-800/80"
              :class="{ 
                // 只有当没有子菜单被选中时，父菜单才高亮
                'menu-item-active': scriptToolsExpanded && !isScriptSubmenuActive(),
                'tw-bg-gray-800/40': !(scriptToolsExpanded && !isScriptSubmenuActive()),
                'tw-px-4 tw-py-2.5': !isCollapsed,
                'tw-p-2.5 tw-justify-center': isCollapsed
              }"
              @click="scriptToolsExpanded = !scriptToolsExpanded"
            >
              <IconCode class="tw-text-blue-400 tw-w-5 tw-h-5" />
              <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300">脚本工具</div>
              <component 
                v-if="!isCollapsed"
                :is="scriptToolsExpanded ? IconCaretDown : IconRight" 
                class="tw-text-gray-400 tw-w-4 tw-h-4 ml-auto"
              />
            </div>

            <!-- 脚本工具子菜单 -->
            <div 
              v-if="!isCollapsed || scriptToolsExpanded"
              class="tw-transition-all tw-duration-300 tw-overflow-hidden"
              :class="{
                'tw-h-0 tw-opacity-0': !scriptToolsExpanded,
                'tw-h-auto tw-opacity-100': scriptToolsExpanded,
                'tw-ml-2': !isCollapsed,
                'tw-ml-0': isCollapsed
              }"
            >
              <!-- 创建脚本子菜单 -->
              <div
                class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-1 tw-transition-all hover:tw-bg-gray-800/80"
                :class="{
                  'menu-item-active': isActive('script-create'),
                  'tw-bg-gray-800/40': !isActive('script-create'),
                  'tw-px-4 tw-py-2.5': !isCollapsed,
                  'tw-p-2.5 tw-justify-center': isCollapsed
                }"
                @click="handleMenuClick('script-create')"
              >
                <IconCode class="tw-text-blue-400 tw-w-4 tw-h-4" />
                <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300 tw-text-sm">创建脚本</div>
              </div>

              <!-- 脚本工具子菜单 -->
              <div
                class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-1 tw-transition-all hover:tw-bg-gray-800/80"
                :class="{
                  'menu-item-active': isActive('script-tools'),
                  'tw-bg-gray-800/40': !isActive('script-tools'),
                  'tw-px-4 tw-py-2.5': !isCollapsed,
                  'tw-p-2.5 tw-justify-center': isCollapsed
                }"
                @click="handleMenuClick('script-tools')"
              >
                <IconCode class="tw-text-blue-400 tw-w-4 tw-h-4" />
                <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300 tw-text-sm">脚本工具</div>
              </div>

              <!-- 脚本依赖子菜单 -->
              <div
                class="menu-item tw-flex tw-items-center tw-cursor-pointer tw-rounded-lg tw-mx-2 tw-mt-1 tw-transition-all hover:tw-bg-gray-800/80"
                :class="{
                  'menu-item-active': isActive('script-deps'),
                  'tw-bg-gray-800/40': !isActive('script-deps'),
                  'tw-px-4 tw-py-2.5': !isCollapsed,
                  'tw-p-2.5 tw-justify-center': isCollapsed
                }"
                @click="handleMenuClick('script-deps')"
              >
                <IconCode class="tw-text-blue-400 tw-w-4 tw-h-4" />
                <div v-if="!isCollapsed" class="tw-ml-3 tw-text-gray-300 tw-text-sm">脚本依赖</div>
              </div>
            </div>
          </div>

          <!-- 收起按钮区域 -->
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
    </div>
  </div>
</template>

<style scoped>
.sidebar-container {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  height: 100vh;
  min-width: 4rem;
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

/* 自定义滚动条样式 */
::-webkit-scrollbar {
  width: 4px;
}

::-webkit-scrollbar-track {
  background: rgba(75, 85, 99, 0.1);
  border-radius: 2px;
}

::-webkit-scrollbar-thumb {
  background: rgba(156, 163, 175, 0.5);
  border-radius: 2px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(156, 163, 175, 0.8);
}

/* 确保滚动区域可以正常滚动 */
.tw-h-full {
  height: 94%;
}

.tw-min-h-full {
  min-height: 90%;
}

/* 高亮菜单项样式增强 - 使用更浅的蓝色 */
.menu-item-active {
  background-color: rgba(96, 165, 250, 0.3) !important; /* 更浅的蓝色 */
  border-color: rgba(96, 165, 250, 0.5) !important;
  color: white !important;
  border-left: 3px solid rgba(96, 165, 250, 0.8) !important;
}

.menu-item-active:hover {
  background-color: rgba(96, 165, 250, 0.4) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
}

/* 图标在高亮状态下的颜色 */
.menu-item-active .tw-text-blue-400 {
  color: rgb(147 197 253) !important; /* 更亮的蓝色 */
}

/* 文字在高亮状态下的颜色 */
.menu-item-active .tw-text-gray-300 {
  color: rgb(219 234 254) !important; /* 更亮的白色/蓝色 */
}
</style>