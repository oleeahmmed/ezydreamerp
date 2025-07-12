from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.auth import get_user_model

# -------------------- EMPLOYEE INFORMATION --------------------

class Department(models.Model):
    """Represents a department within an organization."""
    name = models.CharField(_("Name"), max_length=100)
    code = models.CharField(_("Code"), max_length=20, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")
        ordering = ['name']

class Designation(models.Model):
    """Represents a job role within a department."""
    name = models.CharField(_("Name"), max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, 
                                  related_name='designations', verbose_name=_("Department"))
    description = models.TextField(_("Description"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.department.name})"

    class Meta:
        verbose_name = _("Designation")
        verbose_name_plural = _("Designations")
        ordering = ['name']


class Document(models.Model):
    """Represents a document attached to an employee."""
    document_type = models.CharField("Document Type", max_length=100)
    file = models.FileField("File", upload_to='employee_documents/')
    upload_date = models.DateTimeField("Upload Date", auto_now_add=True)

    def __str__(self):
        return f"{self.document_type} - {self.file.name}"


class Employee(models.Model):
    """Represents an employee with personal and employment details."""
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
    EDUCATIONAL_QUALIFICATION_CHOICES = (
        
        ('PSC', 'PSC/Five Pass'),
        ('JSC', 'JSC/Eight Pass'),
        ('SSC', 'S.S.C'),
        ('HSC', 'H.S.C'),
        ('GRAD', 'Graduation'),
        ('DIPLOMA', 'Diploma'),
        ('OTHERS', 'Others'),
    )    
    MARITAL_STATUS_CHOICES = (
        ('S', 'Single'),
        ('M', 'Married'),
        ('D', 'Divorced'),
        ('W', 'Widowed'),
    )
    RELIGION_CHOICES = (
        ('Islam', 'Islam'),
        ('Hinduism', 'Hinduism'),
        ('Christianity', 'Christianity'),
        # Add other religions as needed
    )
    employee_id = models.CharField(_("Employee ID"), max_length=20, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile', 
                                null=True, blank=True, verbose_name=_("User"))
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    name = models.CharField(_("Full Name"), max_length=100, null=True, blank=True)
    father_name = models.CharField(_("Father's Name"), max_length=100, null=True, blank=True)
    mother_name = models.CharField(_("Mother's Name"), max_length=100, null=True, blank=True)

    card_no = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name=_("Card No"))
    gender = models.CharField(_("Gender"), max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(_("Date of Birth"))
    nid_no = models.CharField("NID No", max_length=20, unique=True,null=True, blank=True)
    religion = models.CharField("Religion", max_length=50, choices=RELIGION_CHOICES,default="Islam")

    blood_group = models.CharField(_("Blood Group"), max_length=3, choices=BLOOD_GROUP_CHOICES, 
                                  null=True, blank=True)
    default_shift = models.ForeignKey('Shift', on_delete=models.SET_NULL, 
                                      null=True, blank=True, 
                                      related_name='employees', 
                                      verbose_name='Default Shift')                                  
    marital_status = models.CharField(_("Marital Status"), max_length=1, choices=MARITAL_STATUS_CHOICES)
    # Mailing Address Fields
    mailing_care_of = models.CharField("Care Of", max_length=100, null=True, blank=True)
    mailing_village_town = models.CharField("Village/Town/Road/House/Flat", max_length=200, null=True, blank=True)
    mailing_district = models.CharField("District", max_length=100, null=True, blank=True)
    mailing_upazila_thana = models.CharField("Upazila/Thana", max_length=100, null=True, blank=True)
    mailing_union = models.CharField("Union", max_length=100, null=True, blank=True)
    mailing_post_office = models.CharField("Post Office", max_length=100, null=True, blank=True)
    mailing_post_code = models.CharField("Post Code", max_length=10, null=True, blank=True)
    mailing_home_phone = models.CharField("Home Phone", max_length=20, null=True, blank=True)
    mailing_mobile = models.CharField("Mobile", max_length=20, null=True, blank=True)
    mailing_email = models.EmailField("Email", null=True, blank=True)

    # Permanent Address Fields
    permanent_care_of = models.CharField("Care Of", max_length=100, null=True, blank=True)
    permanent_village_town = models.CharField("Village/Town/Road/House/Flat", max_length=200, null=True, blank=True)
    permanent_district = models.CharField("District", max_length=100, null=True, blank=True)
    permanent_upazila_thana = models.CharField("Upazila/Thana", max_length=100, null=True, blank=True)
    permanent_union = models.CharField("Union", max_length=100, null=True, blank=True)
    permanent_post_office = models.CharField("Post Office", max_length=100, null=True, blank=True)
    permanent_post_code = models.CharField("Post Code", max_length=10, null=True, blank=True)
    permanent_home_phone = models.CharField("Home Phone", max_length=20, null=True, blank=True)
    permanent_mobile = models.CharField("Mobile", max_length=20, null=True, blank=True)
    permanent_email = models.EmailField("Email", null=True, blank=True)

    

    # Educational Information
    education_qualification = models.CharField("Educational Qualification", max_length=50, choices=EDUCATIONAL_QUALIFICATION_CHOICES,null=True, blank=True)
    major_subject = models.CharField("Major Subject/Group", max_length=100, null=True, blank=True)
    institution = models.CharField("Institution", max_length=100, null=True, blank=True)
    university_board = models.CharField("University/Board", max_length=100, null=True, blank=True)
    passing_year = models.IntegerField("Passing Year", null=True, blank=True)
    result = models.CharField("Result", max_length=50, null=True, blank=True)

    # Employment Information
    department = models.ForeignKey(Department, on_delete=models.CASCADE, 
                                  related_name='employees', verbose_name=_("Department"))
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE, 
                                   related_name='employees', verbose_name=_("Designation"))
    joining_date = models.DateField(_("Joining Date"))
    expected_work_hours = models.PositiveIntegerField(default=8) 
    overtime_grace_minutes = models.PositiveIntegerField(default=15)    
    # Salary Information
    basic_salary = models.DecimalField(_("Basic Salary"), max_digits=10, decimal_places=2)
    gross_salary = models.DecimalField(
        _("Gross Salary"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),  # Default value
        null=True,  # Allows NULL in DB, useful for initial migration
        blank=True  # Allows the field to be blank in forms
    )
    # Status
    is_active = models.BooleanField(_("Active"), default=True)
    
    # System fields
    profile_picture = models.ImageField("Profile Picture", upload_to='employee_profiles/', null=True, blank=True)
    # Document Attachments
    documents = models.ManyToManyField(Document, related_name='employees', blank=True)
                                       
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
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
        
        on_leave = self.leave_applications.filter(
            status='APP',
            start_date__lte=today,
            end_date__gte=today
        ).exists()
        
        if on_leave:
            return 'on_leave'
        
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
    def save(self, *args, **kwargs):
        # Ensure gross_salary is not None if it's meant to be 0.00
        if self.gross_salary is None:
            self.gross_salary = Decimal('0.00')
        super().save(*args, **kwargs)
    class Meta:
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")
        ordering = ['first_name', 'last_name']

