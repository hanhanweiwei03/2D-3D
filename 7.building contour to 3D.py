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
def plot_contours_with_coords(contour_list, img_vis, figsize=(10, 8)):
    """
    可视化轮廓并显示像素坐标系（独立函数，被extract_contours调用）
    :param contour_list: 有效轮廓列表
    :param img_vis: 带红色轮廓的图片
    :param figsize: 画布大小（可选）
    """
    # 转换图片通道（OpenCV BGR → matplotlib RGB）
    img_rgb = cv2.cvtColor(img_vis, cv2.COLOR_BGR2RGB)

    # 创建画布+显示图片
    plt.figure(figsize=figsize)
    plt.imshow(img_rgb)

    # 绘制像素坐标系（原点在左上角，X右、Y下）
    plt.xlabel("X (Pixel)", fontsize=12)
    plt.ylabel("Y (Pixel)", fontsize=12)
    plt.grid(True, alpha=0.3, linestyle='--')  # 网格线辅助看坐标
    plt.axis('on')  # 强制显示坐标轴
    plt.title("Building Contours with Pixel Coordinate System", fontsize=14)
    plt.tight_layout()
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


# 核心流程：提取轮廓+2D可视化+保存红色轮廓图
img_path = "/Users/mac-henry/RA_Environment/2D-3D Project setup/Original_data/3.building contour by gemini/1.80.png"
contour_list, img_vis = extract_contours(img_path, threshold=200)

# 2D可视化+保存红色轮廓图（核心保留环节）
cv2.imshow("Contours", cv2.resize(img_vis, (800, 600)))
cv2.imwrite("contour_vis.png", img_vis)  # 保存红色轮廓图
cv2.waitKey(3000)
cv2.destroyAllWindows()
print(f"提取到{len(contour_list)}个独立轮廓，红色轮廓图已保存为contour_vis.png")

# 3D拉伸核心逻辑（新增封顶功能）
plotter = pv.Plotter()
all_meshes = []
stretch_height = 200  # 拉伸高度（统一管理）
for cnt_2d in contour_list:
    # 生成底部/顶部3D点
    bottom_3d = np.hstack([cnt_2d, np.zeros((len(cnt_2d), 1), np.float32)])
    top_3d = np.hstack([cnt_2d, np.full((len(cnt_2d), 1), stretch_height, np.float32)])

    # 生成带封顶的闭合网格（核心修改）
    mesh = create_capped_mesh(bottom_3d, top_3d)

    plotter.add_mesh(mesh, color="skyblue", opacity=1)
    all_meshes.append(mesh)

# 可视化+导出（文件名称不变）
plotter.add_axes()
plotter.show()
pv.save_meshio("building_3d_50m.stl", pv.MultiBlock(all_meshes))
print("3D模型已导出为 building_3d_50m.stl（带顶部/底部封顶）")