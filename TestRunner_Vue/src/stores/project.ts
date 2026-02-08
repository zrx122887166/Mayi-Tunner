import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getProjects, getProject, type Project } from '@/api/project'

export const useProjectStore = defineStore('project', () => {
  const currentProjectId = ref<string>('')
  const projects = ref<Project[]>([])
  const loading = ref(false)

  // 获取当前选中的项目
  const currentProject = computed(() => 
    currentProjectId.value 
      ? projects.value.find(p => p.id.toString() === currentProjectId.value) || null 
      : null
  )

  // 从 localStorage 恢复选中的项目
  const initFromStorage = () => {
    const stored = localStorage.getItem('currentProjectId')
    if (stored) {
      currentProjectId.value = stored
    }
  }

  // 获取项目列表
  const fetchProjects = async () => {
    loading.value = true
    try {
      const response = await getProjects(1, 100) // 暂时获取前100个项目
      projects.value = response.data.results
      initFromStorage() // 在获取项目列表后恢复存储的项目ID
    } catch (error) {
      console.error('获取项目列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 根据ID获取项目
  const fetchProjectById = async (id: number) => {
    loading.value = true
    try {
      const project = await getProject(id)
      // 如果项目列表中没有这个项目，就添加进去
      if (!projects.value.find(p => p.id === id)) {
        projects.value.push(project.data)
      }
      setCurrentProject(id)
      return project.data
    } catch (error) {
      console.error('获取项目详情失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 设置当前项目
  const setCurrentProject = (projectId: string | number | undefined) => {
    currentProjectId.value = projectId ? projectId.toString() : ''
    if (projectId) {
      localStorage.setItem('currentProjectId', projectId.toString())
    } else {
      localStorage.removeItem('currentProjectId')
    }
  }

  return {
    currentProject,
    currentProjectId,
    projects,
    loading,
    fetchProjects,
    fetchProjectById,
    setCurrentProject,
    initFromStorage
  }
}) 