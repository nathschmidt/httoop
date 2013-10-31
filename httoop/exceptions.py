# -*- coding: utf-8 -*-
class Invalid(ValueError):
	u"""base class for invalid values"""


class InvalidLine(Invalid):
	u"""error raised when first line is invalid"""


class InvalidHeader(Invalid):
	u"""error raised when header is invalid"""


class InvalidURI(Invalid):
	u"""error raised when URI is invalid"""


class InvalidDate(Invalid):
	u"""error raised when Date is invalid"""


class InvalidBody(Invalid):
	u"error raised when Body is invalid"""
