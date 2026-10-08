"""
Flask Route & Endpoint Integration Tests
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import create_app

def test_routes():
    print("Testing Flask Web Routes & API endpoints...")
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    # 1. Test Login Page (GET)
    res = client.get('/login')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"Enterprise Portal Login" in res.data or b"Workforce Management" in res.data
    print("  [PASS] GET /login -> 200 OK")

    # 2. Test API Login with Admin (POST)
    res = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    json_data = res.get_json()
    assert json_data['role'] == 'admin'
    print(f"  [PASS] POST /api/auth/login (Admin) -> 200 OK ({json_data['message']})")

    # 3. Test Admin Dashboard with Session
    res = client.get('/admin/dashboard')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"System Administration" in res.data
    print("  [PASS] GET /admin/dashboard -> 200 OK")

    # 4. Test HR Dashboard with Session
    res = client.get('/hr/dashboard')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"HR & Workforce Intelligence" in res.data
    print("  [PASS] GET /hr/dashboard -> 200 OK")

    # 5. Test Reports Page
    res = client.get('/reports')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"Monthly Attendance Summary Matrix" in res.data
    print("  [PASS] GET /reports -> 200 OK")

    # 6. Test Power BI Center Page
    res = client.get('/powerbi')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert b"Power BI Workforce Analytics Center" in res.data
    print("  [PASS] GET /powerbi -> 200 OK")

    # 7. Test Excel Download Route
    res = client.get('/reports/excel/monthly?year=2026&month=10')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert 'spreadsheetml.sheet' in res.content_type
    print(f"  [PASS] GET /reports/excel/monthly -> 200 OK ({len(res.data)} bytes)")

    # 8. Test PDF Download Route
    res = client.get('/reports/pdf/monthly?year=2026&month=10')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert 'application/pdf' in res.content_type
    print(f"  [PASS] GET /reports/pdf/monthly -> 200 OK ({len(res.data)} bytes)")

    # 9. Test Employee Login & Dashboard
    with client.session_transaction() as sess:
        sess.clear()
    res = client.post('/api/auth/login', json={'username': 'emp101', 'password': 'emp123'})
    assert res.status_code == 200
    res = client.get('/employee/dashboard')
    assert res.status_code == 200
    assert b"Employee Portal" in res.data
    print("  [PASS] GET /employee/dashboard (Employee) -> 200 OK")

    print("\nALL FLASK ROUTE INTEGRATION TESTS PASSED 100%!")

if __name__ == '__main__':
    test_routes()
