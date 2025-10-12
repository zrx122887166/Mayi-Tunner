import request from '@/utils/request'

export interface User {
  id: number
  username: string
  email: string
}

export interface Project {
  id: number
  name: string
  description: string
  creator: User
  members: User[]
  created_at: string
  updated_at: string
}

export interface CreateProjectParams {
  name: string
  description?: string  // 可选参数
}

export interface UpdateProjectParams {
  name: string
  description?: string  // 可选参数
}

export interface ApiResponse<T> {
  status: string
  code: number
  message: string
  data: T
}

export interface PaginatedData<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface AvailableUser {
  id: number
  username: string
  email: string | null
  phone: string | null
  avatar: string
  is_active: boolean
  date_joined: string
  created_at: string
  updated_at: string
}

// 获取项目列表
export const getProjects = (page: number, pageSize: number, search?: string) => {
  return request.get<void, ApiResponse<PaginatedData<Project>>>('/projects/', {
    params: {
      page,
      page_size: pageSize,
      search
    }
  })
}

// 获取项目详情
export const getProject = (id: number) => {
  return request.get<void, ApiResponse<Project>>(`/projects/${id}/`)
}

// 创建项目
export const createProject = (data: CreateProjectParams) => {
  return request.post<CreateProjectParams, ApiResponse<Project>>('/projects/', data)
}

// 更新项目
export const updateProject = (id: number, data: UpdateProjectParams) => {
  return request.put<UpdateProjectParams, ApiResponse<Project>>(`/projects/${id}/`, data)
}

// 删除项目
export const deleteProject = (id: number) => {
  return request.delete<void, ApiResponse<void>>(`/projects/${id}/`)
}

// 添加项目成员
export const addProjectMember = (projectId: number, userId: number) => {
  return request.post<{ user_id: number }, ApiResponse<Project>>(`/projects/${projectId}/add_member/`, {
    user_id: userId
  })
}

// 移除项目成员
export const removeProjectMember = (projectId: number, userId: number) => {
  return request.post<{ user_id: number }, ApiResponse<void>>(`/projects/${projectId}/remove_member/`, {
    user_id: userId
  })
}

// 获取可添加的用户列表
export const getAvailableUsers = (projectId: number, page: number = 1, pageSize: number = 10, search?: string) => {
  return request.get<void, ApiResponse<PaginatedData<AvailableUser>>>(`/projects/${projectId}/available_users/`, {
    params: {
      page,
      page_size: pageSize,
      search
    }
  })
} 