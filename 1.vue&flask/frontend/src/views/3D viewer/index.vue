<template>
  <ParticleBg
    density="6000"
    speed="0.2"
    flickerSpeed="0.008"
  />

  <div class="3d-viewer-container">
    <!-- 新增header容器：放按钮+标题 -->
    <div class="viewer-header">
      <!-- 跳转按钮 -->
      <router-link to="/" class="btn back-btn">
        Back
      </router-link>
      <!-- 标题 -->
      <h1>3D Model（STL）</h1>
    </div>

    <!-- 3D模型组件 -->
    <StlViewer />

    <!-- 可拖动的悬浮容器 -->
    <div
      class="chat-box-float-container"
      ref="chatFloatRef"
      @mousedown="handleDragStart"
    >
      <!-- 可选：加拖动手柄（更直观） -->
      <div class="chat-drag-handle">☰ 拖动</div>
      <ChatBox />
    </div>

  </div>
</template>

<script setup>
import { ref } from 'vue';
// 引入STL查看器组件
import StlViewer from '@/components/StlViewer.vue';
import ParticleBg from '@/components/ParticleBg/Black_star.vue'
import ChatBox from '@/components/ChatBox/chatbox.vue'

// 拖动相关响应式数据
const chatFloatRef = ref(null);
const dragInfo = ref({
  isDragging: false,
  startX: 0,
  startY: 0,
  offsetX: 0,
  offsetY: 0
});
// 开始拖动
const handleDragStart = (e) => {
  // 仅在拖动手柄/容器顶部触发（避免点击输入框时拖动）
  if (e.target.classList.contains('chat-drag-handle') || e.target === chatFloatRef.value) {
    dragInfo.value.isDragging = true;
    // 获取初始位置
    const rect = chatFloatRef.value.getBoundingClientRect();
    dragInfo.value.startX = e.clientX;
    dragInfo.value.startY = e.clientY;
    dragInfo.value.offsetX = rect.left;
    dragInfo.value.offsetY = rect.top;
    // 加鼠标样式
    document.body.style.cursor = 'move';
  }
};
// 拖动中（监听全局mousemove）
document.addEventListener('mousemove', (e) => {
  if (!dragInfo.value.isDragging) return;
  // 计算新位置
  const dx = e.clientX - dragInfo.value.startX;
  const dy = e.clientY - dragInfo.value.startY;
  const newX = dragInfo.value.offsetX + dx;
  const newY = dragInfo.value.offsetY + dy;
  // 限制在可视区域内（避免拖出屏幕）
  const maxX = window.innerWidth - chatFloatRef.value.offsetWidth;
  const maxY = window.innerHeight - chatFloatRef.value.offsetHeight;
  const finalX = Math.max(0, Math.min(newX, maxX));
  const finalY = Math.max(0, Math.min(newY, maxY));
  // 更新位置
  chatFloatRef.value.style.left = `${finalX}px`;
  chatFloatRef.value.style.top = `${finalY}px`;
  chatFloatRef.value.style.right = 'auto'; // 覆盖原有right属性
  chatFloatRef.value.style.bottom = 'auto'; // 覆盖原有bottom属性
});
// 结束拖动
document.addEventListener('mouseup', () => {
  if (dragInfo.value.isDragging) {
    dragInfo.value.isDragging = false;
    document.body.style.cursor = 'default';
  }
});


</script>

<style scoped>
/* 页面总容器 */
.3d-viewer-container {
  position: relative;
  min-height: 100vh;
  z-index: 1;
  padding: 0 20px 20px; /* 移除顶部padding，改到header里更精准 */
  color: #ffffff; /* 文字白色，适配暗黑背景 */
}

/* 头部容器：核心Flex布局 + 顶部留距（关键） */
.viewer-header {
  display: flex;
  align-items: center;
  position: relative;
  padding-top: 60px;      /* 顶部留60px距离（核心！可按需调30-80px） */
  padding-left: 20px;     /* 左侧留距，避免按钮贴边 */
  margin-bottom: 1px;
}

/* 返回按钮：靠左 + 垂直居中于header */
.back-btn {
  position: absolute;
  left: 20px;             /* 离左侧20px，不贴边 */
  top: 50%;               /* 垂直居中于header */
  transform: translateY(-50%); /* 精准居中 */
  z-index: 1;
}

/* 标题：绝对居中 + 适配header顶部间距 */
.viewer-header h1 {
  width: 100%;
  text-align: center;
  margin: 0;
  font-size: 24px;
  /* 标题和按钮垂直对齐，因header有padding-top，自然远离顶部 */
}
/* 原有样式不变，新增以下样式 */
.chat-box-float-container {
  position: fixed;
  right: 30px;
  bottom: 30px;
  z-index: 100;
  box-shadow: 0 0 20px rgba(0, 123, 255, 0.3);
  border-radius: 8px;
  transition: all 0.3s ease;
  /* 加用户选择禁止，避免拖动时选中文字 */
  user-select: none;
}

/* 拖动手柄样式 */
.chat-drag-handle {
  padding: 5px 10px;
  background: #007bff;
  color: #fff;
  text-align: center;
  cursor: move;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  font-size: 12px;
}

/* ChatBox内部样式穿透（避免手柄遮挡） */
.chat-box-float-container >>> .chat-box-container {
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}
</style>