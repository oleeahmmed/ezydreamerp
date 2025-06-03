from .employee_view import (
    EmployeeListView, EmployeeCardView, EmployeeAllView, EmployeeCreateView, 
    EmployeeUpdateView, EmployeeDetailView, EmployeeDeleteView, EmployeeExportView,
    EmployeeBulkDeleteView
)
from .employee_dashboard_view import EmployeeDashboardView
from .employee_separation_view import (
    EmployeeSeparationListView, EmployeeSeparationCreateView, EmployeeSeparationUpdateView,
    EmployeeSeparationDetailView, EmployeeSeparationDeleteView, EmployeeSeparationExportView,
    EmployeeSeparationBulkDeleteView
)
from .department_view import (
    DepartmentListView, DepartmentCreateView, DepartmentUpdateView,
    DepartmentDetailView, DepartmentDeleteView, DepartmentExportView,
    DepartmentBulkDeleteView
)
from .designation_view import (
    DesignationListView, DesignationCreateView, DesignationUpdateView,
    DesignationDetailView, DesignationDeleteView, DesignationExportView,
    DesignationBulkDeleteView
)
from .workplace_view import (
    WorkPlaceListView, WorkPlaceCreateView, WorkPlaceUpdateView,
    WorkPlaceDetailView, WorkPlaceDeleteView, WorkPlaceExportView,
    WorkPlaceBulkDeleteView
)
from .shift_view import (
    ShiftListView, ShiftCreateView, ShiftUpdateView,
    ShiftDetailView, ShiftDeleteView, ShiftExportView,
    ShiftBulkDeleteView
)
from .roster_view import (
    RosterListView, RosterCreateView, RosterUpdateView,
    RosterDetailView, RosterDeleteView, RosterExportView,
    RosterBulkDeleteView
)
from .roster_assignment_view import (
    RosterAssignmentListView, RosterAssignmentCreateView, RosterAssignmentUpdateView,
    RosterAssignmentDetailView, RosterAssignmentDeleteView, RosterAssignmentExportView,
    RosterAssignmentBulkDeleteView
)
from .leave_type_view import (
    LeaveTypeListView, LeaveTypeCreateView, LeaveTypeUpdateView,
    LeaveTypeDetailView, LeaveTypeDeleteView, LeaveTypeExportView,
    LeaveTypeBulkDeleteView
)
from .leave_application_view import (
    LeaveApplicationListView, LeaveApplicationCreateView, LeaveApplicationUpdateView,
    LeaveApplicationDetailView, LeaveApplicationDeleteView, LeaveApplicationExportView,
    LeaveApplicationBulkDeleteView
)
from .short_leave_application_view import (
    ShortLeaveApplicationListView, ShortLeaveApplicationCreateView, ShortLeaveApplicationUpdateView,
    ShortLeaveApplicationDetailView, ShortLeaveApplicationDeleteView, ShortLeaveApplicationExportView,
    ShortLeaveApplicationBulkDeleteView
)
from .leave_balance_view import (
    LeaveBalanceListView, LeaveBalanceCreateView, LeaveBalanceUpdateView,
    LeaveBalanceDetailView, LeaveBalanceDeleteView, LeaveBalanceExportView,
    LeaveBalanceBulkDeleteView, LeaveBalanceInitializeView
)
from .holiday_view import (
    HolidayListView, HolidayCreateView, HolidayUpdateView,
    HolidayDetailView, HolidayDeleteView, HolidayExportView,
    HolidayBulkDeleteView
)
from .attendance_view import (
    AttendanceListView, AttendanceCreateView, AttendanceUpdateView,
    AttendanceDetailView, AttendanceDeleteView, AttendanceExportView,
    AttendanceBulkDeleteView
)
from .attendance_month_view import (
    AttendanceMonthListView, AttendanceMonthCreateView, AttendanceMonthUpdateView,
    AttendanceMonthDetailView, AttendanceMonthDeleteView, AttendanceMonthExportView,
    AttendanceMonthBulkDeleteView
)
from .attendance_log_view import (
    AttendanceLogListView, AttendanceLogCreateView, AttendanceLogUpdateView,
    AttendanceLogDetailView, AttendanceLogDeleteView, AttendanceLogExportView,
    AttendanceLogBulkDeleteView
)
from .overtime_record_view import (
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
