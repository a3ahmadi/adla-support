from django.urls import path

from .views import (
    AgentTicketDetailView,
    AgentTicketListView,
    AgentTicketMessageListCreateView,
    TicketCloseView,
    TicketDetailView,
    TicketListCreateView,
    TicketMarkReadView,
    TicketMessageListCreateView,
    TicketReopenView,
    TicketSummaryView,
    AgentTicketMarkReadView,
    AgentTicketCloseView,
    AgentTicketReopenView,
)


app_name = "support"


urlpatterns = [
    path(
        "tickets/",
        TicketListCreateView.as_view(),
        name="ticket-list-create",
    ),

    path(
        "tickets/summary/",
        TicketSummaryView.as_view(),
        name="ticket-summary",
    ),

    path(
        "tickets/<str:ticket_number>/",
        TicketDetailView.as_view(),
        name="ticket-detail",
    ),

    path(
        "tickets/<str:ticket_number>/messages/",
        TicketMessageListCreateView.as_view(),
        name="ticket-message-list-create",
    ),

    path(
        "tickets/<str:ticket_number>/read/",
        TicketMarkReadView.as_view(),
        name="ticket-mark-read",
    ),

    path(
        "tickets/<str:ticket_number>/close/",
        TicketCloseView.as_view(),
        name="ticket-close",
    ),

    path(
        "tickets/<str:ticket_number>/reopen/",
        TicketReopenView.as_view(),
        name="ticket-reopen",
    ),

    path(
        "agent/tickets/",
        AgentTicketListView.as_view(),
        name="agent-ticket-list",
    ),

    path(
        "agent/tickets/<str:ticket_number>/",
        AgentTicketDetailView.as_view(),
        name="agent-ticket-detail",
    ),

    path(
        "agent/tickets/<str:ticket_number>/messages/",
        AgentTicketMessageListCreateView.as_view(),
        name="agent-ticket-message-list-create",
    ),

    path(
        "agent/tickets/<str:ticket_number>/read/",
        AgentTicketMarkReadView.as_view(),
        name="agent-ticket-mark-read",
    ),

    path(
        "agent/tickets/<str:ticket_number>/close/",
        AgentTicketCloseView.as_view(),
        name="agent-ticket-close",
    ),

    path(
        "agent/tickets/<str:ticket_number>/reopen/",
        AgentTicketReopenView.as_view(),
        name="agent-ticket-reopen",
    ),

]