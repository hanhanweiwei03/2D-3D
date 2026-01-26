import os
import uuid
import numpy as np
import cv2
from flask import Blueprint, request, jsonify, send_file, send_from_directory
from ultralytics import YOLO

# 1. 创建蓝图（命名为home）
home_bp = Blueprint('home', __name__)

# 2. 配置路径（基于当前文件定位资源）
# 获取home.py所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 项目根目录（向上两级：backend/blueprints → backend → 项目根目录）
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))

# 模型路径（替换为你的实际模型路径）
MODEL_PATH = os.path.join(PROJECT_ROOT, "models/best.pt")
# 临时文件目录（放在项目根目录下）
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "temp_uploads")
RESULT_FOLDER = os.path.join(PROJECT_ROOT, "temp_results")

# 创建目录（确保存在）
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# ========== 新增：全局变量存储最新上传图片信息 ==========
latest_image_info = {
    "file_id": None,
    "file_ext": None,
    "is_exists": False
}
# ========== 检测函数（复用原有逻辑） ==========
def slice_large_image(image, slice_size=640, overlap_ratio=0.2):
    h, w = image.shape[:2]
    step = int(slice_size * (1 - overlap_ratio))
    slices = []
    for y in range(0, h, step):
        for x in range(0, w, step):
            y_end = min(y + slice_size, h)
            x_end = min(x + slice_size, w)
            sub_img = image[y:y_end, x:x_end]
            if sub_img.shape[0] < slice_size or sub_img.shape[1] < slice_size:
                pad_h = slice_size - sub_img.shape[0]
                pad_w = slice_size - sub_img.shape[1]
                sub_img = cv2.copyMakeBorder(sub_img, 0, pad_h, 0, pad_w,
                                             cv2.BORDER_CONSTANT, value=(0, 0, 0))
            slices.append((sub_img, x, y))
    return slices


def merge_detections(all_detections, slice_size=640, conf_thres=0.5, iou_thres=0.4):
    all_boxes = []
    all_confs = []
    all_cls = []
    for det, x_off, y_off in all_detections:
        if len(det.boxes) == 0:
            continue
        boxes = det.boxes.xyxy.cpu().numpy()
        confs = det.boxes.conf.cpu().numpy()
        cls = det.boxes.cls.cpu().numpy()
        valid_mask = confs > conf_thres
        boxes = boxes[valid_mask]
        confs = confs[valid_mask]
        cls = cls[valid_mask]
        boxes[:, 0] += x_off
        boxes[:, 1] += y_off
        boxes[:, 2] += x_off
        boxes[:, 3] += y_off
        all_boxes.extend(boxes)
        all_confs.extend(confs)
        all_cls.extend(cls)
    if len(all_boxes) == 0:
        return np.array([]), np.array([]), np.array([])
    indices = cv2.dnn.NMSBoxes(
        [box.tolist() for box in all_boxes],
        all_confs,
        conf_thres,
        iou_thres
    )
    if isinstance(indices, (int, np.integer)):
        indices = [indices]
    else:
        indices = indices.flatten()
    final_boxes = np.array(all_boxes)[indices]
    final_confs = np.array(all_confs)[indices]
    final_cls = np.array(all_cls)[indices]
    return final_boxes, final_confs, final_cls


