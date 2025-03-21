#!/usr/bin/env python
#
# A library that provides a Python interface to the Telegram Bot API
# Copyright (C) 2015-2021
# Leandro Toledo de Souza <devs@python-telegram-bot.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
"""This module contains helper functions."""

import datetime as dtm  # dtm = "DateTime Module"
import re
import signal
import time

from collections import defaultdict
from html import escape
from numbers import Number
from pathlib import Path

from typing import (
    TYPE_CHECKING,
    Any,
    DefaultDict,
    Dict,
    Optional,
    Tuple,
    Union,
    Type,
    cast,
    IO,
)

import pytz  # pylint: disable=E0401

from telegram.utils.types import JSONDict, FileInput

if TYPE_CHECKING:
    from telegram import Message, Update, TelegramObject, InputFile

try:
    import ujson as json
except ImportError:
    import json  # type: ignore[no-redef]


# From https://stackoverflow.com/questions/2549939/get-signal-names-from-numbers-in-python
_signames = {
    v: k
    for k, v in reversed(sorted(vars(signal).items()))
    if k.startswith('SIG') and not k.startswith('SIG_')
}


def get_signal_name(signum: int) -> str:
    """Returns the signal name of the given signal number."""
    return _signames[signum]


def is_local_file(obj: Optional[Union[str, Path]]) -> bool:
    """
    Checks if a given string is a file on local system.

    Args:
        obj (:obj:`str`): The string to check.
    """
    if obj is None:
        return False

    path = Path(obj)
    try:
        return path.is_file()
    except Exception:
        return False


def parse_file_input(
    file_input: Union[FileInput, 'TelegramObject'],
    tg_type: Type['TelegramObject'] = None,
    attach: bool = None,
    filename: str = None,
) -> Union[str, 'InputFile', Any]:
    """
    Parses input for sending files:

    * For string input, if the input is an absolute path of a local file,
      adds the ``file://`` prefix. If the input is a relative path of a local file, computes the
      absolute path and adds the ``file://`` prefix. Returns the input unchanged, otherwise.
    * :class:`pathlib.Path` objects are treated the same way as strings.
    * For IO and bytes input, returns an :class:`telegram.InputFile`.
    * If :attr:`tg_type` is specified and the input is of that type, returns the ``file_id``
      attribute.

    Args:
        file_input (:obj:`str` | :obj:`bytes` | `filelike object` | Telegram media object): The
            input to parse.
        tg_type (:obj:`type`, optional): The Telegram media type the input can be. E.g.
            :class:`telegram.Animation`.
        attach (:obj:`bool`, optional): Whether this file should be send as one file or is part of
            a collection of files. Only relevant in case an :class:`telegram.InputFile` is
            returned.
        filename (:obj:`str`, optional): The filename. Only relevant in case an
            :class:`telegram.InputFile` is returned.

    Returns:
        :obj:`str` | :class:`telegram.InputFile` | :obj:`object`: The parsed input or the untouched
            :attr:`file_input`, in case it's no valid file input.
    """
    # Importing on file-level yields cyclic Import Errors
    from telegram import InputFile  # pylint: disable=C0415

    if isinstance(file_input, str) and file_input.startswith('file://'):
        return file_input
    if isinstance(file_input, (str, Path)):
        return (
            Path(file_input).absolute().as_uri()
            if is_local_file(file_input)
            else file_input
        )

    if isinstance(file_input, bytes):
        return InputFile(file_input, attach=attach, filename=filename)
    if InputFile.is_file(file_input):
        file_input = cast(IO, file_input)
        return InputFile(file_input, attach=attach, filename=filename)
    if tg_type and isinstance(file_input, tg_type):
        return file_input.file_id  # type: ignore[attr-defined]
    return file_input


def escape_markdown(text: str, version: int = 1, entity_type: str = None) -> str:
    """
    Helper function to escape telegram markup symbols.

    Args:
        text (:obj:`str`): The text.
        version (:obj:`int` | :obj:`str`): Use to specify the version of telegrams Markdown.
            Either ``1`` or ``2``. Defaults to ``1``.
        entity_type (:obj:`str`, optional): For the entity types ``PRE``, ``CODE`` and the link
            part of ``TEXT_LINKS``, only certain characters need to be escaped in ``MarkdownV2``.
            See the official API documentation for details. Only valid in combination with
            ``version=2``, will be ignored else.
    """
    if version == 1:
        escape_chars = r'_*`['
    elif version == 2:
        if entity_type in {'pre', 'code'}:
            escape_chars = r'\`'
        elif entity_type == 'text_link':
            escape_chars = r'\)'
        else:
            escape_chars = r'_*[]()~`>#+-=|{}.!'
    else:
        raise ValueError('Markdown version must be either 1 or 2!')

    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


