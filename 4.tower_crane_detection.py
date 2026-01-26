from ultralytics import YOLO

# 1. 加载训练好的模型（替换为你的best.pt路径）
model = YOLO("/Users/mac-henry/RA_Environment/2D-3D Project setup/runs/detect/train18/weights/best.pt")

# 2. 直接识别任意尺寸图片（替换为你的图片路径）
results = model("/Users/mac-henry/RA_Environment/2D-3D Project setup/test/12.png", conf=0.5, device="cpu")

# 3. 打印识别结果 + 保存可视化图片
for r in results:
    # 打印检测到的目标（坐标、置信度、类别）
    print("检测结果：")
    for box in r.boxes:
        print(f"塔吊 | 坐标：{box.xyxy.cpu().numpy()[0]} | 置信度：{box.conf.item():.2f}")
    # 保存带检测框的图片
    r.save("1.detection_result.jpg")

print("\n识别完成！结果已保存为 1.detection_result.jpg")