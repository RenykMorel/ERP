from models import Usuario, Invoice

def generate_users_report(start_date, end_date):
    users = Usuario.query.filter(Usuario.fecha_registro.between(start_date, end_date)).all()
    return [user.to_dict() for user in users]

def generate_revenue_report(start_date, end_date):
    invoices = Invoice.query.filter(Invoice.due_date.between(start_date, end_date)).all()
    total_revenue = sum(invoice.amount for invoice in invoices)
    return {
        'total_revenue': total_revenue,
        'invoices': [invoice.to_dict() for invoice in invoices]
    }