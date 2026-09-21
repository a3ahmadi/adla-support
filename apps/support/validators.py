from pathlib import Path
from .models import TicketMessage
from django.core.exceptions import ValidationError


MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_VOICE_SIZE = 10 * 1024 * 1024


ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

ALLOWED_VOICE_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".ogg",
    ".webm",
    ".m4a",
}


def validate_image_file(file):
    if file.size > MAX_IMAGE_SIZE:
        raise ValidationError(
            "حجم تصویر نباید بیشتر از 5 مگابایت باشد."
        )

    extension = Path(file.name).suffix.lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            "فرمت تصویر مجاز نیست."
        )


def validate_voice_file(file):
    if file.size > MAX_VOICE_SIZE:
        raise ValidationError(
            "حجم فایل صوتی نباید بیشتر از 10 مگابایت باشد."
        )

    extension = Path(file.name).suffix.lower()

    if extension not in ALLOWED_VOICE_EXTENSIONS:
        raise ValidationError(
            "فرمت فایل صوتی مجاز نیست."
        )


def validate_message_content(
    *,
    message_type,
    text,
    file,
):
    text = (text or "").strip()

    if message_type == TicketMessage.MessageType.TEXT:
        if not text:
            raise ValidationError(
                "برای پیام متنی، متن الزامی است."
            )

        if file:
            raise ValidationError(
                "پیام متنی نباید فایل داشته باشد."
            )

    elif message_type == TicketMessage.MessageType.IMAGE:
        if not file:
            raise ValidationError(
                "برای پیام تصویری، فایل الزامی است."
            )

        validate_image_file(file)

    elif message_type == TicketMessage.MessageType.VOICE:
        if not file:
            raise ValidationError(
                "برای پیام صوتی، فایل الزامی است."
            )

        validate_voice_file(file)