<template>
  <div class="stl-viewer-container" ref="viewerContainer">
    <div class="loading" v-if="isLoading">正在加载STL模型...</div>
    <div class="error" v-if="errorMsg">{{ errorMsg }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';

// 组件状态
const viewerContainer = ref(null);
const isLoading = ref(true);
const errorMsg = ref('');

// Three.js核心对象
let scene, camera, renderer, controls;

// 组件挂载后初始化
onMounted(() => {
  initThree();
  loadAndParseSTL();
});

// 组件卸载时销毁资源
onUnmounted(() => {
  if (renderer) renderer.dispose();
  if (controls) controls.dispose();
  window.removeEventListener('resize', handleResize);
});

// 初始化Three.js场景（核心修改：透明背景 + 适配暗色环境的光源）
function initThree() {
  const container = viewerContainer.value;
  if (!container) return;

  // 场景：背景设为完全透明
  scene = new THREE.Scene();
  scene.background = null; // 关键1：取消纯色背景
  scene.fog = null; // 确保无雾效干扰

  // 相机
  camera = new THREE.PerspectiveCamera(
    75,
    container.clientWidth / container.clientHeight,
    0.1,
    10000
  );
  camera.position.set(50, 50, 100);

  // 渲染器：开启透明（关键2）
  renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true // 核心：开启画布透明
  });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  // 可选：优化透明渲染（避免锯齿）
  renderer.alphaToCoverage = true;
  container.appendChild(renderer.domElement);

  // 轨道控制器
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.screenSpacePanning = false;
  controls.maxPolarAngle = Math.PI;
  controls.minPolarAngle = 0;
  controls.maxAzimuthAngle = Infinity;
  controls.minAzimuthAngle = -Infinity;
  controls.enableRotate = true;
  controls.enablePan = true;
  controls.enableZoom = true;

  // 光源：适配暗色背景（降低环境光，提升模型对比度）
  // 1. 环境光（弱化，避免盖过模型）
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
  scene.add(ambientLight);

  // 2. 主平行光（增强，突出模型）
  const directionalLight1 = new THREE.DirectionalLight(0xffffff, 1.0);
  directionalLight1.position.set(100, 200, 100);
  directionalLight1.castShadow = true;
  scene.add(directionalLight1);

  // 3. 辅助平行光（补光，避免模型暗部过黑）
  const directionalLight2 = new THREE.DirectionalLight(0xffffcc, 0.6);
  directionalLight2.position.set(-100, 150, -100);
  scene.add(directionalLight2);

  // 4. 点光源（局部提亮，增强细节）
  const pointLight = new THREE.PointLight(0xccffff, 0.4);
  pointLight.position.set(50, 50, 50);
  scene.add(pointLight);

  // 窗口适配
  window.addEventListener('resize', handleResize);

  // 渲染循环
  animate();
}

// 加载并解析STL文件（核心修改：高对比度模型配色）
function loadAndParseSTL() {
  const loader = new STLLoader();
  loader.load(
    '/building_3d_50m.stl',
    (geometry) => {
      // 高对比度配色方案（亮青色+金色描边，适配暗黑星空）
      // 表面材质：亮青色（#00e5ff）- 暗黑背景下视觉突出且不刺眼
      const surfaceMaterial = new THREE.MeshPhongMaterial({
        color: 0x00e5ff,    // 主色：亮青色（和星空对比强烈）
        shininess: 80,      // 高光强度：增强质感
        specular: 0xffffcc, // 高光颜色：浅金色（柔和不刺眼）
        transparent: false,
        opacity: 1,
        wireframe: false
      });

      // 可选：添加线框描边（增强模型轮廓，视觉更清晰）
      const wireframeMaterial = new THREE.LineBasicMaterial({
        color: 0xffd700, // 线框色：金色（和主色呼应，对比星空）
        linewidth: 1
      });
      const wireframe = new THREE.WireframeGeometry(geometry);
      const line = new THREE.LineSegments(wireframe, wireframeMaterial);

      // 创建模型网格并添加到场景
      const mesh = new THREE.Mesh(geometry, surfaceMaterial);
      scene.add(mesh);
      scene.add(line); // 添加线框描边

      // 适配相机视角
      fitCameraToScene();
      isLoading.value = false;
    },
    (xhr) => {
      console.log(`加载进度：${(xhr.loaded / xhr.total) * 100}%`);
    },
    (err) => {
      errorMsg.value = 'STL加载失败：' + err.message;
      isLoading.value = false;
      console.error(err);
    }
  );
}

// 适配相机到模型
function fitCameraToScene() {
  const box = new THREE.Box3().setFromObject(scene);
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());

  const maxDim = Math.max(size.x, size.y, size.z);
  const fov = camera.fov * (Math.PI / 180);
  const cameraZ = (maxDim / 2) / Math.tan(fov / 2) * 1.5;

  camera.position.set(center.x, center.y, cameraZ);
  controls.target = center;
  controls.update();
}

// 窗口调整
function handleResize() {
  if (!camera || !renderer || !viewerContainer.value) return;
  camera.aspect = viewerContainer.value.clientWidth / viewerContainer.value.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(viewerContainer.value.clientWidth, viewerContainer.value.clientHeight);
}

// 渲染循环
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
</script>

<style scoped>
.stl-viewer-container {
  width: 100%;
  height: 100vh;
  position: relative;
  /* 确保容器背景透明（和Three.js画布呼应） */
  background: transparent !important;
}

.loading, .error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 16px;
  /* 文字适配暗黑背景 */
  color: #ffffff !important;
  text-shadow: 0 0 5px rgba(0,0,0,0.5); /* 增强文字可读性 */
}

.error {
  color: #ff4444 !important; /* 错误文字用亮红，对比更强烈 */
}
</style>