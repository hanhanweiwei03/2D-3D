import { createApp } from 'vue'
import App from './App.vue'
// 导入路由
import router from './router'
// 新增这一行：导入全局样式文件
import './assets/global.css'

// 创建 Vue 实例，挂载路由，挂载到 #app 节点
createApp(App).use(router).mount('#app')