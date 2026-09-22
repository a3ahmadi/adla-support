from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.support.models import Ticket


User = get_user_model()


class TicketTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            password="testpass123",
        )

        self.client.force_authenticate(user=self.user)

        self.url = "/api/v1/support/tickets/"

    def test_create_ticket(self):
        response = self.client.post(
            self.url,
            {
                "subject": "مشکل تست",
                "priority": "normal",
                "message_type": "text",
                "text": "این یک پیام تست است.",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        ticket = Ticket.objects.get()

        self.assertEqual(ticket.user, self.user)
        self.assertEqual(ticket.ticket_number, f"TCK-{ticket.id}")
        self.assertEqual(ticket.subject, "مشکل تست")
        self.assertEqual(ticket.status, Ticket.Status.OPEN)

    def test_ticket_summary(self):
        Ticket.objects.create(
            user=self.user,
            ticket_number="TCK-100",
            subject="تیکت تست",
            priority=Ticket.Priority.NORMAL,
            status=Ticket.Status.OPEN,
        )

        response = self.client.get(
            "/api/v1/support/tickets/summary/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["open"], 1)
        self.assertEqual(response.data["waiting_for_response"], 0)
        self.assertEqual(response.data["closed"], 0)

    def test_ticket_filter_by_status(self):
        Ticket.objects.create(
            user=self.user,
            ticket_number="TCK-100",
            subject="باز",
            priority=Ticket.Priority.NORMAL,
            status=Ticket.Status.OPEN,
        )

        Ticket.objects.create(
            user=self.user,
            ticket_number="TCK-101",
            subject="بسته",
            priority=Ticket.Priority.NORMAL,
            status=Ticket.Status.CLOSED,
        )

        response = self.client.get(
            self.url,
            {"status": "closed"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["status"],
            "closed",
        )

    def test_ticket_search(self):
        Ticket.objects.create(
            user=self.user,
            ticket_number="TCK-100",
            subject="مشکل پرداخت",
            priority=Ticket.Priority.NORMAL,
            status=Ticket.Status.OPEN,
        )

        Ticket.objects.create(
            user=self.user,
            ticket_number="TCK-101",
            subject="مشکل حساب",
            priority=Ticket.Priority.NORMAL,
            status=Ticket.Status.OPEN,
        )

        response = self.client.get(
            self.url,
            {"search": "پرداخت"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["subject"],
            "مشکل پرداخت",
        )


def test_ticket_detail_does_not_include_messages(self):
    self.client.force_authenticate(user=self.user)

    response = self.client.get(
        f"/support/tickets/{self.ticket.ticket_number}/"
    )

    self.assertEqual(response.status_code, 200)
    self.assertNotIn("messages", response.data)