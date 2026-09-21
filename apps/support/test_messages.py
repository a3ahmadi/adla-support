from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.support.models import Ticket, TicketMessage


User = get_user_model()


class TicketMessageTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            password="testpass123",
        )

        self.client.force_authenticate(user=self.user)

        self.ticket = Ticket.objects.create(
            user=self.user,
            ticket_number="TCK-100",
            subject="تیکت تست",
            priority=Ticket.Priority.NORMAL,
            status=Ticket.Status.OPEN,
        )

        self.url = (
            f"/api/v1/support/tickets/"
            f"{self.ticket.ticket_number}/messages/"
        )

    def test_send_text_message(self):
        response = self.client.post(
            self.url,
            {
                "message_type": "text",
                "text": "پیام جدید",
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        message = TicketMessage.objects.get()

        self.assertEqual(message.ticket, self.ticket)
        self.assertEqual(message.sender, self.user)
        self.assertEqual(message.text, "پیام جدید")

        self.ticket.refresh_from_db()

        self.assertEqual(
            self.ticket.status,
            Ticket.Status.WAITING_FOR_RESPONSE,
        )

    def test_text_message_requires_text(self):
        response = self.client.post(
            self.url,
            {
                "message_type": "text",
                "text": "",
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_closed_ticket_cannot_receive_message(self):
        self.ticket.status = Ticket.Status.CLOSED
        self.ticket.save(update_fields=["status"])

        response = self.client.post(
            self.url,
            {
                "message_type": "text",
                "text": "پیام جدید",
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertEqual(
            TicketMessage.objects.count(),
            0,
        )

    def test_mark_ticket_messages_as_read(self):
        message = TicketMessage.objects.create(
            ticket=self.ticket,
            sender=self.user,
            message_type=TicketMessage.MessageType.TEXT,
            text="پیام تست",
        )

        response = self.client.post(
            f"/api/v1/support/tickets/"
            f"{self.ticket.ticket_number}/read/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            message.reads.filter(user=self.user).exists()
        )