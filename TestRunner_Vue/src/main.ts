import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ArcoVue from '@arco-design/web-vue'
import App from './App.vue'
import router from './router'

// Monaco Editor 配置
import './utils/monaco'

// 样式导入
import '@arco-design/web-vue/dist/arco.css'
import './styles/tailwind.css'
import './styles/main.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ArcoVue)

app.mount('#app')
