import uuid
from django.db import transaction
from django.utils import timezone

from .models import Ticket, TicketMessage


def generate_ticket_number(ticket_id):
    return f"TCK-{ticket_id}"


@transaction.atomic
def create_ticket(
    *,
    user,
    subject,
    priority,
    message_type,
    text="",
    file=None,
):
    # Temporary unique value until we have the ticket ID.
    temporary_number = f"TMP-{uuid.uuid4().hex[:12]}"

    ticket = Ticket.objects.create(
        user=user,
        ticket_number=temporary_number,
        subject=subject,
        priority=priority,
        status=Ticket.Status.OPEN,
    )

    ticket.ticket_number = generate_ticket_number(ticket.id)
    ticket.save(update_fields=["ticket_number"])

    TicketMessage.objects.create(
        ticket=ticket,
        sender=user,
        message_type=message_type,
        text=text or "",
        file=file,
    )

    return ticket


@transaction.atomic
def send_message(
    *,
    ticket,
    sender,
    message_type,
    text="",
    file=None,
):
    if ticket.status == Ticket.Status.CLOSED:
        raise ValueError(
            "Closed tickets cannot receive new messages."
        )

    message = TicketMessage.objects.create(
        ticket=ticket,
        sender=sender,
        message_type=message_type,
        text=text or "",
        file=file,
    )

    if sender.is_staff:
        ticket.status = Ticket.Status.OPEN
    else:
        ticket.status = Ticket.Status.WAITING_FOR_RESPONSE

    ticket.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )

    return message


@transaction.atomic
def close_ticket(*, ticket, user):
    if ticket.status == Ticket.Status.CLOSED:
        return ticket

    ticket.status = Ticket.Status.CLOSED
    ticket.closed_at = timezone.now()

    ticket.save(
        update_fields=[
            "status",
            "closed_at",
            "updated_at",
        ]
    )

    return ticket


@transaction.atomic
def reopen_ticket(*, ticket, user):
    if ticket.status != Ticket.Status.CLOSED:
        return ticket

    ticket.status = Ticket.Status.OPEN
    ticket.closed_at = None

    ticket.save(
        update_fields=[
            "status",
            "closed_at",
            "updated_at",
        ]
    )

    return ticket


@transaction.atomic
def change_priority(*, ticket, priority):
    if priority not in Ticket.Priority.values:
        raise ValueError("Invalid ticket priority.")

    ticket.priority = priority

    ticket.save(
        update_fields=[
            "priority",
            "updated_at",
        ]
    )

    return ticket