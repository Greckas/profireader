from flask import Flask
from profapp.controllers.blueprints import user_bp, article_bp, filemanager_bp
import profapp.controllers.views_article as views_art
import profapp.controllers.views_auth as views_auth
import profapp.controllers.views_filemanager as views_fileman
import profapp.controllers.views_index as views_ind

def create_app(config='config.ProductionDevelopmentConfig'):
    app = Flask(__name__)
    app.config.from_object(config)

    app.register_blueprint(views_ind.general_bp, url_prefix='/')
    app.register_blueprint(views_art.article_bp, url_prefix='/articles')
    app.register_blueprint(views_auth.user_bp, url_prefix='/users')
    app.register_blueprint(views_fileman.filemanager_bp,
                           url_prefix='/filemanager')

    return app
