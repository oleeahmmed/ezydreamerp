from .employee_form import (
    EmployeeForm, EmployeeFilterForm
)

from .employee_separation_form import (
    EmployeeSeparationForm, EmployeeSeparationFilterForm
)

from .department_form import (
    DepartmentForm, DepartmentFilterForm
)

from .designation_form import (
    DesignationForm, DesignationFilterForm
)

from .workplace_form import (
    WorkPlaceForm, WorkPlaceFilterForm
)

from .shift_form import (
    ShiftForm, ShiftFilterForm
)

from .roster_form import (
    RosterForm, 
    RosterFilterForm, 
    RosterAssignmentForm,
    RosterAssignmentFormSet
)

from .roster_day_forms import (
    RosterDayForm, RosterDayFilterForm
) 
from .leave_type_form import (
    LeaveTypeForm, LeaveTypeFilterForm
)

from .leave_application_form import (
    LeaveApplicationForm, LeaveApplicationFilterForm
)

from .short_leave_application_form import (
    ShortLeaveApplicationForm, ShortLeaveApplicationFilterForm
)

from .leave_balance_form import (
    LeaveBalanceForm, LeaveBalanceFilterForm, LeaveBalanceInitializeForm
)

from .holiday_form import (
    HolidayForm, HolidayFilterForm
)

from .attendance_forms import (
    AttendanceMonthForm, AttendanceLogForm, AttendanceForm, 
    OvertimeRecordForm, AttendanceFilterForm
)

from .payroll_forms import (
    SalaryComponentForm, EmployeeSalaryStructureForm, SalaryStructureComponentForm,SalaryStructureComponentFormSet,EmployeeSalaryStructureFilterForm,
    BonusSetupForm, BonusMonthForm, EmployeeBonusForm, AdvanceSetupForm,
    EmployeeAdvanceForm, AdvanceInstallmentForm, SalaryMonthForm,
    EmployeeSalaryForm, SalaryDetailForm, PromotionForm,
    IncrementForm, DeductionForm, PayrollFilterForm
)

from .location_forms import (
    LocationForm, LocationFilterForm,
    LocationAttendanceForm, LocationAttendanceFilterForm
)

__all__ = [
    # Employee related forms
    'EmployeeForm', 'EmployeeFilterForm',
    'EmployeeSeparationForm', 'EmployeeSeparationFilterForm',
    'DepartmentForm', 'DepartmentFilterForm',
    'DesignationForm', 'DesignationFilterForm',
    
    # Roster related forms
    'WorkPlaceForm', 'WorkPlaceFilterForm',
    'ShiftForm', 'ShiftFilterForm',
    'RosterForm', 'RosterFilterForm',
    'RosterAssignmentForm', 'RosterAssignmentFormSet','RosterDayForm', 'RosterDayFormSet', 'RosterAssignmentFilterForm',
    
    # Leave related forms
    'LeaveTypeForm', 'LeaveTypeFilterForm',
    'LeaveApplicationForm', 'LeaveApplicationFilterForm',
    'ShortLeaveApplicationForm', 'ShortLeaveApplicationFilterForm',
    'HolidayForm', 'HolidayFilterForm','LeaveBalanceForm', 'LeaveBalanceFilterForm', 'LeaveBalanceInitializeForm',
    
    # Attendance related forms
    'AttendanceMonthForm', 'AttendanceLogForm', 'AttendanceForm',
    'OvertimeRecordForm', 'AttendanceFilterForm',
    
    # Payroll related forms
    'SalaryComponentForm', 'EmployeeSalaryStructureForm', 'SalaryStructureComponentForm',
    'BonusSetupForm', 'BonusMonthForm', 'EmployeeBonusForm', 'AdvanceSetupForm',
    'EmployeeAdvanceForm', 'AdvanceInstallmentForm', 'SalaryMonthForm',
    'EmployeeSalaryForm', 'SalaryDetailForm', 'PromotionForm',
    'IncrementForm', 'DeductionForm', 'PayrollFilterForm',
    
    
    # Location related forms
    'LocationForm', 'LocationFilterForm',
    'LocationAttendanceForm', 'LocationAttendanceFilterForm',    
]

