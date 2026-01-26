import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os


class ImagePreprocessTool:
    def __init__(self, root):
        self.root = root
        self.root.title("图片预处理工具 - 黑色筛选+尺寸标准化(1248x832)")
        self.root.geometry("1000x800")  # 初始窗口大小

        # 目标尺寸（固定1248x832）
        self.target_w = 1248
        self.target_h = 832

        # 初始化变量
        self.img_path = None
        self.img_original = None  # 原始图片
        self.img_processed = None  # 处理后的图片（筛选+标准化尺寸）
        self.img_bgr = None  # 强制3通道BGR

        # HSV参数
        self.h_upper = tk.IntVar(value=180)
        self.s_upper = tk.IntVar(value=30)
        self.v_upper = tk.IntVar(value=40)

        # 创建UI布局
        self.create_menu()
        self.create_control_panel()
        self.create_image_panel()

        # 绑定滑动条事件
        self.h_upper.trace("w", self.update_image)
        self.s_upper.trace("w", self.update_image)
        self.v_upper.trace("w", self.update_image)

        # 绑定窗口大小变化事件，实时适配图片显示
        self.root.bind("<Configure>", self.on_window_resize)

    def create_menu(self):
        """创建文件菜单（打开图片）"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开图片", command=self.open_image)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

    def create_control_panel(self):
        """创建控制面板（滑动条+导出按钮）"""
        control_frame = ttk.LabelFrame(self.root, text="参数控制")
        control_frame.pack(pady=10, padx=20, fill=tk.X)

        # 1. HSV滑动条区域
        slider_frame = ttk.Frame(control_frame)
        slider_frame.pack(pady=10, padx=20, fill=tk.X)

        # 色相H
        ttk.Label(slider_frame, text="1. 色相H上限 (0-180)：").grid(row=0, column=0, sticky=tk.W, padx=5)
        h_slider = ttk.Scale(slider_frame, from_=0, to=180, variable=self.h_upper, orient=tk.HORIZONTAL)
        h_slider.grid(row=0, column=1, sticky=tk.EW, padx=5)
        self.h_label = ttk.Label(slider_frame, text=f"{self.h_upper.get()}")
        self.h_label.grid(row=0, column=2, padx=5)

        # 饱和度S
        ttk.Label(slider_frame, text="2. 饱和度S上限 (0-255)：").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        s_slider = ttk.Scale(slider_frame, from_=0, to=255, variable=self.s_upper, orient=tk.HORIZONTAL)
        s_slider.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.s_label = ttk.Label(slider_frame, text=f"{self.s_upper.get()}")
        self.s_label.grid(row=1, column=2, padx=5, pady=5)

        # 明度V
        ttk.Label(slider_frame, text="3. 明度V上限 (0-255)：").grid(row=2, column=0, sticky=tk.W, padx=5)
        v_slider = ttk.Scale(slider_frame, from_=0, to=255, variable=self.v_upper, orient=tk.HORIZONTAL)
        v_slider.grid(row=2, column=1, sticky=tk.EW, padx=5)
        self.v_label = ttk.Label(slider_frame, text=f"{self.v_upper.get()}")
        self.v_label.grid(row=2, column=2, padx=5)

        slider_frame.columnconfigure(1, weight=1)

        # 2. 导出按钮区域
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(pady=10, padx=20)

        self.export_btn = ttk.Button(btn_frame, text="导出处理后图片", command=self.export_image, state=tk.DISABLED)
        self.export_btn.pack(padx=5)

    def create_image_panel(self):
        """创建图片显示面板"""
        img_frame = ttk.LabelFrame(self.root, text="处理效果预览 (1248x832)")
        img_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # 使用Canvas作为显示容器，支持自适应缩放
        self.canvas = tk.Canvas(img_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 初始提示文字
        self.canvas.create_text(
            self.canvas.winfo_width() // 2,
            self.canvas.winfo_height() // 2,
            text="请先通过【文件】→【打开图片】选择要处理的图片",
            font=("Arial", 12)
        )
        self.img_on_canvas = None  # 存储canvas上的图片对象

    def force_3channel(self, img):
        """强制将图片转为3通道BGR，兼容所有维度情况"""
        try:
            # 打印调试信息（方便定位问题）
            print(f"原始图片维度：{img.shape}")

            # 情况1：4通道（BGRA）→ 转为3通道BGR（透明区域填白）
            if len(img.shape) == 4 and img.shape[2] == 4:
                bgr = img[:, :, :3].copy()
                alpha = img[:, :, 3]
                bgr[alpha == 0] = 255  # 透明区域设为白色
                print("已将4通道PNG转为3通道BGR（透明区域填白）")
                return bgr

            # 情况2：灰度图（2维）→ 转为3通道
            elif len(img.shape) == 2:
                bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                print("已将灰度图转为3通道BGR")
                return bgr

            # 情况3：3通道（BGR/RGB）→ 确保是BGR格式
            elif len(img.shape) == 3:
                if img.shape[2] == 3:
                    # 检查是否是RGB格式（可选，OpenCV默认BGR）
                    return img.copy()
                # 通道数不是3的情况 → 取前3通道
                elif img.shape[2] > 3:
                    bgr = img[:, :, :3].copy()
                    print(f"图片通道数为{img.shape[2]}，已截取前3通道")
                    return bgr
                # 通道数小于3 → 复制扩展为3通道
                else:
                    bgr = np.repeat(img, 3, axis=2)
                    print(f"图片通道数为{img.shape[2]}，已扩展为3通道")
                    return bgr

            # 情况4：其他异常维度 → 创建空白3通道图片
            else:
                print(f"不支持的图片维度{img.shape}，创建空白3通道图片")
                # 创建和原图尺寸一致的白色空白图
                h, w = img.shape[:2] if len(img.shape) >= 2 else (832, 1248)
                bgr = np.ones((h, w, 3), dtype=np.uint8) * 255
                return bgr

        except Exception as e:
            # 所有异常都返回默认空白3通道图
            print(f"维度转换出错：{str(e)}，返回默认空白图")
            return np.ones((self.target_h, self.target_w, 3), dtype=np.uint8) * 255

    def open_image(self):
        """打开图片（支持PNG/JPG，强制转为3通道）"""
        file_path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg"), ("PNG", "*.png"), ("JPG", "*.jpg *.jpeg"),
                       ("所有文件", "*.*")]
        )
        if not file_path:
            return

        # 读取图片（保留透明通道）
        self.img_path = file_path
        self.img_original = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
        if self.img_original is None:
            messagebox.showerror("错误", "无法读取选中的图片，请检查文件是否损坏或格式不支持")
            return

        # 强制转为3通道BGR（兼容所有情况）
        self.img_bgr = self.force_3channel(self.img_original)

        # 启用导出按钮
        self.export_btn.config(state=tk.NORMAL)

        # 立即更新图片，使用after确保窗口初始化完成
        self.root.after(100, self.update_image)

    def resize_and_pad(self, img):
        """等比例缩放+填充至1248x832（不裁切）- 输入必为3通道"""
        # 二次校验：确保是3通道
        img = self.force_3channel(img)

        h, w = img.shape[:2]

        # 计算缩放比例（等比例，不超过目标尺寸）
        scale = min(self.target_w / w, self.target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        # 缩放图片
        img_resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # 创建目标尺寸的空白画布（白色填充）- 固定3通道
        img_padded = np.ones((self.target_h, self.target_w, 3), dtype=np.uint8) * 255

        # 计算填充位置（居中）
        x_offset = (self.target_w - new_w) // 2
        y_offset = (self.target_h - new_h) // 2

        # 确保切片范围有效（防止越界）
        y1 = max(0, y_offset)
        y2 = min(self.target_h, y_offset + new_h)
        x1 = max(0, x_offset)
        x2 = min(self.target_w, x_offset + new_w)

        # 对应的缩放后图片的切片（防止越界）
        img_y1 = max(0, 0 - (y_offset - y1))
        img_y2 = min(new_h, img_y1 + (y2 - y1))
        img_x1 = max(0, 0 - (x_offset - x1))
        img_x2 = min(new_w, img_x1 + (x2 - x1))

        # 赋值（绝对安全，不会维度不匹配）
        img_padded[y1:y2, x1:x2] = img_resized[img_y1:img_y2, img_x1:img_x2]

        return img_padded

    def get_display_size(self):
        """计算图片的最佳显示尺寸（自适应canvas大小，保持比例）"""
        # 获取canvas的实际可用尺寸
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        # 避免初始尺寸为0的情况
        if canvas_w <= 1 or canvas_h <= 1:
            canvas_w = 800
            canvas_h = 600

        # 计算缩放比例（适配canvas，保持1248x832的比例）
        target_ratio = self.target_w / self.target_h
        canvas_ratio = canvas_w / canvas_h

        if target_ratio > canvas_ratio:
            # 按宽度适配
            display_w = canvas_w
            display_h = int(canvas_w / target_ratio)
        else:
            # 按高度适配
            display_h = canvas_h
            display_w = int(canvas_h * target_ratio)

        # 确保尺寸为正整数
        display_w = max(1, display_w)
        display_h = max(1, display_h)

        return display_w, display_h

    def update_image(self, *args):
        """更新图片（黑色筛选+尺寸标准化）"""
        if self.img_bgr is None:
            return

        # 1. 获取HSV参数
        h = self.h_upper.get()
        s = self.s_upper.get()
        v = self.v_upper.get()

        # 更新数值标签
        self.h_label.config(text=f"{h}")
        self.s_label.config(text=f"{s}")
        self.v_label.config(text=f"{v}")

        # 2. HSV筛选黑色（img_bgr已是3通道）
        hsv = cv2.cvtColor(self.img_bgr, cv2.COLOR_BGR2HSV)
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([h, s, v])
        mask = cv2.inRange(hsv, lower_black, upper_black)

        # 应用掩码：保留黑色，其余为白色
        img_filtered = cv2.bitwise_and(self.img_bgr, self.img_bgr, mask=mask)
        img_filtered[mask == 0] = 255

        # 3. 等比例缩放+填充至1248x832（再次强制3通道）
        self.img_processed = self.resize_and_pad(img_filtered)

        # 4. 转换为tkinter显示格式并自适应canvas
        img_rgb = cv2.cvtColor(self.img_processed, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)

        # 获取最佳显示尺寸
        display_w, display_h = self.get_display_size()

        # 缩放图片到显示尺寸（保持比例）
        img_pil_resized = img_pil.resize((display_w, display_h), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img_pil_resized)

        # 更新canvas上的图片
        self.canvas.delete("all")  # 清除原有内容
        # 居中显示图片
        x = (self.canvas.winfo_width() - display_w) // 2
        y = (self.canvas.winfo_height() - display_h) // 2
        self.img_on_canvas = self.canvas.create_image(x, y, anchor=tk.NW, image=img_tk)
        self.canvas.image = img_tk  # 保留引用，避免被垃圾回收

    def on_window_resize(self, event):
        """窗口大小变化时重新适配图片显示"""
        if self.img_processed is not None:
            self.update_image()

    def export_image(self):
        """导出处理后的图片"""
        if self.img_processed is None:
            messagebox.showwarning("提示", "暂无处理后的图片可导出")
            return

        # 获取原始文件名和格式
        file_name = os.path.basename(self.img_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        if file_ext not in ['.png', '.jpg', '.jpeg']:
            file_ext = '.png'  # 默认导出PNG

        # 选择保存路径
        save_path = filedialog.asksaveasfilename(
            title="保存处理后的图片",
            defaultextension=file_ext,
            filetypes=[
                ("PNG文件", "*.png"),
                ("JPG文件", "*.jpg *.jpeg"),
                ("所有文件", "*.*")
            ],
            initialfile=f"processed_{os.path.splitext(file_name)[0]}"
        )

        if not save_path:
            return

        # 保存图片
        try:
            # JPG保存（3通道）
            if file_ext in ['.jpg', '.jpeg']:
                cv2.imwrite(save_path, self.img_processed, [cv2.IMWRITE_JPEG_QUALITY, 95])
            # PNG保存（3通道）
            else:
                cv2.imwrite(save_path, self.img_processed, [cv2.IMWRITE_PNG_COMPRESSION, 0])

            messagebox.showinfo("成功", f"图片已导出至：\n{save_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}\n请检查保存路径是否有权限")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImagePreprocessTool(root)
    root.mainloop()