<!-- src/components/ParticleBg/index.vue -->
<template>
  <!-- 粒子背景容器：绝对定位覆盖整个页面，层级最低 -->
  <div class="particle-bg" ref="containerRef"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// 1. 定义可配置参数（未来改样式只需调这里）
const props = defineProps({
  color: { // 粒子颜色
    type: String,
    default: '#007bff' // 和按钮主色一致，视觉统一
  },
  density: { // 粒子密度（值越小越密）
    type: Number,
    default: 10000
  },
  speed: { // 粒子移动速度
    type: Number,
    default: 1
  }
})

// 2. 容器引用 + 粒子实例
const containerRef = ref(null)
let canvas = null
let ctx = null
let particles = []
let animationId = null

// 3. 粒子类（核心逻辑）
class Particle {
  constructor() {
    this.x = Math.random() * canvas.width
    this.y = Math.random() * canvas.height
    this.size = Math.random() * 3 + 1
    this.speedX = (Math.random() - 0.5) * props.speed
    this.speedY = (Math.random() - 0.5) * props.speed
    this.color = props.color
  }
  update() {
    this.x += this.speedX
    this.y += this.speedY
    // 超出边界重置
    if (this.x > canvas.width) this.x = 0
    if (this.x < 0) this.x = canvas.width
    if (this.y > canvas.height) this.y = 0
    if (this.y < 0) this.y = canvas.height
  }
  draw() {
    ctx.fillStyle = this.color
    ctx.beginPath()
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
    ctx.fill()
  }
}

// 4. 初始化粒子
function init() {
  // 设置Canvas尺寸为容器大小
  canvas.width = containerRef.value.offsetWidth
  canvas.height = containerRef.value.offsetHeight
  // 创建粒子
  particles = []
  const particleCount = (canvas.width * canvas.height) / props.density
  for (let i = 0; i < particleCount; i++) {
    particles.push(new Particle())
  }
}

// 5. 动画循环
function animate() {
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  particles.forEach(particle => {
    particle.update()
    particle.draw()
  })
  animationId = requestAnimationFrame(animate)
}

// 6. 生命周期：挂载时初始化，卸载时销毁（避免内存泄漏）
onMounted(() => {
  if (!containerRef.value) return
  // 创建Canvas元素（避免污染模板）
  canvas = document.createElement('canvas')
  ctx = canvas.getContext('2d')
  containerRef.value.appendChild(canvas)
  // 初始化 + 启动动画
  init()
  animate()
  // 窗口resize时重新计算尺寸
  window.addEventListener('resize', init)
})

onUnmounted(() => {
  // 销毁动画 + 移除监听（工程化必做：防止内存泄漏）
  cancelAnimationFrame(animationId)
  window.removeEventListener('resize', init)
})
</script>

<style scoped>
/* 粒子背景容器：覆盖整个父容器，层级最低 */
.particle-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1; /* 放在所有内容下方 */
  pointer-events: none; /* 不遮挡鼠标事件（比如按钮点击） */
}
/* Canvas自适应容器 */
.particle-bg canvas {
  width: 100%;
  height: 100%;
}
</style>