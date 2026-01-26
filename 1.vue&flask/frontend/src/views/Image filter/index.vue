<template>
  <ParticleBg
    density="8000"
    speed="0.2"
    flickerSpeed="0.008"
  />

  <div class="latest-image-container">
    <h1>Latest Uploaded Image</h1>
    <router-link to="/" class="btn back-btn">Back to Home</router-link>
    <button class="btn refresh-btn" @click="getLatestImage" :disabled="isLoading">
      {{ isLoading ? 'Loading...' : 'Refresh Latest Image' }}
    </button>

    <div class="status" :class="{ error: isError }">{{ statusText }}</div>

    <!-- HSV滑动条 -->
    <div class="hsv-filter-area" v-if="hasImage">
      <h3>HSV Color Filter (Black Line Extraction)</h3>
      <div class="slider-item">
        <label>H Max: {{ hMax }}</label>
        <!-- 修复：明确绑定value，确保数值实时更新 -->
        <input
          type="range"
          min="0"
          max="180"
          :value="hMax"
          @input="(e) => hMax = Number(e.target.value)"
          class="hsv-slider"
        >
      </div>
      <div class="slider-item">
        <label>S Max: {{ sMax }}</label>
        <input
          type="range"
          min="0"
          max="255"
          :value="sMax"
          @input="(e) => sMax = Number(e.target.value)"
          class="hsv-slider"
        >
      </div>
      <div class="slider-item">
        <label>V Max: {{ vMax }}</label>
        <input
          type="range"
          min="0"
          max="255"
          :value="vMax"
          @input="(e) => vMax = Number(e.target.value)"
          class="hsv-slider"
        >
      </div>
    </div>

    <!-- 图片展示：左右并排 + 高度严格对齐 -->
    <div class="image-area" v-if="hasImage">
      <div class="image-wrap">
        <!-- 原始图片 -->
        <div class="image-box">
          <h4>Original Image</h4>
          <img
            :src="originalImageUrl"
            alt="Original"
            class="img"
            @load="handleImageLoad"
          >
        </div>
        <!-- 筛选后图片 -->
        <div class="image-box">
          <h4>Filtered Black Line Image</h4>
          <canvas ref="canvas" class="img"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import ParticleBg from '@/components/ParticleBg/Black_star.vue';

// 基础数据
const isLoading = ref(false);
const isError = ref(false);
const statusText = ref('Click "Refresh" to get latest image');
const hasImage = ref(false);
const originalImageUrl = ref('');
const canvas = ref(null);
const originalImg = ref(null); // 原始图片对象

// HSV阈值（确保是响应式数据，数值更新可被监听）
const hMax = ref(180);
const sMax = ref(50);
const vMax = ref(200);
const hMin = 0;
const sMin = 0;
const vMin = 0;

const BASE_API_URL = 'http://localhost:5001';

// 图片加载完成后初始化
const handleImageLoad = (e) => {
  originalImg.value = e.target; // 绑定实际加载完成的图片对象
  filterImageByHSV(); // 执行首次筛选
};

// 核心：HSV筛选（前端Canvas实时处理）
const filterImageByHSV = () => {
  if (!originalImg.value || !canvas.value) return;

  const ctx = canvas.value.getContext('2d');
  const img = originalImg.value;

  // 设置canvas与原始图片尺寸完全一致
  canvas.value.width = img.naturalWidth;
  canvas.value.height = img.naturalHeight;
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height);
  ctx.drawImage(img, 0, 0);

  // 获取像素数据并处理
  const imageData = ctx.getImageData(0, 0, canvas.value.width, canvas.value.height);
  const data = imageData.data;

  for (let i = 0; i < data.length; i += 4) {
    // RGB转BGR（对应OpenCV），再转HSV
    const hsv = rgbToHsv(data[i+2], data[i+1], data[i]); // b,g,r

    // 范围筛选
    const inRange = hsv.h >= hMin && hsv.h <= hMax.value &&
                    hsv.s >= sMin && hsv.s <= sMax.value &&
                    hsv.v >= vMin && hsv.v <= vMax.value;

    // 反转掩码，生成黑白图
    const gray = inRange ? 0 : 255;
    const finalGray = 255 - gray;

    // 设置像素
    data[i] = finalGray;
    data[i+1] = finalGray;
    data[i+2] = finalGray;
    data[i+3] = 255;
  }

  ctx.putImageData(imageData, 0, 0);
};

