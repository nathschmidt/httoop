# -*- coding: utf-8 -*-
u"""Implements a state machine for the parsing process.
"""

CR = b'\r'
LF = b'\n'
CRLF = CR + LF

from httoop.messages import Request
from httoop.headers import Headers
from httoop.exceptions import InvalidLine, InvalidHeader, InvalidURI

# TODO: make all error messages unicode

class StateMachine(object):
	u"""A HTTP Parser"""

	def __init__(self):
		self.request = Request()
		self.buffer = b''
		self.httperror = None

		# public events
		self.on_message = False
		self.on_requestline = False
		#self.on_method = False
		#self.on_uri = False
		#self.on_protocol = False
		self.on_headers = False
		self.on_body = False

		# private events
		self._on_trailers = True # will be set to false if trailers exists

		self.line_end = CRLF
		self.MAX_URI_LENGTH = 1024
		self.message_length = 0
		self.chunked = False

	def error(self, httperror):
		u"""error an HTTP Error"""
		self.httperror = httperror
		self.on_message = True

	def parse(self, data):
		u""""""

		self.buffer.append(data)

		request = self.request
		line_end = self.line_end

		while True:
			if not self.on_requestline:

				if CRLF not in self.buffer:
					if LF not in self.buffer:
						# request line unfinished
						if len(self.buffer) > self.MAX_URI_LENGTH:
							self.error(REQUEST_URI_TOO_LONG('The maximum length of the request is %d' % self.MAX_URI_LENGTH))
						return
					self.line_end = line_end = LF

				requestline, self.buffer = self.buffer.split(line_end, 1)

				# parse request line
				try:
					request.parse(requestline)
				except InvalidLine as exc:
					return self.error(BAD_REQUEST(str(exc)))

				self.on_requestline = True

			if not self.on_headers:
				header_end = line_end+line_end

				if header_end not in self.buffer:
					# headers incomplete
					return

				headers, self.buffer = self.buffer.split(header_end, 1)

				# parse headers
				if headers:
					try:
						request.headers.parse(headers)
					except InvalidHeader as exc:
						return self.error(BAD_REQUEST(str(exc)))

				self.on_headers = True

			elif not self.on_body:
				if not self.on_body_started:
					# RFC 2616 Section 4.4
					# get message length

					self.on_body_started = True
					if request.protocol >= (1, 1) and 'Transfer-Encoding' in request.headers:
						# chunked transfer in HTTP/1.1
						te = request.headers['Transfer-Encoding'].lower()
						self.chunked = 'chunked' == te
						if not self.chunked:
							return self.error(NOT_IMPLEMENTED('Unknown HTTP/1.1 Transfer-Encoding: %s' % te))
					else:
						# Content-Length header defines the length of the message body
						try:
							self.message_length = int(request.headers.get("Content-Length", "0"))
							if self.message_length < 0:
								raise ValueError
						except ValueError:
							return self.error(BAD_REQUEST('Invalid Content-Length header.'))

				if self.chunked:
					if line_end not in self.buffer:
						# chunk size info not received yet
						return

					line, rest_chunk = self.buffer.split(line_end, 1)
					chunk_size = line.split(b";", 1)[0].strip()
					try:
						chunk_size = int(chunk_size, 16)
						if chunk_size < 0:
							raise ValueError
					except (ValueError, OverflowError):
						return self.error(BAD_REQUEST('Invalid chunk size: %s' % chunk_size))

					if len(rest_chunk) < (chunk_size + len(line_end)):
						# chunk not received completely
						# buffer is untouched
						return

					body_part, rest_chunk = rest_chunk[:chunk_size], rest_chunk[chunk_size:]
					if not rest_chunk.startswith(line_end):
						raise InvalidBody("chunk invalid terminator: [%s]" % data)

					request.body.write(body_part)

					self.buffer = rest_chunk[len(line_end):]

					if chunk_size == 0:
						# finished
						self.on_body = True

				elif self.message_length:
					request.body.write(self.buffer)
					self.buffer = b''

					blen = len(request.body)
					if blen == self.message_length:
						self.on_body = True
					elif blen < self.message_length:
						# the body is not yet received completely
						return
					elif blen > self.message_length:
						self.error(BAD_REQUEST('Body length mismatchs Content-Length header.'))
						return

				elif self.buffer:
					# request without Content-Length header but body
					self.error(LENGTH_REQUIRED('Missing Content-Length header.'))
					return

			elif not self._on_trailers:
				if 'Trailer' in request.headers:
					trailer_end = line_end + line_end
					if trailer_end not in self.buffer:
						# not received yet
						return
					trailers, self.buffer = self.buffer.split(trailer_end, 1)
					request.trailers = Headers()
					try:
						request.trailers.parse(trailers)
					except InvalidHeader as exc:
						self.error(BAD_REQUEST('Invalid trailers: %s' % str(exc)))
						return
					for name in request.headers.values('Trailer'):
						value = request.trailers.pop(value, None)
						if value is not None:
							request.headers.append(name, value)
						else:
							# ignore
							pass
					if request.trailers:
						self.error(BAD_REQUEST('untold trailers: "%s"' % '" ,"'.join(request.trailers.keys())))
					del request.trailers
				self._on_trailers = True
			elif not self.on_message:
				self.on_message = True
			else:
				if self.buffer:
					return self.error(BAD_REQUEST('too much input'))
				break
