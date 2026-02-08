import request from '../utils/request'

export interface LoginParams {
  username: string
  password: string
}

export interface UserInfo {
  id: number
  username: string
  email: string | null
  phone: string | null
  avatar: string | null
  is_active: boolean
  is_staff: boolean
  date_joined: string
  created_at: string
  updated_at: string
}

interface LoginResponse {
  token: string
  user: {
    id: number
    username: string
    email: string | null
  }
}

interface ApiResponse<T> {
  status: string
  code: number
  message: string
  data: T
}

interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface CreateUserParams {
  username: string
  password: string
  email?: string
  phone?: string
  avatar?: string
}

export interface UpdateUserParams {
  username: string
  password?: string
  email?: string
  phone?: string
  avatar?: string
  is_active?: boolean
  is_staff?: boolean
}

export const createUser = (data: CreateUserParams) => {
  return request.post<CreateUserParams, ApiResponse<UserInfo>>('/users/', data)
}

export const login = (data: LoginParams) => {
  return request.post<LoginParams, ApiResponse<LoginResponse>>('/users/login/', data)
}

export const getUserInfo = (id: number) => {
  return request.get<void, ApiResponse<UserInfo>>(`/users/${id}/`)
}

export const getUsers = (page: number = 1, pageSize: number = 10, search?: string) => {
  return request.get<void, ApiResponse<PaginatedResponse<UserInfo>>>('/users/', {
    params: {
      page,
      page_size: pageSize,
      search
    }
  })
}

export const logout = () => {
  return request.post('/users/logout/')
}

// 删除用户
export const deleteUser = (id: number) => {
  return request.delete<void, ApiResponse<void>>(`/users/${id}/`)
}

// 更新用户信息
export const updateUser = (id: number, data: UpdateUserParams) => {
  return request.put<UpdateUserParams, ApiResponse<UserInfo>>(`/users/${id}/`, data)
} 