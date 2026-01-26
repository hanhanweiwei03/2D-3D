from ultralytics import YOLO
import cv2
import numpy as np
import os


def slice_large_image(image, slice_size=640, overlap_ratio=0.2):
    """
    将大图切分为带重叠的640×640子图，返回子图及对应偏移量
    :param image: 原图（np.array）
    :param slice_size: 子图尺寸（匹配模型训练尺寸）
    :param overlap_ratio: 重叠率（0.2=20%，避免目标跨切片）
    :return: list[(子图, x偏移, y偏移)]
    """
    h, w = image.shape[:2]
    step = int(slice_size * (1 - overlap_ratio))  # 切片步长（非重叠部分）
    slices = []

    # 遍历y轴（纵向）
    for y in range(0, h, step):
        # 遍历x轴（横向）
        for x in range(0, w, step):
            # 计算子图边界（防止越界）
            y_end = min(y + slice_size, h)
            x_end = min(x + slice_size, w)

            # 截取子图
            sub_img = image[y:y_end, x:x_end]

            # 若子图尺寸不足640，补黑边（匹配模型输入）
            if sub_img.shape[0] < slice_size or sub_img.shape[1] < slice_size:
                pad_h = slice_size - sub_img.shape[0]
                pad_w = slice_size - sub_img.shape[1]
                sub_img = cv2.copyMakeBorder(sub_img, 0, pad_h, 0, pad_w,
                                             cv2.BORDER_CONSTANT, value=(0, 0, 0))

            slices.append((sub_img, x, y))  # 记录子图和偏移量
    return slices


def merge_detections(all_detections, slice_size=640, conf_thres=0.5, iou_thres=0.4):
    """
    将子图检测结果映射回原图，并去重（NMS）
    :param all_detections: list[(子图检测结果, x偏移, y偏移)]
    :return: 原图坐标的检测框(xyxy)、置信度、类别
    """
    all_boxes = []
    all_confs = []
    all_cls = []

    # 1. 坐标映射：子图→原图
    for det, x_off, y_off in all_detections:
        if len(det.boxes) == 0:
            continue
        # 提取子图内检测框（xyxy格式）
        boxes = det.boxes.xyxy.cpu().numpy()
        confs = det.boxes.conf.cpu().numpy()
        cls = det.boxes.cls.cpu().numpy()

        # 过滤低置信度框
        valid_mask = confs > conf_thres
        boxes = boxes[valid_mask]
        confs = confs[valid_mask]
        cls = cls[valid_mask]

        # 映射到原图坐标（加偏移量）
        boxes[:, 0] += x_off  # x1
        boxes[:, 1] += y_off  # y1
        boxes[:, 2] += x_off  # x2
        boxes[:, 3] += y_off  # y2

        all_boxes.extend(boxes)
        all_confs.extend(confs)
        all_cls.extend(cls)

    # 2. 非极大值抑制（NMS）去重
    if len(all_boxes) == 0:
        return np.array([]), np.array([]), np.array([])

    # 执行NMS
    indices = cv2.dnn.NMSBoxes(
        [box.tolist() for box in all_boxes],
        all_confs,
        conf_thres,
        iou_thres
    )
    # 兼容cv2返回格式（单框返回标量，多框返回数组）
    if isinstance(indices, (int, np.integer)):
        indices = [indices]
    else:
        indices = indices.flatten()

    # 最终结果
    final_boxes = np.array(all_boxes)[indices]
    final_confs = np.array(all_confs)[indices]
    final_cls = np.array(all_cls)[indices]

    return final_boxes, final_confs, final_cls


def detect_large_image(model_path, img_path, slice_size=640, overlap_ratio=0.2, conf_thres=0.5):
    """
    大图检测主函数：切片→推理→合并→可视化
    """
    # 1. 加载模型和原图
    model = YOLO(model_path)
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"无法读取图片：{img_path}")
    img_copy = img.copy()  # 用于绘制结果

    # 2. 切片（带20%重叠）
    print(f"正在切片大图（{img.shape[1]}×{img.shape[0]}），子图尺寸{slice_size}×{slice_size}...")
    slices = slice_large_image(img, slice_size=slice_size, overlap_ratio=overlap_ratio)
    print(f"共切分{len(slices)}张子图")

    # 3. 逐张子图推理
    all_detections = []
    for i, (sub_img, x_off, y_off) in enumerate(slices):
        print(f"推理子图 {i + 1}/{len(slices)} (偏移：x={x_off}, y={y_off})")
        results = model(sub_img, conf=conf_thres, device="cpu", imgsz=slice_size)
        all_detections.append((results[0], x_off, y_off))

    # 4. 合并检测结果（映射+去重）
    final_boxes, final_confs, final_cls = merge_detections(
        all_detections, slice_size=slice_size, conf_thres=conf_thres
    )

    # 5. 在原图上绘制所有检测框
    for box, conf in zip(final_boxes, final_confs):
        x1, y1, x2, y2 = map(int, box)
        # 绘制框（绿色，线宽2）
        cv2.rectangle(img_copy, (x1, y1), (x2, y2), (0, 0, 255), 2)
        # 绘制置信度文本
        cv2.putText(img_copy, f"tower_crane {conf:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # 6. 保存结果并打印信息
    save_path = "large_image_detection_result.jpg"
    cv2.imwrite(save_path, img_copy)
    print(f"\n检测完成！共检测到{len(final_boxes)}个塔吊")
    print(f"结果已保存至：{os.path.abspath(save_path)}")

    # 打印详细检测结果
    for i, (box, conf) in enumerate(zip(final_boxes, final_confs)):
        print(f"tower_crane{i + 1} | 坐标：{box.astype(int)} | 置信度：{conf:.2f}")

    return final_boxes, final_confs


# ===================== 调用示例 =====================
if __name__ == "__main__":
    # 替换为你的模型路径和大图路径
    MODEL_PATH = "/Users/mac-henry/RA_Environment/2D-3D Project setup/runs/detect/train18/weights/best.pt"
    IMG_PATH = "/Original_data/1.19.jpg"

    # 执行大图检测
    detect_large_image(
        model_path=MODEL_PATH,
        img_path=IMG_PATH,
        slice_size=640,  # 匹配模型训练尺寸
        overlap_ratio=0.2,  # 20%重叠率（避免目标跨切片）
        conf_thres=0.5  # 置信度阈值
    )