class EmployeeSeparation(models.Model):
    """Represents an employee’s separation from the organization."""
    SEPARATION_TYPE_CHOICES = (
        ('RES', 'Resignation'),
        ('TER', 'Termination'),
        ('DIS', 'Dismissal'),
        ('RET', 'Retirement'),
        ('EXP', 'Contract Expiry'),
        ('OTH', 'Other'),
    )
    
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, 
                                    related_name='separation', verbose_name=_("Employee"))
    separation_type = models.CharField(_("Separation Type"), max_length=3, 
                                      choices=SEPARATION_TYPE_CHOICES)
    separation_date = models.DateField(_("Separation Date"))
    notice_period_served = models.BooleanField(_("Notice Period Served"), default=True)
    reason = models.TextField(_("Reason"))
    exit_interview_conducted = models.BooleanField(_("Exit Interview Conducted"), default=False)
    clearance_completed = models.BooleanField(_("Clearance Completed"), default=False)
    final_settlement_completed = models.BooleanField(_("Final Settlement Completed"), 
                                                    default=False)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_separation_type_display()} on {self.separation_date}"
    
    def save(self, *args, **kwargs):
        self.employee.is_active = False
        self.employee.save()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Employee Separation")
        verbose_name_plural = _("Employee Separations")
        ordering = ['-separation_date']

# -------------------- ROSTER CONFIGURATION --------------------

