from django.urls import path
from . import views

app_name = "maintenance"

urlpatterns = [
    path("", views.tenant_tickets, name="tenant_tickets"),
    path("create/", views.create_ticket, name="create_ticket"),
    path("ticket/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("owner/", views.owner_tickets, name="owner_tickets"),
    path("owner/ticket/<int:pk>/assign/", views.assign_ticket, name="assign_ticket"),
    path("owner/ticket/<int:pk>/close/", views.close_ticket, name="close_ticket"),
    path("technicians/", views.technician_list, name="technicians"),
    path("technicians/add/", views.technician_create, name="technician_create"),
    path("technicians/<int:pk>/edit/", views.technician_edit, name="technician_edit"),
    path("technicians/<int:pk>/delete/", views.technician_delete, name="technician_delete"),
    path("technician/account/", views.technician_account, name="technician_account"),
    path("technician/tickets/", views.technician_tickets, name="technician_tickets"),
    path("technician/history/", views.technician_history, name="technician_history"),
    path("technician/report/", views.technician_report, name="technician_report"),
    path("technician/ticket/<int:pk>/accept/", views.accept_ticket, name="accept_ticket"),
    path("technician/ticket/<int:pk>/reject/", views.reject_ticket, name="reject_ticket"),
    path("tenant/ticket/<int:pk>/finish/", views.tenant_finish_ticket, name="tenant_finish_ticket"),
    path("technician/ticket/<int:pk>/start/", views.start_ticket, name="start_ticket"),
    path("technician/ticket/<int:pk>/resolve/", views.resolve_ticket, name="resolve_ticket"),
    path("technician/preparation/<int:item_pk>/", views.update_preparation_item, name="update_preparation_item"),
    path("technician/availability/", views.toggle_technician_availability, name="toggle_technician_availability"),
    path("notifications/<int:pk>/read/", views.mark_notification_read, name="mark_notification_read"),
]
