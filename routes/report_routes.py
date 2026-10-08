from flask import Blueprint, request, jsonify, send_file, session
from services.auth_service import login_required, role_required
from services.report_service import (
    get_analytics_summary, get_employee_monthly_matrix,
    generate_excel_report, generate_pdf_report
)
from services.audit_service import get_recent_audit_logs
from powerbi.powerbi_dataset_export import export_all
from datetime import datetime

report_bp = Blueprint('report', __name__)

@report_bp.route('/api/reports/analytics', methods=['GET'])
@login_required
def api_reports_analytics():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    analytics = get_analytics_summary(year, month)
    return jsonify({'success': True, 'analytics': analytics})

@report_bp.route('/api/reports/matrix', methods=['GET'])
@login_required
def api_reports_matrix():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    dept_id = request.args.get('department_id', type=int)
    rows = get_employee_monthly_matrix(year, month, dept_id)
    return jsonify({'success': True, 'matrix': rows})

@report_bp.route('/reports/excel/monthly', methods=['GET'])
@login_required
def download_monthly_excel():
    year = request.args.get('year', type=int) or datetime.now().year
    month = request.args.get('month', type=int) or datetime.now().month

    output = generate_excel_report(year, month)
    filename = f"Attendance_Report_{year}_{month:02d}.xlsx"

    return send_file(
        output,
        download_name=filename,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@report_bp.route('/reports/pdf/monthly', methods=['GET'])
@login_required
def download_monthly_pdf():
    year = request.args.get('year', type=int) or datetime.now().year
    month = request.args.get('month', type=int) or datetime.now().month

    buffer = generate_pdf_report(year, month)
    filename = f"Attendance_Executive_Report_{year}_{month:02d}.pdf"

    return send_file(
        buffer,
        download_name=filename,
        as_attachment=True,
        mimetype='application/pdf'
    )

@report_bp.route('/api/reports/audit-logs', methods=['GET'])
@role_required('admin')
def api_audit_logs():
    limit = request.args.get('limit', default=50, type=int)
    logs = get_recent_audit_logs(limit)
    for l in logs:
        l['created_at'] = l['created_at'].strftime('%Y-%m-%d %I:%M:%S %p')
    return jsonify({'success': True, 'logs': logs})

@report_bp.route('/api/powerbi/export-sync', methods=['POST'])
@role_required('admin', 'hr')
def api_powerbi_sync():
    try:
        export_all()
        return jsonify({'success': True, 'message': 'Power BI Star Schema CSV files successfully refreshed in powerbi/data/'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