# -------- date/time related helpers --------
def _datetime_to_float_timestamp(dt_obj: dtm.datetime) -> float:
    """
    Converts a datetime object to a float timestamp (with sub-second precision).
    If the datetime object is timezone-naive, it is assumed to be in UTC.
    """
    if dt_obj.tzinfo is None:
        dt_obj = dt_obj.replace(tzinfo=dtm.timezone.utc)
    return dt_obj.timestamp()


def to_float_timestamp(
    time_object: Union[int, float, dtm.timedelta, dtm.datetime, dtm.time],
    reference_timestamp: float = None,
    tzinfo: pytz.BaseTzInfo = None,
) -> float:
    """
    Converts a given time object to a float POSIX timestamp.
    Used to convert different time specifications to a common format. The time object
    can be relative (i.e. indicate a time increment, or a time of day) or absolute.
    Any objects from the :class:`datetime` module that are timezone-naive will be assumed
    to be in UTC, if ``bot`` is not passed or ``bot.defaults`` is :obj:`None`.

    Args:
        time_object (int | float | datetime.timedelta | datetime.datetime | datetime.time):
            Time value to convert. The semantics of this parameter will depend on its type:

            * :obj:`int` or :obj:`float` will be interpreted as "seconds from ``reference_t``"
            * :obj:`datetime.timedelta` will be interpreted as
              "time increment from ``reference_t``"
            * :obj:`datetime.datetime` will be interpreted as an absolute date/time value
            * :obj:`datetime.time` will be interpreted as a specific time of day

        reference_timestamp (float, optional): POSIX timestamp that indicates the absolute time
            from which relative calculations are to be performed (e.g. when ``t`` is given as an
            :obj:`int`, indicating "seconds from ``reference_t``"). Defaults to now (the time at
            which this function is called).

            If ``t`` is given as an absolute representation of date & time (i.e. a
            ``datetime.datetime`` object), ``reference_timestamp`` is not relevant and so its
            value should be :obj:`None`. If this is not the case, a ``ValueError`` will be raised.
        tzinfo (:obj:`datetime.tzinfo`, optional): If ``t`` is a naive object from the
            :class:`datetime` module, it will be interpreted as this timezone. Defaults to
            ``pytz.utc``.

    Returns:
        (float | None) The return value depends on the type of argument ``t``. If ``t`` is
            given as a time increment (i.e. as a obj:`int`, :obj:`float` or
            :obj:`datetime.timedelta`), then the return value will be ``reference_t`` + ``t``.

            Else if it is given as an absolute date/time value (i.e. a :obj:`datetime.datetime`
            object), the equivalent value as a POSIX timestamp will be returned.

            Finally, if it is a time of the day without date (i.e. a :obj:`datetime.time`
            object), the return value is the nearest future occurrence of that time of day.

    Raises:
        TypeError: if `t`'s type is not one of those described above
    """

    if reference_timestamp is None:
        reference_timestamp = time.time()
    elif isinstance(time_object, dtm.datetime):
        raise ValueError('t is an (absolute) datetime while reference_timestamp is not None')

    if isinstance(time_object, dtm.timedelta):
        return reference_timestamp + time_object.total_seconds()
    if isinstance(time_object, (int, float)):
        return reference_timestamp + time_object

    if tzinfo is None:
        tzinfo = pytz.utc

    if isinstance(time_object, dtm.time):
        reference_dt = dtm.datetime.fromtimestamp(
            reference_timestamp, tz=time_object.tzinfo or tzinfo
        )
        reference_date = reference_dt.date()
        reference_time = reference_dt.timetz()

        aware_datetime = dtm.datetime.combine(reference_date, time_object)
        if aware_datetime.tzinfo is None:
            aware_datetime = tzinfo.localize(aware_datetime)

        # if the time of day has passed today, use tomorrow
        if reference_time > aware_datetime.timetz():
            aware_datetime += dtm.timedelta(days=1)
        return _datetime_to_float_timestamp(aware_datetime)
    if isinstance(time_object, dtm.datetime):
        if time_object.tzinfo is None:
            time_object = tzinfo.localize(time_object)
        return _datetime_to_float_timestamp(time_object)
    if isinstance(time_object, Number):
        return reference_timestamp + time_object

    raise TypeError(f'Unable to convert {type(time_object).__name__} object to timestamp')