// RGB转HSV（简化版，保证与OpenCV一致）
const rgbToHsv = (r, g, b) => {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const delta = max - min;

  let h = 0, s = 0, v = max * 255;
  if (delta) {
    s = (delta / max) * 255;
    if (max === r) h = ((g - b) / delta) % 6;
    else if (max === g) h = (b - r) / delta + 2;
    else h = (r - g) / delta + 4;
    h = Math.round(h * 30);
    if (h < 0) h += 180;
  }
  return { h, s, v };
};

// 获取最新图片
const getLatestImage = async () => {
  isLoading.value = true;
  try {
    const res = await fetch(`${BASE_API_URL}/get-latest-image`, {
      method: 'GET',
      credentials: 'include',
      mode: 'cors'
    });
    const data = await res.json();
    if (data.success) {
      originalImageUrl.value = `${BASE_API_URL}${data.original_image_url}`;
      hasImage.value = true;
      statusText.value = 'Loaded latest image!';
      // 重置图片对象，等待@load事件绑定
      originalImg.value = null;
    } else {
      statusText.value = 'Error: ' + data.error;
      isError.value = true;
    }
  } catch (err) {
    statusText.value = 'Network Error: ' + err.message;
    isError.value = true;
  } finally {
    isLoading.value = false;
  }
};

// 监听HSV变化，实时触发筛选（确保滑动条数值更新后立即生效）
watch([hMax, sMax, vMax], () => {
  if (hasImage.value && originalImg.value) {
    filterImageByHSV();
  }
});

onMounted(() => {
  getLatestImage();
});
</script>

<style scoped>
.latest-image-container {
  max-width: 100%;
  margin: 50px auto;
  padding: 20px;
  position: relative;
  color: #333;
  text-align: center;
}

.back-btn {
  position: absolute;
  left: 20px;
  top: 60px;
}

.refresh-btn {
  margin: 20px 0;
}

.status {
  margin: 20px 0;
  font-size: 18px;
  text-align: left;
  padding-left: 20px;
  color: #333;
}

.status.error {
  color: red;
}

/* HSV滑动条样式 */
.hsv-filter-area {
  margin: 20px auto;
  padding: 15px 20px;
  border: 1px solid #eee;
  border-radius: 5px;
  max-width: 95%;
  text-align: left;
}

.slider-item {
  margin: 10px 0;
  display: flex;
  align-items: center;
  gap: 15px;
}

.slider-item label {
  width: 100px;
  font-size: 16px;
}

.hsv-slider {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: #ddd;
  outline: none;
  -webkit-appearance: none;
}

.hsv-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #007bff;
  cursor: pointer;
}

/* 图片容器：核心对齐样式（简洁高效） */
.image-area {
  padding: 0 20px;
  margin-top: 30px;
}

.image-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 30px;
  justify-content: flex-start;
  align-items: flex-start;
  width: 100%;
}

/* 图片盒子：强制等高 + 等宽 */
.image-box {
  flex: 1;
  min-width: 300px;
  max-width: calc(50% - 15px);
  text-align: left;
  height: 70vh;
  display: flex;
  flex-direction: column;
}

.image-box h4 {
  margin: 0 0 10px 0;
  font-size: 18px;
  color: #555;
}

/* 图片 + Canvas：严格统一样式，确保高度对齐 */
.img {
  flex: 1;
  width: 100%;
  height: 100%;
  object-fit: contain; /* 完整显示，不裁剪 */
  border: 1px solid #eee;
  border-radius: 5px;
  display: block;
}

/* 按钮通用样式 */
.btn {
  padding: 10px 30px;
  background-color: #007bff;
  color: #fff;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  margin: 10px;
  text-decoration: none;
  transition: background-color 0.3s;
}

.btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.btn:hover:not(:disabled) {
  background-color: #0056b3;
}
</style>