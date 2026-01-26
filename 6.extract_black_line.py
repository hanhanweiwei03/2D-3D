import cv2
import numpy as np

def fix_line_breakpoints(img_path):
    # 1. 读取图像（处理透明通道）
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    if len(img.shape) == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # 2. HSV筛选纯黑色（保持宽松阈值）
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_black = np.array([0, 0, 0])
    #upper_black = np.array([180, 50, 40])
    #extract picture2
    upper_black = np.array([180, 30,200])
    black_mask = cv2.inRange(hsv, lower_black, upper_black)
    black_mask = 255 - black_mask  # 反转：黑线条+白背景


    # 6. 保存结果（对比修复前后）
    cv2.imwrite("/Users/mac-henry/RA_Environment/2D-3D Project setup/Original_data/2.preprocess_data/1.1.png", black_mask)    # 原始线条（有小断点）


if __name__ == "__main__":
    fix_line_breakpoints("/Users/mac-henry/RA_Environment/2D-3D Project setup/Original_data/1.original_data/1.1.png")