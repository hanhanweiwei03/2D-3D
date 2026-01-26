import cv2
import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt

# 提取独立闭合轮廓（仅保留核心逻辑）
def extract_contours(img_path, threshold=200):
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 筛选有效轮廓+绘制红色轮廓线
    valid_contours = []
    img_vis = img.copy()  # 用于绘制红色轮廓的画布
    for cnt in contours:
        if cv2.contourArea(cnt) > 100:
            valid_contours.append(cnt.reshape(-1, 2).astype(np.float32))
            cv2.drawContours(img_vis, [cnt], -1, (0, 0, 255), 2)  # 红色轮廓

    plot_contours_with_coords(valid_contours, img_vis)

    return valid_contours, img_vis


# 独立封装的坐标系可视化函数（保留独立结构，仅被主函数调用）
def plot_contours_with_coords(contour_list, img_vis, dpi=100):
    """
    可视化轮廓并显示像素坐标系（无变形，匹配图片原始尺寸）
    :param contour_list: 有效轮廓列表
    :param img_vis: 带红色轮廓的图片（原始尺寸）
    :param dpi: matplotlib默认DPI（通常100，无需修改）
    """
    # 转换图片通道（OpenCV BGR → matplotlib RGB）
    img_rgb = cv2.cvtColor(img_vis, cv2.COLOR_BGR2RGB)

    # 关键：根据图片像素尺寸计算画布英寸尺寸（消除形变）
    img_h, img_w = img_rgb.shape[:2]
    fig_width = img_w / dpi  # 宽度（英寸）= 像素宽度 / DPI
    fig_height = img_h / dpi  # 高度（英寸）= 像素高度 / DPI

    # 创建和图片原始尺寸匹配的画布
    plt.figure(figsize=(fig_width, fig_height), dpi=dpi)
    plt.imshow(img_rgb)  # 图片填满画布，无拉伸/压缩

    # 绘制像素坐标系（原点在左上角，X右、Y下）
    plt.xlabel("X (Pixel)", fontsize=12)
    plt.ylabel("Y (Pixel)", fontsize=12)
    plt.grid(True, alpha=0.3, linestyle='--')  # 网格线辅助看坐标
    plt.axis('on')  # 强制显示坐标轴
    plt.title("Building Contours with Pixel Coordinate System", fontsize=14)
    plt.tight_layout(pad=0)  # 去除画布边缘空白
    plt.show()

# 生成带封顶的闭合网格（核心新增功能）
def create_capped_mesh(points_bottom, points_top):
    # 1. 构造侧面（原有逻辑）
    faces = []
    n = len(points_bottom)
    for j in range(n):
        jn = (j + 1) % n
        faces.extend([4, j, jn, jn + n, j + n])

    # 2. 构造底部封顶（三角剖分）
    bottom_face = [n] + list(range(n))  # 底部所有点组成的多边形面
    faces.extend(bottom_face)

    # 3. 构造顶部封顶（三角剖分）
    top_face = [n] + list(range(n, 2 * n))  # 顶部所有点组成的多边形面
    faces.extend(top_face)

    # 合并所有点并生成闭合网格
    all_points = np.vstack([points_bottom, points_top])
    mesh = pv.PolyData(all_points, faces=np.array(faces))
    # 三角化多边形面（确保封顶面能正确渲染）
    mesh = mesh.triangulate()
    return mesh


# 新增：生成塔吊轮廓的函数（返回和建筑轮廓同格式的坐标）
def generate_towercrane_contour(center_x, center_y, width=12, height=12):
    """
    生成塔吊的2D轮廓（矩形，模拟底座/塔身）
    :param center_x: 塔吊中心X坐标（需在建筑轮廓外）
    :param center_y: 塔吊中心Y坐标（需在建筑轮廓外）
    :param width: 塔吊宽度（像素）
    :param height: 塔吊高度（像素）
    :return: 塔吊轮廓坐标 (4,2) float32 数组
    """
    # 计算矩形四个顶点（闭合）
    x1 = center_x - width / 2
    y1 = center_y - height / 2
    x2 = center_x + width / 2
    y2 = center_y - height / 2
    x3 = center_x + width / 2
    y3 = center_y + height / 2
    x4 = center_x - width / 2
    y4 = center_y + height / 2

    # 构造轮廓坐标（格式和建筑轮廓一致：float32，(N,2)）
    crane_contour = np.array([[x1, y1], [x2, y2], [x3, y3], [x4, y4]], dtype=np.float32)
    return crane_contour


