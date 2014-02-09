# -*- coding: utf-8 -*-
u"""Implements a state machine for the parsing process.
"""

CR = b'\r'
LF = b'\n'
CRLF = CR + LF
NOT_RECEIVED_YET = True

from httoop.messages import Request, Response
from httoop.headers import Headers
from httoop.exceptions import InvalidLine, InvalidHeader, InvalidBody, InvalidURI, Invalid
from httoop.util import Unicode
from httoop.statuses import (
	BAD_REQUEST, NOT_IMPLEMENTED, LENGTH_REQUIRED,
	HTTPStatusException, REQUEST_URI_TOO_LONG,
	MOVED_PERMANENTLY, HTTP_VERSION_NOT_SUPPORTED
)
from httoop import ServerProtocol, ServerHeader


# TODO: make subclasses for Request and Response parsing
# TODO: message pipelining
class StateMachine(object):
	u"""A HTTP protocol state machine parsing messages and turn them into
		appropriate objects."""

	def __init__(self):
		self.request = Request()
		self.response = Response()
		self.buffer = b''  # TODO: use bytearray
		self.httperror = None
		self.trailers = None

		# public events
		self.on_message = False
		self.on_requestline = False
		self.on_method = False
		self.on_uri = False
		self.on_protocol = False
		self.on_headers = False
		self.on_body = False
		self.on_body_started = False
		self.on_trailers = True  # will be set to false if trailers exists

		self.line_end = CRLF
		self.MAX_URI_LENGTH = 1024
		self.message_length = None
		self.chunked = False

		self._raise_errors = True

	def prepare_response(self):
		u"""prepare for sending the response"""

		self.response.prepare(self.request)

	def error(self, httperror):
		u"""error an HTTP Error"""
		self.httperror = httperror
		self.on_message = True

	def state_changed(self, state):
		setattr(self, 'on_%s' % (state), True)
		getattr(self, 'on_%s_complete' % (state), lambda: None)()

	def on_requestline_complete(self):
		self.state_changed('method')
		self.state_changed('uri')
		self.state_changed('protocol')

	def on_method_complete(self):
		pass

	def on_uri_complete(self):
		self.sanitize_request_uri()
		self.validate_request_uri_scheme()
		self.set_server_header()
		# TODO: set default URI scheme, host, port

	def on_protocol_complete(self):
		self.check_request_protocol()
		self.set_response_protocol()

	def on_headers_complete(self):
		self.check_host_header_exists()
		self.set_body_content_encoding()
		self.set_body_content_type()

	def on_body_complete(self):
		self.check_message_without_body_containing_data()

	def on_message_complete(self):
		self.check_methods_without_body()

	def parse(self, data):
		u"""Appends the given data to the internal buffer
			and parses it as HTTP Request-Message.

			:param data:
				data to parse
			:type  data: bytes
		"""
		self.buffer = "%s%s" % (self.buffer, data)
		try:
			if not self.on_requestline:
				if self.parse_requestline():
					return
				self.state_changed("requestline")

			if not self.on_headers:
				if self.parse_headers():
					return
				self.state_changed("headers")

			if not self.on_body:
				if self.parse_body():
					return
				self.state_changed("body")

			if not self.on_message:
				self.state_changed("message")
				self.request.body.seek(0)

			if self.buffer:
				# FIXME: new message, return
				raise BAD_REQUEST(u'too much input')
		except HTTPStatusException as httperror:
			# TODO: remove exception handling by calling error directly
			self.error(httperror)
			if self._raise_errors:
				raise

	def parse_requestline(self):
		if CRLF not in self.buffer:
			if LF not in self.buffer:
				self._check_uri_max_length(self.buffer)
				# request line unfinished
				return NOT_RECEIVED_YET
			self.line_end = LF

		requestline, self.buffer = self.buffer.split(self.line_end, 1)

		# parse request line
		try:
			self.request.parse(requestline)
		except (InvalidLine, InvalidURI) as exc:
			raise BAD_REQUEST(Unicode(exc))

	def parse_headers(self):
		# empty headers?
		if self.buffer.startswith(self.line_end):
			self.buffer = self.buffer[len(self.line_end):]
			return False

		header_end = self.line_end + self.line_end

		if header_end not in self.buffer:
			# headers incomplete
			return NOT_RECEIVED_YET

		headers, self.buffer = self.buffer.split(header_end, 1)

		# parse headers
		if headers:
			try:
				self.request.headers.parse(headers)
			except InvalidHeader as exc:
				raise BAD_REQUEST(Unicode(exc))

	def parse_body(self):
		if self.message_length is None and not self.chunked:
			self.determine_message_length()

		if self.chunked:
			return self.parse_chunked_body()
		elif self.message_length:
			return self.parse_body_with_message_length()
		else:
			# no message body
			return False

	def determine_message_length(self):
		# RFC 2616 Section 4.4
		# get message length

		request = self.request
		if 'Transfer-Encoding' in request.headers and request.protocol >= (1, 1):
			# chunked transfer in HTTP/1.1
			te = request.headers['Transfer-Encoding'].lower()
			self.chunked = 'chunked' == te
			if not self.chunked:
				raise NOT_IMPLEMENTED(u'Unknown HTTP/1.1 Transfer-Encoding: %s' % te)
		else:
			# Content-Length header defines the length of the message body
			try:
				self.message_length = int(request.headers.get("Content-Length", "0"))
				if self.message_length < 0:
					raise ValueError
			except ValueError:
				raise BAD_REQUEST(u'Invalid Content-Length header.')

	def parse_body_with_message_length(self):
		# TODO: cleanup + message pipelining
		self.request.body.parse(self.buffer)
		self.buffer = b''

		blen = len(self.request.body)
		if blen == self.message_length:
			return False
		elif blen < self.message_length:
			# the body is not yet received completely
			return NOT_RECEIVED_YET
		elif blen > self.message_length:
			raise BAD_REQUEST(u'Body length mismatchs Content-Length header.')

	def parse_chunked_body(self):
		if self.line_end not in self.buffer:
			# chunk size info not received yet
			return NOT_RECEIVED_YET

		chunk_size, rest_chunk = self.__parse_chunk_size()

		if len(rest_chunk) < (len(self.line_end) + chunk_size):
			# chunk not received completely
			return NOT_RECEIVED_YET

		body_part, rest_chunk = rest_chunk[:chunk_size], rest_chunk[chunk_size:]
		self.request.body.parse(body_part)
		self.buffer = rest_chunk

		if chunk_size == 0:
			return self.parse_trailers()

		if not rest_chunk.startswith(self.line_end):
			# TODO: restrict length of error message
			raise InvalidBody(u'chunk invalid terminator: [%r]' % repr(rest_chunk))
		self.buffer = self.buffer[len(self.line_end):]

		# next chunk
		return self.parse_chunked_body()

	def __parse_chunk_size(self):
		line, rest_chunk = self.buffer.split(self.line_end, 1)
		chunk_size = line.split(b";", 1)[0].strip()
		try:
			chunk_size = int(chunk_size, 16)
			if chunk_size < 0:
				raise ValueError
		except (ValueError, OverflowError):
			raise BAD_REQUEST(u'Invalid chunk size: %s' % chunk_size.decode('ISO8859-1'))
		else:
			return chunk_size, rest_chunk

	def parse_trailers(self):
		# TODO: the code is exactly the same as parse_headers but
		# we have to make sure no invalid header fields are send (only values told in Trailer header allowed)
		if self.buffer.startswith(self.line_end):
			self.buffer = self.buffer[len(self.line_end):]
			return False # no trailers

		trailer_end = self.line_end + self.line_end
		if trailer_end not in self.buffer:
			# not received yet
			return NOT_RECEIVED_YET

		trailers, self.buffer = self.buffer.split(trailer_end, 1)
		self.trailers = Headers()
		try:
			self.trailers.parse(trailers)
		except InvalidHeader as exc:
			raise BAD_REQUEST(u'Invalid trailers: %s' % Unicode(exc))

		self.merge_trailer_into_header()
		return False

	def merge_trailer_into_header(self):
		request = self.request
		for name in request.headers.values('Trailer'):
			value = self.trailers.pop(name, None)
			if value is not None:
				request.headers.append(name, value)
			else:
				# ignore
				pass
		if self.trailers:
			msg_trailers = u'" ,"'.join(self.trailers.keys())
			raise BAD_REQUEST(u'untold trailers: "%s"' % msg_trailers)
		del self.trailers

	def check_request_protocol(self):
		# check if we speak the same major HTTP version
		if self.request.protocol > ServerProtocol:
			# the major HTTP version differs
			raise HTTP_VERSION_NOT_SUPPORTED('The server only supports HTTP/1.0 and HTTP/1.1.')

	def set_response_protocol(self):
		# set correct response protocol version
		self.response.protocol = min(self.request.protocol, ServerProtocol)

	def _check_uri_max_length(self, uri):
		if len(uri) > self.MAX_URI_LENGTH:
			raise REQUEST_URI_TOO_LONG(
				u'The maximum length of the request is %d' % self.MAX_URI_LENGTH
			)

	def sanitize_request_uri(self):
		path = self.request.uri.path
		self.request.uri.normalize()
		if path != self.request.uri.path:
			raise MOVED_PERMANENTLY(self.request.uri.path.encode('UTF-8'))

	def validate_request_uri_scheme(self):
		if self.request.uri.scheme:
			if self.request.uri.scheme not in ('http', 'https'):
				raise BAD_REQUEST('Invalid URL: wrong scheme')

	def set_server_header(self):
		self.response.headers.setdefault('Server', ServerHeader)

	def check_host_header_exists(self):
		if self.request.protocol >= (1, 1) and not 'Host' in self.request.headers:
			raise BAD_REQUEST('Missing Host header')

	def set_body_content_encoding(self):
		if 'Content-Encoding' in self.request.headers:
			try:
				self.request.body.content_encoding = self.request.headers.element('Content-Encoding')
				self.request.body.content_encoding.codec
			except Invalid as exc:
				raise NOT_IMPLEMENTED('%s' % (exc,))

	def set_body_content_type(self):
		if 'Content-Type' in self.request.headers:
			self.request.body.mimetype = self.request.headers.element('Content-Type')

	def check_message_without_body_containing_data(self):
		if self.buffer and 'Content-Length' not in self.request.headers:
			# request without Content-Length header but body
			raise LENGTH_REQUIRED(u'Missing Content-Length header.')

	def check_methods_without_body(self):
		if self.request.method.safe and self.request.body:
			raise BAD_REQUEST('A %s request is considered as safe and MUST NOT contain a request body.' % self.request.method)
