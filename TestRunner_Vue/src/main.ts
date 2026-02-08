import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ArcoVue from '@arco-design/web-vue'
import App from './App.vue'
import router from './router'
import './utils/monaco'

import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'  
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// Monaco Editor 配置
import './utils/monaco'

// 样式导入
import '@arco-design/web-vue/dist/arco.css'
import './styles/tailwind.css'
import './styles/main.css'



const app = createApp(App)


app.use(ElementPlus)
// 注册所有图标（可选，若代码中用到Element图标）
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }
  

app.use(createPinia())
app.use(router)
app.use(ArcoVue)

app.mount('#app')