def to_timestamp(
    dt_obj: Union[int, float, dtm.timedelta, dtm.datetime, dtm.time, None],
    reference_timestamp: float = None,
    tzinfo: pytz.BaseTzInfo = None,
) -> Optional[int]:
    """
    Wrapper over :func:`to_float_timestamp` which returns an integer (the float value truncated
    down to the nearest integer).

    See the documentation for :func:`to_float_timestamp` for more details.
    """
    return (
        int(to_float_timestamp(dt_obj, reference_timestamp, tzinfo))
        if dt_obj is not None
        else None
    )


def from_timestamp(
    unixtime: Optional[int], tzinfo: dtm.tzinfo = pytz.utc
) -> Optional[dtm.datetime]:
    """
    Converts an (integer) unix timestamp to a timezone aware datetime object.
    :obj:`None`s are left alone (i.e. ``from_timestamp(None)`` is :obj:`None`).

    Args:
        unixtime (int): Integer POSIX timestamp.
        tzinfo (:obj:`datetime.tzinfo`, optional): The timezone, the timestamp is to be converted
            to. Defaults to UTC.

    Returns:
        timezone aware equivalent :obj:`datetime.datetime` value if ``timestamp`` is not
        :obj:`None`; else :obj:`None`
    """
    if unixtime is None:
        return None

    if tzinfo is not None:
        return dtm.datetime.fromtimestamp(unixtime, tz=tzinfo)
    return dtm.datetime.utcfromtimestamp(unixtime)


# -------- end --------


def mention_html(user_id: Union[int, str], name: str) -> str:
    """
    Args:
        user_id (:obj:`int`) The user's id which you want to mention.
        name (:obj:`str`) The name the mention is showing.

    Returns:
        :obj:`str`: The inline mention for the user as html.
    """
    return f'<a href="tg://user?id={user_id}">{escape(name)}</a>'


def mention_markdown(user_id: Union[int, str], name: str, version: int = 1) -> str:
    """
    Args:
        user_id (:obj:`int`) The user's id which you want to mention.
        name (:obj:`str`) The name the mention is showing.
        version (:obj:`int` | :obj:`str`): Use to specify the version of telegrams Markdown.
            Either ``1`` or ``2``. Defaults to ``1``

    Returns:
        :obj:`str`: The inline mention for the user as markdown.
    """
    return f'[{escape_markdown(name, version=version)}](tg://user?id={user_id})'


def effective_message_type(entity: Union['Message', 'Update']) -> Optional[str]:
    """
    Extracts the type of message as a string identifier from a :class:`telegram.Message` or a
    :class:`telegram.Update`.

    Args:
        entity (:obj:`Update` | :obj:`Message`) The ``update`` or ``message`` to extract from

    Returns:
        str: One of ``Message.MESSAGE_TYPES``

    """

    # Importing on file-level yields cyclic Import Errors
    from telegram import Message, Update  # pylint: disable=C0415

    if isinstance(entity, Message):
        message = entity
    elif isinstance(entity, Update):
        message = entity.effective_message  # type: ignore[assignment]
    else:
        raise TypeError(f"entity is not Message or Update (got: {type(entity)})")

    return next(
        (i for i in Message.MESSAGE_TYPES if getattr(message, i, None)), None
    )


