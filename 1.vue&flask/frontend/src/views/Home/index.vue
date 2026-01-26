<template>
  <ParticleBg
    density="10000"
    speed="0.2"
    flickerSpeed="0.008"
  />

  <div class="container">
    <h1>Construction Drawing Objects Detection</h1>

    <!-- 上传区域 -->
    <div
      class="upload-area"
      @click="triggerFileInput"
      :class="{ hover: isUploadHover }"
    >
      <p>Click to upload JPG/PNG format picture</p>
      <input
        type="file"
        id="file-input"
        accept=".jpg, .png"
        class="file-input"
        @change="handleFileChange"
      >
    </div>

    <!-- 文件名展示 -->
    <p id="file-name">{{ fileNameText }}</p>

    <!-- 识别按钮 -->
    <button
      class="btn"
      :disabled="!selectedFile || isDetecting"
      @click="handleDetect"
    >
      {{ isDetecting ? 'Detecting...' : 'Start Detection' }}
    </button>

    <!-- 新增：Image filter跳转按钮 -->
    <router-link to="/Imagefilter" class="btn">
      Image Filter
    </router-link>

    <!-- 新增：Gemini 2.5 flash跳转按钮 -->
    <router-link to="/VL-model" class="btn">
      Gemini 2.5 flash
    </router-link>

    <!-- 新增：3D模型跳转按钮 -->
    <router-link to="/3d-viewer" class="btn">
      3D Model
    </router-link>

    <!-- 状态提示 -->
    <div class="status" :class="{ error: isError }">{{ statusText }}</div>

    <!-- 结果展示 -->
    <div id="result-area" v-if="showResult">
      <h3>Detection result（Totally<span id="detect-count">{{ detectCount }}</span>Tower Cranes）</h3>
      <img id="result-image" :src="resultImageUrl" alt="Result" v-if="resultImageUrl">
    </div>
    <!-- demo present -->
    <div id="step1-result-area" v-if="showResult">
      <img id="step1-result-image" src="/step1-picture-preprocess.png" alt="picture after data process">
    </div>
    <div id="step2-result-area" v-if="showResult">
      <img id="step2-result-image" src="/step2-picture-fix-by-gemini-flash.png" alt="picture after data process">
    </div>
    <div id="step3-result-area" v-if="showResult">
      <img id="step3-result-image" src="/step3-extract-pixel-point.png" alt="picture after data process">
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import ParticleBg from '@/components/ParticleBg/Black_star.vue'

// 响应式数据
const selectedFile = ref(null); // 选中的文件
const fileNameText = ref('Please select documents'); // 文件名展示文本
const isUploadHover = ref(false); // 上传区域hover状态
const isDetecting = ref(false); // 是否正在识别
const statusText = ref(''); // 状态提示文本
const isError = ref(false); // 是否是错误状态
const showResult = ref(false); // 是否显示结果区域
const detectCount = ref(0); // 识别到的塔吊数量
const resultImageUrl = ref(''); // 结果图片URL

// 触发文件选择框
const triggerFileInput = () => {
  document.getElementById('file-input').click();
};

// 处理文件选择
const handleFileChange = (e) => {
  const file = e.target.files[0];
  if (file) {
    selectedFile.value = file;
    fileNameText.value = `Selected：${file.name}`;
    statusText.value = '';
    isError.value = false;
    showResult.value = false; // 隐藏之前的结果
  } else {
    selectedFile.value = null;
    fileNameText.value = 'Please select documemts';
  }
};

// 处理识别逻辑
const handleDetect = async () => {
  if (!selectedFile.value) return;

  // 重置状态
  isDetecting.value = true;
  statusText.value = 'Detecting，please wait...';
  isError.value = false;
  showResult.value = false;

  // 构建FormData
  const formData = new FormData();
  formData.append('file', selectedFile.value);

  try {
    // 核心修正：补全后端完整地址，语法无错误
    const response = await fetch('http://localhost:5001/upload', {
      method: 'POST',
      body: formData,
      credentials: 'include', // 跨域携带Cookie
      mode: 'cors' // 显式跨域
    });

    if (!response.ok) {
      throw new Error(`请求失败：${response.status}`);
    }

    const data = await response.json();

    if (data.success) {
      // 识别成功：补全图片URL的后端域名
      statusText.value = 'Detection Finished！';
      detectCount.value = data.detect_count || 0;
      resultImageUrl.value = `http://localhost:5001${data.result_image_url}`; // 修正拼接语法
      showResult.value = true;
    } else {
      // 业务错误：修复模板字符串语法
      statusText.value = '错误：' + (data.error || '未知错误'); // 替换模板字符串为普通拼接，避免解析错误
      isError.value = true;
    }
  } catch (error) {
    // 网络/系统错误：同样替换模板字符串
    statusText.value = '网络错误：' + error.message;
    isError.value = true;
    console.error('检测接口报错：', error);
  } finally {
    isDetecting.value = false;
  }
};
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: Arial, sans-serif;
}
.container {
  max-width: 1200px;
  margin: 50px auto;
  padding: 20px;
  text-align: center;
}
.upload-area {
  border: 2px dashed #ccc;
  padding: 50px;
  margin: 20px 0;
  cursor: pointer;
  transition: border-color 0.3s;
}
.upload-area.hover {
  border-color: #007bff;
}
.file-input {
  display: none;
}
.btn {
  padding: 10px 30px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  margin: 10px;
  transition: background-color 0.3s;
}
.btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
#result-area {
  margin-top: 30px;
}
#result-image {
  max-width: 100%;
  border: 1px solid #ddd;
  border-radius: 5px;
  margin-top: 10px;
}
#step1-result-image{
  max-width: 100%;
  border: 1px solid #ddd;
  border-radius: 5px;
  margin-top: 10px;
}
#step2-result-image{
  max-width: 100%;
  border: 1px solid #ddd;
  border-radius: 5px;
  margin-top: 10px;
}
#step3-result-image{
  max-width: 100%;
  border: 1px solid #ddd;
  border-radius: 5px;
  margin-top: 10px;
}
.status {
  margin: 20px 0;
  font-size: 18px;
  color: #333;
}
.status.error {
  color: red;
}
</style>