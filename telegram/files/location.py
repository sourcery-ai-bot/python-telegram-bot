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
"""This module contains an object that represents a Telegram Location."""

from typing import Any

from telegram import TelegramObject


class Location(TelegramObject):
    """This object represents a point on the map.

    Objects of this class are comparable in terms of equality. Two objects of this class are
    considered equal, if their :attr:`longitute` and :attr:`latitude` are equal.

    Args:
        longitude (:obj:`float`): Longitude as defined by sender.
        latitude (:obj:`float`): Latitude as defined by sender.
        horizontal_accuracy (:obj:`float`, optional): The radius of uncertainty for the location,
            measured in meters; 0-1500.
        live_period (:obj:`int`, optional): Time relative to the message sending date, during which
            the location can be updated, in seconds. For active live locations only.
        heading (:obj:`int`, optional): The direction in which user is moving, in degrees; 1-360.
            For active live locations only.
        proximity_alert_radius (:obj:`int`, optional): Maximum distance for proximity alerts about
            approaching another chat member, in meters. For sent live locations only.
        **kwargs (:obj:`dict`): Arbitrary keyword arguments.

    Attributes:
        longitude (:obj:`float`): Longitude as defined by sender.
        latitude (:obj:`float`): Latitude as defined by sender.
        horizontal_accuracy (:obj:`float`): Optional. The radius of uncertainty for the location,
            measured in meters.
        live_period (:obj:`int`): Optional. Time relative to the message sending date, during which
            the location can be updated, in seconds. For active live locations only.
        heading (:obj:`int`): Optional. The direction in which user is moving, in degrees.
            For active live locations only.
        proximity_alert_radius (:obj:`int`): Optional. Maximum distance for proximity alerts about
            approaching another chat member, in meters. For sent live locations only.

    """

    def __init__(
        self,
        longitude: float,
        latitude: float,
        horizontal_accuracy: float = None,
        live_period: int = None,
        heading: int = None,
        proximity_alert_radius: int = None,
        **_kwargs: Any,
    ):
        # Required
        self.longitude = longitude
        self.latitude = latitude

        # Optionals
        self.horizontal_accuracy = horizontal_accuracy or None
        self.live_period = live_period or None
        self.heading = heading or None
        self.proximity_alert_radius = proximity_alert_radius or None

        self._id_attrs = (self.longitude, self.latitude)
