from django.urls import path
from . import views
from .views.location.location_views import (
    LocationListView, LocationCreateView, LocationUpdateView,
    LocationDetailView, LocationDeleteView, LocationBulkDeleteView,
    LocationExportView
)
from .views.location.location_attendance_views import (
    LocationAttendanceListView, LocationAttendanceCreateView,
    LocationAttendanceUpdateView, LocationAttendanceDetailView,
    LocationAttendanceDeleteView, LocationAttendanceBulkDeleteView,
    LocationAttendanceExportView, attendance_page, mark_attendance,
    get_locations
)
from .views.location.user_location_views import (
    UserLocationListView, UserLocationCreateView, UserLocationUpdateView,
    UserLocationDetailView, UserLocationDeleteView, UserLocationBulkDeleteView,
    UserLocationExportView
)
from .views.location.location_debug_view import debug_user_locations


from .views.zktico.zk_device_crud_views import (
    ZKDeviceListView, ZKDeviceCreateView, ZKDeviceUpdateView,
    ZKDeviceDetailView, ZKDeviceDeleteView, ZKDeviceExportView, ZKDeviceBulkDeleteView,
)

from .views.zktico.zk_user_crud_views import (
    ZKUserDeviceListView, ZKUserAddView, ZKUserUpdateView, ZKUserDetailView, ZKUserDeleteView
)

from .views.zktico.zk_attendance_crud_views import (
    ZKAttendanceDeviceListView, 
    ZKAttendanceDetailView, 
    ZKAttendanceImportView
)

from .views.hrm_demo_views import HRMDemoConfigView
from .views.zktico.zk_device_operation_views import (   ZKDeviceConnectionTestView, ZKDeviceSyncView,
    ZKDeviceSaveDataView,  ZKUserSyncView,
    ZKUserSimpleListView, ZKUserSaveView)
from .views.zktico.zk_attendance_log_views import (
    ZKAttendanceLogListView, ZKAttendanceLogCreateView, ZKAttendanceLogDetailView,
    ZKAttendanceLogUpdateView, ZKAttendanceLogExportView, ZKAttendanceLogBulkDeleteView,
    ZKAttendanceLogDeleteView)

from .views.zktico.report_views import HrmReportListView

from .views.zktico.employee_attendance_report import EmployeeDetailedAttendanceReportView
from .views.zktico.attendance_summary_report import AttendanceSummaryReportView
from .views.zktico.missing_punch_report import MissingPunchReportView
from .views.zktico.late_coming_report import LateComingReportView

from .views.zktico.daily_attendance_report import DailyAttendanceReportView
from .views.zktico.early_leaving_report import EarlyLeavingReportView
from .views.zktico.overtime_import_view import OvertimeImportView, OvertimeImportSaveView
from .views.zktico.attendance_import_view import AttendanceImportView, AttendanceImportSaveView

from .views.zktico.payslip_report import PayslipReportView
from .views.zktico.payroll_summary_report import PayrollSummaryReportView



app_name = 'hrm'

