from .routes import cxc_bp

def init_app(app):
    app.register_blueprint(cxc_bp)