import cv2
import numpy as np
import os


def rotate_image_30deg_opencv(input_folder, output_folder=None):
    """
    功能：用OpenCV实现1-5.jpg旋转，每张生成12个角度（0°-330°），保持640×640尺寸，按1-60命名
    :param input_folder: 原始图片文件夹路径
    :param output_folder: 输出文件夹路径，默认与输入文件夹相同
    """
    # 1. 路径配置与初始化
    if output_folder is None:
        output_folder = input_folder
    os.makedirs(output_folder, exist_ok=True)  # 确保输出文件夹存在
    original_images = [f"{i}.jpg" for i in range(1, 6)]  # 1-5.jpg列表
    output_count = 1  # 输出图片序号（1-60）

    # 2. 遍历每张原始图片执行旋转
    for img_name in original_images:
        img_path = os.path.join(input_folder, img_name)

        # 检查原始图片是否存在
        if not os.path.exists(img_path):
            print(f"⚠️ 跳过：原始图片不存在 → {img_path}")
            continue

        try:
            # 读取图片（OpenCV默认BGR格式，后续保存会自动转为RGB）
            img = cv2.imread(img_path)
            if img is None:
                print(f"❌ 无法读取图片：{img_name}（可能是格式错误）")
                continue

            # 获取图片尺寸（确保原始图是640×640，若不是也会按640×640填充）
            img_height, img_width = img.shape[:2]
            target_size = 640  # 目标尺寸640×640

            # 每张图旋转12次（0°、30°...330°）
            for angle in range(0, 360, 30):
                # 步骤1：计算旋转矩阵（以图片中心为旋转点，保持缩放比例1.0）
                center = (img_width // 2, img_height // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, scale=1.0)

                # 步骤2：执行旋转（空白处用黑色填充，保证输出尺寸640×640）
                # borderMode=cv2.BORDER_CONSTANT：固定颜色填充；value=(0,0,0)：黑色填充
                rotated_img = cv2.warpAffine(
                    img,
                    rotation_matrix,
                    (target_size, target_size),  # 输出尺寸强制640×640
                    borderMode=cv2.BORDER_CONSTANT,
                    borderValue=(0, 0, 0)
                )

                # 步骤3：保存旋转后的图片
                output_img_name = f"{output_count}.jpg"
                output_img_path = os.path.join(output_folder, output_img_name)
                cv2.imwrite(output_img_path, rotated_img)

                # 打印进度信息
                print(f"✅ 生成：{output_img_path}（原始图：{img_name}，旋转角度：{angle}°）")
                output_count += 1

        except Exception as e:
            print(f"❌ 处理失败：{img_name} → 错误原因：{str(e)}")

    # 3. 完成后状态提示
    total_generated = output_count - 1
    if total_generated == 60:
        print(f"\n🎉 全部完成！共生成60张图片，保存路径：{output_folder}")
    else:
        print(f"\n⚠️ 生成不完整！实际生成{total_generated}张（需60张），请检查原始图片或错误信息。")


# ------------------- 配置你的路径（修改这里！） -------------------
# 原始1-5.jpg所在文件夹路径（Mac示例）
INPUT_FOLDER = "/Users/mac-henry/RA_Environment/2D-3D Project setup/"
# 若需输出到子文件夹（如Image_640*640），取消下方注释并修改路径
# OUTPUT_FOLDER = "/Users/mac-henry/RA_Environment/2D-3D Project setup"
# rotate_image_30deg_opencv(input_folder=INPUT_FOLDER, output_folder=OUTPUT_FOLDER)

# 默认输出到原始文件夹（直接运行这行）
rotate_image_30deg_opencv(input_folder=INPUT_FOLDER)