from flask import Flask, request, jsonify, send_file, send_from_directory
from ultralytics import YOLO
import cv2
import numpy as np
import os
import uuid

app = Flask(__name__)

# 配置：模型路径、临时文件目录
MODEL_PATH = "/Users/mac-henry/RA_Environment/2D-3D Project setup/runs/detect/train18/weights/best.pt"
UPLOAD_FOLDER = "temp_uploads"
RESULT_FOLDER = "temp_results"
# 修复：使用绝对路径，避免相对路径混乱
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), UPLOAD_FOLDER)
RESULT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), RESULT_FOLDER)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# ========== 检测函数（无需修改） ==========
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

    # 保存检测后的图片（新增调试打印）
    print(f"【调试】检测结果保存到：{save_result_path}")
    cv2.imwrite(save_result_path, img_copy)
    return len(final_boxes)

# ========== 根路由返回前端页面 ==========
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# ========== 上传接口（修复返回的URL） ==========
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "未上传图片"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "文件名为空"}), 400

    # 修复1：支持JPG/PNG格式校验
    allowed_extensions = ['.jpg', '.jpeg', '.png']
    file_ext = os.path.splitext(file.filename)[1].lower()  # 提取文件后缀（如.png）
    if file_ext not in allowed_extensions:
        return jsonify({"error": "仅支持JPG/PNG格式"}), 400

    # 修复2：保留原格式后缀，避免PNG转JPG出错
    file_id = str(uuid.uuid4())
    upload_path = os.path.join(UPLOAD_FOLDER, f"{file_id}{file_ext}")  # 如 xxx.png
    result_path = os.path.join(RESULT_FOLDER, f"{file_id}{file_ext}")  # 如 xxx.png
    file.save(upload_path)
    print(f"【调试】上传文件保存到：{upload_path}")

    try:
        detect_count = detect_large_image(MODEL_PATH, upload_path, result_path)
        # 修复3：返回的URL仍不带后缀（后端拼接时补后缀）
        return jsonify({
            "success": True,
            "detect_count": detect_count,
            "result_image_url": f"/result/{file_id}",
            "file_ext": file_ext  # 新增：传递文件后缀给前端（可选）
        })
    except Exception as e:
        print(f"【错误】检测失败：{str(e)}")
        return jsonify({"error": str(e)}), 500

# ========== 图片返回接口（修复路由+响应配置） ==========
@app.route('/result/<file_id>')
def get_result_image(file_id):
    # 遍历RESULT_FOLDER，匹配file_id开头的文件（兼容.jpg/.png）
    result_file = None
    for f in os.listdir(RESULT_FOLDER):
        if f.startswith(file_id) and os.path.isfile(os.path.join(RESULT_FOLDER, f)):
            result_file = f
            break

    if not result_file:
        return jsonify({"error": f"图片不存在：{file_id}"}), 404

    result_path = os.path.join(RESULT_FOLDER, result_file)
    print(f"【调试】请求图片路径：{result_path}")

    # 自动识别MIME类型（兼容jpg/png）
    mime_type = 'image/jpeg' if result_file.lower().endswith(('.jpg', '.jpeg')) else 'image/png'

    if os.path.exists(result_path):
        return send_file(
            result_path,
            mimetype=mime_type,  # 匹配实际格式
            as_attachment=False
        )
    else:
        return jsonify({"error": f"图片不存在：{result_path}"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)