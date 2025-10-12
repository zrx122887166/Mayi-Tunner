<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { getTestCaseById, type TestCase } from '@/api/testcase'
import TestCaseHistoryReports from './components/TestCaseHistoryReports.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const testcase = ref<TestCase | null>(null)

// 分页配置
const pagination = ref({
  current: 1,
  pageSize: 10,
  total: 0,
  showTotal: true,
  showJumper: true,
  showPageSize: true
})

// 获取测试用例信息
const fetchTestCase = async () => {
  const id = Number(route.params.id)
  if (!id) {
    Message.error('测试用例ID无效')
    return
  }

  try {
    loading.value = true
    const response = await getTestCaseById(id)
    if (response && response.status === 'success') {
      testcase.value = response.data
    } else {
      throw new Error(response?.message || '获取测试用例信息失败')
    }
  } catch (error) {
    console.error('获取测试用例信息失败:', error)
    Message.error(error instanceof Error ? error.message : '获取测试用例信息失败')
  } finally {
    loading.value = false
  }
}

// 返回列表
const handleBack = () => {
  router.back()
}

// 处理分页变化
const handlePageChange = (current: number) => {
  pagination.value.current = current
  // 触发子组件的分页更新
  if (testcase.value) {
    // 这里需要通过ref调用子组件的方法
  }
}

onMounted(() => {
  fetchTestCase()
})
</script>

<template>
  <div class="tw-h-full tw-flex tw-flex-col tw-gap-4 tw-p-4">
    <!-- 头部 -->
    <div class="tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-px-6 tw-py-4">
      <div class="tw-flex tw-items-center tw-justify-between">
        <div class="tw-flex tw-items-center tw-gap-4">
          <a-button class="custom-back-button" @click="handleBack">
            <template #icon>
              <icon-arrow-left />
            </template>
            返回
          </a-button>
          <h2 class="tw-text-lg tw-font-medium tw-text-gray-100">
            测试用例「{{ testcase?.name || '加载中...' }}」历史报告
          </h2>
        </div>
      </div>
    </div>

    <!-- 报告列表 -->
    <div class="tw-flex-1 tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-overflow-hidden">
      <div class="tw-h-full tw-p-6">
        <TestCaseHistoryReports
          v-if="testcase"
          ref="historyReportsRef"
          :testcase-id="testcase.id"
          :pagination="pagination"
          @update:pagination="(val) => pagination = val"
        />
      </div>
    </div>

    <!-- 分页区域 -->
    <div class="tw-bg-gray-800/50 tw-rounded-lg tw-shadow-dark tw-px-6 tw-py-5">
      <a-pagination
        v-model:current="pagination.current"
        v-model:pageSize="pagination.pageSize"
        :total="pagination.total"
        show-total
        show-jumper
        show-page-size
        class="tw-flex tw-justify-end"
        @change="handlePageChange"
        @page-size-change="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.custom-back-button {
  @apply !tw-bg-gray-700/50 !tw-border-gray-600 !tw-text-gray-300;
  
  &:hover {
    @apply !tw-bg-gray-700 !tw-border-gray-500 !tw-text-gray-200;
  }
  
  &:active {
    @apply !tw-bg-gray-800 !tw-border-gray-600 !tw-text-gray-300;
  }
}
</style> 