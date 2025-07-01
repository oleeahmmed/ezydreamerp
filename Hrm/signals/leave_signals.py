from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal
from ..models import LeaveApplication, LeaveBalance

@receiver(pre_save, sender=LeaveApplication)
def update_leave_balance_on_status_change(sender, instance, **kwargs):
    """
    Signal to handle leave balance updates when a leave application status changes
    """
    # Check if this is an existing leave application (has an ID)
    if instance.pk:
        try:
            # Get the original leave application from the database
            old_instance = LeaveApplication.objects.get(pk=instance.pk)
            
            # If status has changed, update leave balances accordingly
            if old_instance.status != instance.status:
                # Get the leave balance for this employee, leave type and year
                current_year = instance.start_date.year
                leave_balance, created = LeaveBalance.objects.get_or_create(
                    employee=instance.employee,
                    leave_type=instance.leave_type,
                    year=current_year,
                    defaults={
                        'total_days': instance.leave_type.max_days_per_year,
                        'used_days': 0,
                        'pending_days': 0
                    }
                )
                
                leave_days = Decimal(instance.days)
                
                # Handle status transitions
                if old_instance.status == 'PEN' and instance.status == 'APP':
                    # Pending to Approved: move days from pending to used
                    leave_balance.pending_days -= leave_days
                    leave_balance.used_days += leave_days
                
                elif old_instance.status == 'PEN' and instance.status in ['REJ', 'CAN']:
                    # Pending to Rejected/Cancelled: remove from pending
                    leave_balance.pending_days -= leave_days
                
                elif old_instance.status == 'APP' and instance.status == 'CAN':
                    # Approved to Cancelled: remove from used
                    leave_balance.used_days -= leave_days
                
                leave_balance.save()
                
        except LeaveApplication.DoesNotExist:
            pass  # This is a new application, handled by post_save

@receiver(post_save, sender=LeaveApplication)
def update_leave_balance_on_create(sender, instance, created, **kwargs):
    """
    Signal to handle leave balance updates when a new leave application is created
    """
    if created:
        # This is a new application
        current_year = instance.start_date.year
        leave_balance, created_balance = LeaveBalance.objects.get_or_create(
            employee=instance.employee,
            leave_type=instance.leave_type,
            year=current_year,
            defaults={
                'total_days': instance.leave_type.max_days_per_year,
                'used_days': 0,
                'pending_days': 0
            }
        )
        
        leave_days = Decimal(instance.days)
        
        # Update balance based on the status of the new application
        if instance.status == 'PEN':
            leave_balance.pending_days += leave_days
        elif instance.status == 'APP':
            leave_balance.used_days += leave_days
        
        leave_balance.save()

@receiver(post_delete, sender=LeaveApplication)
def update_leave_balance_on_delete(sender, instance, **kwargs):
    """
    Signal to handle leave balance updates when a leave application is deleted
    """
    try:
        current_year = instance.start_date.year
        leave_balance = LeaveBalance.objects.get(
            employee=instance.employee,
            leave_type=instance.leave_type,
            year=current_year
        )
        
        leave_days = Decimal(instance.days)
        
        # Update balance based on the status of the deleted application
        if instance.status == 'PEN':
            leave_balance.pending_days -= leave_days
        elif instance.status == 'APP':
            leave_balance.used_days -= leave_days
        
        leave_balance.save()
    except LeaveBalance.DoesNotExist:
        pass