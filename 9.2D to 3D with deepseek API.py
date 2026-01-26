import cv2
import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt
import requests
import json

# ========== 核心配置（双窗口共存关键） ==========
plt.rcParams['figure.max_open_warning'] = 0
plt.ion()  # 开启matplotlib交互模式，非阻塞显示


# ========== 核心函数（精简版） ==========
def extract_contours(img_path, threshold=200):
    """提取轮廓并显示坐标图（非阻塞）"""
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    valid_contours = []
    img_vis = img.copy()
    for cnt in contours:
        if cv2.contourArea(cnt) > 100:
            valid_contours.append(cnt.reshape(-1, 2).astype(np.float32))
            cv2.drawContours(img_vis, [cnt], -1, (0, 0, 255), 2)

    # 显示坐标图（非阻塞）
    img_rgb = cv2.cvtColor(img_vis, cv2.COLOR_BGR2RGB)
    img_h, img_w = img_rgb.shape[:2]
    fig = plt.figure(figsize=(img_w / 100, img_h / 100), dpi=100)
    plt.imshow(img_rgb)
    plt.xlabel("X (Pixel)"), plt.ylabel("Y (Pixel)")
    plt.grid(True, alpha=0.3, linestyle='--'), plt.axis('on')
    plt.title("Building Contours with Pixel Coordinate System"), plt.tight_layout(pad=0)
    plt.show(block=False)  # matplotlib支持block参数
    return valid_contours, img_vis


def create_capped_mesh(points_bottom, points_top):
    """生成带封顶的网格"""
    faces = []
    n = len(points_bottom)
    for j in range(n):
        jn = (j + 1) % n
        faces.extend([4, j, jn, jn + n, j + n])
    bottom_face = [n] + list(range(n))
    faces.extend(bottom_face)
    top_face = [n] + list(range(n, 2 * n))
    faces.extend(top_face)

    all_points = np.vstack([points_bottom, points_top])
    mesh = pv.PolyData(all_points, faces=np.array(faces)).triangulate()
    return mesh


def generate_towercrane_contour(center_x, center_y, width=12, height=12):
    """生成塔吊轮廓"""
    x1, y1 = center_x - width / 2, center_y - height / 2
    x2, y2 = center_x + width / 2, center_y - height / 2
    x3, y3 = center_x + width / 2, center_y + height / 2
    x4, y4 = center_x - width / 2, center_y + height / 2
    return np.array([[x1, y1], [x2, y2], [x3, y3], [x4, y4]], dtype=np.float32)


def add_crane_working_radius(plotter, crane_centers, tower_crane_height, working_radius=150):
    """添加塔吊工作半径"""
    theta = np.linspace(0, 2 * np.pi, 50, endpoint=False)
    x, y = working_radius * np.cos(theta), working_radius * np.sin(theta)
    z = np.full_like(x, tower_crane_height, dtype=np.float32)

    for cx, cy in crane_centers:
        circle_points = np.column_stack([x + cx, y + cy, z])
        faces = [len(circle_points)] + list(range(len(circle_points)))
        circle_mesh = pv.PolyData(circle_points, faces=np.array(faces)).triangulate()
        plotter.add_mesh(circle_mesh, color="red", opacity=0.3)


def render_3d_model(params, contour_list, crane_centers):
    """立即渲染3D模型（修复PyVista无block参数问题）"""
    # 关闭旧的3D窗口（避免多窗口堆积）
    pv.close_all()
    # 创建新的Plotter
    plotter = pv.Plotter()
    # 渲染建筑
    for cnt_2d in contour_list[:5]:
        bottom_3d = np.hstack([cnt_2d, np.zeros((len(cnt_2d), 1), np.float32)])
        top_3d = np.hstack([cnt_2d, np.full((len(cnt_2d), 1), params['stretch_height'], np.float32)])
        plotter.add_mesh(create_capped_mesh(bottom_3d, top_3d), color="skyblue", opacity=1)
    # 渲染塔吊
    for cnt_2d in contour_list[5:]:
        bottom_3d = np.hstack([cnt_2d, np.zeros((len(cnt_2d), 1), np.float32)])
        top_3d = np.hstack([cnt_2d, np.full((len(cnt_2d), 1), params['tower_crane_height'], np.float32)])
        plotter.add_mesh(create_capped_mesh(bottom_3d, top_3d), color="orange", opacity=1)
    # 添加工作半径
    add_crane_working_radius(plotter, crane_centers, params['tower_crane_height'], params['tower_crane_working_R'])

    plotter.add_axes()
    # PyVista的show()无block参数，直接调用（后台渲染，窗口自动弹出）
    plotter.show()
    # 保存STL
    pv.save_meshio("building_3d_50m.stl", pv.MultiBlock(plotter.meshes))
    print(f"\n✅ 3D模型已重新渲染！当前参数：{params}")


