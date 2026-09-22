from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Ticket, TicketMessage, MessageRead


User = get_user_model()


class AgentTicketTests(APITestCase):

    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer"
        )

        self.agent = User.objects.create_user(
            username="agent"
        )
        self.agent.is_staff = True
        self.agent.save()

        self.ticket = Ticket.objects.create(
            user=self.customer,
            ticket_number="TCK-100",
            subject="Test Ticket",
            priority=Ticket.Priority.NORMAL,
            status=Ticket.Status.OPEN,
        )

        self.message = TicketMessage.objects.create(
            ticket=self.ticket,
            sender=self.customer,
            message_type=TicketMessage.MessageType.TEXT,
            text="پیام تست",
        )

        self.client.force_authenticate(
            user=self.agent
        )

    def test_agent_can_list_tickets(self):
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
        response = self.client.get(
            f"/api/v1/support/agent/tickets/"
            f"{self.ticket.ticket_number}/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["ticket_number"],
            "TCK-100",
        )

    def test_agent_can_list_ticket_messages(self):
        response = self.client.get(
            f"/api/v1/support/agent/tickets/"
            f"{self.ticket.ticket_number}/messages/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_agent_can_send_message(self):
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