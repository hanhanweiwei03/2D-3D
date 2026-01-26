import os
from PIL import Image


def concat_images_to_fixed_size(folder_path, output_path, target_size=(1248, 832), grid=(4, 5)):
    """
    将文件夹中的图片拼接成指定尺寸的图片（1248x832）

    Args:
        folder_path (str): 图片文件夹路径
        output_path (str): 拼接后图片的保存路径
        target_size (tuple): 目标图片尺寸 (宽, 高)，默认1248x832
        grid (tuple): 图片排布网格 (行数, 列数)，默认4行5列（适配20张图）
    """
    # 支持的图片格式
    valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')

    # 获取文件夹中所有图片文件并排序
    image_files = [
        os.path.join(folder_path, f)
        for f in sorted(os.listdir(folder_path))
        if f.lower().endswith(valid_extensions)
    ]

    # 检查图片数量
    total_imgs = len(image_files)
    if total_imgs == 0:
        raise ValueError("文件夹中未找到图片文件")
    if total_imgs != 20:
        print(f"警告：文件夹中找到 {total_imgs} 张图片，不是预期的20张")
        # 只取前20张或补空白（这里选择取前20张）
        image_files = image_files[:20]
        total_imgs = len(image_files)

    rows, cols = grid
    # 计算每张图片需要调整到的尺寸（适配目标画布）
    img_width = target_size[0] // cols
    img_height = target_size[1] // rows

    # 读取并调整所有图片尺寸
    images = []
    for img_path in image_files:
        try:
            img = Image.open(img_path)
            # 调整图片尺寸到计算出的单张尺寸（保持比例并裁剪，避免拉伸）
            img.thumbnail((img_width, img_height), Image.Resampling.LANCZOS)
            # 创建空白画布，将缩放后的图片居中放置（解决尺寸不完全匹配问题）
            new_img = Image.new('RGB', (img_width, img_height), color='white')
            paste_x = (img_width - img.size[0]) // 2
            paste_y = (img_height - img.size[1]) // 2
            new_img.paste(img, (paste_x, paste_y))
            images.append(new_img)
        except Exception as e:
            print(f"读取图片 {img_path} 失败: {e}")

    # 创建固定尺寸的目标画布（1248x832）
    result = Image.new('RGB', target_size, color='white')

    # 按网格排布拼接图片
    x_offset = 0
    y_offset = 0
    img_idx = 0
    for row in range(rows):
        x_offset = 0  # 每行开始时重置x偏移
        for col in range(cols):
            if img_idx < len(images):
                result.paste(images[img_idx], (x_offset, y_offset))
                x_offset += img_width  # 列偏移增加
                img_idx += 1
        y_offset += img_height  # 行偏移增加

    # 保存拼接后的图片
    result.save(output_path)
    print(f"图片拼接完成！已保存至: {output_path}")
    print(f"最终图片尺寸: {result.size} (目标: {target_size})")


# 主程序
if __name__ == "__main__":
    # ========== 请修改以下配置 ==========
    # 图片文件夹路径（绝对路径或相对路径）
    IMAGE_FOLDER = r"/Users/mac-henry/RA_Environment/2D-3D Project setup/Original_data/3.building contour by gemini"
    # 拼接后图片保存路径
    OUTPUT_IMAGE = r"/Users/mac-henry/RA_Environment/2D-3D Project setup/contact.png"
    # 目标尺寸（固定为1248x832）
    TARGET_SIZE = (1248, 832)
    # 网格排布（4行5列，刚好放20张图）
    GRID_LAYOUT = (4, 5)
    # ====================================

    try:
        concat_images_to_fixed_size(IMAGE_FOLDER, OUTPUT_IMAGE, TARGET_SIZE, GRID_LAYOUT)
    except Exception as e:
        print(f"程序执行出错: {e}")