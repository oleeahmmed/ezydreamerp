from django.contrib import admin
from unfold.admin import ModelAdmin
from django import forms
from .models import *
from django_ckeditor_5.widgets import CKEditor5Widget


# ✅ Notice Model with CKEditor
class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = '__all__'
        widgets = {
            'content': CKEditor5Widget(config_name='default'),
        }


@admin.register(Notice)
class NoticeAdmin(ModelAdmin):
    list_display = ('title', 'target_type')
    form = NoticeForm


# ✅ Inline Examples
class RosterAssignmentInline(admin.TabularInline):
    model = RosterAssignment
    extra = 1


class SalaryStructureComponentInline(admin.TabularInline):
    model = SalaryStructureComponent
    extra = 1


class LeaveBalanceInline(admin.TabularInline):
    model = LeaveBalance
    extra = 1


# ✅ Employee Example
@admin.register(Employee)
class EmployeeAdmin(ModelAdmin):
    list_display = ('employee_id', 'first_name', 'last_name', 'department', 'designation', 'is_active')
    search_fields = ('employee_id', 'first_name', 'last_name')
    inlines = [LeaveBalanceInline]


# ✅ Department
@admin.register(Department)
class DepartmentAdmin(ModelAdmin):
    list_display = ('name', 'code')


# ✅ Designation
@admin.register(Designation)
class DesignationAdmin(ModelAdmin):
    list_display = ('name', 'department')


# ✅ Shift
@admin.register(Shift)
class ShiftAdmin(ModelAdmin):
    list_display = ('name', 'start_time', 'end_time')


# ✅ WorkPlace
@admin.register(WorkPlace)
class WorkPlaceAdmin(ModelAdmin):
    list_display = ('name', 'address')


# ✅ Roster
@admin.register(Roster)
class RosterAdmin(ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')
    inlines = [RosterAssignmentInline]


# ✅ RosterAssignment
@admin.register(RosterAssignment)
class RosterAssignmentAdmin(ModelAdmin):
    list_display = ('roster', 'employee', 'shift')


# ✅ LeaveType
@admin.register(LeaveType)
class LeaveTypeAdmin(ModelAdmin):
    list_display = ('name', 'code', 'paid')


# ✅ LeaveApplication
@admin.register(LeaveApplication)
class LeaveApplicationAdmin(ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status')


# ✅ Attendance Example
@admin.register(Attendance)
class AttendanceAdmin(ModelAdmin):
    list_display = ('employee', 'date', 'status')


# ✅ SalaryComponent
@admin.register(SalaryComponent)
class SalaryComponentAdmin(ModelAdmin):
    list_display = ('name', 'code', 'component_type')


# ✅ EmployeeSalaryStructure
@admin.register(EmployeeSalaryStructure)
class EmployeeSalaryStructureAdmin(ModelAdmin):
    list_display = ('employee', 'gross_salary', 'net_salary')
    inlines = [SalaryStructureComponentInline]
