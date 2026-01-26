import pyvista as pv
import ezdxf
import os


def stl_to_dxf(stl_file_path, dxf_file_path):
    """
    适配所有ezdxf版本的STL转DXF（彻底解决参数报错）
    依赖：pyvista（已安装） + ezdxf（任意版本）
    """
    # 1. 校验文件
    if not os.path.exists(stl_file_path):
        raise FileNotFoundError(f"STL文件不存在：{stl_file_path}")

    # 2. 解析STL
    print(f"正在解析STL文件：{stl_file_path}")
    stl_mesh = pv.read(stl_file_path)
    if not stl_mesh.is_all_triangles:
        stl_mesh = stl_mesh.triangulate()

    # 3. 提取网格数据
    points = stl_mesh.points  # (N, 3) 顶点坐标
    faces = stl_mesh.faces.reshape(-1, 4)[:, 1:]  # (M, 3) 三角面索引

    # 4. 创建DXF文档
    doc = ezdxf.new(dxfversion='R2018')
    msp = doc.modelspace()

    # 5. 逐面绘制（✅ 核心修复：适配所有ezdxf版本的参数格式）
    print(f"正在转换{len(faces)}个三角面到DXF...")
    for face in faces:
        # 提取3个顶点并转为列表格式
        vertices = [
            tuple(points[face[0]]),  # 顶点1 (x,y,z)
            tuple(points[face[1]]),  # 顶点2 (x,y,z)
            tuple(points[face[2]])  # 顶点3 (x,y,z)
        ]
        # 关键：用列表传入顶点，兼容所有ezdxf版本
        # 格式：add_3dface(vertices) → 仅1个位置参数（除self外）
        msp.add_3dface(vertices)

    # 6. 保存文件
    try:
        doc.saveas(dxf_file_path)
        print(f"✅ 转换成功！DXF文件路径：{dxf_file_path}")
        print("📌 操作指引：")
        print("   1. AutoCAD打开该DXF → 输入ZOOM → 选EXTENTS显示全部模型")
        print("   2. 文件→另存为 → 选择DWG格式保存")
    except Exception as e:
        raise RuntimeError(f"保存DXF失败：{str(e)}")


# ========== 调用入口（替换为你的文件路径） ==========
if __name__ == "__main__":
    STL_PATH = "/Users/mac-henry/RA_Environment/2D-3D Project setup/building_3d_50m.stl"
    DXF_PATH = "/Users/mac-henry/RA_Environment/2D-3D Project setup/building_3d_50m.dxf"

    try:
        stl_to_dxf(STL_PATH, DXF_PATH)
    except Exception as e:
        print(f"❌ 转换失败：{str(e)}")