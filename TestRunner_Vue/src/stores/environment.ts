import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getEnvironments, type Environment } from '../api/environment'
import { Message } from '@arco-design/web-vue'

export const useEnvironmentStore = defineStore('environment', () => {
  const currentEnvironmentId = ref<string>('')
  const environments = ref<Environment[]>([])
  const loading = ref(false)

  // 从localStorage初始化
  const initFromStorage = () => {
    const storedId = localStorage.getItem('currentEnvironmentId')
    if (storedId) {
      currentEnvironmentId.value = storedId
    }
  }

  // 获取环境列表
  const fetchEnvironments = async (projectId?: number) => {
    if (!projectId) {
      environments.value = []
      setCurrentEnvironment(null)
      return
    }

    try {
      loading.value = true
      const response = await getEnvironments({
        project_id: projectId,
        page_size: 100
      })
      environments.value = response.data.results
      
      // 如果有存储的环境ID，检查它是否在当前环境列表中
      const storedId = localStorage.getItem('currentEnvironmentId')
      if (storedId && response.data.results.some(env => env.id.toString() === storedId)) {
        setCurrentEnvironment(storedId)
      }
      // 如果没有存储的环境ID或存储的环境不在当前列表中，且有环境数据，则选择第一个
      else if (response.data.results.length > 0) {
        setCurrentEnvironment(response.data.results[0].id)
      } else {
        setCurrentEnvironment(null)
      }
    } catch (error) {
      console.error('获取环境列表失败:', error)
      Message.error('获取环境列表失败')
      environments.value = []
      setCurrentEnvironment(null)
    } finally {
      loading.value = false
    }
  }

  // 设置当前环境
  const setCurrentEnvironment = (environmentId: string | number | boolean | Record<string, any> | (string | number | boolean | Record<string, any>)[] | null) => {
    if (!environmentId || typeof environmentId === 'boolean') {
      currentEnvironmentId.value = ''
      localStorage.removeItem('currentEnvironmentId')
      return
    }
    
    const idString = String(environmentId)
    currentEnvironmentId.value = idString
    localStorage.setItem('currentEnvironmentId', idString)
  }

  return {
    currentEnvironmentId,
    environments,
    loading,
    initFromStorage,
    fetchEnvironments,
    setCurrentEnvironment
  }
}) 