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
"""This module contains an object that represents a Telegram ForceReply."""

from typing import Any

from telegram import ReplyMarkup


class ForceReply(ReplyMarkup):
    """
    Upon receiving a message with this object, Telegram clients will display a reply interface to
    the user (act as if the user has selected the bot's message and tapped 'Reply'). This can be
    extremely useful if you want to create user-friendly step-by-step interfaces without having
    to sacrifice privacy mode.

    Objects of this class are comparable in terms of equality. Two objects of this class are
    considered equal, if their :attr:`selective` is equal.

    Args:
        selective (:obj:`bool`, optional): Use this parameter if you want to force reply from
            specific users only. Targets:

            1) Users that are @mentioned in the text of the Message object.
            2) If the bot's message is a reply (has reply_to_message_id), sender of the
               original message.

        **kwargs (:obj:`dict`): Arbitrary keyword arguments.

    Attributes:
        force_reply (:obj:`True`): Shows reply interface to the user, as if they manually selected
            the bots message and tapped 'Reply'.
        selective (:obj:`bool`): Optional. Force reply from specific users only.

    """

    def __init__(self, force_reply: bool = True, selective: bool = False, **_kwargs: Any):
        # Required
        self.force_reply = force_reply
        # Optionals
        self.selective = selective

        self._id_attrs = (self.selective,)
