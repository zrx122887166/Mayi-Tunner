<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { IconCaretDown, IconExport } from '@arco-design/web-vue/es/icon'

const router = useRouter()
const userStore = useUserStore()
const showUserMenu = ref(false)

const handleLogout = () => {
  localStorage.removeItem('token')
  router.push({ name: 'login' })
}

// 点击其他地方关闭用户菜单
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (!target.closest('.user-menu')) {
    showUserMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="tw-relative user-menu tw-mr-2">
    <div 
      class="menu-item tw-flex tw-items-center tw-gap-2 tw-px-3 tw-py-1.5 tw-rounded-lg tw-cursor-pointer hover:tw-bg-gray-800/40 tw-transition-all"
      :class="{ 'tw-bg-gray-800/90': showUserMenu }"
      @click="showUserMenu = !showUserMenu"
    >
      <div class="tw-flex tw-items-center tw-gap-2">
        <div class="tw-w-8 tw-h-8 tw-rounded-full tw-bg-gradient-to-r tw-from-blue-500 tw-to-indigo-500 tw-flex tw-items-center tw-justify-center tw-text-white tw-font-medium">
          {{ userStore.userInfo?.username?.[0]?.toUpperCase() || 'U' }}
        </div>
        <div class="tw-flex tw-flex-col tw-items-start">
          <span class="tw-text-sm tw-font-medium">{{ userStore.userInfo?.username || '用户' }}</span>
          <span class="tw-text-xs tw-text-gray-400">{{ userStore.userInfo?.email || '未设置邮箱' }}</span>
        </div>
        <IconCaretDown 
          class="tw-w-4 tw-h-4 tw-text-gray-400 tw-transition-transform tw-ml-2"
          :class="{ 'tw-rotate-180': showUserMenu }"
        />
      </div>

      <!-- 用户菜单下拉框 -->
      <div 
        v-if="showUserMenu" 
        class="tw-absolute tw-right-0 tw-top-full tw-mt-1 tw-w-[120px] tw-z-50"
      >
        <div class="menu-item tw-flex tw-items-center tw-gap-2 tw-px-3 tw-py-2 tw-rounded-lg tw-cursor-pointer tw-bg-gray-800/40 hover:tw-bg-gray-800/90 tw-transition-all"
          @click="handleLogout"
        >
          <IconExport class="tw-text-blue-500 tw-w-4 tw-h-4" />
          <span class="tw-text-gray-300 tw-text-sm">退出</span>
        </div>
      </div>
    </div>
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
</style>