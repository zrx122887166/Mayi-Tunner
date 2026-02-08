<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { useUserStore } from '../../stores/user'
import { useProjectStore } from '../../stores/project'
import { IconUser, IconLock} from '@arco-design/web-vue/es/icon'

const router = useRouter()
const userStore = useUserStore()
const projectStore = useProjectStore()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const handleSubmit = async () => {
  if (!loginForm.username || !loginForm.password) {
    Message.warning('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    await userStore.login(loginForm.username, loginForm.password)
    Message.success('登录成功')
    
    // 登录成功后检查用户是否有项目
    try {
      await projectStore.fetchProjects()
      if (projectStore.projects.length === 0) {
        Message.info('您还没有项目，请新建项目')
        router.push('/projects') // 跳转到项目页面
      } else {
        router.push('/') // 有项目则跳转到首页
      }
    } catch (error) {
      console.error('获取项目列表失败:', error)
      router.push('/') // 如果获取项目列表失败，仍然跳转到首页
    }
  } catch (error: any) {
    if (error && error.message) {
      Message.error(error.message)
    } else {
      Message.error('登录失败，请稍后重试')
    }
    console.error('登录错误:', error)
  } finally {
    loading.value = false
  }
}

const clearForm = () => {
  loginForm.username = ''
  loginForm.password = ''
}

const handleInputFocus = (event: Event) => {
  const input = event.target as HTMLInputElement
  input.removeAttribute('readonly')
}

onMounted(() => {
  clearForm()
})
</script>

<template>
  <div class="login-container">
    <!-- 背景装饰 -->
    <div class="login-background">
      <div class="shape"></div>
      <div class="shape"></div>
    </div>

    <div class="tw-flex tw-min-h-screen tw-items-center tw-justify-center tw-px-4 tw-relative tw-z-10">
      <!-- 登录卡片 -->
      <div class="login-card">
        <div class="tw-text-center">
          <div class="tw-flex tw-justify-center tw-mb-4">
            <div class="logo-container">
              <span class="logo-text">蚂蚁</span>
            </div>
          </div>
          <h1 class="tw-text-2xl tw-font-bold tw-mb-1 tw-bg-clip-text tw-text-transparent tw-bg-gradient-to-r tw-from-blue-500 tw-to-purple-600">
            蚂蚁自动化测试平台
          </h1>
          <p class="tw-text-gray-500 tw-mb-6 tw-text-sm">多功能自动化测试平台</p>
        </div>

        <a-form
          :model="loginForm"
          @submit="handleSubmit"
          class="tw-space-y-4"
          autocomplete="off"
        >
          <!-- 添加隐藏的假表单来欺骗浏览器 -->
          <div style="display: none">
            <input type="text" name="fakeusernameremembered" />
            <input type="password" name="fakepasswordremembered" />
          </div>
          
          <a-form-item field="username" hide-label class="tw-mb-3">
            <a-input
              v-model="loginForm.username"
              placeholder="用户名"
              :style="{ width: '100%' }"
              size="large"
              class="login-input"
              :readonly="true"
              @focus="handleInputFocus"
              autocomplete="off"
            >
              <template #prefix>
                <icon-user />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item field="password" hide-label class="tw-mb-3">
            <a-input-password
              v-model="loginForm.password"
              placeholder="密码"
              :style="{ width: '100%' }"
              size="large"
              class="login-input"
              :readonly="true"
              @focus="handleInputFocus"
              autocomplete="off"
            >
              <template #prefix>
                <icon-lock />
              </template>
            </a-input-password>
          </a-form-item>

          <div class="tw-flex tw-justify-between tw-items-center tw-mb-4">
            <a-checkbox>记住我</a-checkbox>
            <a-link>忘记密码？</a-link>
          </div>

          <a-button
            type="primary"
            html-type="submit"
            long
            :loading="loading"
            size="large"
            class="login-button"
          >
            登录
          </a-button>
        </a-form>

        <div class="tw-mt-6 tw-text-center tw-text-gray-400 tw-text-xs">
          © {{ new Date().getFullYear() }} AntRunner. All rights reserved.
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="postcss">
.login-container {
  min-height: 100vh;
  background: linear-gradient(45deg, #1a1a1a, #2d3748);
  position: relative;
  overflow: hidden;
}

.login-background {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  overflow: hidden;
}

.shape {
  position: absolute;
  filter: blur(90px);
  transform: rotate(-45deg);
}

.shape:nth-child(1) {
  background: linear-gradient(90deg, #4c6ef5, #15aabf);
  width: 600px;
  height: 600px;
  top: -300px;
  left: -300px;
  opacity: 0.4;
  animation: move 8s infinite alternate;
}

.shape:nth-child(2) {
  background: linear-gradient(90deg, #862e9c, #be4bdb);
  width: 500px;
  height: 500px;
  bottom: -250px;
  right: -250px;
  opacity: 0.4;
  animation: move 10s infinite alternate-reverse;
}

@keyframes move {
  from {
    transform: rotate(-45deg) translate(0, 0);
  }
  to {
    transform: rotate(-45deg) translate(50px, 50px);
  }
}

.login-card {
  @apply tw-bg-gray-900/95 tw-backdrop-blur-md tw-border tw-border-gray-800/50 tw-rounded-xl tw-shadow-2xl;
  width: 480px !important;
  padding: 24px 32px !important;
}

.logo-container {
  @apply tw-w-12 tw-h-12 tw-bg-gradient-to-r tw-from-blue-500 tw-to-indigo-500 tw-rounded-xl tw-flex tw-items-center tw-justify-center tw-shadow-lg;
}

.logo-text {
  @apply tw-text-white tw-text-xl tw-font-bold;
}

.login-input {
  :deep(.arco-input-wrapper) {
    height: 44px !important;
    background-color: rgba(17, 24, 39, 0.7) !important;
    border-color: rgba(75, 85, 99, 0.3) !important;
    border-radius: 8px !important;
    transition: all 0.2s ease-in-out !important;

    &:hover {
      border-color: #60a5fa !important;
      background-color: rgba(17, 24, 39, 0.8) !important;
    }

    &:focus-within {
      border-color: #3b82f6 !important;
      background-color: rgba(17, 24, 39, 0.8) !important;
      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
    }

    .arco-input {
      color: #e2e8f0 !important;
      
      &::placeholder {
        color: #64748b !important;
      }
    }

    .arco-input-prefix {
      margin-right: 10px !important;
      color: #60a5fa !important;
    }

    .arco-input-suffix {
      color: #94a3b8 !important;
    }
  }
}

.login-button {
  height: 42px;
  border-radius: 8px !important;
  background: linear-gradient(135deg, #4c6ef5, #15aabf) !important;
  border: none !important;
  box-shadow: 0 10px 20px rgba(76, 110, 245, 0.2);
  transition: transform 0.2s, box-shadow 0.2s;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(76, 110, 245, 0.25);
}

/* 响应式调整 */
@media (max-width: 640px) {
  .login-card {
    margin: 16px;
    padding: 24px;
  }
}

:deep(.arco-checkbox) {
  .arco-checkbox-label {
    color: #94a3b8 !important;
  }

  .arco-checkbox-icon {
    border-color: #4b5563 !important;
    background-color: rgba(17, 24, 39, 0.7) !important;
  }

  &:hover {
    .arco-checkbox-icon {
      border-color: #60a5fa !important;
    }
  }

  &.arco-checkbox-checked {
    .arco-checkbox-icon {
      background-color: #3b82f6 !important;
      border-color: #3b82f6 !important;
    }
  }
}

:deep(.arco-link) {
  color: #60a5fa !important;
  
  &:hover {
    color: #93c5fd !important;
  }
}
</style> 