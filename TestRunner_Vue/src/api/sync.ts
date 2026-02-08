import type { ApiResponse } from '@/utils/request'
import request from '@/utils/request'

export interface SyncConfig {
  id: number
  name: string
  description?: string
  sync_fields: string[]
  sync_fields_count: number
  sync_enabled: boolean
  sync_mode: 'manual' | 'auto'
  sync_mode_display: string
  is_active: boolean
  is_current: boolean
  created_by_info?: {
    id: number
    username: string
  }
  created_time?: string
  updated_time?: string
}

export interface ApiSyncConfig {
  id: number
  name: string
  description?: string
  interface_info: {
    id: number
    name: string
    method: string
    url: string
  }
  testcase_info: {
    id: number
    name: string
  }
  step_info: {
    id: number
    name: string
    order: number
  }
  sync_fields: string[]
  sync_enabled: boolean
  sync_mode: 'manual' | 'auto'
  sync_trigger: {
    fields_to_watch: string[]
  }
  created_by_info?: {
    id: number
    username: string
  }
  created_time?: string
  updated_time?: string
}

export interface SyncHistory {
  id: number
  project?: number
  config?: SyncConfig
  sync_config_info?: {
    id: number
    name: string
    interface?: {
      id: number
      name: string
    }
    testcase?: {
      id: number
      name: string
    }
    step?: {
      id: number
      name: string
    }
  }
  status?: 'success' | 'failed'
  sync_status?: 'success' | 'failed'
  error_message?: string
  sync_fields: string[]
  created_by_info?: {
    id: number
    username: string
  }
  operator_info?: {
    id: number
    username: string
  }
  created_time?: string
  sync_time?: string
  old_data?: any
  new_data?: any
  sync_config?: number
  operator?: number
}

export interface SyncHistoriesData {
  histories?: SyncHistory[]
  total?: number
  count?: number
  next?: string | null
  previous?: string | null
  results?: SyncHistory[]
}

export interface SyncConfigsData {
  configs: SyncConfig[]
  active_config_id: number | null
}

export interface CreateSyncConfigRequest {
  project: number
  name: string
  description?: string
  sync_fields: string[]
  sync_enabled?: boolean
  sync_mode: 'manual' | 'auto'
  is_active?: boolean
}

export interface UpdateSyncConfigRequest {
  project: number
  name: string
  description?: string
  sync_fields: string[]
  sync_enabled?: boolean
  sync_mode: 'manual' | 'auto'
  is_active?: boolean
}

export interface ApiSyncConfigsResponse {
  count: number
  next: string | null
  previous: string | null
  results: ApiSyncConfig[]
}

export interface CreateApiSyncConfigRequest {
  name: string
  description?: string
  interface: number
  testcase: number
  step: number
  sync_fields: string[]
  sync_enabled?: boolean
  sync_mode?: 'manual' | 'auto'
  sync_trigger?: {
    fields_to_watch: string[]
  }
}

export interface ApiInterface {
  id: number
  name: string
  method: string
  url: string
}

export interface TestCase {
  id: number
  name: string
}

export interface TestStep {
  id: number
  name: string
  order: number
  interface_info?: ApiInterface
}

export interface ApiInterfacesResponse {
  count: number
  next: string | null
  previous: string | null
  results: ApiInterface[]
}

export interface TestCasesResponse {
  count: number
  next: string | null
  previous: string | null
  results: TestCase[]
}

export interface TestStepsResponse {
  id: number
  name: string
  teststeps: TestStep[]
}

export const syncApi = {
  /**
   * 获取同步配置列表
   */
  getConfigs(projectId: number): Promise<ApiResponse<SyncConfigsData>> {
    return request.get('/sync/global-configs/', {
      params: { project_id: projectId }
    })
  },

  /**
   * 创建同步配置
   */
  createConfig(data: CreateSyncConfigRequest): Promise<ApiResponse<SyncConfig>> {
    return request.post('/sync/global-configs/', data)
  },

  /**
   * 设置当前配置
   */
  setActiveConfig(configId: number): Promise<ApiResponse<null>> {
    return request.post(`/sync/global-configs/${configId}/set_active/`)
  },

  /**
   * 立即同步
   */
  syncNow(): Promise<ApiResponse<null>> {
    return request.post('/sync/sync-now/')
  },

  /**
   * 更新同步配置
   */
  updateConfig(configId: number, data: UpdateSyncConfigRequest): Promise<ApiResponse<SyncConfig>> {
    return request.put(`/sync/global-configs/${configId}/`, data)
  },

  /**
   * 删除同步配置
   */
  deleteConfig(configId: number): Promise<ApiResponse<null>> {
    return request.delete(`/sync/global-configs/${configId}/`)
  },

  /**
   * 获取同步历史列表
   */
  getHistories(params: { project_id: number; page?: number; page_size?: number }): Promise<ApiResponse<SyncHistoriesData>> {
    return request.get('/sync/histories/', { params })
  },

  /**
   * 获取同步历史详情
   */
  getHistoryDetail(historyId: number): Promise<ApiResponse<SyncHistory>> {
    return request.get(`/sync/histories/${historyId}/`)
  },

  /**
   * 回滚到指定的历史记录
   */
  rollbackHistory(historyId: number): Promise<ApiResponse<null>> {
    return request.post(`/sync/histories/${historyId}/rollback/`)
  },

  /**
   * 获取接口同步配置列表
   */
  getApiConfigs(projectId: number): Promise<ApiResponse<ApiSyncConfigsResponse>> {
    return request.get('/sync/configs/', {
      params: { project_id: projectId }
    })
  },

  /**
   * 创建接口同步配置
   */
  createApiConfig(data: CreateApiSyncConfigRequest): Promise<ApiResponse<ApiSyncConfig>> {
    return request.post('/sync/configs/', data)
  },

  /**
   * 获取接口列表
   */
  getInterfaces(projectId: number): Promise<ApiResponse<ApiInterfacesResponse>> {
    return request.get('/interfaces/', {
      params: { 
        project_id: projectId,
        page_size: 1000  // 设置较大的页面大小以获取所有数据
      }
    })
  },

  /**
   * 获取用例列表
   */
  getTestCases(projectId: number): Promise<ApiResponse<TestCasesResponse>> {
    return request.get('/testcases/', {
      params: { project_id: projectId }
    })
  },

  /**
   * 获取用例下的步骤列表
   */
  getTestSteps(testcaseId: number): Promise<ApiResponse<TestStepsResponse>> {
    return request.get(`/testcases/${testcaseId}/`)
  },

  /**
   * 获取同步配置详情
   */
  getConfigDetail(configId: number): Promise<ApiResponse<ApiSyncConfig>> {
    return request.get(`/sync/configs/${configId}/`)
  },

  /**
   * 更新接口同步配置
   */
  updateApiConfig(configId: number, data: CreateApiSyncConfigRequest): Promise<ApiResponse<ApiSyncConfig>> {
    return request.put(`/sync/configs/${configId}/`, data)
  },

  /**
   * 删除接口同步配置
   */
  deleteApiConfig(configId: number): Promise<ApiResponse<null>> {
    return request.delete(`/sync/configs/${configId}/`)
  },

  /**
   * 立即执行同步
   */
  syncNowConfig(configId: number): Promise<ApiResponse<null>> {
    return request.post(`/sync/configs/${configId}/sync_now/`)
  }
} 