urlpatterns = [
    # Employee related URLs
    path('employee/', views.EmployeeListView.as_view(), name='employee_list'),
    path('employee/create/', views.EmployeeCreateView.as_view(), name='employee_create'),
    path('employee/<int:pk>/update/', views.EmployeeUpdateView.as_view(), name='employee_update'),
    path('employee/<int:pk>/', views.EmployeeDetailView.as_view(), name='employee_detail'),
    path('employee/<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee_delete'),
    path('employee/export/', views.EmployeeExportView.as_view(), name='employee_export'),
    path('employee/bulk-delete/', views.EmployeeBulkDeleteView.as_view(), name='employee_bulk_delete'),
    path('employee-cards/', views.EmployeeCardView.as_view(), name='employee_card_view'),
    path('employee-all/', views.EmployeeAllView.as_view(), name='employee_all_view'),
    path('my-dashboard/', views.EmployeeDashboardView.as_view(), name='employee_dashboard'),
    path('employee-separation/', views.EmployeeSeparationListView.as_view(), name='employee_separation_list'),
    path('employee-separation/create/', views.EmployeeSeparationCreateView.as_view(), name='employee_separation_create'),
    path('employee-separation/<int:pk>/update/', views.EmployeeSeparationUpdateView.as_view(), name='employee_separation_update'),
    path('employee-separation/<int:pk>/', views.EmployeeSeparationDetailView.as_view(), name='employee_separation_detail'),
    path('employee-separation/<int:pk>/delete/', views.EmployeeSeparationDeleteView.as_view(), name='employee_separation_delete'),
    path('employee-separation/export/', views.EmployeeSeparationExportView.as_view(), name='employee_separation_export'),
    path('employee-separation/bulk-delete/', views.EmployeeSeparationBulkDeleteView.as_view(), name='employee_separation_bulk_delete'),
    # Department URLs
    path('department/', views.DepartmentListView.as_view(), name='department_list'),
    path('department/create/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('department/<int:pk>/update/', views.DepartmentUpdateView.as_view(), name='department_update'),
    path('department/<int:pk>/', views.DepartmentDetailView.as_view(), name='department_detail'),
    path('department/<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='department_delete'),
    path('department/export/', views.DepartmentExportView.as_view(), name='department_export'),
    path('department/bulk-delete/', views.DepartmentBulkDeleteView.as_view(), name='department_bulk_delete'),
    # Designation URLs
    path('designation/', views.DesignationListView.as_view(), name='designation_list'),
    path('designation/create/', views.DesignationCreateView.as_view(), name='designation_create'),
    path('designation/<int:pk>/update/', views.DesignationUpdateView.as_view(), name='designation_update'),
    path('designation/<int:pk>/', views.DesignationDetailView.as_view(), name='designation_detail'),
    path('designation/<int:pk>/delete/', views.DesignationDeleteView.as_view(), name='designation_delete'),
    path('designation/export/', views.DesignationExportView.as_view(), name='designation_export'),
    path('designation/bulk-delete/', views.DesignationBulkDeleteView.as_view(), name='designation_bulk_delete'),
    # Workplace URLs
    path('workplace/', views.WorkPlaceListView.as_view(), name='workplace_list'),
    path('workplace/create/', views.WorkPlaceCreateView.as_view(), name='workplace_create'),
    path('workplace/<int:pk>/update/', views.WorkPlaceUpdateView.as_view(), name='workplace_update'),
    path('workplace/<int:pk>/', views.WorkPlaceDetailView.as_view(), name='workplace_detail'),
    path('workplace/<int:pk>/delete/', views.WorkPlaceDeleteView.as_view(), name='workplace_delete'),
    path('workplace/export/', views.WorkPlaceExportView.as_view(), name='workplace_export'),
    path('workplace/bulk-delete/', views.WorkPlaceBulkDeleteView.as_view(), name='workplace_bulk_delete'),
    # Shift URLs
    path('shift/', views.ShiftListView.as_view(), name='shift_list'),
    path('shift/create/', views.ShiftCreateView.as_view(), name='shift_create'),
    path('shift/<int:pk>/update/', views.ShiftUpdateView.as_view(), name='shift_update'),
    path('shift/<int:pk>/', views.ShiftDetailView.as_view(), name='shift_detail'),
    path('shift/<int:pk>/delete/', views.ShiftDeleteView.as_view(), name='shift_delete'),
    path('shift/export/', views.ShiftExportView.as_view(), name='shift_export'),
    path('shift/bulk-delete/', views.ShiftBulkDeleteView.as_view(), name='shift_bulk_delete'),


    path('roster/', views.RosterListView.as_view(), name='roster_list'),
    path('roster/create/', views.RosterCreateView.as_view(), name='roster_create'),
    path('roster/<int:pk>/update/', views.RosterUpdateView.as_view(), name='roster_update'),
    path('roster/<int:pk>/', views.RosterDetailView.as_view(), name='roster_detail'),
    path('roster/<int:pk>/delete/', views.RosterDeleteView.as_view(), name='roster_delete'),
    path('roster/export/', views.RosterExportView.as_view(), name='roster_export'),
    path('roster/bulk-delete/', views.RosterBulkDeleteView.as_view(), name='roster_bulk_delete'),
    
    path('roster-day/', views.RosterDayListView.as_view(), name='roster_day_list'),
    path('roster-day/create/', views.RosterDayCreateView.as_view(), name='roster_day_create'),
    path('roster-day/<int:pk>/update/', views.RosterDayUpdateView.as_view(), name='roster_day_update'),
    path('roster-day/<int:pk>/', views.RosterDayDetailView.as_view(), name='roster_day_detail'),
    path('roster-day/<int:pk>/delete/', views.RosterDayDeleteView.as_view(), name='roster_day_delete'),
    path('roster-day/export/', views.RosterDayExportView.as_view(), name='roster_day_export'),
    path('roster-day/bulk-delete/', views.RosterDayBulkDeleteView.as_view(), name='roster_day_bulk_delete'),   
    # Leave Type URLs
    path('leave-type/', views.LeaveTypeListView.as_view(), name='leave_type_list'),
    path('leave-type/create/', views.LeaveTypeCreateView.as_view(), name='leave_type_create'),
    path('leave-type/<int:pk>/update/', views.LeaveTypeUpdateView.as_view(), name='leave_type_update'),
    path('leave-type/<int:pk>/', views.LeaveTypeDetailView.as_view(), name='leave_type_detail'),
    path('leave-type/<int:pk>/delete/', views.LeaveTypeDeleteView.as_view(), name='leave_type_delete'),
    path('leave-type/export/', views.LeaveTypeExportView.as_view(), name='leave_type_export'),
    path('leave-type/bulk-delete/', views.LeaveTypeBulkDeleteView.as_view(), name='leave_type_bulk_delete'),
    # Leave Application URLs
    path('leave-application/', views.LeaveApplicationListView.as_view(), name='leave_application_list'),
    path('leave-application/create/', views.LeaveApplicationCreateView.as_view(), name='leave_application_create'),
    path('leave-application/<int:pk>/update/', views.LeaveApplicationUpdateView.as_view(), name='leave_application_update'),
    path('leave-application/<int:pk>/', views.LeaveApplicationDetailView.as_view(), name='leave_application_detail'),
    path('leave-application/<int:pk>/delete/', views.LeaveApplicationDeleteView.as_view(), name='leave_application_delete'),
    path('leave-application/export/', views.LeaveApplicationExportView.as_view(), name='leave_application_export'),
    path('leave-application/bulk-delete/', views.LeaveApplicationBulkDeleteView.as_view(), name='leave_application_bulk_delete'),
    # Short Leave Application URLs
    path('short-leave-application/', views.ShortLeaveApplicationListView.as_view(), name='short_leave_application_list'),
    path('short-leave-application/create/', views.ShortLeaveApplicationCreateView.as_view(), name='short_leave_application_create'),
    path('short-leave-application/<int:pk>/update/', views.ShortLeaveApplicationUpdateView.as_view(), name='short_leave_application_update'),
    path('short-leave-application/<int:pk>/', views.ShortLeaveApplicationDetailView.as_view(), name='short_leave_application_detail'),
    path('short-leave-application/<int:pk>/delete/', views.ShortLeaveApplicationDeleteView.as_view(), name='short_leave_application_delete'),
    path('short-leave-application/export/', views.ShortLeaveApplicationExportView.as_view(), name='short_leave_application_export'),
    path('short-leave-application/bulk-delete/', views.ShortLeaveApplicationBulkDeleteView.as_view(), name='short_leave_application_bulk_delete'),
    # Leave Balance URLs
    path('leave-balance/', views.LeaveBalanceListView.as_view(), name='leave_balance_list'),
    path('leave-balance/create/', views.LeaveBalanceCreateView.as_view(), name='leave_balance_create'),
    path('leave-balance/<int:pk>/', views.LeaveBalanceDetailView.as_view(), name='leave_balance_detail'),
    path('leave-balance/<int:pk>/update/', views.LeaveBalanceUpdateView.as_view(), name='leave_balance_update'),
    path('leave-balance/<int:pk>/delete/', views.LeaveBalanceDeleteView.as_view(), name='leave_balance_delete'),
    path('leave-balance/export/', views.LeaveBalanceExportView.as_view(), name='leave_balance_export'),
    path('leave-balance/bulk-delete/', views.LeaveBalanceBulkDeleteView.as_view(), name='leave_balance_bulk_delete'),
    path('leave-balance/initialize/', views.LeaveBalanceInitializeView.as_view(), name='leave_balance_initialize'),
    # Holiday URLs
    path('holiday/', views.HolidayListView.as_view(), name='holiday_list'),
    path('holiday/create/', views.HolidayCreateView.as_view(), name='holiday_create'),
    path('holiday/<int:pk>/update/', views.HolidayUpdateView.as_view(), name='holiday_update'),
    path('holiday/<int:pk>/', views.HolidayDetailView.as_view(), name='holiday_detail'),
    path('holiday/<int:pk>/delete/', views.HolidayDeleteView.as_view(), name='holiday_delete'),
    path('holiday/export/', views.HolidayExportView.as_view(), name='holiday_export'),
    path('holiday/bulk-delete/', views.HolidayBulkDeleteView.as_view(), name='holiday_bulk_delete'),
    # Attendance URLs
    path('attendance/', views.AttendanceListView.as_view(), name='attendance_list'),
    path('attendance/create/', views.AttendanceCreateView.as_view(), name='attendance_create'),
    path('attendance/<int:pk>/update/', views.AttendanceUpdateView.as_view(), name='attendance_update'),
    path('attendance/<int:pk>/', views.AttendanceDetailView.as_view(), name='attendance_detail'),
    path('attendance/<int:pk>/delete/', views.AttendanceDeleteView.as_view(), name='attendance_delete'),
    path('attendance/export/', views.AttendanceExportView.as_view(), name='attendance_export'),
    path('attendance/bulk-delete/', views.AttendanceBulkDeleteView.as_view(), name='attendance_bulk_delete'),
    path('reports/attendance-summery/', views.AttendanceSummaryView.as_view(), name='attendance_model_attendance_summery'),
    path('reports/employee_attendance_details/', views.EmployeeAttendanceDetailView.as_view(), name='attendance_model_attendance_details'),


    # Attendance Reports URLs
   

    # Attendance Month URLs
    path('attendance-month/', views.AttendanceMonthListView.as_view(), name='attendance_month_list'),
    path('attendance-month/create/', views.AttendanceMonthCreateView.as_view(), name='attendance_month_create'),
    path('attendance-month/<int:pk>/update/', views.AttendanceMonthUpdateView.as_view(), name='attendance_month_update'),
    path('attendance-month/<int:pk>/', views.AttendanceMonthDetailView.as_view(), name='attendance_month_detail'),
    path('attendance-month/<int:pk>/delete/', views.AttendanceMonthDeleteView.as_view(), name='attendance_month_delete'),
    path('attendance-month/export/', views.AttendanceMonthExportView.as_view(), name='attendance_month_export'),
    path('attendance-month/bulk-delete/', views.AttendanceMonthBulkDeleteView.as_view(), name='attendance_month_bulk_delete'),
    # Attendance Log URLs
    path('attendance-log/', views.AttendanceLogListView.as_view(), name='attendance_log_list'),
    path('attendance-log/create/', views.AttendanceLogCreateView.as_view(), name='attendance_log_create'),
    path('attendance-log/<int:pk>/update/', views.AttendanceLogUpdateView.as_view(), name='attendance_log_update'),
    path('attendance-log/<int:pk>/', views.AttendanceLogDetailView.as_view(), name='attendance_log_detail'),
    path('attendance-log/<int:pk>/delete/', views.AttendanceLogDeleteView.as_view(), name='attendance_log_delete'),
    path('attendance-log/export/', views.AttendanceLogExportView.as_view(), name='attendance_log_export'),
    path('attendance-log/bulk-delete/', views.AttendanceLogBulkDeleteView.as_view(), name='attendance_log_bulk_delete'),
    # Overtime Record URLs
    path('overtime-record/', views.OvertimeRecordListView.as_view(), name='overtime_record_list'),
    path('overtime-record/create/', views.OvertimeRecordCreateView.as_view(), name='overtime_record_create'),
    path('overtime-record/<int:pk>/update/', views.OvertimeRecordUpdateView.as_view(), name='overtime_record_update'),
    path('overtime-record/<int:pk>/', views.OvertimeRecordDetailView.as_view(), name='overtime_record_detail'),
    path('overtime-record/<int:pk>/delete/', views.OvertimeRecordDeleteView.as_view(), name='overtime_record_delete'),
    path('overtime-record/export/', views.OvertimeRecordExportView.as_view(), name='overtime_record_export'),
    path('overtime-record/bulk-delete/', views.OvertimeRecordBulkDeleteView.as_view(), name='overtime_record_bulk_delete'),
    path('reports/attendance-overtime-summery/', views.OvertimeSummaryView.as_view(), name='attendance_over_time_summery'),

    # Location URLs
    path('locations/', LocationListView.as_view(), name='location_list'),
    path('locations/create/', LocationCreateView.as_view(), name='location_create'),
    path('locations/<int:pk>/update/', LocationUpdateView.as_view(), name='location_update'),
    path('locations/<int:pk>/', LocationDetailView.as_view(), name='location_detail'),
    path('locations/<int:pk>/delete/', LocationDeleteView.as_view(), name='location_delete'),
    path('locations/bulk-delete/', LocationBulkDeleteView.as_view(), name='location_bulk_delete'),
    path('locations/export/', LocationExportView.as_view(), name='location_export'),
    # Location Attendance URLs
    path('location-attendance/', LocationAttendanceListView.as_view(), name='location_attendance_list'),
    path('location-attendance/create/', LocationAttendanceCreateView.as_view(), name='location_attendance_create'),
    path('location-attendance/<int:pk>/update/', LocationAttendanceUpdateView.as_view(), name='location_attendance_update'),
    path('location-attendance/<int:pk>/', LocationAttendanceDetailView.as_view(), name='location_attendance_detail'),
    path('location-attendance/<int:pk>/delete/', LocationAttendanceDeleteView.as_view(), name='location_attendance_delete'),
    path('location-attendance/bulk-delete/', LocationAttendanceBulkDeleteView.as_view(), name='location_attendance_bulk_delete'),
    path('location-attendance/export/', LocationAttendanceExportView.as_view(), name='location_attendance_export'),
    # User Location URLs
    path('user-locations/', UserLocationListView.as_view(), name='user_location_list'),
    path('user-locations/create/', UserLocationCreateView.as_view(), name='user_location_create'),
    path('user-locations/<int:pk>/update/', UserLocationUpdateView.as_view(), name='user_location_update'),
    path('user-locations/<int:pk>/', UserLocationDetailView.as_view(), name='user_location_detail'),
    path('user-locations/<int:pk>/delete/', UserLocationDeleteView.as_view(), name='user_location_delete'),
    path('user-locations/bulk-delete/', UserLocationBulkDeleteView.as_view(), name='user_location_bulk_delete'),
    path('user-locations/export/', UserLocationExportView.as_view(), name='user_location_export'),
    # Attendance Page URLs
    path('attendance-page/', attendance_page, name='attendance_page'),
    path('mark-attendance/', mark_attendance, name='mark_attendance'),
    path('get-locations/', get_locations, name='get_locations'),
    path('debug-locations/', debug_user_locations, name='debug_locations'),


    # ZK Device URLs
    path('zk-devices/', ZKDeviceListView.as_view(), name='zk_device_list'),
    path('zk-devices/create/', ZKDeviceCreateView.as_view(), name='zk_device_create'),
    path('zk-devices/<int:pk>/update/', ZKDeviceUpdateView.as_view(), name='zk_device_update'),
    path('zk-devices/<int:pk>/', ZKDeviceDetailView.as_view(), name='zk_device_detail'),
    path('zk-devices/<int:pk>/delete/', ZKDeviceDeleteView.as_view(), name='zk_device_delete'),
    path('zk-devices/export/', ZKDeviceExportView.as_view(), name='zk_device_export'),
    path('zk-devices/bulk-delete/', ZKDeviceBulkDeleteView.as_view(), name='zk_device_bulk_delete'),

    
    path('zk-devices/test-connection/', ZKDeviceConnectionTestView.as_view(), name='zk_device_test_connection'),
    path('zk-devices/sync/', ZKDeviceSyncView.as_view(), name='zk_device_sync'),
    path('zk-devices/save-data/', ZKDeviceSaveDataView.as_view(), name='zk_device_save_data'),
    path('zk-user-sync/', ZKUserSyncView.as_view(), name='zk_user_sync'),
    path('zk-user-simple-list/', ZKUserSimpleListView.as_view(), name='zk_user_simple_list'),
    path('zk-user-save/', ZKUserSaveView.as_view(), name='zk_user_save'),


    # ZK Attendance Log URLs
    path('zk-attendance-logs/', ZKAttendanceLogListView.as_view(), name='zk_attendance_log_list'),
    path('zk-attendance-logs/create/', ZKAttendanceLogCreateView.as_view(), name='zk_attendance_log_create'),
    path('zk-attendance-logs/<int:pk>/', ZKAttendanceLogDetailView.as_view(), name='zk_attendance_log_detail'),
    path('zk-attendance-logs/<int:pk>/update/', ZKAttendanceLogUpdateView.as_view(), name='zk_attendance_log_update'),
    path('zk-attendance-logs/export/', ZKAttendanceLogExportView.as_view(), name='zk_attendance_log_export'),
    path('zk-attendance-logs/bulk-delete/', ZKAttendanceLogBulkDeleteView.as_view(), name='zk_attendance_log_bulk_delete'),
    path('zk-attendance-logs/delete/<int:pk>/', ZKAttendanceLogDeleteView.as_view(), name='zk_attendance_log_delete'),
    

    # ZK User Management (Direct from Device)
    path('zk-users-device/', ZKUserDeviceListView.as_view(), name='zk_user_list_device'),
    path('zk-users/add/', ZKUserAddView.as_view(), name='zk_user_add'),
    path('zk-users/<int:device_id>/<str:user_id>/', ZKUserDetailView.as_view(), name='zk_user_detail'),
    path('zk-users/<int:device_id>/<str:user_id>/update/', ZKUserUpdateView.as_view(), name='zk_user_update'),
    path('zk-users/<int:device_id>/<str:user_id>/delete/', ZKUserDeleteView.as_view(), name='zk_user_delete'),
   

    # ZK Attendance CRUD URLs (Read-only with Import)
    path('zk-attendance-device/', ZKAttendanceDeviceListView.as_view(), name='zk_attendance_list_device'),
    path('zk-attendance/import/', ZKAttendanceImportView.as_view(), name='zk_attendance_import'),
    path('zk-attendance/<int:device_id>/<str:user_id>/<str:timestamp>/', ZKAttendanceDetailView.as_view(), name='zk_attendance_detail'),
        
    
    
    
    # Salary Component URLs
    path('salary-component/', views.SalaryComponentListView.as_view(), name='salary_component_list'),
    path('salary-component/create/', views.SalaryComponentCreateView.as_view(), name='salary_component_create'),
    path('salary-component/<int:pk>/update/', views.SalaryComponentUpdateView.as_view(), name='salary_component_update'),
    path('salary-component/<int:pk>/', views.SalaryComponentDetailView.as_view(), name='salary_component_detail'),
    path('salary-component/<int:pk>/delete/', views.SalaryComponentDeleteView.as_view(), name='salary_component_delete'),
    path('salary-component/export/', views.SalaryComponentExportView.as_view(), name='salary_component_export'),
    path('salary-component/bulk-delete/', views.SalaryComponentBulkDeleteView.as_view(), name='salary_component_bulk_delete'),
    # Employee Salary Structure URLs
    path('employee-salary-structure/', views.EmployeeSalaryStructureListView.as_view(), name='employee_salary_structure_list'),
    path('employee-salary-structure/create/', views.EmployeeSalaryStructureCreateView.as_view(), name='employee_salary_structure_create'),
    path('employee-salary-structure/<int:pk>/update/', views.EmployeeSalaryStructureUpdateView.as_view(), name='employee_salary_structure_update'),
    path('employee-salary-structure/<int:pk>/', views.EmployeeSalaryStructureDetailView.as_view(), name='employee_salary_structure_detail'),
    path('employee-salary-structure/<int:pk>/delete/', views.EmployeeSalaryStructureDeleteView.as_view(), name='employee_salary_structure_delete'),
    path('employee-salary-structure/export/', views.EmployeeSalaryStructureExportView.as_view(), name='employee_salary_structure_export'),
    path('employee-salary-structure/bulk-delete/', views.EmployeeSalaryStructureBulkDeleteView.as_view(), name='employee_salary_structure_bulk_delete'),
    # Bonus Setup URLs
    path('bonus-setup/', views.BonusSetupListView.as_view(), name='bonus_setup_list'),
    path('bonus-setup/create/', views.BonusSetupCreateView.as_view(), name='bonus_setup_create'),
    path('bonus-setup/<int:pk>/update/', views.BonusSetupUpdateView.as_view(), name='bonus_setup_update'),
    path('bonus-setup/<int:pk>/', views.BonusSetupDetailView.as_view(), name='bonus_setup_detail'),
    path('bonus-setup/<int:pk>/delete/', views.BonusSetupDeleteView.as_view(), name='bonus_setup_delete'),
    path('bonus-setup/export/', views.BonusSetupExportView.as_view(), name='bonus_setup_export'),
    path('bonus-setup/bulk-delete/', views.BonusSetupBulkDeleteView.as_view(), name='bonus_setup_bulk_delete'),
    # Bonus Month URLs
    path('bonus-month/', views.BonusMonthListView.as_view(), name='bonus_month_list'),
    path('bonus-month/create/', views.BonusMonthCreateView.as_view(), name='bonus_month_create'),
    path('bonus-month/<int:pk>/update/', views.BonusMonthUpdateView.as_view(), name='bonus_month_update'),
    path('bonus-month/<int:pk>/', views.BonusMonthDetailView.as_view(), name='bonus_month_detail'),
    path('bonus-month/<int:pk>/delete/', views.BonusMonthDeleteView.as_view(), name='bonus_month_delete'),
    path('bonus-month/export/', views.BonusMonthExportView.as_view(), name='bonus_month_export'),
    path('bonus-month/bulk-delete/', views.BonusMonthBulkDeleteView.as_view(), name='bonus_month_bulk_delete'),
    # Employee Bonus URLs
    path('employee-bonus/', views.EmployeeBonusListView.as_view(), name='employee_bonus_list'),
    path('employee-bonus/create/', views.EmployeeBonusCreateView.as_view(), name='employee_bonus_create'),
    path('employee-bonus/<int:pk>/update/', views.EmployeeBonusUpdateView.as_view(), name='employee_bonus_update'),
    path('employee-bonus/<int:pk>/', views.EmployeeBonusDetailView.as_view(), name='employee_bonus_detail'),
    path('employee-bonus/<int:pk>/delete/', views.EmployeeBonusDeleteView.as_view(), name='employee_bonus_delete'),
    path('employee-bonus/export/', views.EmployeeBonusExportView.as_view(), name='employee_bonus_export'),
    path('employee-bonus/bulk-delete/', views.EmployeeBonusBulkDeleteView.as_view(), name='employee_bonus_bulk_delete'),
    # Advance Setup URLs
    path('advance-setup/', views.AdvanceSetupListView.as_view(), name='advance_setup_list'),
    path('advance-setup/create/', views.AdvanceSetupCreateView.as_view(), name='advance_setup_create'),
    path('advance-setup/<int:pk>/update/', views.AdvanceSetupUpdateView.as_view(), name='advance_setup_update'),
    path('advance-setup/<int:pk>/', views.AdvanceSetupDetailView.as_view(), name='advance_setup_detail'),
    path('advance-setup/<int:pk>/delete/', views.AdvanceSetupDeleteView.as_view(), name='advance_setup_delete'),
    path('advance-setup/export/', views.AdvanceSetupExportView.as_view(), name='advance_setup_export'),
    path('advance-setup/bulk-delete/', views.AdvanceSetupBulkDeleteView.as_view(), name='advance_setup_bulk_delete'),
    # Employee Advance URLs
    path('employee-advance/', views.EmployeeAdvanceListView.as_view(), name='employee_advance_list'),
    path('employee-advance/create/', views.EmployeeAdvanceCreateView.as_view(), name='employee_advance_create'),
    path('employee-advance/<int:pk>/update/', views.EmployeeAdvanceUpdateView.as_view(), name='employee_advance_update'),
    path('employee-advance/<int:pk>/', views.EmployeeAdvanceDetailView.as_view(), name='employee_advance_detail'),
    path('employee-advance/<int:pk>/delete/', views.EmployeeAdvanceDeleteView.as_view(), name='employee_advance_delete'),
    path('employee-advance/export/', views.EmployeeAdvanceExportView.as_view(), name='employee_advance_export'),
    path('employee-advance/bulk-delete/', views.EmployeeAdvanceBulkDeleteView.as_view(), name='employee_advance_bulk_delete'),
    # Advance Installment URLs
    path('advance-installment/', views.AdvanceInstallmentListView.as_view(), name='advance_installment_list'),
    path('advance-installment/create/', views.AdvanceInstallmentCreateView.as_view(), name='advance_installment_create'),
    path('advance-installment/<int:pk>/update/', views.AdvanceInstallmentUpdateView.as_view(), name='advance_installment_update'),
    path('advance-installment/<int:pk>/', views.AdvanceInstallmentDetailView.as_view(), name='advance_installment_detail'),
    path('advance-installment/<int:pk>/delete/', views.AdvanceInstallmentDeleteView.as_view(), name='advance_installment_delete'),
    path('advance-installment/export/', views.AdvanceInstallmentExportView.as_view(), name='advance_installment_export'),
    path('advance-installment/bulk-delete/', views.AdvanceInstallmentBulkDeleteView.as_view(), name='advance_installment_bulk_delete'),
    # Salary Month URLs
    path('salary-month/', views.SalaryMonthListView.as_view(), name='salary_month_list'),
    path('salary-month/create/', views.SalaryMonthCreateView.as_view(), name='salary_month_create'),
    path('salary-month/<int:pk>/update/', views.SalaryMonthUpdateView.as_view(), name='salary_month_update'),
    path('salary-month/<int:pk>/', views.SalaryMonthDetailView.as_view(), name='salary_month_detail'),
    path('salary-month/<int:pk>/delete/', views.SalaryMonthDeleteView.as_view(), name='salary_month_delete'),
    path('salary-month/export/', views.SalaryMonthExportView.as_view(), name='salary_month_export'),
    path('salary-month/bulk-delete/', views.SalaryMonthBulkDeleteView.as_view(), name='salary_month_bulk_delete'),
    # Employee Salary URLs
    path('employee-salary/', views.EmployeeSalaryListView.as_view(), name='employee_salary_list'),
    path('employee-salary/create/', views.EmployeeSalaryCreateView.as_view(), name='employee_salary_create'),
    path('employee-salary/<int:pk>/update/', views.EmployeeSalaryUpdateView.as_view(), name='employee_salary_update'),
    path('employee-salary/<int:pk>/', views.EmployeeSalaryDetailView.as_view(), name='employee_salary_detail'),
    path('employee-salary/<int:pk>/delete/', views.EmployeeSalaryDeleteView.as_view(), name='employee_salary_delete'),
    path('employee-salary/export/', views.EmployeeSalaryExportView.as_view(), name='employee_salary_export'),
    path('employee-salary/bulk-delete/', views.EmployeeSalaryBulkDeleteView.as_view(), name='employee_salary_bulk_delete'),
    # Promotion URLs
    path('promotion/', views.PromotionListView.as_view(), name='promotion_list'),
    path('promotion/create/', views.PromotionCreateView.as_view(), name='promotion_create'),
    path('promotion/<int:pk>/update/', views.PromotionUpdateView.as_view(), name='promotion_update'),
    path('promotion/<int:pk>/', views.PromotionDetailView.as_view(), name='promotion_detail'),
    path('promotion/<int:pk>/delete/', views.PromotionDeleteView.as_view(), name='promotion_delete'),
    path('promotion/export/', views.PromotionExportView.as_view(), name='promotion_export'),
    path('promotion/bulk-delete/', views.PromotionBulkDeleteView.as_view(), name='promotion_bulk_delete'),
    # Increment URLs
    path('increment/', views.IncrementListView.as_view(), name='increment_list'),
    path('increment/create/', views.IncrementCreateView.as_view(), name='increment_create'),
    path('increment/<int:pk>/update/', views.IncrementUpdateView.as_view(), name='increment_update'),
    path('increment/<int:pk>/', views.IncrementDetailView.as_view(), name='increment_detail'),
    path('increment/<int:pk>/delete/', views.IncrementDeleteView.as_view(), name='increment_delete'),
    path('increment/export/', views.IncrementExportView.as_view(), name='increment_export'),
    path('increment/bulk-delete/', views.IncrementBulkDeleteView.as_view(), name='increment_bulk_delete'),
    # Deduction URLs
    path('deduction/', views.DeductionListView.as_view(), name='deduction_list'),
    path('deduction/create/', views.DeductionCreateView.as_view(), name='deduction_create'),
    path('deduction/<int:pk>/update/', views.DeductionUpdateView.as_view(), name='deduction_update'),
    path('deduction/<int:pk>/', views.DeductionDetailView.as_view(), name='deduction_detail'),
    path('deduction/<int:pk>/delete/', views.DeductionDeleteView.as_view(), name='deduction_delete'),
    path('deduction/export/', views.DeductionExportView.as_view(), name='deduction_export'),
    path('deduction/bulk-delete/', views.DeductionBulkDeleteView.as_view(), name='deduction_bulk_delete'),

   # Demo Config URL
    path('demo/config/', HRMDemoConfigView.as_view(), name='hrm_demo_config'),


    # Attendance Reports
    path('reports/', HrmReportListView.as_view(), name='report-list'),
    path('attendance/reports/detailed/', EmployeeDetailedAttendanceReportView.as_view(), name='attendance-detailed'),
    path('attendance/reports/summary/', AttendanceSummaryReportView.as_view(), name='attendance-summary'),
    path('attendance/reports/missing-punch/', MissingPunchReportView.as_view(), name='attendance-missing-punch'),
    path('attendance/reports/late-coming/', LateComingReportView.as_view(), name='attendance-late-coming'),
    path('attendance/reports/daily/', DailyAttendanceReportView.as_view(), name='attendance-daily'),
    path('attendance/reports/early-leaving/', EarlyLeavingReportView.as_view(), name='attendance-early-leaving'),

    
    # Attendance Import
    path('attendance/import/', AttendanceImportView.as_view(), name='zk-attendance-import'),
    path('attendance/import/save/', AttendanceImportSaveView.as_view(), name='attendance-import-save'),   

        # Overtime Import (new)
    path('overtime/import/', OvertimeImportView.as_view(), name='overtime-import'),
    path('overtime/import/save/', OvertimeImportSaveView.as_view(), name='overtime-import-save'),
    # Payroll Reports
    path('payroll/reports/payslip/', PayslipReportView.as_view(), name='payroll-payslip'),
    path('payroll/reports/summary/', PayrollSummaryReportView.as_view(), name='payroll-summary'),
]