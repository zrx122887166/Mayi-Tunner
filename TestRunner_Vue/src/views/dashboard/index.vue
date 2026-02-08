<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { 
  IconCode, 
  IconFolder, 
  IconFile, 
  IconCheckCircle,
  IconRobot,
  IconBug,
  IconCalendar, 
  IconDashboard,
  IconCloseCircle,
  IconRight,
  IconUp,
  IconDown
} from '@arco-design/web-vue/es/icon'
import { Message } from '@arco-design/web-vue'
import { getDashboardSummary } from '@/api/dashboard'
import type { DashboardSummary, RecentTask } from '@/api/dashboard'

// 扩展DashboardSummary类型以包含recent_reports
interface ExtendedDashboardSummary extends DashboardSummary {
  recent_reports?: RecentReport[]
}

// 定义RecentReport接口
interface RecentReport {
  id: number
  name: string
  status: string
  start_time: string
  duration: number
  success_count: number
  fail_count: number
  error_count: number
  testcase__name: string
  success_rate: number
}

const router = useRouter()
const loading = ref(false)
const dashboardData = ref<ExtendedDashboardSummary | null>(null)

// 获取仪表盘数据
const fetchDashboardData = async () => {
  try {
    loading.value = true
    const res = await getDashboardSummary()
    dashboardData.value = res.data
  } catch (error) {
    console.error('获取仪表盘数据失败:', error)
    Message.error('获取仪表盘数据失败')
  } finally {
    loading.value = false
  }
}

// 计算统计卡片数据
const statistics = computed(() => {
  if (!dashboardData.value) return []
  
  return [
    {
      title: '测试用例',
      value: dashboardData.value.total_testcases,
      key: 'cases',
      icon: IconCode,
      trend: '+12%',
      trendType: 'up',
      color: 'from-blue-500 to-blue-600'
    },
    {
      title: '接口数量',
      value: dashboardData.value.total_interfaces,
      key: 'interfaces',
      icon: IconFolder,
      trend: '+3%',
      trendType: 'up',
      color: 'from-purple-500 to-purple-600'
    },
    {
      title: '项目数量',
      value: dashboardData.value.total_projects,
      key: 'projects',
      icon: IconFile,
      trend: '+8%',
      trendType: 'up',
      color: 'from-green-500 to-green-600'
    },
    {
      title: '测试任务',
      value: dashboardData.value?.total_tasks || 0,
      key: 'tasks',
      icon: IconCalendar,
      trend: '+5%',
      trendType: 'up',
      color: 'from-orange-500 to-orange-600'
    },
    {
      title: '测试成功率',
      value: dashboardData.value ? `${(dashboardData.value.success_rate * 100).toFixed(1)}%` : '0%',
      key: 'success_rate',
      icon: IconCheckCircle,
      trend: '+2.1%',
      trendType: 'up',
      color: 'from-yellow-500 to-yellow-600'
    }
  ]
})

// 获取最近5条任务数据
const recentTasks = computed(() => {
  if (!dashboardData.value || !dashboardData.value.recent_tasks) return []
  return dashboardData.value.recent_tasks.slice(0, 5)
})

// 获取最近5条报告数据
const recentReports = computed(() => {
  if (!dashboardData.value || !dashboardData.value.recent_reports) return []
  return dashboardData.value.recent_reports.slice(0, 5)
})

// 格式化日期
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffDay > 0) {
    return `${diffDay}天前`
  } else if (diffHour > 0) {
    return `${diffHour}小时前`
  } else if (diffMin > 0) {
    return `${diffMin}分钟前`
  } else {
    return '刚刚'
  }
}

// 格式化持续时间（秒）为可读格式
const formatDuration = (seconds: number) => {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}秒`
  } else {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}分${remainingSeconds.toFixed(0)}秒`
  }
}

// 跳转到任务详情
const goToTaskDetail = (taskId: number) => {
  router.push(`/testtasks/executions/${taskId}/case-results/`)
}