class WorkPlace(models.Model):
    """Represents a workplace or office location."""
    name = models.CharField(_("Name"), max_length=100)
    address = models.TextField(_("Address"))
    description = models.TextField(_("Description"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("WorkPlace")
        verbose_name_plural = _("WorkPlaces")
        ordering = ['name']

class Shift(models.Model):
    """Represents a work shift with start and end times."""
    name = models.CharField(_("Name"), max_length=100)
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    break_time = models.PositiveIntegerField(_("Break Time (minutes)"), default=60)
    grace_time = models.PositiveIntegerField(_("Grace Time (minutes)"), default=15)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"
    
    @property
    def duration(self):
        start_datetime = timezone.datetime.combine(timezone.now().date(), self.start_time)
        end_datetime = timezone.datetime.combine(timezone.now().date(), self.end_time)
        
        if end_datetime < start_datetime:
            end_datetime += timezone.timedelta(days=1)
        
        duration = end_datetime - start_datetime
        duration_in_minutes = duration.total_seconds() / 60 - self.break_time
        
        hours = int(duration_in_minutes // 60)
        minutes = int(duration_in_minutes % 60)
        
        return f"{hours}h {minutes}m"
    @property
    def duration_minutes(self):
        start = timezone.datetime.combine(timezone.now().date(), self.start_time)
        end = timezone.datetime.combine(timezone.now().date(), self.end_time)
        if end < start:
            end += timezone.timedelta(days=1)
        return int((end - start).total_seconds() / 60 - self.break_time)

    @property
    def duration_hours(self):
        return round(self.duration_minutes / 60, 2)

        class Meta:
            verbose_name = _("Shift")
            verbose_name_plural = _("Shifts")
            ordering = ['start_time']

class Roster(models.Model):
    """Represents a roster schedule for employees."""
    name = models.CharField(_("Name"), max_length=100)
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    description = models.TextField(_("Description"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"
    
    def extend_roster(self, new_end_date):
        if new_end_date <= self.end_date:
            raise ValueError("New end date must be after the current end date")
        
        assignments = self.roster_assignments.all()
        days_to_extend = (new_end_date - self.end_date).days
        
        for assignment in assignments:
            last_day = assignment.roster_days.order_by('-date').first()
            if last_day:
                shift = last_day.shift
                workplace = last_day.workplace
                
                for i in range(1, days_to_extend + 1):
                    new_date = self.end_date + timezone.timedelta(days=i)
                    RosterDay.objects.create(
                        roster_assignment=assignment,
                        date=new_date,
                        shift=shift,
                        workplace=workplace
                    )
        
        self.end_date = new_end_date
        self.save()

    class Meta:
        verbose_name = _("Roster")
        verbose_name_plural = _("Rosters")
        ordering = ['-start_date']

class RosterAssignment(models.Model):
    """Assigns an employee to a roster."""
    roster = models.ForeignKey(Roster, on_delete=models.CASCADE, 
                              related_name='roster_assignments', verbose_name=_("Roster"))
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='roster_assignments', verbose_name=_("Employee"))
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, 
                             related_name='roster_assignment', verbose_name=_("Shift"))                                
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.roster.name}"

    class Meta:
        verbose_name = _("Roster Assignment")
        verbose_name_plural = _("Roster Assignments")
        unique_together = ('roster', 'employee')
        ordering = ['roster__name', 'employee__first_name']

class RosterDay(models.Model):
    """Represents a specific day in a roster assignment."""
    roster_assignment = models.ForeignKey(RosterAssignment, on_delete=models.CASCADE, 
                                         related_name='roster_days', 
                                         verbose_name=_("Roster Assignment"))
    date = models.DateField(_("Date"))
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, 
                             related_name='roster_days', verbose_name=_("Shift"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.roster_assignment.employee.get_full_name()} - {self.date} - {self.shift.name}"

    class Meta:
        verbose_name = _("Roster Day")
        verbose_name_plural = _("Roster Days")
        unique_together = ('roster_assignment', 'date')
        ordering = ['date']

# -------------------- LEAVE MANAGEMENT --------------------

class Holiday(models.Model):
    """Represents a public or organizational holiday."""
    name = models.CharField(_("Name"), max_length=100)
    date = models.DateField(_("Date"))
    description = models.TextField(_("Description"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.date}"

    class Meta:
        verbose_name = _("Holiday")
        verbose_name_plural = _("Holidays")
        ordering = ['date']

class LeaveType(models.Model):
    """Defines types of leaves available to employees."""
    name = models.CharField(_("Name"), max_length=100)
    code = models.CharField(_("Code"), max_length=20, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    paid = models.BooleanField(_("Paid"), default=True)
    max_days_per_year = models.PositiveIntegerField(_("Max Days Per Year"))
    carry_forward = models.BooleanField(_("Carry Forward"), default=False)
    max_carry_forward_days = models.PositiveIntegerField(_("Max Carry Forward Days"), default=0)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Leave Type")
        verbose_name_plural = _("Leave Types")
        ordering = ['name']

class LeaveApplication(models.Model):
    """Represents an employee’s leave application."""
    STATUS_CHOICES = (
        ('PEN', 'Pending'),
        ('APP', 'Approved'),
        ('REJ', 'Rejected'),
        ('CAN', 'Cancelled'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='leave_applications', verbose_name=_("Employee"))
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, 
                                  related_name='leave_applications', verbose_name=_("Leave Type"))
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    reason = models.TextField(_("Reason"))
    status = models.CharField(_("Status"), max_length=3, choices=STATUS_CHOICES, default='PEN')
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='approved_leaves', verbose_name=_("Approved By"))
    approved_date = models.DateTimeField(_("Approved Date"), null=True, blank=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
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

    class Meta:
        verbose_name = _("Leave Application")
        verbose_name_plural = _("Leave Applications")
        ordering = ['-start_date']

class ShortLeaveApplication(models.Model):
    """Represents an employee’s short leave application."""
    STATUS_CHOICES = (
        ('PEN', 'Pending'),
        ('APP', 'Approved'),
        ('REJ', 'Rejected'),
        ('CAN', 'Cancelled'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='short_leave_applications', verbose_name=_("Employee"))
    date = models.DateField(_("Date"))
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    reason = models.TextField(_("Reason"))
    status = models.CharField(_("Status"), max_length=3, choices=STATUS_CHOICES, default='PEN')
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='approved_short_leaves', verbose_name=_("Approved By"))
    approved_date = models.DateTimeField(_("Approved Date"), null=True, blank=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - Short Leave on {self.date} ({self.start_time} to {self.end_time})"
    
    @property
    def duration_hours(self):
        start_datetime = timezone.datetime.combine(timezone.now().date(), self.start_time)
        end_datetime = timezone.datetime.combine(timezone.now().date(), self.end_time)
        
        if end_datetime < start_datetime:
            end_datetime += timezone.timedelta(days=1)
        
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

    class Meta:
        verbose_name = _("Short Leave Application")
        verbose_name_plural = _("Short Leave Applications")
        ordering = ['-date']

class LeaveBalance(models.Model):
    """Tracks employee leave balances by leave type."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='leave_balances', verbose_name=_("Employee"))
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, 
                                  related_name='leave_balances', verbose_name=_("Leave Type"))
    year = models.PositiveIntegerField(_("Year"))
    total_days = models.DecimalField(_("Total Days"), max_digits=6, decimal_places=2)
    used_days = models.DecimalField(_("Used Days"), max_digits=6, decimal_places=2, default=0)
    pending_days = models.DecimalField(_("Pending Days"), max_digits=6, decimal_places=2, default=0)
    carried_forward_days = models.DecimalField(_("Carried Forward Days"), max_digits=6, 
                                              decimal_places=2, default=0)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True, null=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True, null=True)                                            
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.leave_type.name} - {self.year}"
    
    @property
    def available_days(self):
        return self.total_days - self.used_days - self.pending_days
    
    @property
    def is_sufficient_balance(self, requested_days):
        return self.available_days >= requested_days

    class Meta:
        verbose_name = _("Leave Balance")
        verbose_name_plural = _("Leave Balances")
        unique_together = ('employee', 'leave_type', 'year')
        ordering = ['year', 'employee__first_name']

# -------------------- ATTENDANCE MANAGEMENT --------------------

class AttendanceMonth(models.Model):
    """Represents a monthly attendance period."""
    year = models.PositiveIntegerField(_("Year"))
    month = models.PositiveIntegerField(_("Month"))
    is_processed = models.BooleanField(_("Is Processed"), default=False)
    processed_date = models.DateTimeField(_("Processed Date"), null=True, blank=True)
    processed_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='processed_attendance_months', 
                                    verbose_name=_("Processed By"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.year}-{self.month:02d}"
    
    def process_attendance(self, processed_by):
        self.is_processed = True
        self.processed_date = timezone.now()
        self.processed_by = processed_by
        self.save()

    class Meta:
        verbose_name = _("Attendance Month")
        verbose_name_plural = _("Attendance Months")
        unique_together = ('year', 'month')
        ordering = ['year', 'month']

class AttendanceLog(models.Model):
    """Records individual attendance check-ins and check-outs."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='attendance_logs', verbose_name=_("Employee"))
    timestamp = models.DateTimeField(_("Timestamp"))
    is_in = models.BooleanField(_("Is Check-in"))
    location = models.CharField(_("Location"), max_length=255, null=True, blank=True)
    device = models.CharField(_("Device"), max_length=100, null=True, blank=True)
    notes = models.TextField(_("Notes"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    def __str__(self):
        log_type = "Check-in" if self.is_in else "Check-out"
        return f"{self.employee.get_full_name()} - {log_type} at {self.timestamp}"

    class Meta:
        verbose_name = _("Attendance Log")
        verbose_name_plural = _("Attendance Logs")
        ordering = ['-timestamp']

class Attendance(models.Model):
    """Tracks daily attendance status for employees."""
    STATUS_CHOICES = (
        ('PRE', 'Present'),
        ('ABS', 'Absent'),
        ('LAT', 'Late'),
        ('LEA', 'Leave'),
        ('HOL', 'Holiday'),
        ('WEE', 'Weekend'),
        ('HAL', 'Half Day'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='attendances', verbose_name=_("Employee"))
    date = models.DateField(_("Date"))
    status = models.CharField(_("Status"), max_length=3, choices=STATUS_CHOICES)
    roster_day = models.ForeignKey(RosterDay, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='attendances', verbose_name=_("Roster Day"))
    check_in = models.DateTimeField(_("Check-in"), null=True, blank=True)
    check_out = models.DateTimeField(_("Check-out"), null=True, blank=True)
    late_minutes = models.PositiveIntegerField(_("Late Minutes"), default=0)
    early_out_minutes = models.PositiveIntegerField(_("Early Out Minutes"), default=0)
    overtime_minutes = models.PositiveIntegerField(_("Overtime Minutes"), default=0)
    is_manual = models.BooleanField(_("Is Manual"), default=False)
    remarks = models.TextField(_("Remarks"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.date} - {self.get_status_display()}"
    
    @property
    def working_hours(self):
        if not self.check_in or not self.check_out:
            return 0
        
        duration = self.check_out - self.check_in
        hours = duration.total_seconds() / 3600
        
        return round(hours, 2)

    class Meta:
        verbose_name = _("Attendance")
        verbose_name_plural = _("Attendances")
        unique_together = ('employee', 'date')
        ordering = ['-date']

class OvertimeRecord(models.Model):
    """Records employee overtime hours."""
    STATUS_CHOICES = (
        ('PEN', 'Pending'),
        ('APP', 'Approved'),
        ('REJ', 'Rejected'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='overtime_records', verbose_name=_("Employee"))
    date = models.DateField(_("Date"))
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    hours = models.DecimalField(_("Hours"), max_digits=5, decimal_places=2)
    reason = models.TextField(_("Reason"))
    status = models.CharField(_("Status"), max_length=3, choices=STATUS_CHOICES, default='PEN')
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='approved_overtimes', verbose_name=_("Approved By"))
    approved_date = models.DateTimeField(_("Approved Date"), null=True, blank=True)
    remarks = models.TextField(_("Remarks"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
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

    class Meta:
        verbose_name = _("Overtime Record")
        verbose_name_plural = _("Overtime Records")
        ordering = ['-date']


class Notice(models.Model):
    TARGET_CHOICES = [
        ('ALL', 'All Departments'),
        ('DEPT', 'Specific Departments'),
        ('USER', 'Specific Users'),
    ]

    title = models.CharField(max_length=255)
    content = CKEditor5Field('Content')  

    department = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    target_type = models.CharField(max_length=50, choices=TARGET_CHOICES, default='all')
    
    file = models.FileField(upload_to='notices/', null=True, blank=True)    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)


    def __str__(self):
        return self.title    

# -------------------- PAYROLL MANAGEMENT --------------------
class SalaryComponent(models.Model):
    """Defines components of an employee's salary."""
    COMPONENT_TYPE_CHOICES = (
        ('EARN', 'Earning'),
        ('DED', 'Deduction'),
    )
    
    name = models.CharField(_("Name"), max_length=100)
    code = models.CharField(_("Code"), max_length=20, unique=True)
    component_type = models.CharField(_("Component Type"), max_length=4, choices=COMPONENT_TYPE_CHOICES)
    is_taxable = models.BooleanField(_("Is Taxable"), default=True)
    is_fixed = models.BooleanField(_("Is Fixed"), default=True)
    description = models.TextField(_("Description"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_component_type_display()})"

    class Meta:
        verbose_name = _("Salary Component")
        verbose_name_plural = _("Salary Components")
        ordering = ['component_type', 'name']

class EmployeeSalaryStructure(models.Model):
    """Defines an employee's salary structure."""
    employee = models.OneToOneField('Employee', on_delete=models.CASCADE, 
                                   related_name='salary_structure', verbose_name=_("Employee"))
    effective_date = models.DateField(_("Effective Date"))
    basic_salary = models.DecimalField(_("Basic Salary"), max_digits=10, decimal_places=2, default=0,
                                      help_text=_("Base salary amount before allowances"))
    gross_salary = models.DecimalField(_("Gross Salary"), max_digits=10, decimal_places=2,default=0,
                                      help_text=_("Total salary including all earnings"))
    net_salary = models.DecimalField(_("Net Salary"), max_digits=10, decimal_places=2,default=0,
                                    help_text=_("Final salary after deductions"))
    total_earnings = models.DecimalField(_("Total Earnings"), max_digits=10, decimal_places=2, 
                                        default=0, help_text=_("Sum of all earning components"))
    total_deductions = models.DecimalField(_("Total Deductions"), max_digits=10, decimal_places=2, 
                                          default=0, help_text=_("Sum of all deduction components"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def calculate_totals(self):
        """Calculate total earnings, deductions, gross and net salary"""
        earnings = Decimal('0.00')
        deductions = Decimal('0.00')
        
        # Calculate earnings (including basic salary)
        earnings += self.basic_salary
        for component in self.components.filter(component__component_type='EARN'):
            if component.percentage:
                # Calculate percentage of basic salary
                amount = (self.basic_salary * component.percentage) / 100
            else:
                amount = component.amount or Decimal('0.00')
            earnings += amount
        
        # Calculate deductions
        for component in self.components.filter(component__component_type='DED'):
            if component.percentage:
                # Calculate percentage of gross salary
                amount = (earnings * component.percentage) / 100
            else:
                amount = component.amount or Decimal('0.00')
            deductions += amount
        
        # Update totals
        self.total_earnings = earnings
        self.total_deductions = deductions
        self.gross_salary = earnings
        self.net_salary = earnings - deductions
        
        return {
            'total_earnings': self.total_earnings,
            'total_deductions': self.total_deductions,
            'gross_salary': self.gross_salary,
            'net_salary': self.net_salary
        }
    
    def save(self, *args, **kwargs):
        """Override save to auto-calculate totals"""
        # Save first to ensure we have an ID for related components
        super().save(*args, **kwargs)
        
        # Calculate and update totals
        self.calculate_totals()
        
        # Save again with calculated values
        super().save(update_fields=['total_earnings', 'total_deductions', 'gross_salary', 'net_salary'])

        if self.employee:
            #  Update Employee basic_salary
            if self.employee.basic_salary != self.basic_salary:
                self.employee.basic_salary = self.basic_salary
                self.employee.save(update_fields=['basic_salary'])
            # Only save the employee if the gross_salary has actually changed
            if self.employee.gross_salary != self.gross_salary:
                self.employee.gross_salary = self.gross_salary
                # Save only the updated 'gross_salary' field on the Employee model
                self.employee.save(update_fields=['gross_salary'])            
    def clean(self):
        """Validate salary structure"""
        super().clean()
        
        if self.basic_salary and self.basic_salary < 0:
            raise ValidationError({'basic_salary': _('Basic salary cannot be negative.')})
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.gross_salary}"

    class Meta:
        verbose_name = _("Employee Salary Structure")
        verbose_name_plural = _("Employee Salary Structures")
        ordering = ['employee__first_name']

class SalaryStructureComponent(models.Model):
    """Links salary components to an employee's salary structure."""
    salary_structure = models.ForeignKey(EmployeeSalaryStructure, on_delete=models.CASCADE, 
                                        related_name='components', 
                                        verbose_name=_("Salary Structure"))
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE, 
                                 related_name='structure_components', verbose_name=_("Component"))
    amount = models.DecimalField(_("Fixed Amount"), max_digits=10, decimal_places=2, 
                                null=True, blank=True,
                                help_text=_("Fixed amount for this component"))
    percentage = models.DecimalField(_("Percentage"), max_digits=5, decimal_places=2, 
                                    null=True, blank=True,
                                    help_text=_("Percentage of basic/gross salary"))
    calculated_amount = models.DecimalField(_("Calculated Amount"), max_digits=10, decimal_places=2,
                                           default=0, help_text=_("Final calculated amount"))
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def calculate_amount(self):
        """Calculate the final amount for this component"""
        if self.percentage:
            if self.component.component_type == 'EARN':
                # Earnings percentage based on basic salary
                base_amount = self.salary_structure.basic_salary
            else:
                # Deductions percentage based on gross salary
                base_amount = self.salary_structure.gross_salary or self.salary_structure.basic_salary
            
            self.calculated_amount = (base_amount * self.percentage) / 100
        else:
            self.calculated_amount = self.amount or Decimal('0.00')
        
        return self.calculated_amount
    
    def save(self, *args, **kwargs):
        """Override save to calculate amount and update salary structure"""
        self.calculate_amount()
        super().save(*args, **kwargs)
        
        # Recalculate salary structure totals
        if self.salary_structure_id:
            self.salary_structure.save()
    
    def delete(self, *args, **kwargs):
        """Override delete to update salary structure totals"""
        salary_structure = self.salary_structure
        super().delete(*args, **kwargs)
        
        # Recalculate salary structure totals after deletion
        if salary_structure:
            salary_structure.save()
    
    def clean(self):
        """Validate component"""
        super().clean()
        
        if not self.amount and not self.percentage:
            raise ValidationError(_('Either amount or percentage must be provided.'))
        
        if self.amount and self.amount < 0:
            raise ValidationError({'amount': _('Amount cannot be negative.')})
        
        if self.percentage and (self.percentage < 0 or self.percentage > 100):
            raise ValidationError({'percentage': _('Percentage must be between 0 and 100.')})
    
    def __str__(self):
        return f"{self.salary_structure.employee.get_full_name()} - {self.component.name} - {self.calculated_amount}"

    class Meta:
        verbose_name = _("Salary Structure Component")
        verbose_name_plural = _("Salary Structure Components")
        unique_together = ('salary_structure', 'component')
        ordering = ['salary_structure__employee__first_name', 'component__component_type', 'component__name']


class BonusSetup(models.Model):
    """Defines bonus configurations."""
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Bonus Setup")
        verbose_name_plural = _("Bonus Setups")
        ordering = ['name']

class BonusMonth(models.Model):
    """Represents a monthly bonus period."""
    bonus_setup = models.ForeignKey(BonusSetup, on_delete=models.CASCADE, 
                                   related_name='bonus_months', verbose_name=_("Bonus Setup"))
    year = models.PositiveIntegerField(_("Year"))
    month = models.PositiveIntegerField(_("Month"))
    is_generated = models.BooleanField(_("Is Generated"), default=False)
    generated_date = models.DateTimeField(_("Generated Date"), null=True, blank=True)
    generated_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='generated_bonuses', verbose_name=_("Generated By"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.bonus_setup.name} - {self.year}-{self.month:02d}"

    class Meta:
        verbose_name = _("Bonus Month")
        verbose_name_plural = _("Bonus Months")
        unique_together = ('bonus_setup', 'year', 'month')
        ordering = ['year', 'month']

class EmployeeBonus(models.Model):
    """Records bonuses awarded to employees."""
    bonus_month = models.ForeignKey(BonusMonth, on_delete=models.CASCADE, 
                                   related_name='employee_bonuses', verbose_name=_("Bonus Month"))
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='bonuses', verbose_name=_("Employee"))
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    remarks = models.TextField(_("Remarks"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.bonus_month.bonus_setup.name} - {self.amount}"

    class Meta:
        verbose_name = _("Employee Bonus")
        verbose_name_plural = _("Employee Bonuses")
        unique_together = ('bonus_month', 'employee')
        ordering = ['bonus_month__year', 'bonus_month__month', 'employee__first_name']

class AdvanceSetup(models.Model):
    """Defines advance payment configurations."""
    name = models.CharField(_("Name"), max_length=100)
    max_amount = models.DecimalField(_("Max Amount"), max_digits=10, decimal_places=2)
    max_installments = models.PositiveIntegerField(_("Max Installments"))
    interest_rate = models.DecimalField(_("Interest Rate"), max_digits=5, decimal_places=2, default=0)
    description = models.TextField(_("Description"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Advance Setup")
        verbose_name_plural = _("Advance Setups")
        ordering = ['name']

class EmployeeAdvance(models.Model):
    """Records advances given to employees."""
    STATUS_CHOICES = (
        ('PEN', 'Pending'),
        ('APP', 'Approved'),
        ('REJ', 'Rejected'),
        ('PAI', 'Paid'),
        ('CLS', 'Closed'),
    )
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='advances', verbose_name=_("Employee"))
    advance_setup = models.ForeignKey(AdvanceSetup, on_delete=models.CASCADE, 
                                     related_name='employee_advances', verbose_name=_("Advance Setup"))
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    installments = models.PositiveIntegerField(_("Installments"))
    installment_amount = models.DecimalField(_("Installment Amount"), max_digits=10, decimal_places=2)
    interest_amount = models.DecimalField(_("Interest Amount"), max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=10, decimal_places=2)
    application_date = models.DateField(_("Application Date"))
    approval_date = models.DateField(_("Approval Date"), null=True, blank=True)
    approved_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='approved_advances', verbose_name=_("Approved By"))
    status = models.CharField(_("Status"), max_length=3, choices=STATUS_CHOICES, default='PEN')
    reason = models.TextField(_("Reason"))
    remarks = models.TextField(_("Remarks"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
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

    class Meta:
        verbose_name = _("Employee Advance")
        verbose_name_plural = _("Employee Advances")
        ordering = ['-application_date']

class AdvanceInstallment(models.Model):
    """Tracks installments for employee advances."""
    advance = models.ForeignKey(EmployeeAdvance, on_delete=models.CASCADE, 
                               related_name='advance_installments', verbose_name=_("Advance"))
    installment_number = models.PositiveIntegerField(_("Installment Number"))
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    due_date = models.DateField(_("Due Date"))
    is_paid = models.BooleanField(_("Is Paid"), default=False)
    payment_date = models.DateField(_("Payment Date"), null=True, blank=True)
    remarks = models.TextField(_("Remarks"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.advance.employee.get_full_name()} - Installment {self.installment_number} - {self.amount}"

    class Meta:
        verbose_name = _("Advance Installment")
        verbose_name_plural = _("Advance Installments")
        ordering = ['due_date']

class SalaryMonth(models.Model):
    """Represents a monthly salary period."""
    year = models.PositiveIntegerField(_("Year"))
    month = models.PositiveIntegerField(_("Month"))
    is_generated = models.BooleanField(_("Is Generated"), default=False)
    generated_date = models.DateTimeField(_("Generated Date"), null=True, blank=True)
    generated_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='generated_salaries', verbose_name=_("Generated By"))
    is_paid = models.BooleanField(_("Is Paid"), default=False)
    payment_date = models.DateField(_("Payment Date"), null=True, blank=True)
    remarks = models.TextField(_("Remarks"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"Salary {self.year}-{self.month:02d}"

    class Meta:
        verbose_name = _("Salary Month")
        verbose_name_plural = _("Salary Months")
        unique_together = ('year', 'month')
        ordering = ['year', 'month']

class EmployeeSalary(models.Model):
    """Records salary details for an employee in a given month."""
    salary_month = models.ForeignKey(SalaryMonth, on_delete=models.CASCADE, 
                                    related_name='employee_salaries', verbose_name=_("Salary Month"))
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='salaries', verbose_name=_("Employee"))
    basic_salary = models.DecimalField(_("Basic Salary"), max_digits=10, decimal_places=2)
    gross_salary = models.DecimalField(_("Gross Salary"), max_digits=10, decimal_places=2)
    total_earnings = models.DecimalField(_("Total Earnings"), max_digits=10, decimal_places=2)
    total_deductions = models.DecimalField(_("Total Deductions"), max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(_("Net Salary"), max_digits=10, decimal_places=2)
    working_days = models.PositiveIntegerField(_("Working Days"))
    present_days = models.PositiveIntegerField(_("Present Days"))
    absent_days = models.PositiveIntegerField(_("Absent Days"))
    leave_days = models.PositiveIntegerField(_("Leave Days"))
    overtime_hours = models.DecimalField(_("Overtime Hours"), max_digits=5, decimal_places=2, default=0)
    overtime_amount = models.DecimalField(_("Overtime Amount"), max_digits=10, decimal_places=2, default=0)
    is_separation_salary = models.BooleanField(_("Is Separation Salary"), default=False)
    remarks = models.TextField(_("Remarks"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.salary_month}"

    class Meta:
        verbose_name = _("Employee Salary")
        verbose_name_plural = _("Employee Salaries")
        unique_together = ('salary_month', 'employee')
        ordering = ['salary_month__year', 'salary_month__month', 'employee__first_name']

class SalaryDetail(models.Model):
    """Details specific salary components for an employee’s salary."""
    salary = models.ForeignKey(EmployeeSalary, on_delete=models.CASCADE, 
                              related_name='details', verbose_name=_("Salary"))
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE, 
                                 related_name='salary_details', verbose_name=_("Component"))
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.salary.employee.get_full_name()} - {self.component.name} - {self.amount}"

    class Meta:
        verbose_name = _("Salary Detail")
        verbose_name_plural = _("Salary Details")
        ordering = ['salary__employee__first_name', 'component__name']

class Promotion(models.Model):
    """Records employee promotions."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='promotions', verbose_name=_("Employee"))
    from_designation = models.ForeignKey(Designation, on_delete=models.CASCADE, 
                                        related_name='promotions_from', 
                                        verbose_name=_("From Designation"))
    to_designation = models.ForeignKey(Designation, on_delete=models.CASCADE, 
                                      related_name='promotions_to', 
                                      verbose_name=_("To Designation"))
    effective_date = models.DateField(_("Effective Date"))
    salary_increment = models.DecimalField(_("Salary Increment"), max_digits=10, 
                                          decimal_places=2, default=0)
    remarks = models.TextField(_("Remarks"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.from_designation.name} to {self.to_designation.name}"
    
    def save(self, *args, **kwargs):
        self.employee.designation = self.to_designation
        if self.salary_increment > 0:
            self.employee.basic_salary += self.salary_increment
        self.employee.save()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Promotion")
        verbose_name_plural = _("Promotions")
        ordering = ['-effective_date']

class Increment(models.Model):
    """Records salary increments for employees."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='increments', verbose_name=_("Employee"))
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    percentage = models.DecimalField(_("Percentage"), max_digits=5, decimal_places=2, 
                                    null=True, blank=True)
    effective_date = models.DateField(_("Effective Date"))
    remarks = models.TextField(_("Remarks"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.amount} ({self.percentage}%)"
    
    def save(self, *args, **kwargs):
        self.employee.basic_salary += self.amount
        self.employee.save()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Increment")
        verbose_name_plural = _("Increments")
        ordering = ['-effective_date']

class Deduction(models.Model):
    """Records deductions applied to employee salaries."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='deductions', verbose_name=_("Employee"))
    salary_month = models.ForeignKey(SalaryMonth, on_delete=models.CASCADE, 
                                    related_name='deductions', verbose_name=_("Salary Month"))
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    reason = models.TextField(_("Reason"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.salary_month} - {self.amount}"

    class Meta:
        verbose_name = _("Deduction")
        verbose_name_plural = _("Deductions")
        ordering = ['-salary_month__year', '-salary_month__month']

# -------------------- PROVIDENT FUND MANAGEMENT --------------------

class ProvidentFundSetting(models.Model):
    """Defines provident fund contribution settings."""
    employee_contribution = models.DecimalField(_("Employee Contribution (%)"), 
                                               max_digits=5, decimal_places=2)
    employer_contribution = models.DecimalField(_("Employer Contribution (%)"), 
                                               max_digits=5, decimal_places=2)
    effective_date = models.DateField(_("Effective Date"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"PF Setting - Employee: {self.employee_contribution}%, Employer: {self.employer_contribution}%"

    class Meta:
        verbose_name = _("Provident Fund Setting")
        verbose_name_plural = _("Provident Fund Settings")
        ordering = ['-effective_date']

class EmployeeProvidentFund(models.Model):
    """Tracks an employee’s provident fund enrollment."""
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, 
                                   related_name='provident_fund', verbose_name=_("Employee"))
    enrollment_date = models.DateField(_("Enrollment Date"))
    employee_contribution = models.DecimalField(_("Employee Contribution (%)"), 
                                               max_digits=5, decimal_places=2)
    employer_contribution = models.DecimalField(_("Employer Contribution (%)"), 
                                               max_digits=5, decimal_places=2)
    is_active = models.BooleanField(_("Is Active"), default=True)
    remarks = models.TextField(_("Remarks"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - PF"

    class Meta:
        verbose_name = _("Employee Provident Fund")
        verbose_name_plural = _("Employee Provident Funds")
        ordering = ['employee__first_name']

class ProvidentFundTransaction(models.Model):
    """Records transactions for an employee’s provident fund."""
    TRANSACTION_TYPE_CHOICES = (
        ('CON', 'Contribution'),
        ('WIT', 'Withdrawal'),
        ('INT', 'Interest'),
        ('LOA', 'Loan'),
        ('REP', 'Loan Repayment'),
    )
    
    employee_pf = models.ForeignKey(EmployeeProvidentFund, on_delete=models.CASCADE,  related_name='transactions', verbose_name=_("Employee Provident Fund"))
    transaction_date = models.DateField(_("Transaction Date"))
    transaction_type = models.CharField(_("Transaction Type"), max_length=3, 
                                       choices=TRANSACTION_TYPE_CHOICES)
    employee_amount = models.DecimalField(_("Employee Amount"), max_digits=10, 
                                         decimal_places=2, default=0)
    employer_amount = models.DecimalField(_("Employer Amount"), max_digits=10, 
                                         decimal_places=2, default=0)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=10, decimal_places=2)
    reference = models.CharField(_("Reference"), max_length=100, null=True, blank=True)
    remarks = models.TextField(_("Remarks"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.employee_pf.employee.get_full_name()} - {self.get_transaction_type_display()} - {self.total_amount}"

    class Meta:
        verbose_name = _("Provident Fund Transaction")
        verbose_name_plural = _("Provident Fund Transactions")
        ordering = ['-transaction_date']

class FixedDepositReceipt(models.Model):
    """Represents a fixed deposit receipt."""
    fdr_number = models.CharField(_("FDR Number"), max_length=100, unique=True)
    bank_name = models.CharField(_("Bank Name"), max_length=100)
    branch_name = models.CharField(_("Branch Name"), max_length=100)
    amount = models.DecimalField(_("Amount"), max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(_("Interest Rate"), max_digits=5, decimal_places=2)
    start_date = models.DateField(_("Start Date"))
    maturity_date = models.DateField(_("Maturity Date"))
    is_active = models.BooleanField(_("Is Active"), default=True)
    remarks = models.TextField(_("Remarks"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"FDR {self.fdr_number} - {self.amount} - {self.bank_name}"

    class Meta:
        verbose_name = _("Fixed Deposit Receipt")
        verbose_name_plural = _("Fixed Deposit Receipts")
        ordering = ['-start_date']

# -------------------- VAT & TAX MANAGEMENT --------------------

class TaxYear(models.Model):
    """Defines a tax year for tax calculations."""
    name = models.CharField(_("Name"), max_length=100)
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Tax Year")
        verbose_name_plural = _("Tax Years")
        ordering = ['-start_date']

class TaxRate(models.Model):
    """Defines tax rates for a tax year."""
    tax_year = models.ForeignKey(TaxYear, on_delete=models.CASCADE, related_name='tax_rates', verbose_name=_("Tax Year"))
    min_amount = models.DecimalField(_("Minimum Amount"), max_digits=15, decimal_places=2)
    max_amount = models.DecimalField(_("Maximum Amount"), max_digits=15, decimal_places=2, 
                                    null=True, blank=True)
    rate = models.DecimalField(_("Rate (%)"), max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        if self.max_amount:
            return f"{self.min_amount} to {self.max_amount} - {self.rate}%"
        return f"Above {self.min_amount} - {self.rate}%"

    class Meta:
        verbose_name = _("Tax Rate")
        verbose_name_plural = _("Tax Rates")
        ordering = ['min_amount']

class AllowanceCalculationPlan(models.Model):
    """Defines plans for calculating allowances."""
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Allowance Calculation Plan")
        verbose_name_plural = _("Allowance Calculation Plans")
        ordering = ['name']

class AllowanceCalculation(models.Model):
    """Links salary components to allowance calculation plans."""
    plan = models.ForeignKey(AllowanceCalculationPlan, on_delete=models.CASCADE, 
                            related_name='calculations', verbose_name=_("Plan"))
    component = models.ForeignKey(SalaryComponent, on_delete=models.CASCADE, 
                                 related_name='allowance_calculations', verbose_name=_("Component"))
    percentage = models.DecimalField(_("Percentage"), max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.plan.name} - {self.component.name} - {self.percentage}%"

    class Meta:
        verbose_name = _("Allowance Calculation")
        verbose_name_plural = _("Allowance Calculations")
        ordering = ['plan__name', 'component__name']

class EmployeeInvestment(models.Model):
    """Records employee investments for tax purposes."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='investments', verbose_name=_("Employee"))
    tax_year = models.ForeignKey(TaxYear, on_delete=models.CASCADE, 
                                related_name='employee_investments', verbose_name=_("Tax Year"))
    investment_type = models.CharField(_("Investment Type"), max_length=100)
    amount = models.DecimalField(_("Amount"), max_digits=15, decimal_places=2)
    document = models.FileField(_("Document"), upload_to='investment_documents/', 
                               null=True, blank=True)
    remarks = models.TextField(_("Remarks"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.investment_type} - {self.amount}"

    class Meta:
        verbose_name = _("Employee Investment")
        verbose_name_plural = _("Employee Investments")
        ordering = ['-tax_year__start_date', 'employee__first_name']

class EmployeeTax(models.Model):
    """Calculates tax liabilities for employees."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='taxes', verbose_name=_("Employee"))
    tax_year = models.ForeignKey(TaxYear, on_delete=models.CASCADE, 
                                related_name='employee_taxes', verbose_name=_("Tax Year"))
    total_income = models.DecimalField(_("Total Income"), max_digits=12, decimal_places=2)
    total_exemptions = models.DecimalField(_("Total Exemptions"), max_digits=10, decimal_places=2)
    total_investments = models.DecimalField(_("Total Investments"), max_digits=10, decimal_places=2)
    taxable_income = models.DecimalField(_("Taxable Income"), max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=10, decimal_places=2)
    generated_date = models.DateTimeField(_("Generated Date"))
    generated_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='generated_taxes', verbose_name=_("Generated By"))
    remarks = models.TextField(_("Remarks"), null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.tax_year.name} - {self.tax_amount}"

    class Meta:
        verbose_name = _("Employee Tax")
        verbose_name_plural = _("Employee Taxes")
        unique_together = ('employee', 'tax_year')
        ordering = ['-tax_year__start_date', 'employee__first_name']

# -------------------- LETTER MANAGEMENT --------------------

class LetterTemplate(models.Model):
    LETTER_TYPE_CHOICES = [
        ('APP', 'Appointment'), ('CON', 'Confirmation'), ('PRO', 'Promotion'),
        ('INC', 'Increment'), ('INC_PRO', 'Increment with Promotion'),
        ('ABS', 'Absent'), ('SHO', 'Show Cause'), ('AGE', 'Age Proof & Fitness Certificate'),
        ('TER', 'Termination'), ('DIS', 'Dismissal'), ('SUS', 'Suspension'),
        ('FIN', 'Final Settlement'), ('OTH', 'Other'),
    ]
    name = models.CharField(max_length=100)
    letter_type = models.CharField(max_length=7, choices=LETTER_TYPE_CHOICES)
    content = models.TextField(help_text="Use {{variable}} for dynamic content")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_letter_type_display()})"

class EmployeeLetter(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='letters')
    template = models.ForeignKey(LetterTemplate, on_delete=models.CASCADE, related_name='employee_letters')
    reference_number = models.CharField(max_length=100)
    duration_date = models.DurationField()
    content = models.TextField()
    issued_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_letters')
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.template.get_letter_type_display()} - {self.created_at.date()}"

    class Meta:
        verbose_name = _("Employee Letter")
        verbose_name_plural = _("Employee Letters")
        ordering = ['-created_at']

# -------------------- MOBILE APP ATTENDANCE ------------------

class MobileAttendance(models.Model):
    """Tracks employee attendance via mobile devices."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, 
                                related_name='mobile_attendances', verbose_name=_("Employee"))
    check_in = models.DateTimeField(_("Check-in"))
    check_out = models.DateTimeField(_("Check-out"), null=True, blank=True)
    check_in_location = models.CharField(_("Check-in Location"), max_length=255)
    check_out_location = models.CharField(_("Check-out Location"), max_length=255, 
                                         null=True, blank=True)
    check_in_notes = models.TextField(_("Check-in Notes"), null=True, blank=True)
    check_out_notes = models.TextField(_("Check-out Notes"), null=True, blank=True)
    check_in_image = models.ImageField(_("Check-in Image"), 
                                      upload_to='mobile_attendance/', null=True, blank=True)
    check_out_image = models.ImageField(_("Check-out Image"), 
                                      upload_to='mobile_attendance/', null=True, blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.check_in.date()}"

    class Meta:
        verbose_name = _("Mobile Attendance")
        verbose_name_plural = _("Mobile Attendances")
        ordering = ['-check_in']

class Location(models.Model):
    """Represents a geolocation for attendance tracking."""
    name = models.CharField(_("Name"), max_length=100)
    address = models.TextField(_("Address"))
    latitude = models.DecimalField(_("Latitude"), max_digits=10, decimal_places=8)
    longitude = models.DecimalField(_("Longitude"), max_digits=11, decimal_places=8)
    radius = models.DecimalField(_("Radius (km)"), max_digits=5, decimal_places=2)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")
        ordering = ['name']

class UserLocation(models.Model):
    """Associates users with locations for attendance tracking."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, 
                            related_name='user_locations', verbose_name=_("User"))
    location = models.ForeignKey(Location, on_delete=models.CASCADE, 
                                related_name='user_locations', verbose_name=_("Location"))
    is_primary = models.BooleanField(_("Is Primary"), default=False)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.location.name}"

    class Meta:
        verbose_name = _("User Location")
        verbose_name_plural = _("User Locations")
        unique_together = ('user', 'location')
        ordering = ['user__username', 'location__name']

class LocationAttendance(models.Model):
    """Records attendance at specific locations."""
    ATTENDANCE_TYPE_CHOICES = (
        ('IN', 'Check-in'),
        ('OUT', 'Check-out'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, 
                            related_name='location_attendances', verbose_name=_("User"))
    location = models.ForeignKey(Location, on_delete=models.CASCADE, 
                                related_name='attendances', verbose_name=_("Location"))
    attendance_type = models.CharField(_("Attendance Type"), max_length=3, 
                                      choices=ATTENDANCE_TYPE_CHOICES)
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)
    latitude = models.DecimalField(_("Latitude"), max_digits=10, decimal_places=8)
    longitude = models.DecimalField(_("Longitude"), max_digits=11, decimal_places=8)
    is_within_radius = models.BooleanField(_("Is Within Radius"), default=False)
    distance = models.DecimalField(_("Distance (km)"), max_digits=8, decimal_places=2)
    device_info = models.TextField(_("Device Info"), blank=True, null=True)
    ip_address = models.GenericIPAddressField(_("IP Address"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.location.name} - {self.get_attendance_type_display()} - {self.timestamp}"

    class Meta:
        verbose_name = _("Location Attendance")
        verbose_name_plural = _("Location Attendances")
        ordering = ['-timestamp']

class ZKDevice(models.Model):
    """Stores ZKTeco device information."""
    name = models.CharField(_("Device Name"), max_length=100)
    ip_address = models.GenericIPAddressField(_("IP Address"))
    port = models.IntegerField(_("Port"), default=4370)
    device_id = models.CharField(_("Device ID"), max_length=100, blank=True, null=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    last_sync = models.DateTimeField(_("Last Sync"), blank=True, null=True)
    location = models.CharField(_("Location"), max_length=255, blank=True, null=True)
    timeout = models.IntegerField(_("Timeout"), default=5)
    password = models.CharField(_("Device Password"), max_length=100, blank=True, null=True)
    force_udp = models.BooleanField(_("Force UDP"), default=False)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.ip_address})"
    
    def get_connection_params(self):
        port = int(self.port) if self.port else 4370
        timeout = int(self.timeout) if self.timeout else 5
        password = self.password if self.password else ''
        return {
            'ip': self.ip_address,
            'port': port,
            'timeout': timeout,
            'password': password,
            'force_udp': bool(self.force_udp),
            'ommit_ping': False,
        }

    class Meta:
        verbose_name = _("ZK Device")
        verbose_name_plural = _("ZK Devices")
        ordering = ['name']

class ZKAttendanceLog(models.Model):
    """
    Stores comprehensive attendance logs from ZKTeco devices, capturing all possible fields.
    """
    device = models.ForeignKey(
        ZKDevice,
        on_delete=models.CASCADE,
        related_name='attendance_logs',
        verbose_name=_("Device"),
        help_text=_("The ZKTeco device that recorded this attendance log.")
    )
    device_serial_no = models.CharField(
        _("Device Serial Number"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Serial number or unique identifier of the device, matching ZKDevice.device_id.")
    )
    user_id = models.CharField(
        _("User ID"),
        max_length=255,
        help_text=_("Unique identifier of the user as recorded by the device.")
    )
    timestamp = models.DateTimeField(
        _("Timestamp"),
        help_text=_("Date and time when the attendance was recorded.")
    )
    punch_type = models.CharField(
        _("Punch Type"),
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Type of punch (e.g., Check In, Check Out, Break In).")
    )
    status = models.CharField(
        _("Status"),
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Status code or description of the attendance record.")
    )
    verify_type = models.CharField(
        _("Verification Type"),
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Method of verification (e.g., Fingerprint, Card, Password).")
    )
    work_code = models.CharField(
        _("Work Code"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Work or task code associated with the attendance.")
    )
    card_no = models.CharField(
        _("Card Number"),
        max_length=50,
        blank=True,
        null=True,
        help_text=_("Card number used for authentication, if applicable.")
    )
    record_id = models.CharField(
        _("Record ID"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Unique record identifier from the device.")
    )
    reserved = models.CharField(
        _("Reserved Field"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Device-specific reserved data, if any.")
    )
    created_at = models.DateTimeField(
        _("Created At"),
        auto_now_add=True,
        help_text=_("When this log was saved to the database.")
    )
    updated_at = models.DateTimeField(
        _("Updated At"),
        auto_now=True,
        help_text=_("When this log was last updated in the database.")
    )

    def __str__(self):
        return f"{self.user_id} - {self.device.name if self.device else 'No Device'} - {self.timestamp}"

    def clean(self):
        """Validate user_id and timestamp."""
        if not self.user_id.strip():
            raise ValidationError(_("User ID cannot be empty."))
        # Fix: Use timezone.now() instead of timezone.utc
        if self.timestamp > timezone.now():
            raise ValidationError(_("Timestamp cannot be in the future."))

    class Meta:
        verbose_name = _("ZK Attendance Log")
        verbose_name_plural = _("ZK Attendance Logs")
        unique_together = ('device', 'user_id', 'timestamp', 'punch_type')
        indexes = [
            models.Index(fields=['device', 'user_id', 'timestamp']),
            models.Index(fields=['user_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['device_serial_no']),
            models.Index(fields=['record_id']),
        ]
        ordering = ['-timestamp']

    def get_punch_type_display(self):
        """Return human-readable punch type."""
        punch_types = {
            '0': _("Check In"),
            '1': _("Check Out"),
            '2': _("Break Out"),
            '3': _("Break In"),
            '4': _("Overtime In"),
            '5': _("Overtime Out"),
        }
        return punch_types.get(self.punch_type, self.punch_type or _("Unknown"))