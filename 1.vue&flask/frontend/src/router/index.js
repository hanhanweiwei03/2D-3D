// 导入路由核心方法
import { createRouter, createWebHistory } from 'vue-router'
// 导入首页组件
import Home from '@/views/Home/index.vue'
import Dxf3DViewer from '@/views/3D viewer/index.vue'; // 引入3D viewer视图
import VLmodel from '@/views/VL model/index.vue';
import Imagefilter from '@/views/Image filter/index.vue'

// 路由规则：URL → 页面的对应关系
const routes = [
  {
    path: '/',        // 根路径（浏览器访问 localhost:5173/）
    name: 'Home',     // 路由名称（可选）
    component: Home   // 对应首页组件
  },
  {
    path: '/3d-viewer', // 访问路径
    name: '3DViewer',
    component: Dxf3DViewer
  },
  {
    path: '/VL-model',
    name: 'VLmodel',
    component: VLmodel
  },
  {
    path: '/Imagefilter',
    name: 'Imagefilter',
    component: Imagefilter
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(), // 路由模式（默认）
  routes                       // 传入路由规则
})

// 导出路由，供 main.js 使用
export default router