<!-- src/components/ParticleBg/index.vue -->
<template>
  <div class="particle-bg" ref="containerRef"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// 可配置参数（星空风格默认值）
const props = defineProps({
  starColor: { // 星星主色（渐变用）
    type: String,
    default: '#ffffff'
  },
  starColorSecondary: { // 星星渐变次色
    type: String,
    default: '#4488ff'
  },
  density: { // 星星密度（值越小越密）
    type: Number,
    default: 8000
  },
  speed: { // 星星移动速度（星空建议低速）
    type: Number,
    default: 0.3
  },
  flickerSpeed: { // 闪烁速度（0=不闪烁）
    type: Number,
    default: 0.005
  }
})

const containerRef = ref(null)
let canvas = null
let ctx = null
let particles = []
let animationId = null

// 星空粒子类（保留原有逻辑）
class Star {
  constructor() {
    this.x = Math.random() * canvas.width
    this.y = Math.random() * canvas.height
    this.size = Math.random() * 2.5 + 0.1
    this.speedX = (Math.random() - 0.5) * props.speed
    this.speedY = (Math.random() - 0.5) * props.speed
    this.alpha = Math.random() * 0.8 + 0.2
    this.alphaStep = Math.random() * props.flickerSpeed * 2 - props.flickerSpeed
  }

  update() {
    this.x += this.speedX
    this.y += this.speedY
    if (this.x > canvas.width) this.x = 0
    if (this.x < 0) this.x = canvas.width
    if (this.y > canvas.height) this.y = 0
    if (this.y < 0) this.y = canvas.height

    this.alpha += this.alphaStep
    if (this.alpha > 1) {
      this.alpha = 1
      this.alphaStep = -Math.abs(this.alphaStep)
    }
    if (this.alpha < 0.1) {
      this.alpha = 0.1
      this.alphaStep = Math.abs(this.alphaStep)
    }
  }

  draw() {
    ctx.save()
    const gradient = ctx.createRadialGradient(
      this.x, this.y, 0,
      this.x, this.y, this.size
    )
    gradient.addColorStop(0, `${props.starColor}${Math.floor(this.alpha * 255).toString(16)}`)
    gradient.addColorStop(1, `${props.starColorSecondary}00`)

    ctx.fillStyle = gradient
    ctx.beginPath()
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
    ctx.fill()
    ctx.restore()
  }
}

// 【核心修改】重新计算容器/画布尺寸（适配页面总高度）
function getPageFullSize() {
  // 取「浏览器视口高度」和「页面内容总高度」的最大值
  const pageHeight = Math.max(
    document.documentElement.scrollHeight,
    document.body.scrollHeight,
    window.innerHeight
  )
  const pageWidth = window.innerWidth
  return { width: pageWidth, height: pageHeight }
}

// 初始化（修改尺寸计算逻辑）
function init() {
  if (!canvas || !containerRef.value) return
  // 改用页面总尺寸，而非容器尺寸
  const { width, height } = getPageFullSize()
  canvas.width = width
  canvas.height = height
  particles = []
  const starCount = (canvas.width * canvas.height) / props.density
  for (let i = 0; i < starCount; i++) {
    particles.push(new Star())
  }
}

// 动画循环（保留原有逻辑）
function animate() {
  ctx.fillStyle = 'rgba(0, 0, 10, 0.1)'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  particles.forEach(star => {
    star.update()
    star.draw()
  })
  animationId = requestAnimationFrame(animate)
}

// 生命周期（补充滚动监听）
onMounted(() => {
  if (!containerRef.value) return
  canvas = document.createElement('canvas')
  ctx = canvas.getContext('2d')
  containerRef.value.appendChild(canvas)

  // 初始化画布为页面总尺寸
  const { width, height } = getPageFullSize()
  canvas.width = width
  canvas.height = height
  ctx.fillStyle = '#000010'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  init()
  animate()
  // 【新增】监听窗口大小变化 + 页面滚动（确保尺寸实时更新）
  window.addEventListener('resize', init)
  window.addEventListener('scroll', init)
})

onUnmounted(() => {
  cancelAnimationFrame(animationId)
  // 移除所有监听
  window.removeEventListener('resize', init)
  window.removeEventListener('scroll', init)
})
</script>

<style scoped>
.particle-bg {
  /* 【核心修改】fixed定位：相对于浏览器视口，始终固定在页面背景 */
  position: fixed;
  top: 0;
  left: 0;
  /* 宽高设为100vw/100%：覆盖整个视口，fixed定位下100%是视口高度 */
  width: 100vw;
  height: 100%;
  z-index: -1;
  pointer-events: none;
  background: #000010; /* 暗黑星空底色 */
  /* 新增：防止画布溢出 */
  overflow: hidden;
}

.particle-bg canvas {
  /* 画布宽高100%：继承容器的fixed尺寸 */
  width: 100%;
  height: 100%;
  /* 新增：消除canvas默认的像素偏移 */
  display: block;
}
</style>