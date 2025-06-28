from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

class BaseModel(models.Model):
    """Base model with common fields for all models."""
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        abstract = True

# -------------------- EMPLOYEE INFORMATION --------------------

class Department(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Designation(BaseModel):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='designations')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.department.name})"

class Employee(BaseModel):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )
    
    MARITAL_STATUS_CHOICES = (
        ('S', 'Single'),
        ('M', 'Married'),
        ('D', 'Divorced'),
        ('W', 'Widowed'),
    )
    
    employee_id = models.CharField(max_length=20, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile', null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, null=True, blank=True)
    marital_status = models.CharField(max_length=1, choices=MARITAL_STATUS_CHOICES)
    
    # Contact Information
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, null=True, blank=True)
    
    # Address Information
    present_address = models.TextField()
    permanent_address = models.TextField()
    
    # Employment Information
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='employees')
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE, related_name='employees')
    joining_date = models.DateField()
    confirmation_date = models.DateField(null=True, blank=True)
    
    # Salary Information
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # System fields
    profile_picture = models.ImageField(upload_to='employee_profiles/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def service_duration(self):
        if not self.is_active and hasattr(self, 'separation'):
            end_date = self.separation.separation_date
        else:
            end_date = timezone.now().date()
        
        delta = end_date - self.joining_date
        years = delta.days // 365
        months = (delta.days % 365) // 30
        days = (delta.days % 365) % 30
        
        return f"{years} years, {months} months, {days} days"
    def get_leave_status(self):
        """
        Returns the current leave status of the employee:
        - 'on_leave': Currently on approved leave
        - 'pending': Has pending leave applications
        - 'available': Not on leave and no pending applications
        """
        today = timezone.now().date()
        
        # Check if employee is currently on leave
        on_leave = self.leave_applications.filter(
            status='APP',
            start_date__lte=today,
            end_date__gte=today
        ).exists()
        
        if on_leave:
            return 'on_leave'
        
        # Check if employee has pending leave applications
        pending = self.leave_applications.filter(status='PEN').exists()
        
        if pending:
            return 'pending'
        
        return 'available'

    def get_leave_balances(self):
        """
        Returns the leave balances for the current year
        """
        current_year = timezone.now().year
        return self.leave_balances.filter(year=current_year)
class EmployeeSeparation(BaseModel):
    SEPARATION_TYPE_CHOICES = (
        ('RES', 'Resignation'),
        ('TER', 'Termination'),
        ('DIS', 'Dismissal'),
        ('RET', 'Retirement'),
        ('EXP', 'Contract Expiry'),
        ('OTH', 'Other'),
    )
    
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='separation')
    separation_type = models.CharField(max_length=3, choices=SEPARATION_TYPE_CHOICES)
    separation_date = models.DateField()
    notice_period_served = models.BooleanField(default=True)
    reason = models.TextField()
    exit_interview_conducted = models.BooleanField(default=False)
    clearance_completed = models.BooleanField(default=False)
    final_settlement_completed = models.BooleanField(default=False)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_separation_type_display()} on {self.separation_date}"
    
    def save(self, *args, **kwargs):
        # Update employee status when separation is recorded
        self.employee.is_active = False
        self.employee.save()
        super().save(*args, **kwargs)

# -------------------- ROSTER CONFIGURATION --------------------

class WorkPlace(BaseModel):
    name = models.CharField(max_length=100)
    address = models.TextField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Shift(BaseModel):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_time = models.PositiveIntegerField(help_text="Break time in minutes", default=60)
    grace_time = models.PositiveIntegerField(help_text="Grace time in minutes", default=15)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"
    
    @property
    def duration(self):
        start_datetime = timezone.datetime.combine(timezone.now().date(), self.start_time)
        end_datetime = timezone.datetime.combine(timezone.now().date(), self.end_time)
        
        # If end time is earlier than start time, it means the shift spans across midnight
        if end_datetime < start_datetime:
            end_datetime = end_datetime + timezone.timedelta(days=1)
        
        duration = end_datetime - start_datetime
        # Subtract break time
        duration_in_minutes = duration.total_seconds() / 60 - self.break_time
        
        hours = int(duration_in_minutes // 60)
        minutes = int(duration_in_minutes % 60)
        
        return f"{hours}h {minutes}m"

class Roster(BaseModel):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"
    
    def extend_roster(self, new_end_date):
        if new_end_date <= self.end_date:
            raise ValueError("New end date must be after the current end date")
        
        # Get all roster assignments for this roster
        assignments = self.roster_assignments.all()
        
        # Calculate days to extend
        days_to_extend = (new_end_date - self.end_date).days
        
        # For each assignment, create new daily assignments
        for assignment in assignments:
            last_day = assignment.roster_days.order_by('-date').first()
            if last_day:
                shift = last_day.shift
                workplace = last_day.workplace
                
                # Create new roster days for the extended period
                for i in range(1, days_to_extend + 1):
                    new_date = self.end_date + timezone.timedelta(days=i)
                    RosterDay.objects.create(
                        roster_assignment=assignment,
                        date=new_date,
                        shift=shift,
                        workplace=workplace
                    )
        
        # Update the roster end date
        self.end_date = new_end_date
        self.save()

class RosterAssignment(BaseModel):
    roster = models.ForeignKey(Roster, on_delete=models.CASCADE, related_name='roster_assignments')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='roster_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('roster', 'employee')
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.roster.name}"