def call_deepseek_api(prompt, current_params, api_key):
    """调用DeepSeek API，识别意图并返回结果"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    params_str = json.dumps(current_params, ensure_ascii=False)

    # 系统提示词：区分闲聊/查参数/改参数
    system_prompt = f"""
    你是3D模型参数助手，规则：
    1. 闲聊：用户说无关参数的话（如你好、天气），友好回复（纯文字）；
    2. 查询参数：用户问参数相关（如当前参数、塔吊高度），返回参数信息（纯文字）；
    3. 修改参数：用户要求改参数（如塔吊高度改为300），仅返回JSON格式参数字典（无其他文字），变量名：
       stretch_height/ tower_crane_height/ tower_crane_working_R
    当前参数：{params_str}
    """

    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(data)).json()
        content = resp["choices"][0]["message"]["content"].strip()
        # 识别意图：先判断是否是修改参数（JSON）
        try:
            return "modify", json.loads(content)
        except:
            # 判断是否是查询参数
            if any(key in prompt for key in ["参数", "高度", "半径", "多少"]):
                return "query", content
            # 否则是闲聊
            else:
                return "chat", content
    except Exception as e:
        return "error", f"API调用失败：{str(e)}"


# ========== 主流程（核心：多轮对话+改参数立即渲染） ==========
if __name__ == "__main__":
    # 基础配置
    DEEPSEEK_API_KEY = "sk-93bce4d30eae4f0d99de4b6b93e59e88"
    img_path = "/Users/mac-henry/RA_Environment/2D-3D Project setup/Firefly_Gemini Flash_remove noise and text, keep building contour 481034.png"
    crane_centers = [(283, 556), (304, 342), (598, 167), (785, 421), (814, 639)]
    params = {"stretch_height": 200, "tower_crane_height": 250, "tower_crane_working_R": 200}

    # 1. 初始化：提取轮廓+显示坐标图（非阻塞）
    contour_list, _ = extract_contours(img_path)
    # 添加塔吊轮廓
    for idx, (cx, cy) in enumerate(crane_centers):
        contour_list.append(generate_towercrane_contour(cx, cy))

    # 2. 多轮对话主循环
    print("===== 3D模型智能对话助手 =====")
    print("📌 支持：闲聊/查询参数/修改参数（改参数立即渲染）")
    print("📌 输入“退出”关闭所有窗口\n")

    while True:
        user_input = input("请输入指令：")
        # 退出条件
        if user_input.strip() in ["退出", "quit", "exit"]:
            print("✅ 退出程序，关闭所有窗口...")
            plt.close('all')
            pv.close_all()
            break
        # 空输入跳过
        if not user_input.strip():
            print("⚠️ 请输入有效指令！\n")
            continue
        # API Key验证
        if DEEPSEEK_API_KEY.strip() == "" or DEEPSEEK_API_KEY == "your_deepseek_api_key_here":
            print("⚠️ API Key未配置！\n")
            continue

        # 3. 调用API识别意图
        resp_type, content = call_deepseek_api(user_input, params, DEEPSEEK_API_KEY)

        # 4. 按意图处理
        if resp_type == "chat":
            print(f"🤖 助手回复：{content}\n")
        elif resp_type == "query":
            print(f"📊 参数查询：{content}\n")
        elif resp_type == "modify":
            params.update(content)
            # 改参数立即渲染3D模型（修复后）
            render_3d_model(params, contour_list, crane_centers)
        elif resp_type == "error":
            print(f"❌ {content}\n")

        # 保持matplotlib窗口存活
        plt.pause(0.1)