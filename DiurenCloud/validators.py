from django.core.exceptions import ValidationError
from django.utils.translation import gettext, gettext_lazy as _

ILLEGAL_CHARACTERS = {'/', '\\', '*', '?', '!', '<', '>', '|'}


def validate_object_name_special_characters(obj_name: str):
    chars = ILLEGAL_CHARACTERS & set(obj_name)
    if chars:
        raise ValidationError(_('文件名中不能包含 %s') % chars)