class RosterDay(BaseModel):
    roster_assignment = models.ForeignKey(RosterAssignment, on_delete=models.CASCADE, related_name='roster_days')
    date = models.DateField()
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='roster_days')
    workplace = models.ForeignKey(WorkPlace, on_delete=models.CASCADE, related_name='roster_days')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('roster_assignment', 'date')
    
    def __str__(self):
        return f"{self.roster_assignment.employee.get_full_name()} - {self.date} - {self.shift.name}"

# -------------------- LEAVE MANAGEMENT --------------------

class Holiday(BaseModel):
    name = models.CharField(max_length=100)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.date}"

class LeaveType(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    paid = models.BooleanField(default=True)
    max_days_per_year = models.PositiveIntegerField()
    carry_forward = models.BooleanField(default=False)
    max_carry_forward_days = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class LeaveApplication(BaseModel):
    STATUS_CHOICES = (
        ('PEN', 'Pending'),
        ('APP', 'Approved'),
        ('REJ', 'Rejected'),
        ('CAN', 'Cancelled'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='leave_applications')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='PEN')
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_date = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.name} ({self.start_date} to {self.end_date})"
    
    @property
    def days(self):
        delta = self.end_date - self.start_date
        return delta.days + 1
    
    def approve(self, approved_by):
        self.status = 'APP'
        self.approved_by = approved_by
        self.approved_date = timezone.now()
        self.save()
    
    def reject(self, remarks):
        self.status = 'REJ'
        self.remarks = remarks
        self.save()
    
    def cancel(self):
        self.status = 'CAN'
        self.save()

class ShortLeaveApplication(BaseModel):
    STATUS_CHOICES = (
        ('PEN', 'Pending'),
        ('APP', 'Approved'),
        ('REJ', 'Rejected'),
        ('CAN', 'Cancelled'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='short_leave_applications')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    reason = models.TextField()
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='PEN')
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_short_leaves')
    approved_date = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - Short Leave on {self.date} ({self.start_time} to {self.end_time})"
    
    @property
    def duration_hours(self):
        start_datetime = timezone.datetime.combine(timezone.now().date(), self.start_time)
        end_datetime = timezone.datetime.combine(timezone.now().date(), self.end_time)
        
        # If end time is earlier than start time, it means the leave spans across midnight
        if end_datetime < start_datetime:
            end_datetime = end_datetime + timezone.timedelta(days=1)
        
        duration = end_datetime - start_datetime
        hours = duration.total_seconds() / 3600
        
        return round(hours, 2)
    
    def approve(self, approved_by):
        self.status = 'APP'
        self.approved_by = approved_by
        self.approved_date = timezone.now()
        self.save()
    
    def reject(self, remarks):
        self.status = 'REJ'
        self.remarks = remarks
        self.save()
    
    def cancel(self):
        self.status = 'CAN'
        self.save()
class LeaveBalance(BaseModel):
    """
    Model to track employee leave balances by leave type
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='leave_balances')
    year = models.PositiveIntegerField()
    total_days = models.DecimalField(max_digits=6, decimal_places=2, 
                                     help_text="Total allocated days for this leave type")
    used_days = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                   help_text="Days used so far")
    pending_days = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                      help_text="Days in pending leave applications")
    carried_forward_days = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                             help_text="Days carried forward from previous year")
    
    class Meta:
        unique_together = ('employee', 'leave_type', 'year')
        verbose_name = "Leave Balance"
        verbose_name_plural = "Leave Balances"
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.name} - {self.year}"
    
    @property
    def available_days(self):
        """Calculate available days (total - used - pending)"""
        return self.total_days - self.used_days - self.pending_days
    
    @property
    def is_sufficient_balance(self, requested_days):
        """Check if there's sufficient balance for requested days"""
        return self.available_days >= requested_days
