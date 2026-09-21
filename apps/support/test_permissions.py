from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.support.models import Ticket


User = get_user_model()


class TicketPermissionTests(APITestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1",
            password="testpass123",
        )

        self.user2 = User.objects.create_user(
            username="user2",
            password="testpass123",
        )

        self.ticket = Ticket.objects.create(
            user=self.user1,
            ticket_number="TCK-100",
            subject="تیکت خصوصی",
            priority=Ticket.Priority.NORMAL,
            status=Ticket.Status.OPEN,
        )

    def test_user_cannot_access_other_users_ticket(self):
        self.client.force_authenticate(user=self.user2)

        response = self.client.get(
            f"/api/v1/support/tickets/"
            f"{self.ticket.ticket_number}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_user_cannot_send_message_to_other_users_ticket(self):
        self.client.force_authenticate(user=self.user2)

        response = self.client.post(
            f"/api/v1/support/tickets/"
            f"{self.ticket.ticket_number}/messages/",
            {
                "message_type": "text",
                "text": "پیام غیرمجاز",
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_user_cannot_close_other_users_ticket(self):
        self.client.force_authenticate(user=self.user2)

        response = self.client.post(
            f"/api/v1/support/tickets/"
            f"{self.ticket.ticket_number}/close/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )