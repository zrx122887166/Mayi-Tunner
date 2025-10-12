<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  visible: boolean
  width?: string | number
  maskClosable?: boolean
}>()

const emit = defineEmits(['update:visible', 'close'])

const dialogRef = ref<HTMLElement | null>(null)

// 处理点击遮罩层关闭
const handleMaskClick = (e: MouseEvent) => {
  if (props.maskClosable && e.target === dialogRef.value) {
    emit('update:visible', false)
    emit('close')
  }
}

// 处理ESC键关闭
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.visible) {
    emit('update:visible', false)
    emit('close')
  }
}

// 监听可见性变化
watch(() => props.visible, (newVal) => {
  if (newVal) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <Transition name="dialog-fade">
    <div
      v-if="visible"
      ref="dialogRef"
      class="custom-dialog-mask"
      @click="handleMaskClick"
    >
      <Transition name="dialog-zoom">
        <div
          v-if="visible"
          class="custom-dialog"
          :style="{ width: typeof width === 'number' ? `${width}px` : width }"
          @click.stop
        >
          <slot></slot>
        </div>
      </Transition>
    </div>
  </Transition>
</template>

<style scoped>
.custom-dialog-mask {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 1000;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  padding-top: 0;
}

.custom-dialog {
  background-color: transparent;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

/* 遮罩层动画 */
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.3s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

/* 对话框动画 */
.dialog-zoom-enter-active,
.dialog-zoom-leave-active {
  transition: all 0.3s ease;
}

.dialog-zoom-enter-from,
.dialog-zoom-leave-to {
  transform: scale(0.5);
  opacity: 0;
}
</style>