# -------------------- ATTENDANCE MANAGEMENT --------------------

class AttendanceMonth(BaseModel):
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    is_processed = models.BooleanField(default=False)
    processed_date = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_attendance_months')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('year', 'month')
    
    def __str__(self):
        return f"{self.year}-{self.month:02d}"
    
    def process_attendance(self, processed_by):
        # Mark as processed
        self.is_processed = True
        self.processed_date = timezone.now()
        self.processed_by = processed_by
        self.save()

class AttendanceLog(BaseModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_logs')
    timestamp = models.DateTimeField()
    is_in = models.BooleanField(help_text="True for check-in, False for check-out")
    location = models.CharField(max_length=255, null=True, blank=True)
    device = models.CharField(max_length=100, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        log_type = "Check-in" if self.is_in else "Check-out"
        return f"{self.employee.get_full_name()} - {log_type} at {self.timestamp}"

class Attendance(BaseModel):
    STATUS_CHOICES = (
        ('PRE', 'Present'),
        ('ABS', 'Absent'),
        ('LAT', 'Late'),
        ('LEA', 'Leave'),
        ('HOL', 'Holiday'),
        ('WEE', 'Weekend'),
        ('HAL', 'Half Day'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=3, choices=STATUS_CHOICES)
    roster_day = models.ForeignKey(RosterDay, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendances')
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    late_minutes = models.PositiveIntegerField(default=0)
    early_out_minutes = models.PositiveIntegerField(default=0)
    overtime_minutes = models.PositiveIntegerField(default=0)
    is_manual = models.BooleanField(default=False)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('employee', 'date')
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date} - {self.get_status_display()}"
    
    @property
    def working_hours(self):
        if not self.check_in or not self.check_out:
            return 0
        
        duration = self.check_out - self.check_in
        # Convert to hours
        hours = duration.total_seconds() / 3600
        
        return round(hours, 2)

class OvertimeRecord(BaseModel):
    STATUS_CHOICES = (
        ('PEN', 'Pending'),
        ('APP', 'Approved'),
        ('REJ', 'Rejected'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='overtime_records')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='PEN')
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_overtimes')
    approved_date = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - OT on {self.date} ({self.hours} hours)"
    
    def approve(self, approved_by):
        self.status = 'APP'
        self.approved_by = approved_by
        self.approved_date = timezone.now()
        self.save()
    
    def reject(self, remarks):
        self.status = 'REJ'
        self.remarks = remarks
        self.save()

# -------------------- PAYROLL MANAGEMENT --------------------

class SalaryComponent(BaseModel):
    COMPONENT_TYPE_CHOICES = (
        ('EARN', 'Earning'),
        ('DED', 'Deduction'),
    )
    
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    component_type = models.CharField(max_length=4, choices=COMPONENT_TYPE_CHOICES)
    is_taxable = models.BooleanField(default=True)
    is_fixed = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_component_type_display()})"

class EmployeeSalaryStructure(BaseModel):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='salary_structure')
    effective_date = models.DateField()
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.gross_salary}"

class SalaryStructureComponent(BaseModel):
    salary_structure = models.ForeignKey(EmployeeSalaryStructure, on_delete=models.CASCADE, related_name='components')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE, related_name='structure_components')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.salary_structure.employee.get_full_name()} - {self.component.name} - {self.amount}"

class BonusSetup(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class BonusMonth(BaseModel):
    bonus_setup = models.ForeignKey(BonusSetup, on_delete=models.CASCADE, related_name='bonus_months')
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    is_generated = models.BooleanField(default=False)
    generated_date = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_bonuses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('bonus_setup', 'year', 'month')
    
    def __str__(self):
        return f"{self.bonus_setup.name} - {self.year}-{self.month:02d}"

class EmployeeBonus(BaseModel):
    bonus_month = models.ForeignKey(BonusMonth, on_delete=models.CASCADE, related_name='employee_bonuses')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='bonuses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('bonus_month', 'employee')
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.bonus_month.bonus_setup.name} - {self.amount}"

class AdvanceSetup(BaseModel):
    name = models.CharField(max_length=100)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2)
    max_installments = models.PositiveIntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class EmployeeAdvance(BaseModel):
    STATUS_CHOICES = (
        ('PEN', 'Pending'),
        ('APP', 'Approved'),
        ('REJ', 'Rejected'),
        ('PAI', 'Paid'),
        ('CLS', 'Closed'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='advances')
    advance_setup = models.ForeignKey(AdvanceSetup, on_delete=models.CASCADE, related_name='employee_advances')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    installments = models.PositiveIntegerField()
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    application_date = models.DateField()
    approval_date = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_advances')
    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='PEN')
    reason = models.TextField()
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.amount} - {self.get_status_display()}"
    
    def approve(self, approved_by):
        self.status = 'APP'
        self.approved_by = approved_by
        self.approval_date = timezone.now().date()
        self.save()
    
    def reject(self, remarks):
        self.status = 'REJ'
        self.remarks = remarks
        self.save()
    
    def close(self):
        self.status = 'CLS'
        self.save()

class AdvanceInstallment(BaseModel):
    advance = models.ForeignKey(EmployeeAdvance, on_delete=models.CASCADE, related_name='advance_installments')
    installment_number = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.advance.employee.get_full_name()} - Installment {self.installment_number} - {self.amount}"

class SalaryMonth(BaseModel):
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    is_generated = models.BooleanField(default=False)
    generated_date = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_salaries')
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('year', 'month')
    
    def __str__(self):
        return f"Salary {self.year}-{self.month:02d}"

class EmployeeSalary(BaseModel):
    salary_month = models.ForeignKey(SalaryMonth, on_delete=models.CASCADE, related_name='employee_salaries')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salaries')
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    working_days = models.PositiveIntegerField()
    present_days = models.PositiveIntegerField()
    absent_days = models.PositiveIntegerField()
    leave_days = models.PositiveIntegerField()
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_separation_salary = models.BooleanField(default=False)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('salary_month', 'employee')
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.salary_month}"

class SalaryDetail(BaseModel):
    salary = models.ForeignKey(EmployeeSalary, on_delete=models.CASCADE, related_name='details')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE, related_name='salary_details')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.salary.employee.get_full_name()} - {self.component.name} - {self.amount}"

class Promotion(BaseModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='promotions')
    from_designation = models.ForeignKey(Designation, on_delete=models.CASCADE, related_name='promotions_from')
    to_designation = models.ForeignKey(Designation, on_delete=models.CASCADE, related_name='promotions_to')
    effective_date = models.DateField()
    salary_increment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.from_designation.name} to {self.to_designation.name}"
    
    def save(self, *args, **kwargs):
        # Update employee designation
        self.employee.designation = self.to_designation
        
        # Update employee salary if there's an increment
        if self.salary_increment > 0:
            self.employee.basic_salary += self.salary_increment
        
        self.employee.save()
        super().save(*args, **kwargs)

class Increment(BaseModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='increments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    effective_date = models.DateField()
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.amount} ({self.percentage}%)"
    
    def save(self, *args, **kwargs):
        # Update employee salary
        self.employee.basic_salary += self.amount
        self.employee.save()
        super().save(*args, **kwargs)

class Deduction(BaseModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='deductions')
    salary_month = models.ForeignKey(SalaryMonth, on_delete=models.CASCADE, related_name='deductions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.salary_month} - {self.amount}"

# -------------------- PROVIDENT FUND MANAGEMENT --------------------

class ProvidentFundSetting(BaseModel):
    employee_contribution = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage of basic salary")
    employer_contribution = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage of basic salary")
    effective_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"PF Setting - Employee: {self.employee_contribution}%, Employer: {self.employer_contribution}%"

class EmployeeProvidentFund(BaseModel):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='provident_fund')
    enrollment_date = models.DateField()
    employee_contribution = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage of basic salary")
    employer_contribution = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage of basic salary")
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - PF"

