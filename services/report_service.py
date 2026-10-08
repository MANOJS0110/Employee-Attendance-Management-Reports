import io
from datetime import datetime, date
from db import get_db_cursor
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def get_analytics_summary(year=None, month=None):
    """
    Returns aggregated metrics for Chart.js visuals and Power BI comparison.
    """
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    with get_db_cursor() as cursor:
        # 1. Total Active Employees
        cursor.execute("SELECT COUNT(*) as total FROM employees WHERE status = 'ACTIVE';")
        total_employees = cursor.fetchone()['total']

        # 2. Status distribution for month
        cursor.execute(
            """SELECT status, COUNT(*) as cnt, COALESCE(SUM(working_hours), 0) as total_hours
               FROM attendance
               WHERE YEAR(date) = %s AND MONTH(date) = %s
               GROUP BY status;""",
            (year, month)
        )
        status_rows = cursor.fetchall()

        present_total = 0
        late_total = 0
        half_day_total = 0
        absent_total = 0
        leave_total = 0
        total_hours = 0.0

        for r in status_rows:
            total_hours += float(r['total_hours'])
            st = r['status']
            cnt = r['cnt']
            if st == 'PRESENT':
                present_total += cnt
            elif st == 'LATE':
                late_total += cnt
            elif st == 'HALF_DAY':
                half_day_total += cnt
            elif st == 'ABSENT':
                absent_total += cnt
            elif st == 'ON_LEAVE':
                leave_total += cnt

        total_entries = present_total + late_total + half_day_total + absent_total + leave_total
        effective_present = present_total + late_total + half_day_total
        overall_attendance_pct = round((effective_present / total_entries * 100), 1) if total_entries > 0 else 0.0

        # 3. Monthly Daily Trend (for Line/Bar Chart)
        cursor.execute(
            """SELECT date, 
                      SUM(CASE WHEN status IN ('PRESENT', 'LATE', 'HALF_DAY') THEN 1 ELSE 0 END) as present_cnt,
                      SUM(CASE WHEN is_late = 1 OR status = 'LATE' THEN 1 ELSE 0 END) as late_cnt,
                      SUM(CASE WHEN status = 'ABSENT' THEN 1 ELSE 0 END) as absent_cnt,
                      SUM(CASE WHEN status = 'ON_LEAVE' THEN 1 ELSE 0 END) as leave_cnt
               FROM attendance
               WHERE YEAR(date) = %s AND MONTH(date) = %s
               GROUP BY date
               ORDER BY date ASC;""",
            (year, month)
        )
        daily_trend = cursor.fetchall()
        for d in daily_trend:
            d['date_str'] = d['date'].strftime('%d %b')

        # 4. Department-wise Attendance Performance
        cursor.execute(
            """SELECT d.department_name,
                      COUNT(a.attendance_id) as total_days,
                      SUM(CASE WHEN a.status IN ('PRESENT', 'LATE', 'HALF_DAY') THEN 1 ELSE 0 END) as present_days,
                      SUM(CASE WHEN a.is_late = 1 OR a.status = 'LATE' THEN 1 ELSE 0 END) as late_days,
                      SUM(CASE WHEN a.status = 'ON_LEAVE' THEN 1 ELSE 0 END) as leave_days
               FROM departments d
               JOIN employees e ON d.department_id = e.department_id
               LEFT JOIN attendance a ON e.employee_id = a.employee_id AND YEAR(a.date) = %s AND MONTH(a.date) = %s
               GROUP BY d.department_id, d.department_name
               ORDER BY d.department_name ASC;""",
            (year, month)
        )
        dept_rows = cursor.fetchall()
        dept_analytics = []
        for dept in dept_rows:
            tot = float(dept['total_days'] or 0)
            pres = float(dept['present_days'] or 0)
            pct = round((pres / tot * 100), 1) if tot > 0 else 0.0
            dept_analytics.append({
                'department_name': dept['department_name'],
                'total_days': int(tot),
                'present_days': int(pres),
                'late_days': int(dept['late_days'] or 0),
                'leave_days': int(dept['leave_days'] or 0),
                'attendance_pct': pct
            })

        # 5. Leave Type Distribution
        cursor.execute(
            """SELECT leave_type, COUNT(*) as cnt, COALESCE(SUM(total_days), 0) as total_days
               FROM leave_requests
               WHERE status = 'APPROVED'
               GROUP BY leave_type;"""
        )
        leave_dist_raw = cursor.fetchall()
        leave_dist = []
        for l in leave_dist_raw:
            leave_dist.append({
                'leave_type': l['leave_type'],
                'cnt': int(l['cnt']),
                'total_days': float(l['total_days'])
            })

        # 6. Top Late Arrivals
        cursor.execute(
            """SELECT e.employee_id, e.name, d.department_name, COUNT(a.attendance_id) as late_count
               FROM attendance a
               JOIN employees e ON a.employee_id = e.employee_id
               LEFT JOIN departments d ON e.department_id = d.department_id
               WHERE (a.is_late = 1 OR a.status = 'LATE') 
                 AND YEAR(a.date) = %s AND MONTH(a.date) = %s
               GROUP BY e.employee_id, e.name, d.department_name
               ORDER BY late_count DESC
               LIMIT 5;""",
            (year, month)
        )
        top_late = cursor.fetchall()

        return {
            'year': year,
            'month': month,
            'total_employees': total_employees,
            'present_total': present_total,
            'late_total': late_total,
            'half_day_total': half_day_total,
            'absent_total': absent_total,
            'leave_total': leave_total,
            'total_hours': round(total_hours, 1),
            'overall_attendance_pct': overall_attendance_pct,
            'daily_trend': daily_trend,
            'dept_analytics': dept_analytics,
            'leave_distribution': leave_dist,
            'top_late': top_late
        }

