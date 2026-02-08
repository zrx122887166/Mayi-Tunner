import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import { useProjectStore } from '../stores/project'
import { Message } from '@arco-design/web-vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/login/index.vue'),
    meta: {
      requiresAuth: false,
    },
  },
  {
    path: '/',
    component: MainLayout,
    meta: {
      requiresAuth: true,
    },
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('../views/dashboard/index.vue'),
      },
      {
        path: 'projects',
        name: 'projects',
        component: () => import('../views/projects/index.vue'),
      },
      {
        path: 'apis',
        name: 'apis',
        component: () => import('../views/apis/index.vue'),
        meta: {
          requiresAuth: true,
          title: '接口管理'
        }
      },
      {
        path: 'functions',
        name: 'functions',
        component: () => import('../views/functions/index.vue'),
        meta: {
          requiresAuth: true,
          title: '函数管理'
        }
      },
      {
        path: 'environments',
        name: 'environments',
        component: () => import('../views/environments/index.vue'),
      },
      {
        path: 'user-management',
        name: 'user-management',
        component: () => import('../views/user-management/index.vue'),
      },
      {
        path: 'test-cases',
        name: 'test-cases',
        component: () => import('../views/test-cases/index.vue'),
        meta: {
          requiresAuth: true,
          title: '用例管理'
        }
      },
      {
        path: 'test-cases/create',
        name: 'test-case-create',
        component: () => import('../views/test-cases/components/TestCaseForm.vue'),
        meta: {
          requiresAuth: true,
          title: '新建用例'
        },
        props: route => ({
          mode: 'create',
          projectId: Number(route.query.projectId)
        })
      },
      {
        path: 'test-cases/:id/edit',
        name: 'test-case-edit',
        component: () => import('../views/test-cases/components/TestCaseForm.vue'),
        meta: {
          requiresAuth: true,
          title: '编辑用例'
        },
        props: route => ({
          mode: 'edit',
          projectId: Number(route.query.projectId),
          initialData: null
        })
      },
      {
        path: 'test-cases/:id',
        name: 'test-case-detail',
        component: () => import('../views/test-cases/components/TestCaseForm.vue'),
        meta: {
          requiresAuth: true,
          title: '用例详情'
        },
        props: route => ({
          mode: 'view',
          projectId: Number(route.query.projectId),
          initialData: null
        })
      },
      {
        path: 'test-cases/:id/reports',
        name: 'test-case-reports',
        component: () => import('../views/test-cases/reports.vue'),
        meta: {
          requiresAuth: true,
          title: '用例报告'
        }
      },
      {
        path: 'testtasks',
        name: 'testtasks',
        component: () => import('../views/testtasks/index.vue'),
        meta: {
          requiresAuth: true,
          title: '测试任务'
        }
      },
      {
        path: 'testtasks/create',
        name: 'testtask-create',
        component: () => import('../views/testtasks/components/TestTaskForm.vue'),
        meta: {
          requiresAuth: true,
          title: '新建测试任务'
        },
        props: {
          mode: 'create'
        }
      },
      {
        path: 'testtasks/:id/edit',
        name: 'testtask-edit',
        component: () => import('../views/testtasks/components/TestTaskForm.vue'),
        meta: {
          requiresAuth: true,
          title: '编辑测试任务'
        },
        props: route => ({
          mode: 'edit',
          id: route.params.id
        })
      },
      {
        path: 'testtasks/:id',
        name: 'testtask-detail',
        component: () => import('../views/testtasks/detail.vue'),
        meta: {
          requiresAuth: true,
          title: '测试任务详情'
        },
        props: route => ({
          mode: 'view',
          id: route.params.id
        })
      },
      {
        path: 'testtasks/:id/history',
        name: 'testtask-history',
        component: () => import('../views/testtasks/components/TestTaskExecutionHistory.vue'),
        meta: {
          requiresAuth: true,
          title: '测试任务执行历史'
        }
      },
      {
        path: 'testtasks/executions/:id',
        name: 'test-task-execution-detail',
        component: () => import('../views/testtasks/components/TestTaskExecutionDetail.vue'),
        meta: {
          requiresAuth: true,
          title: '测试任务执行详情'
        }
      },
      {
        path: 'testtasks/executions/:id/case-results',
        name: 'test-task-execution-case-results',
        component: () => import('../views/testtasks/components/TestTaskExecutionCaseResults.vue'),
        meta: {
          requiresAuth: true,
          title: '测试任务执行结果'
        }
      },
      {
        path: 'test-reports',
        name: 'test-reports',
        component: () => import('../views/test-reports/index.vue'),
        meta: {
          requiresAuth: true,
          title: '测试报告'
        }
      },
      {
        path: 'test-reports/:id',
        name: 'test-report-detail',
        component: () => import('../views/test-reports/detail.vue'),
        meta: {
          requiresAuth: true,
          title: '报告详情'
        }
      },
      {
        path: 'sync-config',
        name: 'sync-config',
        component: () => import('../views/sync-config/index.vue'),
        meta: {
          requiresAuth: true,
          title: '同步配置'
        }
      },
      {
        path: 'sync-config/history',
        name: 'sync-history',
        component: () => import('../views/sync-config/history.vue'),
        meta: {
          requiresAuth: true,
          title: '同步历史'
        }
      },
      // 脚本工具相关路由
      {
        path: 'script-tools',
        name: 'script-tools',
        component: () => import('@/views/script-tools/index-python.vue'),
        meta: { title: '脚本工具' }
      },
      {
        path: 'script-tools/create',
        name: 'script-create',
        component: () => import('@/views/script-tools/index.vue'),
        meta: { title: '创建脚本' }
      },
      {
        path: 'script-tools/deps',
        name: 'script-deps',
        component: () => import('@/views/script-tools/index-python-rely.vue'),
        meta: { title: '脚本依赖' }
      },
    ],
  },
]