def detect_large_image(model_path, img_path, save_result_path):
    model = YOLO(model_path)
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"无法读取图片：{img_path}")
    img_copy = img.copy()

    slices = slice_large_image(img, slice_size=640, overlap_ratio=0.2)
    all_detections = []
    for i, (sub_img, x_off, y_off) in enumerate(slices):
        results = model(sub_img, conf=0.5, device="cpu", imgsz=640)
        all_detections.append((results[0], x_off, y_off))

    final_boxes, final_confs, final_cls = merge_detections(
        all_detections, slice_size=640, conf_thres=0.5
    )

    # 绘制红色检测框
    for box, conf in zip(final_boxes, final_confs):
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(img_copy, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(img_copy, f"tower_crane {conf:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # 保存检测后的图片
    print(f"【调试】检测结果保存到：{save_result_path}")
    cv2.imwrite(save_result_path, img_copy)
    return len(final_boxes)


# ========== 路由注册（绑定到蓝图） ==========
# 根路由（返回前端页面，需确保前端构建后静态文件路径正确）
@home_bp.route('/')
def index():
    return "塔吊检测后端服务已启动，前端请访问：http://localhost:5173"


# 上传接口
# ========== 原有代码不变，修改 upload_image 接口，更新最新图片信息 ==========
@home_bp.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "未上传图片"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "文件名为空"}), 400

    # 格式校验
    allowed_extensions = ['.jpg', '.jpeg', '.png']
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return jsonify({"error": "仅支持JPG/PNG格式"}), 400

    # 保存文件
    file_id = str(uuid.uuid4())
    upload_path = os.path.join(UPLOAD_FOLDER, f"{file_id}{file_ext}")
    result_path = os.path.join(RESULT_FOLDER, f"{file_id}{file_ext}")
    file.save(upload_path)
    print(f"【调试】上传文件保存到：{upload_path}")

    try:
        detect_count = detect_large_image(MODEL_PATH, upload_path, result_path)

        # ========== 新增：更新最新图片信息 ==========
        global latest_image_info
        latest_image_info["file_id"] = file_id
        latest_image_info["file_ext"] = file_ext
        latest_image_info["is_exists"] = True

        return jsonify({
            "success": True,
            "detect_count": detect_count,
            "result_image_url": f"/result/{file_id}"
        })
    except Exception as e:
        print(f"【错误】检测失败：{str(e)}")
        return jsonify({"error": str(e)}), 500


# 结果图片返回接口
@home_bp.route('/result/<file_id>')
def get_result_image(file_id):
    # 匹配对应文件
    result_file = None
    for f in os.listdir(RESULT_FOLDER):
        if f.startswith(file_id) and os.path.isfile(os.path.join(RESULT_FOLDER, f)):
            result_file = f
            break

    if not result_file:
        return jsonify({"error": f"图片不存在：{file_id}"}), 404

    result_path = os.path.join(RESULT_FOLDER, result_file)
    print(f"【调试】请求图片路径：{result_path}")

    # 识别MIME类型
    mime_type = 'image/jpeg' if result_file.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
    return send_file(result_path, mimetype=mime_type, as_attachment=False)

# ========== 新增：获取最新上传图片接口 ==========
@home_bp.route('/get-latest-image', methods=['GET'])
def get_latest_image():
    global latest_image_info
    # 判断是否存在最新图片
    if not latest_image_info["is_exists"] or not latest_image_info["file_id"]:
        return jsonify({
            "success": False,
            "error": "暂无最新上传的图片"
        }), 404

    # 返回最新图片的访问URL和基础信息
    return jsonify({
        "success": True,
        "file_id": latest_image_info["file_id"],
        "file_ext": latest_image_info["file_ext"],
        "original_image_url": f"/upload/{latest_image_info['file_id']}{latest_image_info['file_ext']}",  # 原始图片
        "result_image_url": f"/result/{latest_image_info['file_id']}"  # 检测后的图片（和你现有接口一致）
    })
# ========== 新增：获取原始上传图片接口（可选，若需要展示原始图片） ==========
@home_bp.route('/upload/<file_name>', methods=['GET'])
def get_original_image(file_name):
    original_path = os.path.join(UPLOAD_FOLDER, file_name)
    if not os.path.exists(original_path):
        return jsonify({"error": "原始图片不存在"}), 404

    # 识别MIME类型
    file_ext = os.path.splitext(file_name)[1].lower()
    mime_type = 'image/jpeg' if file_ext in ['.jpg', '.jpeg'] else 'image/png'
    return send_file(original_path, mimetype=mime_type, as_attachment=False)