class ProvidentFundTransaction(BaseModel):
    TRANSACTION_TYPE_CHOICES = (
        ('CON', 'Contribution'),
        ('WIT', 'Withdrawal'),
        ('INT', 'Interest'),
        ('LOA', 'Loan'),
        ('REP', 'Loan Repayment'),
    )
    
    employee_pf = models.ForeignKey(EmployeeProvidentFund, on_delete=models.CASCADE, related_name='transactions')
    transaction_date = models.DateField()
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPE_CHOICES)
    employee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    employer_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee_pf.employee.get_full_name()} - {self.get_transaction_type_display()} - {self.total_amount}"

class FixedDepositReceipt(BaseModel):
    fdr_number = models.CharField(max_length=100, unique=True)
    bank_name = models.CharField(max_length=100)
    branch_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    maturity_date = models.DateField()
    is_active = models.BooleanField(default=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"FDR {self.fdr_number} - {self.amount} - {self.bank_name}"

# -------------------- VAT & TAX MANAGEMENT --------------------

class TaxYear(BaseModel):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class TaxRate(BaseModel):
    tax_year = models.ForeignKey(TaxYear, on_delete=models.CASCADE, related_name='tax_rates')
    min_amount = models.DecimalField(max_digits=15, decimal_places=2)
    max_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.max_amount:
            return f"{self.min_amount} to {self.max_amount} - {self.rate}%"
        return f"Above {self.min_amount} - {self.rate}%"

class AllowanceCalculationPlan(BaseModel):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class AllowanceCalculation(BaseModel):
    plan = models.ForeignKey(AllowanceCalculationPlan, on_delete=models.CASCADE, related_name='calculations')
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE, related_name='allowance_calculations')
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.plan.name} - {self.component.name} - {self.percentage}%"

class EmployeeInvestment(BaseModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='investments')
    tax_year = models.ForeignKey(TaxYear, on_delete=models.CASCADE, related_name='employee_investments')
    investment_type = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    document = models.FileField(upload_to='investment_documents/', null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.investment_type} - {self.amount}"

class EmployeeTax(BaseModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='taxes')
    tax_year = models.ForeignKey(TaxYear, on_delete=models.CASCADE, related_name='employee_taxes')
    total_income = models.DecimalField(max_digits=15, decimal_places=2)
    total_exemptions = models.DecimalField(max_digits=15, decimal_places=2)
    total_investments = models.DecimalField(max_digits=15, decimal_places=2)
    taxable_income = models.DecimalField(max_digits=15, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2)
    generated_date = models.DateTimeField()
    generated_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_taxes')
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('employee', 'tax_year')
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.tax_year.name} - {self.tax_amount}"

# -------------------- LETTER MANAGEMENT --------------------

class LetterTemplate(BaseModel):
    LETTER_TYPE_CHOICES = (
        ('APP', 'Appointment'),
        ('CON', 'Confirmation'),
        ('PRO', 'Promotion'),
        ('INC', 'Increment'),
        ('INC_PRO', 'Increment with Promotion'),
        ('ABS', 'Absent'),
        ('SHO', 'Show Cause'),
        ('AGE', 'Age Proof & Fitness Certificate'),
        ('TER', 'Termination'),
        ('DIS', 'Dismissal'),
        ('SUS', 'Suspension'),
        ('FIN', 'Final Settlement'),
        ('OTH', 'Other'),
    )
    
    name = models.CharField(max_length=100)
    letter_type = models.CharField(max_length=7, choices=LETTER_TYPE_CHOICES)
    content = models.TextField(help_text="Use {{variable}} for dynamic content")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_letter_type_display()})"

class EmployeeLetter(BaseModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='letters')
    template = models.ForeignKey(LetterTemplate, on_delete=models.CASCADE, related_name='employee_letters')
    reference_number = models.CharField(max_length=100)
    issue_date = models.DateField()
    content = models.TextField()
    issued_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_letters')
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.template.get_letter_type_display()} - {self.issue_date}"

# -------------------- MOBILE APP ATTENDANCE --------------------

