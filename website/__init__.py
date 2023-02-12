from flask import Flask, appcontext_popped, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
import logging

#Path Math
import sys
import os
from . import config

db:SQLAlchemy = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()

DB_NAME = "main"

def create_app(name):
    #Flask Instance
    app = Flask(__name__)
    #app.config.from_pyfile('config.py')
    app.config.from_object(config.DevConfig)
    
    if name  != '__main__':
        gunicorn_logger=logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    #Database
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db'
    #app.config['SECRET_KEY'] = '123'
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/main'
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    #migrate = Migrate(app, db)
    
    with app.app_context():
        db.create_all()
        from .views import views
        from .auth import auth
        from .campaign_route import campaign_route
        from .shift_route import shift_route
        from .import_route import import_route
        from .export_route import export_route

        # Models
        from .models.abstracts import AbstractStamps
        from .models.paystamps import PayStamps
        from .models.campaigns import Campaigns, admins, Campaign_Contracts
        from .models.users import Users, SystemLevels
        from .models.people import People
        from .models.shiftstamps import ShiftStamps, Activities
        from .models.admincommands import AdminCommands
        from .models.receipts import Receipts
        from .models.imports import Imports
        from .models.exports import Exports

        app.register_blueprint(views, url_prefix='/')
        app.register_blueprint(auth, url_prefix='/')
        app.register_blueprint(campaign_route, url_prefix='/')
        app.register_blueprint(shift_route, url_prefix='/')
        app.register_blueprint(import_route, url_prefix='/')
        app.register_blueprint(export_route, url_prefix='/')

        from .helper_functions import migration_handling as mgh
        app.before_first_request(mgh.run_back_check)

        login_manager = LoginManager()
        login_manager.login_view = 'auth.login'
        login_manager.init_app(app)
        login_manager.login_message = "User needs to be logged in to view this page"

        @login_manager.user_loader
        def load_user(id):
            return Users.query.get(int(id))

    from .helper_functions import exc
    app.register_error_handler(404, exc.page_not_found_error)
    app.register_error_handler(403, exc.access_denied_error)
    app.register_error_handler(500, exc.internal_server_error)

    return app