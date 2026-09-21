from django.db import models
from django.conf import settings

class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "باز"
        WAITING_FOR_RESPONSE = "waiting_for_response", "در انتظار پاسخ"
        CLOSED = "closed", "بسته شده"

    class Priority(models.TextChoices):
        HIGH = "high", "اولویت بالا"
        NORMAL = "normal", "اولویت عادی"
        LOW = "low", "اولویت پایین"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets",
    )


    ticket_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    subject = models.CharField(max_length=200)

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.OPEN,
    )

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "support_tickets"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["status", "updated_at"]),
            models.Index(fields=["priority", "updated_at"]),
        ]
        verbose_name = "تیکت"
        verbose_name_plural = "تیکت‌ها"

    def __str__(self):
        return self.ticket_number


class TicketMessage(models.Model):
    class MessageType(models.TextChoices):
        TEXT = "text", "متن"
        IMAGE = "image", "تصویر"
        VOICE = "voice", "صوت"

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_messages",
    )

    message_type = models.CharField(
        max_length=10,
        choices=MessageType.choices,
    )

    text = models.TextField(blank=True)

    file = models.FileField(
        upload_to="support/messages/%Y/%m/",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "support_messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["ticket", "created_at"]),
            models.Index(fields=["sender", "created_at"]),
        ]
        verbose_name = "پیام پشتیبانی"
        verbose_name_plural = "پیام‌های پشتیبانی"

    def __str__(self):
        return f"{self.ticket.ticket_number} - {self.id}"


class MessageRead(models.Model):
    message = models.ForeignKey(
        TicketMessage,
        on_delete=models.CASCADE,
        related_name="reads",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_message_reads",
    )

    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "support_message_reads"
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user"],
                name="unique_message_read_by_user",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "read_at"]),
        ]
        verbose_name = "خواندن پیام"
        verbose_name_plural = "خواندن پیام‌ها"

    def __str__(self):
        return f"{self.user_id} read message {self.message_id}"