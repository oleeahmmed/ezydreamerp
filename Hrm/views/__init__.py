from .employee.employee_view import (
    EmployeeListView, EmployeeCardView, EmployeeAllView, EmployeeCreateView, 
    EmployeeUpdateView, EmployeeDetailView, EmployeeDeleteView, EmployeeExportView,
    EmployeeBulkDeleteView
)
from .employee.employee_dashboard_view import EmployeeDashboardView
from .employee.employee_separation_view import (
    EmployeeSeparationListView, EmployeeSeparationCreateView, EmployeeSeparationUpdateView,
    EmployeeSeparationDetailView, EmployeeSeparationDeleteView, EmployeeSeparationExportView,
    EmployeeSeparationBulkDeleteView
)
from .employee.department_view import (
    DepartmentListView, DepartmentCreateView, DepartmentUpdateView,
    DepartmentDetailView, DepartmentDeleteView, DepartmentExportView,
    DepartmentBulkDeleteView
)
from .employee.designation_view import (
    DesignationListView, DesignationCreateView, DesignationUpdateView,
    DesignationDetailView, DesignationDeleteView, DesignationExportView,
    DesignationBulkDeleteView
)
from .roster.workplace_view import (
    WorkPlaceListView, WorkPlaceCreateView, WorkPlaceUpdateView,
    WorkPlaceDetailView, WorkPlaceDeleteView, WorkPlaceExportView,
    WorkPlaceBulkDeleteView
)
from .roster.shift_view import (
    ShiftListView, ShiftCreateView, ShiftUpdateView,
    ShiftDetailView, ShiftDeleteView, ShiftExportView,
    ShiftBulkDeleteView
)
from .roster.roster_view import (
    RosterListView,
    RosterCreateView, 
    RosterUpdateView,
    RosterDetailView,
    RosterDeleteView,
    RosterExportView,
    RosterBulkDeleteView
)
from .roster.roster_day_views import (
    RosterDayListView, RosterDayCreateView, RosterDayUpdateView,
    RosterDayDetailView, RosterDayDeleteView, RosterDayExportView,
    RosterDayBulkDeleteView
)


from .leave.leave_type_view import (
    LeaveTypeListView, LeaveTypeCreateView, LeaveTypeUpdateView,
    LeaveTypeDetailView, LeaveTypeDeleteView, LeaveTypeExportView,
    LeaveTypeBulkDeleteView
)
from .leave.leave_application_view import (
    LeaveApplicationListView, LeaveApplicationCreateView, LeaveApplicationUpdateView,
    LeaveApplicationDetailView, LeaveApplicationDeleteView, LeaveApplicationExportView,
    LeaveApplicationBulkDeleteView
)
from .leave.short_leave_application_view import (
    ShortLeaveApplicationListView, ShortLeaveApplicationCreateView, ShortLeaveApplicationUpdateView,
    ShortLeaveApplicationDetailView, ShortLeaveApplicationDeleteView, ShortLeaveApplicationExportView,
    ShortLeaveApplicationBulkDeleteView
)
from .leave.leave_balance_view import (
    LeaveBalanceListView, LeaveBalanceCreateView, LeaveBalanceUpdateView,
    LeaveBalanceDetailView, LeaveBalanceDeleteView, LeaveBalanceExportView,
    LeaveBalanceBulkDeleteView, LeaveBalanceInitializeView
)
from .leave.holiday_view import (
    HolidayListView, HolidayCreateView, HolidayUpdateView,
    HolidayDetailView, HolidayDeleteView, HolidayExportView,
    HolidayBulkDeleteView
)
from .attendance.attendance_view import (
    AttendanceListView, AttendanceCreateView, AttendanceUpdateView,
    AttendanceDetailView, AttendanceDeleteView, AttendanceExportView,
    AttendanceBulkDeleteView
)
from .attendance.attendance_month_view import (
    AttendanceMonthListView, AttendanceMonthCreateView, AttendanceMonthUpdateView,
    AttendanceMonthDetailView, AttendanceMonthDeleteView, AttendanceMonthExportView,
    AttendanceMonthBulkDeleteView
)
from .attendance.attendance_log_view import (
    AttendanceLogListView, AttendanceLogCreateView, AttendanceLogUpdateView,
    AttendanceLogDetailView, AttendanceLogDeleteView, AttendanceLogExportView,
    AttendanceLogBulkDeleteView
)

