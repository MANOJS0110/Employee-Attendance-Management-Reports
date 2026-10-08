from flask import Flask, render_template, jsonify
from flask_cors import CORS
from config import Config
from datetime import datetime

# Import route blueprints
from routes.auth_routes import auth_bp
from routes.attendance_routes import attendance_bp
from routes.leave_routes import leave_bp
from routes.employee_routes import emp_bp
from routes.report_routes import report_bp
from routes.web_routes import web_bp

def create_app():
    """Application factory for Employee Attendance & Workforce Management System."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for REST API consumers
    CORS(app)

    # Register Blueprints
    app.register_blueprint(web_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(leave_bp)
    app.register_blueprint(emp_bp)
    app.register_blueprint(report_bp)

    # Global context processor
    @app.context_processor
    def inject_global_vars():
        return {
            'system_year': datetime.now().year,
            'current_date': datetime.now().strftime('%A, %B %d, %Y')
        }

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('login.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({
            'success': False,
            'message': 'An internal server error occurred.'
        }), 500

    return app

if __name__ == '__main__':
    app = create_app()
    print("=" * 70)
    print(" EMPLOYEE ATTENDANCE & WORKFORCE MANAGEMENT SYSTEM")
    print(" Server running at: http://127.0.0.1:5000")
    print("=" * 70)
    app.run(host='0.0.0.0', port=5000, debug=True)