// 需要项目上下文的路由名称列表（移除了脚本工具相关路由）
const ROUTES_REQUIRING_PROJECT = [
  'environments',
  'test-cases',
  'test-reports',
  'apis',
  'functions',
  'testtasks',
  'sync-config',
  'user-management',
  'test-case-create',
  'test-case-edit',
  'test-case-detail',
  'test-case-reports',
  'testtask-create',
  'testtask-edit',
  'testtask-detail',
  'testtask-history',
  'test-task-execution-detail',
  'test-task-execution-case-results',
  'test-report-detail',
  'sync-history'
]

// 可以在没有项目的情况下访问的路由（添加脚本工具相关路由）
const ROUTES_WITHOUT_PROJECT = [
  'dashboard',
  'projects',
  'login',
  'script-tools',
  'script-create',
  'script-deps'
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 添加路由守卫
router.beforeEach(async (to, from, next) => {
  // 检查是否需要登录
  const token = localStorage.getItem('token')
  if (!token && to.name !== 'login') {
    next({ name: 'login' })
    return
  }

  if (token && to.name === 'login') {
    next({ name: 'dashboard' })
    return
  }

  // 检查是否需要项目上下文（排除脚本工具路由）
  if (ROUTES_REQUIRING_PROJECT.includes(to.name as string)) {
    const projectStore = useProjectStore()

    // 先检查是否有项目列表
    if (projectStore.projects.length === 0) {
      try {
        await projectStore.fetchProjects()
        if (projectStore.projects.length === 0) {
          Message.warning('请先新建项目')
          next({ name: 'projects' })
          return
        }
      } catch (error) {
        console.error('获取项目列表失败:', error)
        Message.error('获取项目列表失败')
        next({ name: 'dashboard' })
        return
      }
    }

    // 继续检查是否有当前项目
    const savedProjectId = localStorage.getItem('currentProjectId')

    if (!projectStore.currentProject?.id && savedProjectId) {
      // 如果 store 中没有项目，但 localStorage 中有，则先加载项目
      try {
        await projectStore.fetchProjectById(Number(savedProjectId))
      } catch (error) {
        console.error('加载项目失败:', error)
        Message.warning('请先选择项目')
        next({ name: 'dashboard' })
        return
      }
    } else if (!projectStore.currentProject?.id && !savedProjectId) {
      // 如果既没有当前项目，localStorage 中也没有，则返回首页
      Message.warning('请先选择项目')
      next({ name: 'dashboard' })
      return
    }
  }

  next()
})

// 添加路由后置守卫用于调试
router.afterEach((to) => {
  console.log(`导航到路由: ${to.name}`, to.path)
})

export default router