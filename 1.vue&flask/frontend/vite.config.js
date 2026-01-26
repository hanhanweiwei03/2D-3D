import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path' // 新增：导入路径模块

export default defineConfig({
  plugins: [vue()],
  resolve: {
    // 新增：配置路径别名
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  }
})