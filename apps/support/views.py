from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from .pagination import TicketPagination, MessagePagination

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Ticket, TicketMessage, MessageRead
from .permissions import IsTicketOwner, IsSupportAgent
from .serializers import (
    TicketCreateSerializer,
    TicketDetailSerializer,
    TicketListSerializer,
    TicketMessageSerializer,
)
from .services import (
    change_priority,
    close_ticket,
    reopen_ticket,
    send_message,
)


class TicketListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tickets = (
            Ticket.objects
            .filter(user=request.user)
            .annotate(
                unread_count=Count(
                    "messages",
                    filter=~Q(
                        messages__reads__user=request.user
                    ),
                    distinct=True,
                )
            )
            .order_by("-updated_at")
        )

        status_filter = request.query_params.get("status")
        search = request.query_params.get("search")

        if status_filter:
            if status_filter not in dict(Ticket.Status.choices):
                return Response(
                    {"detail": "وضعیت نامعتبر است."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            tickets = tickets.filter(status=status_filter)

        if search:
            tickets = tickets.filter(
                Q(ticket_number__icontains=search)
                | Q(subject__icontains=search)
            )

        paginator = TicketPagination()

        page = paginator.paginate_queryset(
            tickets,
            request,
        )

        serializer = TicketListSerializer(
            page,
            many=True,
            context={"request": request},
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def post(self, request):
        serializer = TicketCreateSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        ticket = serializer.save()

        return Response(
            TicketDetailSerializer(
                ticket,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class TicketSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tickets = Ticket.objects.filter(
            user=request.user
        )

        data = {
            "open": tickets.filter(
                status=Ticket.Status.OPEN
            ).count(),

            "waiting_for_response": tickets.filter(
                status=Ticket.Status.WAITING_FOR_RESPONSE
            ).count(),

            "closed": tickets.filter(
                status=Ticket.Status.CLOSED
            ).count(),
        }

        return Response(data)


class TicketDetailView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsTicketOwner,
    ]

    def get_object(self, request, ticket_number):
        ticket = get_object_or_404(
            Ticket,
            ticket_number=ticket_number,
            user=request.user,
        )

        self.check_object_permissions(request, ticket)

        return ticket

    def get(self, request, ticket_number):
        ticket = self.get_object(
            request,
            ticket_number,
        )

        serializer = TicketDetailSerializer(
            ticket,
            context={"request": request},
        )

        return Response(serializer.data)


class TicketMessageListCreateView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsTicketOwner,
    ]

    def get(self, request, ticket_number):
        ticket = get_object_or_404(
            Ticket,
            ticket_number=ticket_number,
            user=request.user,
        )

        self.check_object_permissions(
            request,
            ticket,
        )

        messages = (
            TicketMessage.objects
            .filter(ticket=ticket)
            .select_related("sender")
            .prefetch_related("reads")
            .order_by("-created_at")
        )

        paginator = MessagePagination()

        page = paginator.paginate_queryset(
            messages,
            request,
        )

        serializer = TicketMessageSerializer(
            page,
            many=True,
            context={"request": request},
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def post(self, request, ticket_number):
        ticket = get_object_or_404(
            Ticket,
            ticket_number=ticket_number,
            user=request.user,
        )

        self.check_object_permissions(request, ticket)

        if ticket.status == Ticket.Status.CLOSED:
            return Response(
                {
                    "detail": "این تیکت بسته شده است."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TicketMessageSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        message = send_message(
            ticket=ticket,
            sender=request.user,
            message_type=serializer.validated_data[
                "message_type"
            ],
            text=serializer.validated_data.get(
                "text",
                "",
            ),
            file=serializer.validated_data.get(
                "file"
            ),
        )

        return Response(
            TicketMessageSerializer(
                message,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class TicketMarkReadView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsTicketOwner,
    ]

    def post(self, request, ticket_number):
        ticket = get_object_or_404(
            Ticket,
            ticket_number=ticket_number,
            user=request.user,
        )

        self.check_object_permissions(request, ticket)

        unread_messages = (
            ticket.messages
            .exclude(reads__user=request.user)
        )

        MessageRead.objects.bulk_create(
            [
                MessageRead(
                    message=message,
                    user=request.user,
                )
                for message in unread_messages
            ],
            ignore_conflicts=True,
        )

        return Response({
            "detail": "پیام‌ها خوانده شدند."
        })


class TicketCloseView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsTicketOwner,
    ]

    def post(self, request, ticket_number):
        ticket = get_object_or_404(
            Ticket,
            ticket_number=ticket_number,
            user=request.user,
        )

        self.check_object_permissions(request, ticket)

        ticket = close_ticket(
            ticket=ticket,
            user=request.user,
        )

        return Response(
            TicketDetailSerializer(
                ticket,
                context={"request": request},
            ).data
        )


class TicketReopenView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsTicketOwner,
    ]

    def post(self, request, ticket_number):
        ticket = get_object_or_404(
            Ticket,
            ticket_number=ticket_number,
            user=request.user,
        )

        self.check_object_permissions(request, ticket)

        ticket = reopen_ticket(
            ticket=ticket,
            user=request.user,
        )

        return Response(
            TicketDetailSerializer(
                ticket,
                context={"request": request},
            ).data
        )


class AgentTicketListView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSupportAgent,
    ]

    def get(self, request):
        tickets = (
            Ticket.objects
            .select_related("user")
            .annotate(
                unread_count=Count(
                    "messages",
                    filter=~Q(
                        messages__reads__user=request.user
                    ),
                    distinct=True,
                )
            )
            .order_by("-updated_at")
        )

        status_filter = request.query_params.get("status")
        priority_filter = request.query_params.get("priority")
        search = request.query_params.get("search")

        if status_filter:
            if status_filter not in dict(Ticket.Status.choices):
                return Response(
                    {"detail": "وضعیت نامعتبر است."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            tickets = tickets.filter(
                status=status_filter
            )

        if priority_filter:
            if priority_filter not in dict(Ticket.Priority.choices):
                return Response(
                    {"detail": "اولویت نامعتبر است."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            tickets = tickets.filter(
                priority=priority_filter
            )

        if search:
            tickets = tickets.filter(
                Q(ticket_number__icontains=search)
                | Q(subject__icontains=search)
                | Q(user__phone_number__icontains=search)
            )

        paginator = TicketPagination()

        page = paginator.paginate_queryset(
            tickets,
            request,
        )

        serializer = TicketListSerializer(
            page,
            many=True,
            context={"request": request},
        )

        return paginator.get_paginated_response(
            serializer.data
        )


class AgentTicketDetailView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSupportAgent,
    ]

    def get(self, request, ticket_number):
        ticket = get_object_or_404(
            Ticket.objects.prefetch_related(
                "messages__reads",
                "messages__sender",
            ),
            ticket_number=ticket_number,
        )

        serializer = TicketDetailSerializer(
            ticket,
            context={"request": request},
        )

        return Response(serializer.data)


class AgentTicketMessageListCreateView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSupportAgent,
    ]

    def get(self, request, ticket_number):
        ticket = get_object_or_404(
            Ticket,
            ticket_number=ticket_number,
        )

        messages = (
            TicketMessage.objects
            .filter(ticket=ticket)
            .select_related("sender")
            .prefetch_related("reads")
            .order_by("-created_at")
        )

        paginator = MessagePagination()

        page = paginator.paginate_queryset(
            messages,
            request,
        )

        serializer = TicketMessageSerializer(
            page,
            many=True,
            context={"request": request},
        )

        return paginator.get_paginated_response(
            serializer.data
        )

    def post(self, request, ticket_number):
        ticket = get_object_or_404(
            Ticket,
            ticket_number=ticket_number,
        )

        if ticket.status == Ticket.Status.CLOSED:
            return Response(
                {
                    "detail": "این تیکت بسته شده است."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TicketMessageSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(raise_exception=True)

        message = send_message(
            ticket=ticket,
            sender=request.user,
            message_type=serializer.validated_data[
                "message_type"
            ],
            text=serializer.validated_data.get(
                "text",
                "",
            ),
            file=serializer.validated_data.get(
                "file"
            ),
        )

        return Response(
            TicketMessageSerializer(
                message,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )


class AgentTicketMarkReadView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSupportAgent,
    ]

    def post(self, request, ticket_number):
        ticket = get_object_or_404(
            Ticket,
            ticket_number=ticket_number,
        )

        unread_messages = (
            ticket.messages
            .exclude(reads__user=request.user)
        )

        MessageRead.objects.bulk_create(
            [
                MessageRead(
                    message=message,
                    user=request.user,
                )
                for message in unread_messages
            ],
            ignore_conflicts=True,
        )

        return Response({
            "detail": "پیام‌ها خوانده شدند."
        })


class AgentTicketCloseView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSupportAgent,
    ]

    def post(self, request, ticket_number):
        ticket = get_object_or_404(
            Ticket,
            ticket_number=ticket_number,
        )

        ticket = close_ticket(
            ticket=ticket,
            user=request.user,
        )

        return Response(
            TicketDetailSerializer(
                ticket,
                context={"request": request},
            ).data
        )


class AgentTicketReopenView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSupportAgent,
    ]

    def post(self, request, ticket_number):
        ticket = get_object_or_404(
            Ticket,
            ticket_number=ticket_number,
        )

        ticket = reopen_ticket(
            ticket=ticket,
            user=request.user,
        )

        return Response(
            TicketDetailSerializer(
                ticket,
                context={"request": request},
            ).data
        )