from .attendance.reports.attendance_summary_views import (AttendanceSummaryView,EmployeeAttendanceDetailView)
from .attendance.reports.overtime_summary_views import (OvertimeSummaryView)

from .attendance.overtime_record_view import (
    OvertimeRecordListView, OvertimeRecordCreateView, OvertimeRecordUpdateView,
    OvertimeRecordDetailView, OvertimeRecordDeleteView, OvertimeRecordExportView,
    OvertimeRecordBulkDeleteView
)
from .salary_component_view import (
    SalaryComponentListView, SalaryComponentCreateView, SalaryComponentUpdateView,
    SalaryComponentDetailView, SalaryComponentDeleteView, SalaryComponentExportView,
    SalaryComponentBulkDeleteView
)
from .employee_salary_structure_view import (
    EmployeeSalaryStructureListView, EmployeeSalaryStructureCreateView, EmployeeSalaryStructureUpdateView,
    EmployeeSalaryStructureDetailView, EmployeeSalaryStructureDeleteView, EmployeeSalaryStructureExportView,
    EmployeeSalaryStructureBulkDeleteView
)
from .bonus_setup_view import (
    BonusSetupListView, BonusSetupCreateView, BonusSetupUpdateView,
    BonusSetupDetailView, BonusSetupDeleteView, BonusSetupExportView,
    BonusSetupBulkDeleteView
)
from .bonus_month_view import (
    BonusMonthListView, BonusMonthCreateView, BonusMonthUpdateView,
    BonusMonthDetailView, BonusMonthDeleteView, BonusMonthExportView,
    BonusMonthBulkDeleteView
)
from .employee_bonus_view import (
    EmployeeBonusListView, EmployeeBonusCreateView, EmployeeBonusUpdateView,
    EmployeeBonusDetailView, EmployeeBonusDeleteView, EmployeeBonusExportView,
    EmployeeBonusBulkDeleteView
)
from .advance_setup_view import (
    AdvanceSetupListView, AdvanceSetupCreateView, AdvanceSetupUpdateView,
    AdvanceSetupDetailView, AdvanceSetupDeleteView, AdvanceSetupExportView,
    AdvanceSetupBulkDeleteView
)
from .employee_advance_view import (
    EmployeeAdvanceListView, EmployeeAdvanceCreateView, EmployeeAdvanceUpdateView,
    EmployeeAdvanceDetailView, EmployeeAdvanceDeleteView, EmployeeAdvanceExportView,
    EmployeeAdvanceBulkDeleteView
)
from .advance_installment_view import (
    AdvanceInstallmentListView, AdvanceInstallmentCreateView, AdvanceInstallmentUpdateView,
    AdvanceInstallmentDetailView, AdvanceInstallmentDeleteView, AdvanceInstallmentExportView,
    AdvanceInstallmentBulkDeleteView
)
from .salary_month_view import (
    SalaryMonthListView, SalaryMonthCreateView, SalaryMonthUpdateView,
    SalaryMonthDetailView, SalaryMonthDeleteView, SalaryMonthExportView,
    SalaryMonthBulkDeleteView
)
from .employee_salary_view import (
    EmployeeSalaryListView, EmployeeSalaryCreateView, EmployeeSalaryUpdateView,
    EmployeeSalaryDetailView, EmployeeSalaryDeleteView, EmployeeSalaryExportView,
    EmployeeSalaryBulkDeleteView
)
from .promotion_view import (
    PromotionListView, PromotionCreateView, PromotionUpdateView,
    PromotionDetailView, PromotionDeleteView, PromotionExportView,
    PromotionBulkDeleteView
)
from .increment_view import (
    IncrementListView, IncrementCreateView, IncrementUpdateView,
    IncrementDetailView, IncrementDeleteView, IncrementExportView,
    IncrementBulkDeleteView
)
from .deduction_view import (
    DeductionListView, DeductionCreateView, DeductionUpdateView,
    DeductionDetailView, DeductionDeleteView, DeductionExportView,
    DeductionBulkDeleteView
)
