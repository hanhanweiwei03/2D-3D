import xml.etree.ElementTree as ET
import os

def xml_to_yolo_simple(xml_folder, img_size=640, target_range=(51,60)):
    # 1. 关键：修改为你XML中的实际类别（这里是tower_crane）
    class_map = {"tower_crane": 0}  # 类别名→ID映射
    start, end = target_range

    for num in range(start, end+1):
        xml_path = os.path.join(xml_folder, f"{num}.xml")
        if not os.path.exists(xml_path):
            print(f"⚠️ 跳过：{num}.xml不存在")
            continue

        try:
            # 解析XML
            tree = ET.parse(xml_path)
            root = tree.getroot()
            txt_content = ""

            # 提取目标信息
            for obj in root.findall("object"):
                cls_name = obj.find("name").text.strip()
                # 匹配类别（不匹配则跳过，避免空TXT）
                if cls_name not in class_map:
                    print(f"❌ {num}.xml：未知类别{cls_name}，跳过")
                    continue

                # 提取边界框
                bndbox = obj.find("bndbox")
                xmin = float(bndbox.find("xmin").text)
                ymin = float(bndbox.find("ymin").text)
                xmax = float(bndbox.find("xmax").text)
                ymax = float(bndbox.find("ymax").text)

                # 转换为YOLO归一化坐标
                x_center = (xmin + xmax) / 2 / img_size
                y_center = (ymin + ymax) / 2 / img_size
                width = (xmax - xmin) / img_size
                height = (ymax - ymin) / img_size

                # 写入内容
                txt_content += f"{class_map[cls_name]} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n"

            # 保存TXT
            txt_path = xml_path.replace(".xml", ".txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(txt_content)
            print(f"✅ 完成：{num}.xml → {num}.txt")

        except Exception as e:
            print(f"❌ {num}.xml转换失败：{str(e)}")

# ------------------- 配置路径（修改为你的XML文件夹） -------------------
XML_FOLDER = "/Users/mac-henry/RA_Environment/2D-3D Project setup/labels/test"
# 执行转换（处理1-50号XML，图片尺寸640）
xml_to_yolo_simple(xml_folder=XML_FOLDER)