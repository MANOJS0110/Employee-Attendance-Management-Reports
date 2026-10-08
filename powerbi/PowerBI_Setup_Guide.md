# Power BI Setup & Analytics Dashboard Guide
**Enterprise Employee Leave, Attendance & Workforce Analytics**

This project includes complete Power BI Business Intelligence integration. You can connect Power BI Desktop to this system either via **Direct MySQL Connection** or via the **One-Click Pre-Exported Star Schema CSV Files**.

---

## 1. Option A: Direct MySQL Database Connection

1. Open **Power BI Desktop**.
2. Click **Get Data** -> **MySQL database**.
3. Enter Connection details:
   - **Server**: `localhost:3306`
   - **Database**: `employee_attendance_db`
   - **Data Connectivity mode**: `Import` (or DirectQuery)
4. In the credentials dialog:
   - **User name**: `root`
   - **Password**: `ManojS@0311`
5. Select the following tables to load:
   - `employees`
   - `departments`
   - `attendance`
   - `leave_requests`
   - `leave_balance`
   - `holidays`
6. Click **Transform Data** (Power Query) or **Load**.

---

## 2. Option B: 1-Click CSV Import (Fastest & Easiest)

All tables are already exported in Star-Schema format in `powerbi/data/`:
1. `Dim_Departments.csv`
2. `Dim_Employees.csv`
3. `Fact_Attendance.csv`
4. `Fact_LeaveRequests.csv`
5. `Fact_LeaveBalance.csv`
6. `Dim_Date.csv` (Complete calendar dimension)

In Power BI:
1. Click **Get Data** -> **Text/CSV**.
2. Select each file from `Employee Attendance Management Reports\powerbi\data\`.
3. Click **Load**.

---

## 3. Data Model Relationships (Star Schema)

Switch to the **Model View** in Power BI and verify or configure these relationships:

| From Table (Many) | Column | To Table (One) | Column | Cardinality | Cross Filter |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Fact_Attendance` | `employee_id` | `Dim_Employees` | `employee_id` | Many to 1 (*:1) | Single |
| `Fact_Attendance` | `date` | `Dim_Date` | `Date` | Many to 1 (*:1) | Single |
| `Dim_Employees` | `department_id` | `Dim_Departments` | `department_id` | Many to 1 (*:1) | Single |
| `Fact_LeaveRequests` | `employee_id` | `Dim_Employees` | `employee_id` | Many to 1 (*:1) | Single |
| `Fact_LeaveBalance` | `employee_id` | `Dim_Employees` | `employee_id` | 1 to 1 (1:1) | Both |

---

## 4. Ready-to-Copy DAX Measures

Create a new table in Power BI named `_Measures` or add these measures to `Fact_Attendance`:

### A. Workforce & Headcount
```dax
Total Workforce = 
DISTINCTCOUNT(Dim_Employees[employee_id])
```

```dax
Active Employees = 
CALCULATE(
    DISTINCTCOUNT(Dim_Employees[employee_id]), 
    Dim_Employees[status] = "ACTIVE"
)
```

### B. Attendance Performance & Rates
```dax
Total Logged Records = 
COUNTROWS(Fact_Attendance)
```

```dax
Present Days = 
CALCULATE(
    COUNTROWS(Fact_Attendance),
    Fact_Attendance[status] IN {"PRESENT", "LATE", "HALF_DAY"}
)
```

```dax
Absent Days = 
CALCULATE(
    COUNTROWS(Fact_Attendance),
    Fact_Attendance[status] = "ABSENT"
)
```

```dax
Attendance Percentage = 
DIVIDE([Present Days], [Total Logged Records], 0)
```

```dax
Late Arrival Count = 
CALCULATE(
    COUNTROWS(Fact_Attendance),
    Fact_Attendance[is_late] = TRUE() || Fact_Attendance[status] = "LATE"
)
```

```dax
Late Arrival Rate = 
DIVIDE([Late Arrival Count], [Present Days], 0)
```

```dax
Half Day Count = 
CALCULATE(
    COUNTROWS(Fact_Attendance),
    Fact_Attendance[status] = "HALF_DAY"
)
```

### C. Working Hours & Productivity
```dax
Total Working Hours = 
SUM(Fact_Attendance[working_hours])
```

```dax
Avg Daily Working Hours = 
AVERAGEX(
    FILTER(Fact_Attendance, Fact_Attendance[working_hours] > 0),
    Fact_Attendance[working_hours]
)
```

### D. Leave Analytics
```dax
Approved Leave Days = 
CALCULATE(
    SUM(Fact_LeaveRequests[total_days]),
    Fact_LeaveRequests[status] = "APPROVED"
)
```

```dax
Pending Leave Requests = 
CALCULATE(
    COUNTROWS(Fact_LeaveRequests),
    Fact_LeaveRequests[status] = "PENDING"
)
```

```dax
Total Leave Balance Available = 
SUM(Fact_LeaveBalance[casual_leave]) + 
SUM(Fact_LeaveBalance[sick_leave]) + 
SUM(Fact_LeaveBalance[earned_leave]) + 
SUM(Fact_LeaveBalance[optional_leave])
```

---

## 5. Recommended Visuals for Power BI Dashboard

### Page 1: HR Executive Attendance Overview
1. **KPI Cards (Top Row)**:
   - Card 1: `[Total Workforce]`
   - Card 2: `[Attendance Percentage]` (Format as %)
   - Card 3: `[Late Arrival Rate]` (Format as %)
   - Card 4: `[Avg Daily Working Hours]` (Format as Decimal, e.g., 8.4h)
   - Card 5: `[Approved Leave Days]`
2. **Attendance Trend (Middle)**:
   - **Line Chart**: X-Axis: `Dim_Date[Date]`, Y-Axis: `[Present Days]` and `[Late Arrival Count]`
3. **Department Performance (Bottom Left)**:
   - **Clustered Bar Chart**: Y-Axis: `Dim_Departments[department_name]`, X-Axis: `[Attendance Percentage]`
4. **Leave Distribution (Bottom Right)**:
   - **Donut Chart**: Legend: `Fact_LeaveRequests[leave_type]`, Values: `Fact_LeaveRequests[total_days]`
5. **Slicers (Left or Top Filter Bar)**:
   - Department Dropdown (`Dim_Departments[department_name]`)
   - Date Range Slider (`Dim_Date[Date]`)

### Page 2: Employee Deep-Dive & Punctuality
1. **Employee Selector**: Slicer on `Dim_Employees[name]`
2. **KPIs**: `[Present Days]`, `[Late Arrival Count]`, `[Half Day Count]`, `[Absent Days]`
3. **Monthly Calendar Heatmap / Matrix**:
   - Rows: `Dim_Employees[name]`
   - Columns: `Dim_Date[Day]`
   - Values: `Fact_Attendance[status]`
