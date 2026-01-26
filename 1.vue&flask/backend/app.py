# 导入 Flask 核心库
from flask import Flask, jsonify
# 导入跨域支持库（解决前后端跨域问题）
from flask_cors import CORS
from blueprints import register_all_blueprints


# 创建 Flask 实例
app = Flask(__name__)
# 配置跨域：允许前端地址（localhost:5173）访问
CORS(
    app,
    resources={r"/*": {"origins": "http://localhost:5173"}},  # 允许前端5173访问所有后端路由
    supports_credentials=True  # 支持跨域携带Cookie（和前端的credentials: 'include'对应）
)

#每次添加后端接口
register_all_blueprints(app)

# 启动 Flask 应用
if __name__ == '__main__':
    # debug=True：修改代码后自动重启；port=5000：端口号（和前端请求的端口一致）
    app.run(debug=True, port=5001)