def get_employee_monthly_matrix(year=None, month=None, department_id=None):
    """
    Returns monthly summary row per employee.
    """
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    query = """
        SELECT e.employee_id, e.name, e.designation, d.department_name,
               COUNT(a.attendance_id) as logged_days,
               SUM(CASE WHEN a.status = 'PRESENT' THEN 1 ELSE 0 END) as present_days,
               SUM(CASE WHEN a.is_late = 1 OR a.status = 'LATE' THEN 1 ELSE 0 END) as late_days,
               SUM(CASE WHEN a.status = 'HALF_DAY' THEN 1 ELSE 0 END) as half_days,
               SUM(CASE WHEN a.status = 'ABSENT' THEN 1 ELSE 0 END) as absent_days,
               SUM(CASE WHEN a.status = 'ON_LEAVE' THEN 1 ELSE 0 END) as leave_days,
               COALESCE(SUM(a.working_hours), 0) as total_working_hours
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.department_id
        LEFT JOIN attendance a ON e.employee_id = a.employee_id AND YEAR(a.date) = %s AND MONTH(a.date) = %s
        WHERE e.status = 'ACTIVE'
    """
    params = [year, month]

    if department_id:
        query += " AND e.department_id = %s"
        params.append(department_id)

    query += " GROUP BY e.employee_id, e.name, e.designation, d.department_name ORDER BY e.employee_id ASC;"

    with get_db_cursor() as cursor:
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        for r in rows:
            tot = float(r['logged_days'] or 0)
            pres = float((r['present_days'] or 0) + (r['late_days'] or 0) + (r['half_days'] or 0))
            r['effective_present'] = int(pres)
            r['attendance_pct'] = round((pres / tot * 100), 1) if tot > 0 else 0.0
            r['total_working_hours'] = round(float(r['total_working_hours'] or 0.0), 1)
            r['avg_hours'] = round(r['total_working_hours'] / pres, 1) if pres > 0 else 0.0

        return rows