def create_deep_linked_url(bot_username: str, payload: str = None, group: bool = False) -> str:
    """
    Creates a deep-linked URL for this ``bot_username`` with the specified ``payload``.
    See  https://core.telegram.org/bots#deep-linking to learn more.

    The ``payload`` may consist of the following characters: ``A-Z, a-z, 0-9, _, -``

    Note:
        Works well in conjunction with
        ``CommandHandler("start", callback, filters = Filters.regex('payload'))``

    Examples:
        ``create_deep_linked_url(bot.get_me().username, "some-params")``

    Args:
        bot_username (:obj:`str`): The username to link to
        payload (:obj:`str`, optional): Parameters to encode in the created URL
        group (:obj:`bool`, optional): If :obj:`True` the user is prompted to select a group to
            add the bot to. If :obj:`False`, opens a one-on-one conversation with the bot.
            Defaults to :obj:`False`.

    Returns:
        :obj:`str`: An URL to start the bot with specific parameters
    """
    if bot_username is None or len(bot_username) <= 3:
        raise ValueError("You must provide a valid bot_username.")

    base_url = f'https://t.me/{bot_username}'
    if not payload:
        return base_url

    if len(payload) > 64:
        raise ValueError("The deep-linking payload must not exceed 64 characters.")

    if not re.match(r'^[A-Za-z0-9_-]+$', payload):
        raise ValueError(
            "Only the following characters are allowed for deep-linked "
            "URLs: A-Z, a-z, 0-9, _ and -"
        )

    key = 'startgroup' if group else 'start'
    return f'{base_url}?{key}={payload}'


def encode_conversations_to_json(conversations: Dict[str, Dict[Tuple, Any]]) -> str:
    """Helper method to encode a conversations dict (that uses tuples as keys) to a
    JSON-serializable way. Use :attr:`_decode_conversations_from_json` to decode.

    Args:
        conversations (:obj:`dict`): The conversations dict to transform to JSON.

    Returns:
        :obj:`str`: The JSON-serialized conversations dict
    """
    tmp: Dict[str, JSONDict] = {
        handler: {json.dumps(key): state for key, state in states.items()}
        for handler, states in conversations.items()
    }

    return json.dumps(tmp)


def decode_conversations_from_json(json_string: str) -> Dict[str, Dict[Tuple, Any]]:
    """Helper method to decode a conversations dict (that uses tuples as keys) from a
    JSON-string created with :attr:`_encode_conversations_to_json`.

    Args:
        json_string (:obj:`str`): The conversations dict as JSON string.

    Returns:
        :obj:`dict`: The conversations dict after decoding
    """
    tmp = json.loads(json_string)
    conversations: Dict[str, Dict[Tuple, Any]] = {
        handler: {
            tuple(json.loads(key)): state for key, state in states.items()
        }
        for handler, states in tmp.items()
    }

    return conversations


def decode_user_chat_data_from_json(data: str) -> DefaultDict[int, Dict[Any, Any]]:
    """Helper method to decode chat or user data (that uses ints as keys) from a
    JSON-string.

    Args:
        data (:obj:`str`): The user/chat_data dict as JSON string.

    Returns:
        :obj:`dict`: The user/chat_data defaultdict after decoding
    """

    tmp: DefaultDict[int, Dict[Any, Any]] = defaultdict(dict)
    decoded_data = json.loads(data)
    for user, user_data in decoded_data.items():
        user = int(user)
        tmp[user] = {}
        for key, value in user_data.items():
            try:
                key = int(key)
            except ValueError:
                pass
            tmp[user][key] = value
    return tmp


class DefaultValue:
    """Wrapper for immutable default arguments that allows to check, if the default value was set
    explicitly. Usage::

        DefaultOne = DefaultValue(1)
        def f(arg=DefaultOne):
            if arg is DefaultOne:
                print('`arg` is the default')
                arg = arg.value
            else:
                print('`arg` was set explicitly')
            print('`arg` = ' + str(arg))

    This yields::

        >>> f()
        `arg` is the default
        `arg` = 1
        >>> f(1)
        `arg` was set explicitly
        `arg` = 1
        >>> f(2)
        `arg` was set explicitly
        `arg` = 2

    Also allows to evaluate truthiness::

        default = DefaultValue(value)
        if default:
            ...

    is equivalent to::

        default = DefaultValue(value)
        if value:
            ...

    Args:
        value (:obj:`obj`): The value of the default argument

    Attributes:
        value (:obj:`obj`): The value of the default argument

    """

    def __init__(self, value: Any = None):
        self.value = value

    def __bool__(self) -> bool:
        return bool(self.value)


DEFAULT_NONE: DefaultValue = DefaultValue(None)
""":class:`DefaultValue`: Default `None`"""

DEFAULT_FALSE: DefaultValue = DefaultValue(False)
""":class:`DefaultValue`: Default `False`"""
