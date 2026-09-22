from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Ticket, TicketMessage, MessageRead


User = get_user_model()


class AgentTicketTests(APITestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            phone_number="09120000001",
        )

        self.agent = User.objects.create_user(
            phone_number="09120000002",
        )
        self.agent.is_staff = True
        self.agent.save()

        self.other_user = User.objects.create_user(
            phone_number="09120000003",
        )

        self.ticket = Ticket.objects.create(
            user=self.customer,
            ticket_number="TCK-253",
            subject="مشکل پرداخت",
            priority=Ticket.Priority.NORMAL,
            status=Ticket.Status.OPEN,
        )

        self.message = TicketMessage.objects.create(
            ticket=self.ticket,
            sender=self.customer,
            message_type=TicketMessage.MessageType.TEXT,
            text="پرداخت من انجام نشده",
        )

    def test_agent_can_list_tickets(self):
        self.client.force_authenticate(
            user=self.agent
        )

        response = self.client.get(
            "/api/v1/support/agent/tickets/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_customer_cannot_access_agent_list(self):
        self.client.force_authenticate(
            user=self.customer
        )

        response = self.client.get(
            "/api/v1/support/agent/tickets/"
        )

        self.assertEqual(response.status_code, 403)

    def test_agent_can_view_ticket(self):
        self.client.force_authenticate(
            user=self.agent
        )

        response = self.client.get(
            f"/api/v1/support/agent/tickets/"
            f"{self.ticket.ticket_number}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["ticket_number"],
            "TCK-253",
        )

    def test_agent_can_send_message(self):
        self.client.force_authenticate(
            user=self.agent
        )

        response = self.client.post(
            f"/api/v1/support/agent/tickets/"
            f"{self.ticket.ticket_number}/messages/",
            {
                "message_type": "text",
                "text": "در حال بررسی درخواست شما هستیم.",
            },
        )

        self.assertEqual(response.status_code, 201)

        self.ticket.refresh_from_db()

        self.assertEqual(
            self.ticket.status,
            Ticket.Status.OPEN,
        )

        self.assertEqual(
            TicketMessage.objects.filter(
                ticket=self.ticket
            ).count(),
            2,
        )

    def test_customer_cannot_send_through_agent_endpoint(self):
        self.client.force_authenticate(
            user=self.customer
        )

        response = self.client.post(
            f"/api/v1/support/agent/tickets/"
            f"{self.ticket.ticket_number}/messages/",
            {
                "message_type": "text",
                "text": "پیام غیرمجاز",
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_agent_can_mark_messages_as_read(self):
        self.client.force_authenticate(
            user=self.agent
        )

        response = self.client.post(
            f"/api/v1/support/agent/tickets/"
            f"{self.ticket.ticket_number}/read/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            MessageRead.objects.filter(
                message=self.message,
                user=self.agent,
            ).exists()
        )