# ========== 修复：返回半径网格，而非仅添加到plotter ==========
def add_crane_working_radius(plotter, crane_centers, tower_crane_height, working_radius=150):
    """
    为每个塔吊添加顶部工作半径圆形平面（红色半透明），并返回半径网格列表
    :param plotter: PyVista绘图器对象
    :param crane_centers: 塔吊中心坐标列表 [(cx1, cy1), ...]
    :param tower_crane_height: 塔吊高度（Z轴）
    :param working_radius: 工作半径（默认150）
    :return: 半径网格列表
    """
    radius_meshes = []  # 存储半径网格，用于后续导出
    # 生成圆形顶点（50个点保证平滑）
    theta = np.linspace(0, 2 * np.pi, 50, endpoint=False)
    x = working_radius * np.cos(theta)
    y = working_radius * np.sin(theta)
    z = np.full_like(x, tower_crane_height, dtype=np.float32)

    for (cx, cy) in crane_centers:
        # 平移圆形到塔吊中心
        circle_points = np.column_stack([x + cx, y + cy, z])
        # 手动构造闭合圆形网格（兼容所有PyVista版本）
        faces = [len(circle_points)] + list(range(len(circle_points)))
        circle_mesh = pv.PolyData(circle_points, faces=np.array(faces))
        # 三角化确保渲染正常
        circle_mesh = circle_mesh.triangulate()
        # 添加到绘图器（红色半透明）
        plotter.add_mesh(circle_mesh, color="red", opacity=0.3)
        # 加入半径网格列表（关键：用于导出）
        radius_meshes.append(circle_mesh)

    return radius_meshes

# 核心流程：提取轮廓+2D可视化+保存红色轮廓图
img_path = "/Users/mac-henry/RA_Environment/2D-3D Project setup/Firefly_Gemini Flash_remove noise and text, keep building contour 481034.png"
contour_list, img_vis = extract_contours(img_path, threshold=200)

# 1. 定义5个塔吊的中心坐标（需确保在建筑轮廓外，可根据图片尺寸调整）
crane_centers = [
    (283, 556),  # 塔吊1坐标
    (304, 342),  # 塔吊2坐标
    (598, 167),  # 塔吊3坐标
    (785, 421),  # 塔吊4坐标
    (814, 639)   # 塔吊5坐标
]

# 2. 生成塔吊轮廓并append到contour_list
for idx, (cx, cy) in enumerate(crane_centers):
    crane_contour = generate_towercrane_contour(cx, cy)
    contour_list.append(crane_contour)  # 直接append，格式匹配即可
    print(f"已添加第{idx+1}个塔吊轮廓，坐标中心：({cx}, {cy})")

# 3D拉伸核心逻辑（新增封顶功能）
plotter = pv.Plotter()
all_meshes = []  # 存储所有需要导出的网格（建筑+塔吊+半径）
stretch_height = 200  # 拉伸高度（统一管理）
tower_crane_height= 250
tower_crane_working_R=200

# 处理前5个建筑轮廓
for cnt_2d in contour_list[:5]:
    bottom_3d = np.hstack([cnt_2d, np.zeros((len(cnt_2d), 1), np.float32)])
    top_3d = np.hstack([cnt_2d, np.full((len(cnt_2d), 1), stretch_height, np.float32)])
    mesh = create_capped_mesh(bottom_3d, top_3d)
    plotter.add_mesh(mesh, color="skyblue", opacity=1)
    all_meshes.append(mesh)

# 处理后5个塔吊轮廓（高度250）
for cnt_2d in contour_list[5:]:  # 切片取后5个
    bottom_3d = np.hstack([cnt_2d, np.zeros((len(cnt_2d), 1), np.float32)])
    top_3d = np.hstack([cnt_2d, np.full((len(cnt_2d), 1), tower_crane_height, np.float32)])
    mesh = create_capped_mesh(bottom_3d, top_3d)
    plotter.add_mesh(mesh, color="orange", opacity=1)  # 塔吊用橙色（便于区分）
    all_meshes.append(mesh)

# ========== 修复1：获取半径网格并加入导出列表 ==========
radius_meshes = add_crane_working_radius(plotter, crane_centers, tower_crane_height, tower_crane_working_R)
all_meshes.extend(radius_meshes)  # 半径网格加入导出列表

# ========== 修复2：完整导出所有网格（建筑+塔吊+半径） ==========
# 方案：合并所有网格为单个UnstructuredGrid（兼容所有PyVista版本，无需meshio）
if len(all_meshes) == 1:
    combined_mesh = all_meshes[0]
else:
    # 逐个合并（低版本PyVista兼容）
    combined_mesh = all_meshes[0]
    for mesh in all_meshes[1:]:
        combined_mesh = combined_mesh.merge(mesh)

# 原生导出STL（无依赖，完整包含所有元素）
combined_mesh.save("building_3d_50m.stl")
print("3D模型已导出为 building_3d_50m.stl（包含建筑+塔吊+工作半径）")

# 可视化+导出（文件名称不变）
plotter.add_axes()
plotter.show()