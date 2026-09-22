from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Ticket, TicketMessage


User = get_user_model()


class TicketMessageListTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="customer"
        )

        self.other_user = User.objects.create_user(
            username="other"
        )

        self.ticket = Ticket.objects.create(
            user=self.user,
            ticket_number="TCK-100",
            subject="Test Ticket",
            priority=Ticket.Priority.NORMAL,
            status=Ticket.Status.OPEN,
        )

        for i in range(25):
            TicketMessage.objects.create(
                ticket=self.ticket,
                sender=self.user,
                message_type=TicketMessage.MessageType.TEXT,
                text=f"Message {i}",
            )

    def test_customer_can_list_ticket_messages(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            f"/api/v1/support/tickets/"
            f"{self.ticket.ticket_number}/messages/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 25)
        self.assertEqual(
            len(response.data["results"]),
            20,
        )

    def test_customer_can_paginate_messages(self):
        self.client.force_authenticate(
            user=self.user
        )

        response = self.client.get(
            f"/api/v1/support/tickets/"
            f"{self.ticket.ticket_number}/messages/?page=2"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.data["results"]),
            5,
        )

    def test_other_user_cannot_list_messages(self):
        self.client.force_authenticate(
            user=self.other_user
        )

        response = self.client.get(
            f"/api/v1/support/tickets/"
            f"{self.ticket.ticket_number}/messages/"
        )

        self.assertEqual(response.status_code, 404)