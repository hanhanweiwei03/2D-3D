// 等待页面加载完成
document.addEventListener('DOMContentLoaded', () => {
    // 1. 初始化Three.js核心对象
    const container = document.getElementById('viewer-container');
    const loadingText = document.querySelector('.loading');

    // 场景
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf5f5f5);

    // 相机
    const camera = new THREE.PerspectiveCamera(
        75,                     // 视角
        container.clientWidth / container.clientHeight,  // 宽高比
        0.1,                    // 近裁剪面
        10000                   // 远裁剪面
    );
    camera.position.set(50, 50, 100); // 初始相机位置（适配建筑模型）

    // 渲染器
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);
    loadingText.remove(); // 移除加载提示

    // 轨道控制器（支持鼠标交互：旋转、缩放、平移）
    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true; // 阻尼效果，更顺滑
    controls.dampingFactor = 0.05;
    controls.screenSpacePanning = false;
    controls.minDistance = 1;
    controls.maxDistance = 1000;

    // 光源（让模型更清晰）
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7); // 环境光
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8); // 平行光
    directionalLight.position.set(100, 200, 100);
    scene.add(directionalLight);

    // 2. 加载并解析DXF文件
    const parser = new DxfParser();
    fetch('building_3D_50m.dxf')
        .then(response => {
            if (!response.ok) throw new Error('DXF文件加载失败');
            return response.arrayBuffer();
        })
        .then(buffer => {
            // 将二进制转换为文本（DXF为ASCII格式）
            const text = new TextDecoder('utf-8').decode(buffer);
            // 解析DXF为JSON结构
            const dxfData = parser.parseSync(text);
            console.log('DXF解析结果：', dxfData);

            // 3. 解析3D实体并添加到场景
            parseDxfEntities(dxfData.entities, scene);

            // 自动适配模型视角
            fitCameraToScene(camera, controls, scene);
        })
        .catch(error => {
            console.error('错误：', error);
            loadingText.textContent = '加载失败：' + error.message;
            loadingText.style.color = 'red';
        });

    // 4. 窗口大小适配
    window.addEventListener('resize', () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });

    // 5. 渲染循环
    function animate() {
        requestAnimationFrame(animate);
        controls.update(); // 更新控制器
        renderer.render(scene, camera);
    }
    animate();

    /**
     * 解析DXF实体并转换为Three.js几何体
     * @param {Array} entities DXF实体列表
     * @param {THREE.Scene} scene 场景对象
     */
    function parseDxfEntities(entities, scene) {
        if (!entities || entities.length === 0) {
            alert('DXF文件中未找到3D实体');
            return;
        }

        // 材质（可根据图层自定义颜色）
        const defaultMaterial = new THREE.MeshBasicMaterial({
            color: 0x0066cc,
            wireframe: true, // 线框模式（适合查看建筑结构）
            transparent: true,
            opacity: 0.8
        });

        // 遍历所有实体
        entities.forEach(entity => {
            switch (entity.type) {
                // 3D面（最常见的3D实体）
                case '3DFACE':
                    create3DFace(entity, scene, defaultMaterial);
                    break;
                // 多段线（可能包含3D顶点）
                case 'POLYLINE':
                    createPolyline(entity, scene, defaultMaterial);
                    break;
                // 直线（3D线）
                case 'LINE':
                    createLine(entity, scene);
                    break;
                // 可扩展支持其他实体：SOLID、CIRCLE、ARC等
                default:
                    console.log('暂不支持的实体类型：', entity.type);
            }
        });
    }

    /**
     * 创建3D面
     * @param {Object} faceEntity 3DFACE实体
     * @param {THREE.Scene} scene 场景
     * @param {THREE.Material} material 材质
     */
    function create3DFace(faceEntity, scene, material) {
        const points = faceEntity.points;
        if (points.length < 3) return; // 至少3个点构成面

        // 创建几何体
        const geometry = new THREE.BufferGeometry();
        const vertices = [];
        // 提取3D坐标
        points.forEach(point => {
            vertices.push(point.x || 0, point.y || 0, point.z || 0);
        });
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        // 生成面索引（三角化）
        const indices = [0, 1, 2];
        if (points.length === 4) indices.push(0, 2, 3); // 四边形拆分为两个三角形
        geometry.setIndex(indices);

        const mesh = new THREE.Mesh(geometry, material);
        scene.add(mesh);
    }

    /**
     * 创建3D多段线
     * @param {Object} polyEntity POLYLINE实体
     * @param {THREE.Scene} scene 场景
     * @param {THREE.Material} material 材质
     */
    function createPolyline(polyEntity, scene, material) {
        if (!polyEntity.vertices || polyEntity.vertices.length < 2) return;

        const points = [];
        polyEntity.vertices.forEach(v => {
            points.push(new THREE.Vector3(v.x || 0, v.y || 0, v.z || 0));
        });

        // 线几何体
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const line = new THREE.Line(geometry, material);
        scene.add(line);
    }

    /**
     * 创建3D直线
     * @param {Object} lineEntity LINE实体
     * @param {THREE.Scene} scene 场景
     */
    function createLine(lineEntity, scene) {
        const start = lineEntity.start;
        const end = lineEntity.end;
        if (!start || !end) return;

        const points = [
            new THREE.Vector3(start.x || 0, start.y || 0, start.z || 0),
            new THREE.Vector3(end.x || 0, end.y || 0, end.z || 0)
        ];
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({ color: 0xff0000 });
        const line = new THREE.Line(geometry, material);
        scene.add(line);
    }

    /**
     * 自动适配相机视角到整个模型
     * @param {THREE.Camera} camera 相机
     * @param {THREE.OrbitControls} controls 控制器
     * @param {THREE.Scene} scene 场景
     */
    function fitCameraToScene(camera, controls, scene) {
        const box = new THREE.Box3().setFromObject(scene); // 计算模型包围盒
        const center = box.getCenter(new THREE.Vector3()); // 模型中心
        const size = box.getSize(new THREE.Vector3()); // 模型尺寸

        // 调整相机位置
        const maxDim = Math.max(size.x, size.y, size.z);
        const fov = camera.fov * (Math.PI / 180);
        let cameraZ = (maxDim / 2) * Math.tan(fov / 2);
        cameraZ *= 1.5; // 留出一定余量

        camera.position.set(center.x, center.y, cameraZ);
        controls.target = center; // 控制器聚焦到模型中心
        controls.update();
    }
});