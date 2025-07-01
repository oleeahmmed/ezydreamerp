from Finance.models import GeneralLedger

def post_to_general_ledger(journal_entry):
    if journal_entry.is_posted:
        # Clear old GL entries
        GeneralLedger.objects.filter(journal_entry=journal_entry).delete()

        # Loop through lines
        for line in journal_entry.lines.all():
            balance = line.debit_amount - line.credit_amount
            GeneralLedger.objects.create(
                account=line.account,
                posting_date=journal_entry.posting_date,
                journal_entry=journal_entry,
                debit_amount=line.debit_amount,
                credit_amount=line.credit_amount,
                balance=balance,
                currency=journal_entry.currency,
                cost_center=journal_entry.cost_center  
            )
