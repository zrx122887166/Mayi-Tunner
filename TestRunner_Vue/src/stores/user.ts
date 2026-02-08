import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, logout as logoutApi, getUserInfo } from '../api/user'

interface SimpleUserInfo {
  id: number
  username: string
  email: string | null
  is_staff: boolean
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref<SimpleUserInfo | null>(null)

  // 初始化用户信息
  const initUserInfo = async () => {
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      token.value = storedToken
      try {
        // 从本地存储中获取用户ID
        const storedUserInfo = localStorage.getItem('userInfo')
        if (storedUserInfo) {
          const { id } = JSON.parse(storedUserInfo)
          const response = await getUserInfo(id)
          userInfo.value = {
            id: response.data.id,
            username: response.data.username,
            email: response.data.email,
            is_staff: response.data.is_staff
          }
          localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
        // 如果获取用户信息失败，清除token和用户信息
        token.value = ''
        userInfo.value = null
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
      }
    }
  }

  const login = async (username: string, password: string) => {
    try {
      const response = await loginApi({ username, password })
      
      // 检查响应状态，如果是错误状态，则直接抛出包含message的错误
      if (response.status === 'error') {
        throw new Error(response.message)
      }
      
      token.value = response.data.token
      localStorage.setItem('token', response.data.token)
      
      const fullUserInfo = await getUserInfo(response.data.user.id)
      userInfo.value = {
        id: fullUserInfo.data.id,
        username: fullUserInfo.data.username,
        email: fullUserInfo.data.email,
        is_staff: fullUserInfo.data.is_staff,
      }
      // 保存用户信息到本地存储
      localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    } catch (error) {
      // 直接抛出错误，让调用方处理
      throw error
    }
  }

  const logout = async () => {
    try {
      await logoutApi()
    } finally {
      token.value = ''
      userInfo.value = null
      localStorage.removeItem('token')
    }
  }

  return {
    token,
    userInfo,
    login,
    logout,
    initUserInfo
  }
}) 