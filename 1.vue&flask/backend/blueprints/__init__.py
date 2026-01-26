from .home import home_bp
from .chatbox import chatbox_bp
# 统一导出蓝图
def register_all_blueprints(app):

    app.register_blueprint(home_bp)
    app.register_blueprint(chatbox_bp)