// 跳转到报告详情
const goToReportDetail = (reportId: number) => {
  router.push(`/test-reports/${reportId}`)
}

// 跳转到测试用例页面
const goToTestCases = () => {
  router.push({ name: 'test-cases' })
}

// 跳转到测试任务页面
const goToTestTasks = () => {
  router.push({ name: 'testtasks' })
}

// 跳转到接口管理页面
const goToApis = () => {
  router.push({ name: 'apis' })
}

// 跳转到项目管理页面
const goToProjects = () => {
  router.push({ name: 'projects' })
}

// 跳转到测试报告页面
const goToTestReports = () => {
  router.push({ name: 'test-reports' })
}

// 跳转到环境管理页面
const goToEnvironments = () => {
  router.push({ name: 'environments' })
}

// 跳转到函数管理页面
const goToFunctions = () => {
  router.push({ name: 'functions' })
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<template>
  <div class="tw-h-full tw-w-full tw-overflow-auto">
    <div class="tw-p-4 sm:tw-p-6 tw-w-full tw-box-border">

        

      
      <a-spin :loading="loading" class="tw-w-full" tip="加载中...">
    <!-- 统计卡片 -->
        <div class="tw-grid tw-grid-cols-1 sm:tw-grid-cols-3 lg:tw-grid-cols-5 tw-gap-4 tw-w-full tw-box-border">
          <div 
            v-for="item in statistics" 
            :key="item.key"
            class="tw-bg-gradient-to-br tw-rounded-lg tw-p-4 sm:tw-p-5 tw-relative tw-overflow-hidden group hover:tw-scale-[1.02] tw-transition-all tw-duration-300 tw-border tw-border-white/10 hover:tw-border-white/20 tw-shadow-xl tw-cursor-pointer"
            :class="item.color"
          >
            <!-- 背景装饰 -->
            <div class="tw-absolute tw-right-0 tw-bottom-0 tw-opacity-10 tw-transition-transform group-hover:tw-scale-110">
              <component :is="item.icon" :style="{ fontSize: '80px' }" />
            </div>
            
            <!-- 内容 -->
            <div class="tw-relative">
              <div class="tw-flex tw-items-center tw-gap-2 tw-mb-2">
                <component :is="item.icon" class="tw-text-xl" />
                <span class="tw-text-sm tw-opacity-90">{{ item.title }}</span>
              </div>
              <div class="tw-text-2xl sm:tw-text-3xl tw-font-bold tw-mb-2">{{ item.value }}</div>
              <div class="tw-flex tw-items-center tw-text-sm">
                <icon-up v-if="item.trendType === 'up'" class="tw-mr-1" />
                <icon-down v-else class="tw-mr-1" />
                <span>{{ item.trend }} 较上周</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 下方内容区域 -->
        <div class="tw-grid tw-grid-cols-1 md:tw-grid-cols-3 tw-gap-4 tw-mt-6 tw-w-full tw-box-border">
          <!-- 左侧快速导航 -->
          <div class="tw-bg-gray-700 tw-rounded-lg tw-p-4 sm:tw-p-6 tw-shadow-xl tw-border tw-border-white/10 tw-box-border">
            <div class="tw-text-lg tw-font-medium tw-mb-6">快速导航</div>
            <div class="tw-space-y-4">
              <div 
                class="tw-flex tw-items-center tw-justify-between tw-p-3 sm:tw-p-4 tw-rounded-lg tw-bg-gray-800/50 hover:tw-bg-gray-750 tw-transition-all hover:tw-translate-x-1 tw-border tw-border-white/5 hover:tw-border-white/10 tw-backdrop-blur-sm tw-cursor-pointer tw-box-border"
                @click="goToTestCases"
              >
                <div class="tw-flex tw-items-center tw-gap-3">
                  <div class="tw-w-8 tw-h-8 sm:tw-w-10 sm:tw-h-10 tw-rounded-lg tw-flex tw-items-center tw-justify-center tw-backdrop-blur-sm tw-bg-blue-500/20 tw-text-blue-500">
                    <IconCode />
                  </div>
                  <div>
                    <div class="tw-font-medium">测试用例</div>
                    <div class="tw-text-sm tw-text-gray-400">
                      {{ dashboardData?.total_testcases || 0 }} 个用例
                    </div>
                  </div>
                </div>
                <IconRight class="tw-text-gray-400" />
              </div>
              
              <div 
                class="tw-flex tw-items-center tw-justify-between tw-p-3 sm:tw-p-4 tw-rounded-lg tw-bg-gray-800/50 hover:tw-bg-gray-750 tw-transition-all hover:tw-translate-x-1 tw-border tw-border-white/5 hover:tw-border-white/10 tw-backdrop-blur-sm tw-cursor-pointer tw-box-border"
                @click="goToApis"
              >
                <div class="tw-flex tw-items-center tw-gap-3">
                  <div class="tw-w-8 tw-h-8 sm:tw-w-10 sm:tw-h-10 tw-rounded-lg tw-flex tw-items-center tw-justify-center tw-backdrop-blur-sm tw-bg-purple-500/20 tw-text-purple-500">
                    <IconRobot />
                  </div>
                  <div>
                    <div class="tw-font-medium">接口管理</div>
                    <div class="tw-text-sm tw-text-gray-400">
                      {{ dashboardData?.total_interfaces || 0 }} 个接口
                    </div>
                  </div>
                </div>
                <IconRight class="tw-text-gray-400" />
              </div>
              
              <div 
                class="tw-flex tw-items-center tw-justify-between tw-p-3 sm:tw-p-4 tw-rounded-lg tw-bg-gray-800/50 hover:tw-bg-gray-750 tw-transition-all hover:tw-translate-x-1 tw-border tw-border-white/5 hover:tw-border-white/10 tw-backdrop-blur-sm tw-cursor-pointer tw-box-border"
                @click="goToProjects"
              >
                <div class="tw-flex tw-items-center tw-gap-3">
                  <div class="tw-w-8 tw-h-8 sm:tw-w-10 sm:tw-h-10 tw-rounded-lg tw-flex tw-items-center tw-justify-center tw-backdrop-blur-sm tw-bg-green-500/20 tw-text-green-500">
                    <IconFolder />
                  </div>
                  <div>
                    <div class="tw-font-medium">项目管理</div>
                    <div class="tw-text-sm tw-text-gray-400">
                      {{ dashboardData?.total_projects || 0 }} 个项目
                    </div>
                  </div>
                </div>
                <IconRight class="tw-text-gray-400" />
              </div>
              
              <div 
                class="tw-flex tw-items-center tw-justify-between tw-p-3 sm:tw-p-4 tw-rounded-lg tw-bg-gray-800/50 hover:tw-bg-gray-750 tw-transition-all hover:tw-translate-x-1 tw-border tw-border-white/5 hover:tw-border-white/10 tw-backdrop-blur-sm tw-cursor-pointer tw-box-border"
                @click="goToEnvironments"
              >
                <div class="tw-flex tw-items-center tw-gap-3">
                  <div class="tw-w-8 tw-h-8 sm:tw-w-10 sm:tw-h-10 tw-rounded-lg tw-flex tw-items-center tw-justify-center tw-backdrop-blur-sm tw-bg-cyan-500/20 tw-text-cyan-500">
                    <IconFolder />
                  </div>
                  <div>
                    <div class="tw-font-medium">环境管理</div>
                    <div class="tw-text-sm tw-text-gray-400">配置测试环境</div>
                  </div>
                </div>
                <IconRight class="tw-text-gray-400" />
              </div>
              
              <div 
                class="tw-flex tw-items-center tw-justify-between tw-p-3 sm:tw-p-4 tw-rounded-lg tw-bg-gray-800/50 hover:tw-bg-gray-750 tw-transition-all hover:tw-translate-x-1 tw-border tw-border-white/5 hover:tw-border-white/10 tw-backdrop-blur-sm tw-cursor-pointer tw-box-border"
                @click="goToFunctions"
              >
                <div class="tw-flex tw-items-center tw-gap-3">
                  <div class="tw-w-8 tw-h-8 sm:tw-w-10 sm:tw-h-10 tw-rounded-lg tw-flex tw-items-center tw-justify-center tw-backdrop-blur-sm tw-bg-amber-500/20 tw-text-amber-500">
                    <IconCode />
                  </div>
                  <div>
                    <div class="tw-font-medium">函数管理</div>
                    <div class="tw-text-sm tw-text-gray-400">自定义测试函数</div>
                  </div>
                </div>
                <IconRight class="tw-text-gray-400" />
              </div>
            </div>
          </div>

          <!-- 中间测试报告情况 -->
          <div class="tw-bg-gray-700 tw-rounded-lg tw-p-4 sm:tw-p-6 tw-shadow-xl tw-border tw-border-white/10 tw-box-border">
            <div class="tw-flex tw-flex-col sm:tw-flex-row tw-justify-between tw-items-start sm:tw-items-center tw-mb-6">
              <div class="tw-text-lg tw-font-medium tw-mb-2 sm:tw-mb-0">测试报告情况</div>
              <a-button type="outline" class="hover:tw-border-blue-500 hover:tw-text-blue-500 tw-transition-colors" @click="goToTestReports">
                查看全部
                <template #icon>
                  <icon-right />
                </template>
              </a-button>
            </div>
            
            <div class="tw-space-y-4">
              <div 
                v-for="(item, index) in recentReports" 
                :key="index"
                class="tw-flex tw-flex-col sm:tw-flex-row tw-items-start sm:tw-items-center tw-justify-between tw-p-3 sm:tw-p-4 tw-rounded-lg tw-bg-gray-800/50 hover:tw-bg-gray-750 tw-transition-all hover:tw-translate-x-1 tw-border tw-border-white/5 hover:tw-border-white/10 tw-cursor-pointer tw-box-border"
                @click="goToReportDetail(item.id)"
              >
                <div class="tw-flex tw-items-center tw-gap-3 sm:tw-gap-4 tw-mb-3 sm:tw-mb-0">
                  <div class="tw-w-8 tw-h-8 sm:tw-w-10 sm:tw-h-10 tw-rounded-lg tw-flex tw-items-center tw-justify-center tw-backdrop-blur-sm"
                    :class="item.status === 'success' ? 'tw-bg-green-500/20 tw-text-green-500' : 'tw-bg-red-500/20 tw-text-red-500'"
                  >
                    <icon-check-circle v-if="item.status === 'success'" />
                    <icon-close-circle v-else />
                  </div>
                  <div class="tw-max-w-[180px] sm:tw-max-w-none">
                    <div class="tw-font-medium tw-truncate">{{ item.testcase__name }}</div>
                    <div class="tw-text-sm tw-text-gray-400">{{ formatDate(item.start_time) }} · {{ formatDuration(item.duration) }}</div>
                  </div>
                </div>
                <div class="tw-flex tw-items-center tw-gap-4 sm:tw-gap-8 tw-w-full sm:tw-w-auto tw-justify-between sm:tw-justify-start">
                  <div class="tw-text-right">
                    <div class="tw-font-medium">通过率</div>
                    <div class="tw-text-sm" :class="item.success_rate === 1 ? 'tw-text-green-500' : 'tw-text-yellow-500'">
                      {{ (item.success_rate * 100).toFixed(0) }}%
                    </div>
                  </div>
                  <a-button shape="circle" size="small" class="hover:tw-border-blue-500 hover:tw-text-blue-500 tw-transition-colors">
                    <template #icon>
                      <icon-right />
                    </template>
                  </a-button>
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧执行列表 -->
          <div class="tw-bg-gray-700 tw-rounded-lg tw-p-4 sm:tw-p-6 tw-shadow-xl tw-border tw-border-white/10 tw-box-border">
            <div class="tw-flex tw-flex-col sm:tw-flex-row tw-justify-between tw-items-start sm:tw-items-center tw-mb-6">
              <div class="tw-text-lg tw-font-medium tw-mb-2 sm:tw-mb-0">最近执行情况</div>
              <a-button type="outline" class="hover:tw-border-blue-500 hover:tw-text-blue-500 tw-transition-colors" @click="goToTestTasks">
            查看全部
            <template #icon>
              <icon-right />
            </template>
          </a-button>
        </div>
        
        <div class="tw-space-y-4">
          <div 
                v-for="(item, index) in recentTasks" 
            :key="index"
                class="tw-flex tw-flex-col sm:tw-flex-row tw-items-start sm:tw-items-center tw-justify-between tw-p-3 sm:tw-p-4 tw-rounded-lg tw-bg-gray-800/50 hover:tw-bg-gray-750 tw-transition-all hover:tw-translate-x-1 tw-border tw-border-white/5 hover:tw-border-white/10 tw-cursor-pointer tw-box-border"
                @click="goToTaskDetail(item.id)"
              >
                <div class="tw-flex tw-items-center tw-gap-3 sm:tw-gap-4 tw-mb-3 sm:tw-mb-0">
                  <div class="tw-w-8 tw-h-8 sm:tw-w-10 sm:tw-h-10 tw-rounded-lg tw-flex tw-items-center tw-justify-center tw-backdrop-blur-sm"
                    :class="item.status === 'completed' && item.success_rate === 1 ? 'tw-bg-green-500/20 tw-text-green-500' : 'tw-bg-red-500/20 tw-text-red-500'"
                  >
                    <icon-check-circle v-if="item.status === 'completed' && item.success_rate === 1" />
                <icon-close-circle v-else />
              </div>
                  <div class="tw-max-w-[180px] sm:tw-max-w-none">
                    <div class="tw-font-medium tw-truncate">{{ item.task_suite__name }}</div>
                    <div class="tw-text-sm tw-text-gray-400">{{ formatDate(item.created_time) }}</div>
              </div>
            </div>
                <div class="tw-flex tw-items-center tw-gap-4 sm:tw-gap-8 tw-w-full sm:tw-w-auto tw-justify-between sm:tw-justify-start">
              <div class="tw-text-right">
                <div class="tw-font-medium">通过率</div>
                    <div class="tw-text-sm" :class="item.success_rate === 1 ? 'tw-text-green-500' : 'tw-text-yellow-500'">
                      {{ (item.success_rate * 100).toFixed(0) }}%
                </div>
              </div>
              <a-button shape="circle" size="small" class="hover:tw-border-blue-500 hover:tw-text-blue-500 tw-transition-colors">
                <template #icon>
                  <icon-right />
                </template>
              </a-button>
            </div>
          </div>
            </div>
          </div>
        </div>
      </a-spin>
    </div>
  </div>
</template>

<style scoped>
.hover\:tw-bg-gray-750:hover {
  background-color: rgba(31, 41, 55, 0.7);
}

.tw-backdrop-blur-sm {
  backdrop-filter: blur(8px);
}

/* 隐藏滚动条但保持可滚动 - 全局应用 */
:deep(::-webkit-scrollbar) {
  width: 0 !important;
  height: 0 !important;
  display: none !important;
}

/* Firefox */
* {
  scrollbar-width: none !important;
}

/* IE */
* {
  -ms-overflow-style: none !important;
}

/* 确保主容器可以滚动但无滚动条 */
.tw-h-full.tw-w-full.tw-overflow-auto {
  scrollbar-width: none !important;
  -ms-overflow-style: none !important;
}

.tw-h-full.tw-w-full.tw-overflow-auto::-webkit-scrollbar {
  width: 0 !important;
  height: 0 !important;
  display: none !important;
}

.tw-shadow-xl {
  box-shadow: 0 -4px 10px -1px rgba(0, 0, 0, 0.2),
              0 10px 25px -5px rgba(0, 0, 0, 0.4),
              -8px 0 15px -3px rgba(0, 0, 0, 0.3),
              8px 0 15px -3px rgba(0, 0, 0, 0.3);
}
</style> 