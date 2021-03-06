# -*- coding: utf-8 -*-
"""HTTP request and response messages

.. seealso:: :rfc:`2616#section-4`
"""

__all__ = ('Method',)

import re

from httoop.exceptions import InvalidLine
from httoop.util import Unicode
from httoop.meta import HTTPSemantic


class Method(object):
	u"""A HTTP request method"""
	__metaclass__ = HTTPSemantic
	__slots__ = ('__method')

	@property
	def safe(self):
		return self in self.safe_methods

	@property
	def idempotent(self):
		return self in self.idempotent_methods

	safe_methods = (u'GET', u'HEAD')
	idempotent_methods = (u'GET', u'HEAD', u'PUT', u'DELETE', u'OPTIONS', u'TRACE')
	METHOD_RE = re.compile(r"^[A-Z0-9$-_.]{1,20}\Z", re.IGNORECASE)

	def __init__(self, method=None):
		self.set(method or u'GET')

	def set(self, method):
		if isinstance(method, Unicode):
			method = method.encode('ASCII')
		self.parse(method)

	def parse(self, method):
		if not self.METHOD_RE.match(method):
			raise InvalidLine(u"Invalid method: %r" % method.decode('ISO8859-1'))
		self.__method = method

	def compose(self):
		return self.__method
