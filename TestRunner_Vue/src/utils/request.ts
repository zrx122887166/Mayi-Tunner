import axios from 'axios'
import { Message } from '@arco-design/web-vue'
import router from '../router'
import axiosRetry from 'axios-retry'

export interface ApiResponse<T> {
  status: 'success' | 'error'
  code: number
  message: string
  data: T
  errors?: {
    name?: string[]
    code?: string[]
    [key: string]: string[] | undefined
  }
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const request = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  }
})

// 配置重试机制
axiosRetry(request, { 
  retries: 3,
  retryDelay: (retryCount) => {
    return retryCount * 1000
  },
  retryCondition: (error) => {
    return axiosRetry.isNetworkOrIdempotentRequestError(error) || error.code === 'ECONNABORTED'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      const url = error.config.url || ''
      
      switch (status) {
        case 400:
          return Promise.reject(data)
        case 401:
          // 如果是登录接口，直接返回错误信息让业务层处理
          if (url.includes('/users/login/')) {
            return Promise.reject(new Error(data.message || '用户名或密码错误'))
          } else {
            // 其他接口的401视为token过期
            localStorage.removeItem('token')
            router.push('/login')
            Message.error('登录已过期，请重新登录')
          }
          break
        case 403:
          Message.error('权限不足')
          break
        case 404:
          Message.error('请求的资源不存在')
          break
        default:
          Message.error(data?.message || '请求失败')
      }
    } else if (error.code === 'ECONNABORTED') {
      Message.error('请求超时，请稍后重试')
    } else if (error.request) {
      Message.error('网络错误，请检查您的网络连接')
    } else {
      Message.error('请求配置错误')
    }
    return Promise.reject(error)
  }
)

export default request 