from rest_framework import serializers
from .models import Ticket, TicketMessage, MessageRead

class TicketListSerializer(serializers.ModelSerializer):
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "ticket_number",
            "subject",
            "status",
            "priority",
            "unread_count",
            "created_at",
            "updated_at",
        ]

    def get_unread_count(self, obj):
        user = self.context["request"].user

        return obj.messages.exclude(
            reads__user=user
        ).count()


class TicketMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = TicketMessage
        fields = [
            "id",
            "sender",
            "sender_name",
            "message_type",
            "text",
            "file",
            "is_read",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "sender",
            "sender_name",
            "is_read",
            "created_at",
        ]

    def get_sender_name(self, obj):
        user = obj.sender

        return getattr(
            user,
            "name",
            None,
        ) or user.get_username()

    def get_is_read(self, obj):
        user = self.context["request"].user

        return obj.reads.filter(
            user=user
        ).exists()

    def validate(self, attrs):
        message_type = attrs.get("message_type")
        text = attrs.get("text", "").strip()
        file = attrs.get("file")

        if message_type == TicketMessage.MessageType.TEXT:
            if not text:
                raise serializers.ValidationError({
                    "text": "متن پیام الزامی است."
                })

            if file:
                raise serializers.ValidationError({
                    "file": "پیام متنی نباید فایل داشته باشد."
                })

        elif message_type in [
            TicketMessage.MessageType.IMAGE,
            TicketMessage.MessageType.VOICE,
        ]:
            if not file:
                raise serializers.ValidationError({
                    "file": "برای این نوع پیام ارسال فایل الزامی است."
                })

        return attrs


class TicketDetailSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "ticket_number",
            "subject",
            "status",
            "priority",
            "messages",
            "created_at",
            "updated_at",
            "closed_at",
        ]
        read_only_fields = [
            "id",
            "ticket_number",
            "status",
            "created_at",
            "updated_at",
            "closed_at",
        ]


class TicketCreateSerializer(serializers.ModelSerializer):
    message_type = serializers.ChoiceField(
        choices=TicketMessage.MessageType.choices
    )

    text = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    file = serializers.FileField(
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Ticket
        fields = [
            "subject",
            "priority",
            "message_type",
            "text",
            "file",
        ]

    def validate(self, attrs):
        message_type = attrs.get("message_type")
        text = attrs.get("text", "").strip()
        file = attrs.get("file")

        if message_type == TicketMessage.MessageType.TEXT:
            if not text:
                raise serializers.ValidationError({
                    "text": "متن پیام الزامی است."
                })

            if file:
                raise serializers.ValidationError({
                    "file": "پیام متنی نباید فایل داشته باشد."
                })

        elif message_type in [
            TicketMessage.MessageType.IMAGE,
            TicketMessage.MessageType.VOICE,
        ]:
            if not file:
                raise serializers.ValidationError({
                    "file": "برای این نوع پیام ارسال فایل الزامی است."
                })

        return attrs

    def create(self, validated_data):
        from .services import create_ticket

        return create_ticket(
            user=self.context["request"].user,
            **validated_data,
        )