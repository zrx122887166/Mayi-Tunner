import request from '@/utils/request'

export interface Group {
  id: number
  name: string
  parent: number | null
  project: number
  created_by: number
  created_time: string
  full_path: string
  children: Group[]
}

export interface CreateGroupData {
  name: string
  parent?: number | null
  project: number
}

export const groupApi = {
  // 获取分组树
  getGroupTree: (projectId: number) => {
    return request.get<Group[]>('/testcases/groups/tree/', {
      params: { project_id: projectId }
    })
  },

  // 获取分组列表
  getGroups: (params: {
    project_id: number
    parent?: number
    search?: string
  }) => {
    return request.get<Group[]>('/testcases/groups/', { params })
  },

  // 创建分组
  createGroup: (data: CreateGroupData) => {
    return request.post<Group>('/testcases/groups/', data)
  },

  // 更新分组
  updateGroup: (id: number, data: CreateGroupData) => {
    return request.put<Group>(`/testcases/groups/${id}/`, data)
  },

  // 删除分组
  deleteGroup: (id: number) => {
    return request.delete(`/testcases/groups/${id}/`)
  },

  // 获取分组详情
  getGroupDetail: (id: number) => {
    return request.get<Group>(`/testcases/groups/${id}/`)
  },

  // 获取分组下的用例
  getGroupTestCases: (id: number) => {
    return request.get(`/testcases/groups/${id}/testcases/`)
  }
} 