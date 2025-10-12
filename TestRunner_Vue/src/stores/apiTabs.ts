import { defineStore } from 'pinia'
import type { ApiInterface } from '@/api/interface'

// 页签数据结构
export interface ApiTab {
  id: string // 唯一标识
  interfaceId?: number // 接口ID（已保存的接口）
  name: string // 页签名称
  method: string // 请求方法
  url: string // 请求路径
  module?: number // 所属模块
  // 请求数据
  params?: any
  headers?: any
  body?: any
  setupHooks?: any[]
  teardownHooks?: any[]
  extractRules?: any
  assertRules?: any[]
  // 响应数据
  response?: {
    status: number | null
    time: number | null
    size: number | null
    data: any
    request: any
    response: any
    validation_results: any
    extracted_variables: any
  }
  // UI状态
  activeTab?: string // 当前选中的配置tab（headers、params、body等）
  // 时间戳
  createdAt: number
  updatedAt: number
}

export const useApiTabsStore = defineStore('apiTabs', {
  state: () => ({
    tabs: [] as ApiTab[],
    activeTabId: null as string | null,
    maxTabs: 10 // 最大页签数量限制
  }),

  getters: {
    // 获取当前激活的页签
    activeTab: (state) => {
      if (!state.activeTabId) return null
      return state.tabs.find(tab => tab.id === state.activeTabId)
    },

    // 获取页签数量
    tabCount: (state) => state.tabs.length,

    // 是否达到最大页签数
    isMaxTabs: (state) => state.tabs.length >= state.maxTabs
  },

  actions: {
    // 创建新页签
    createTab(interfaceData?: ApiInterface) {
      if (this.isMaxTabs) {
        // 如果达到最大数量，关闭最旧的页签
        this.removeTab(this.tabs[0].id)
      }

      const timestamp = Date.now()
      const tabId = `tab_${timestamp}_${Math.random().toString(36).substr(2, 9)}`
      
      const newTab: ApiTab = {
        id: tabId,
        interfaceId: interfaceData?.id,
        name: interfaceData?.name || '新接口',
        method: interfaceData?.method || 'GET',
        url: interfaceData?.url || '',
        module: interfaceData?.module,
        params: interfaceData?.params,
        headers: interfaceData?.headers,
        body: interfaceData?.body,
        setupHooks: interfaceData?.setup_hooks,
        teardownHooks: interfaceData?.teardown_hooks,
        extractRules: interfaceData?.extract,
        assertRules: interfaceData?.validators,
        response: undefined, // 新页签没有响应数据
        createdAt: timestamp,
        updatedAt: timestamp
      }

      this.tabs.push(newTab)
      this.activeTabId = tabId
      return tabId
    },

    // 更新页签数据
    updateTab(tabId: string, data: Partial<ApiTab>) {
      const tabIndex = this.tabs.findIndex(tab => tab.id === tabId)
      if (tabIndex !== -1) {
        this.tabs[tabIndex] = {
          ...this.tabs[tabIndex],
          ...data,
          updatedAt: Date.now()
        }
      }
    },

    // 更新页签的请求数据
    updateTabRequest(tabId: string, requestData: {
      method?: string
      url?: string
      name?: string
      module?: number
      params?: any
      headers?: any
      body?: any
      setupHooks?: any[]
      teardownHooks?: any[]
      extractRules?: any
      assertRules?: any[]
    }) {
      const tab = this.tabs.find(t => t.id === tabId)
      if (tab) {
        Object.assign(tab, {
          ...requestData,
          updatedAt: Date.now()
        })
      }
    },

    // 更新页签的响应数据
    updateTabResponse(tabId: string, response: ApiTab['response']) {
      const tab = this.tabs.find(t => t.id === tabId)
      if (tab) {
        tab.response = response
        tab.updatedAt = Date.now()
      }
    },

    // 清空页签的响应数据
    clearTabResponse(tabId: string) {
      const tab = this.tabs.find(t => t.id === tabId)
      if (tab) {
        tab.response = undefined
        tab.updatedAt = Date.now()
      }
    },

    // 更新页签的UI状态
    updateTabUIState(tabId: string, uiState: { activeTab?: string }) {
      const tab = this.tabs.find(t => t.id === tabId)
      if (tab) {
        if (uiState.activeTab !== undefined) {
          tab.activeTab = uiState.activeTab
        }
        tab.updatedAt = Date.now()
      }
    },

    // 激活页签
    activateTab(tabId: string) {
      const tab = this.tabs.find(t => t.id === tabId)
      if (tab) {
        this.activeTabId = tabId
      }
    },

    // 关闭页签
    removeTab(tabId: string) {
      const index = this.tabs.findIndex(tab => tab.id === tabId)
      if (index !== -1) {
        this.tabs.splice(index, 1)
        
        // 如果关闭的是当前激活的页签，激活相邻的页签
        if (this.activeTabId === tabId) {
          if (this.tabs.length > 0) {
            // 优先激活右边的页签，如果没有则激活左边的
            const newIndex = Math.min(index, this.tabs.length - 1)
            this.activeTabId = this.tabs[newIndex].id
          } else {
            this.activeTabId = null
          }
        }
      }
    },

    // 检查接口是否已在页签中打开
    findTabByInterface(interfaceId: number): ApiTab | undefined {
      return this.tabs.find(tab => tab.interfaceId === interfaceId)
    },

    // 打开或激活接口页签
    openOrActivateInterface(interfaceData: ApiInterface): string {
      // 如果接口已经在页签中打开，激活它
      if (interfaceData.id) {
        const existingTab = this.findTabByInterface(interfaceData.id)
        if (existingTab) {
          this.activeTabId = existingTab.id
          return existingTab.id
        }
      }

      // 否则创建新页签
      return this.createTab(interfaceData)
    },

    // 清空所有页签
    clearAllTabs() {
      this.tabs = []
      this.activeTabId = null
    },

    // 保存页签数据到本地存储
    saveToLocalStorage() {
      const data = {
        tabs: this.tabs,
        activeTabId: this.activeTabId
      }
      localStorage.setItem('apiTabs', JSON.stringify(data))
    },

    // 从本地存储恢复页签数据
    loadFromLocalStorage() {
      const stored = localStorage.getItem('apiTabs')
      if (stored) {
        try {
          const data = JSON.parse(stored)
          this.tabs = data.tabs || []
          this.activeTabId = data.activeTabId || null
        } catch (e) {
          console.error('Failed to load tabs from localStorage:', e)
        }
      }
    }
  }
})