class MobileAttendance(BaseModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='mobile_attendances')
    check_in = models.DateTimeField()
    check_out = models.DateTimeField(null=True, blank=True)
    check_in_location = models.CharField(max_length=255)
    check_out_location = models.CharField(max_length=255, null=True, blank=True)
    check_in_notes = models.TextField(null=True, blank=True)
    check_out_notes = models.TextField(null=True, blank=True)
    check_in_image = models.ImageField(upload_to='mobile_attendance/', null=True, blank=True)
    check_out_image = models.ImageField(upload_to='mobile_attendance/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.check_in.date()}"


class Location(models.Model):
    name = models.CharField(_("Name"), max_length=100)
    address = models.TextField(_("Address"))
    latitude = models.DecimalField(_("Latitude"), max_digits=10, decimal_places=8)
    longitude = models.DecimalField(_("Longitude"), max_digits=11, decimal_places=8)
    radius = models.DecimalField(_("Radius (km)"), max_digits=5, decimal_places=2)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")
        ordering = ['name']
    
    def __str__(self):
        return self.name

class UserLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_locations', verbose_name=_("User"))
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='user_locations', verbose_name=_("Location"))
    is_primary = models.BooleanField(_("Is Primary"), default=False)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("User Location")
        verbose_name_plural = _("User Locations")
        unique_together = ('user', 'location')
        ordering = ['user__username', 'location__name']
    
    def __str__(self):
        return f"{self.user.username} - {self.location.name}"

class LocationAttendance(models.Model):
    ATTENDANCE_TYPE_CHOICES = (
        ('IN', _("Check-in")),
        ('OUT', _("Check-out")),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='location_attendances', verbose_name=_("User"))
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='attendances', verbose_name=_("Location"))
    attendance_type = models.CharField(_("Attendance Type"), max_length=3, choices=ATTENDANCE_TYPE_CHOICES)
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)
    latitude = models.DecimalField(_("Latitude"), max_digits=10, decimal_places=8)
    longitude = models.DecimalField(_("Longitude"), max_digits=11, decimal_places=8)
    is_within_radius = models.BooleanField(_("Is Within Radius"), default=False)
    distance = models.DecimalField(_("Distance (km)"), max_digits=8, decimal_places=2)
    device_info = models.TextField(_("Device Info"), blank=True, null=True)
    ip_address = models.GenericIPAddressField(_("IP Address"), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    
    class Meta:
        verbose_name = _("Location Attendance")
        verbose_name_plural = _("Location Attendances")
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username} - {self.location.name} - {self.get_attendance_type_display()} - {self.timestamp}"
    
    


class ZKDevice(models.Model):
    """Model to store ZKTeco device information"""
    name = models.CharField(_("Device Name"), max_length=100)
    ip_address = models.GenericIPAddressField(_("IP Address"))
    port = models.IntegerField(_("Port"), default=4370, null=True, blank=True)
    device_id = models.CharField(_("Device ID"), max_length=100, blank=True, null=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    last_sync = models.DateTimeField(_("Last Sync"), blank=True, null=True)
    
    # Connection settings
    timeout = models.IntegerField(_("Timeout"), default=5, null=True, blank=True)
    password = models.CharField(_("Device Password"), max_length=100, blank=True, null=True, 
                               help_text=_("Leave blank if no password is set on the device"))
    force_udp = models.BooleanField(_("Force UDP"), default=False, 
                                   help_text=_("Use UDP instead of TCP for connection"))
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("ZK Device")
        verbose_name_plural = _("ZK Devices")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.ip_address})"
    
    def get_connection_params(self):
        try:
            port = int(self.port)
        except (ValueError, TypeError):
            port = 4370

        try:
            timeout = int(self.timeout)
        except (ValueError, TypeError):
            timeout = 5

        # ✅ Ensure password is string (even if blank)
        password = self.password if self.password else ''

        return {
            'ip': self.ip_address,
            'port': port,
            'timeout': timeout,
            'password': password,
            'force_udp': bool(self.force_udp),
            'ommit_ping': False,
        }







class ZKAttendanceLog(models.Model):
    """Model to store attendance logs retrieved from ZK devices"""
    device = models.ForeignKey(ZKDevice, on_delete=models.CASCADE, related_name='attendance_logs')
    user_id = models.CharField(_("User ID"), max_length=100)
    timestamp = models.DateTimeField(_("Timestamp"))
    punch_type = models.CharField(_("Punch Type"), max_length=50, blank=True, null=True)
    status = models.IntegerField(_("Status Code"), blank=True, null=True)
    
    # Additional fields that might be available from the device
    verify_type = models.CharField(_("Verification Type"), max_length=50, blank=True, null=True)
    work_code = models.CharField(_("Work Code"), max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("ZK Attendance Log")
        verbose_name_plural = _("ZK Attendance Logs")
        ordering = ['-timestamp']
        unique_together = ['device', 'user_id', 'timestamp']
    
    def __str__(self):
        return f"{self.user_id} - {self.timestamp}"    