def generate_excel_report(year=None, month=None):
    """
    Generates a professional corporate Excel workbook containing:
    1. Monthly Employee Summary Matrix
    2. Detailed Attendance Punch Logs
    3. Leave Balance & Requests
    4. Department Performance Metrics
    """
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    month_name = datetime(year, month, 1).strftime('%B %Y')

    matrix_rows = get_employee_monthly_matrix(year, month)
    analytics = get_analytics_summary(year, month)

    wb = openpyxl.Workbook()
    # Sheet 1: Summary Matrix
    ws1 = wb.active
    ws1.title = "Monthly Summary"

    # Styling palettes
    header_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid") # Navy
    sub_header_fill = PatternFill(start_color="2A4D7A", end_color="2A4D7A", fill_type="solid")
    accent_fill = PatternFill(start_color="EAF2F8", end_color="EAF2F8", fill_type="solid")
    zebra_fill = PatternFill(start_color="F9FAFC", end_color="F9FAFC", fill_type="solid")
    
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=16, bold=True, color="1B365D")
    meta_font = Font(name="Calibri", size=10, italic=True, color="555555")
    bold_font = Font(name="Calibri", size=11, bold=True)
    regular_font = Font(name="Calibri", size=10)

    thin_border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )

    # Title block
    ws1.merge_cells("A1:K1")
    ws1["A1"] = f"ENTERPRISE EMPLOYEE ATTENDANCE & WORKFORCE REPORT - {month_name.upper()}"
    ws1["A1"].font = title_font
    ws1["A1"].alignment = Alignment(horizontal="left", vertical="center")

    ws1.merge_cells("A2:K2")
    ws1["A2"] = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Active Staff: {analytics['total_employees']} | Overall Attendance: {analytics['overall_attendance_pct']}%"
    ws1["A2"].font = meta_font

    # Headers for Sheet 1
    headers1 = [
        "Employee ID", "Employee Name", "Department", "Designation",
        "Total Days", "Present", "Late", "Half Day", "Absent", "On Leave",
        "Total Hours", "Attendance %"
    ]
    
    ws1.row_dimensions[4].height = 26
    for col_idx, h in enumerate(headers1, 1):
        cell = ws1.cell(row=4, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center" if col_idx > 4 else "left", vertical="center")
        cell.border = thin_border

    # Data Rows
    current_row = 5
    for idx, r in enumerate(matrix_rows):
        ws1.row_dimensions[current_row].height = 20
        fill = zebra_fill if idx % 2 == 1 else None

        values = [
            r['employee_id'], r['name'], r['department_name'], r['designation'],
            r['logged_days'], r['present_days'], r['late_days'], r['half_days'],
            r['absent_days'], r['leave_days'], r['total_working_hours'], f"{r['attendance_pct']}%"
        ]

        for col_idx, val in enumerate(values, 1):
            cell = ws1.cell(row=current_row, column=col_idx, value=val)
            cell.font = regular_font
            if fill:
                cell.fill = fill
            cell.alignment = Alignment(horizontal="center" if col_idx > 4 else "left", vertical="center")
            cell.border = thin_border

        current_row += 1

    # Sheet 2: Daily Attendance Logs
    ws2 = wb.create_sheet(title="Daily Punch Logs")
    ws2.merge_cells("A1:I1")
    ws2["A1"] = f"DETAILED PUNCH & ATTENDANCE LOGS - {month_name.upper()}"
    ws2["A1"].font = title_font
    
    headers2 = ["Date", "Employee ID", "Name", "Department", "Check-In", "Check-Out", "Working Hours", "Status", "Remarks"]
    ws2.row_dimensions[3].height = 25
    for col_idx, h in enumerate(headers2, 1):
        cell = ws2.cell(row=3, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = sub_header_fill
        cell.alignment = Alignment(horizontal="center" if col_idx in (1, 5, 6, 7, 8) else "left", vertical="center")
        cell.border = thin_border

    with get_db_cursor() as cursor:
        cursor.execute(
            """SELECT a.date, a.employee_id, e.name, d.department_name, a.check_in, a.check_out,
                      a.working_hours, a.status, a.is_late, a.remarks
               FROM attendance a
               JOIN employees e ON a.employee_id = e.employee_id
               LEFT JOIN departments d ON e.department_id = d.department_id
               WHERE YEAR(a.date) = %s AND MONTH(a.date) = %s
               ORDER BY a.date DESC, a.check_in ASC;""",
            (year, month)
        )
        logs = cursor.fetchall()

    row2 = 4
    for idx, l in enumerate(logs):
        ws2.row_dimensions[row2].height = 19
        fill = zebra_fill if idx % 2 == 1 else None

        ci_str = str(l['check_in']) if l['check_in'] else "-"
        co_str = str(l['check_out']) if l['check_out'] else "-"

        vals = [
            l['date'].strftime('%Y-%m-%d'), l['employee_id'], l['name'], l['department_name'],
            ci_str, co_str, float(l['working_hours'] or 0.0), l['status'], l['remarks'] or ''
        ]
        for c_idx, val in enumerate(vals, 1):
            cell = ws2.cell(row=row2, column=c_idx, value=val)
            cell.font = regular_font
            if fill:
                cell.fill = fill
            cell.alignment = Alignment(horizontal="center" if c_idx in (1, 5, 6, 7, 8) else "left", vertical="center")
            cell.border = thin_border
        row2 += 1

    # Auto-adjust column widths on all sheets
    for ws in [ws1, ws2]:
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

def generate_pdf_report(year=None, month=None):
    """
    Generates a PDF executive attendance report using reportlab.
    """
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    month_name = datetime(year, month, 1).strftime('%B %Y')

    analytics = get_analytics_summary(year, month)
    matrix_rows = get_employee_monthly_matrix(year, month)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'RepTitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#1B365D')
    )
    subtitle_style = ParagraphStyle(
        'RepSub', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#555555')
    )
    card_title_style = ParagraphStyle(
        'CardT', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.HexColor('#1B365D'), alignment=1
    )
    card_val_style = ParagraphStyle(
        'CardV', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=15, leading=18, textColor=colors.HexColor('#0F52BA'), alignment=1
    )
    table_hdr_style = ParagraphStyle(
        'TH', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.white, alignment=1
    )
    table_cell_style = ParagraphStyle(
        'TC', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=10, textColor=colors.black
    )
    table_cell_center = ParagraphStyle(
        'TCC', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, leading=10, textColor=colors.black, alignment=1
    )

    story = []

    # Title Banner
    story.append(Paragraph(f"ENTERPRISE ATTENDANCE & WORKFORCE REPORT", title_style))
    story.append(Paragraph(f"Reporting Month: <b>{month_name}</b> | Generated on: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}", subtitle_style))
    story.append(Spacer(1, 14))

    # KPI Summary Cards Table
    kpi_data = [
        [
            Paragraph("TOTAL WORKFORCE", card_title_style),
            Paragraph("OVERALL ATTENDANCE", card_title_style),
            Paragraph("TOTAL PRESENT DAYS", card_title_style),
            Paragraph("LATE ARRIVALS", card_title_style),
            Paragraph("APPROVED LEAVES", card_title_style),
            Paragraph("TOTAL WORKING HOURS", card_title_style)
        ],
        [
            Paragraph(f"{analytics['total_employees']}", card_val_style),
            Paragraph(f"{analytics['overall_attendance_pct']}%", card_val_style),
            Paragraph(f"{analytics['present_total']}", card_val_style),
            Paragraph(f"{analytics['late_total']}", card_val_style),
            Paragraph(f"{analytics['leave_total']}", card_val_style),
            Paragraph(f"{analytics['total_hours']}h", card_val_style)
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[120, 130, 120, 110, 120, 130])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F0F4F8')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 15))

    # Main Attendance Summary Table
    table_headers = [
        Paragraph("Emp ID", table_hdr_style),
        Paragraph("Employee Name", table_hdr_style),
        Paragraph("Department", table_hdr_style),
        Paragraph("Designation", table_hdr_style),
        Paragraph("Days", table_hdr_style),
        Paragraph("Present", table_hdr_style),
        Paragraph("Late", table_hdr_style),
        Paragraph("Half Day", table_hdr_style),
        Paragraph("Absent", table_hdr_style),
        Paragraph("Leave", table_hdr_style),
        Paragraph("Hours", table_hdr_style),
        Paragraph("Att %", table_hdr_style)
    ]
    t_rows = [table_headers]

    for idx, r in enumerate(matrix_rows):
        t_rows.append([
            Paragraph(r['employee_id'], table_cell_center),
            Paragraph(r['name'], table_cell_style),
            Paragraph(r['department_name'] or '', table_cell_style),
            Paragraph(r['designation'] or '', table_cell_style),
            Paragraph(str(r['logged_days']), table_cell_center),
            Paragraph(str(r['present_days']), table_cell_center),
            Paragraph(str(r['late_days']), table_cell_center),
            Paragraph(str(r['half_days']), table_cell_center),
            Paragraph(str(r['absent_days']), table_cell_center),
            Paragraph(str(r['leave_days']), table_cell_center),
            Paragraph(str(r['total_working_hours']), table_cell_center),
            Paragraph(f"<b>{r['attendance_pct']}%</b>", table_cell_center)
        ])

    data_table = Table(
        t_rows,
        colWidths=[55, 110, 110, 115, 38, 42, 38, 45, 40, 40, 48, 50]
    )
    data_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B365D')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ]))
    story.append(data_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
