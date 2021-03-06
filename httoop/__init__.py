# -*- coding: utf-8 -*-
"""HTTPOOP - an OOP model of the HTTP protocol

.. seealso:: :rfc:`2616`
"""

__version__ = 0.0
__all__ = ['Status', 'Body', 'Headers', 'URI', 'Method',
           'Request', 'Response', 'Protocol', 'Date', 'ServerStateMachine', 'ClientStateMachine',
           'InvalidLine', 'InvalidHeader', 'InvalidURI', 'InvalidBody', 'InvalidDate',
           'CONTINUE', 'SWITCHING_PROTOCOLS', 'OK', 'CREATED', 'ACCEPTED',
           'NON_AUTHORITATIVE_INFORMATION', 'NO_CONTENT', 'RESET_CONTENT',
           'PARTIAL_CONTENT', 'MULTIPLE_CHOICES', 'MOVED_PERMANENTLY', 'FOUND',
           'SEE_OTHER', 'NOT_MODIFIED', 'USE_PROXY', 'TEMPORARY_REDIRECT',
           'BAD_REQUEST', 'UNAUTHORIZED', 'PAYMENT_REQUIRED', 'FORBIDDEN',
           'NOT_FOUND', 'METHOD_NOT_ALLOWED', 'NOT_ACCEPTABLE', 'GONE',
           'PROXY_AUTHENTICATION_REQUIRED', 'REQUEST_TIMEOUT', 'CONFLICT',
           'LENGTH_REQUIRED', 'PRECONDITION_FAILED', 'REQUEST_ENTITY_TOO_LARGE',
           'REQUEST_URI_TOO_LONG', 'UNSUPPORTED_MEDIA_TYPE', 'BAD_GATEWAY',
           'REQUEST_RANGE_NOT_SATISFIABLE', 'EXPECTATION_FAILED',
           'I_AM_A_TEAPOT', 'INTERNAL_SERVER_ERROR', 'NOT_IMPLEMENTED',
           'SERVICE_UNAVAILABLE', 'GATEWAY_TIMEOUT',
           'HTTP_VERSION_NOT_SUPPORTED', 'HTTPStatusException', 'ServerProtocol']

from httoop.header import Server as __Server, UserAgent as __UserAgent
from httoop.messages import Protocol
UserAgentHeader = __UserAgent.from_str('%s/%s' % (__name__, __version__))
ServerHeader = __Server.from_str('%s/%s' % (__name__, __version__))
ServerProtocol = Protocol((1, 1))

from httoop.status import Status
from httoop.date import Date
from httoop.header import Headers
from httoop.uri import URI
from httoop.messages import Body, Request, Response, Protocol, Method
from httoop.exceptions import InvalidLine, InvalidHeader, InvalidURI, InvalidBody, InvalidDate, DecodeError, EncodeError
from httoop.server import ServerStateMachine
from httoop.client import ClientStateMachine

from httoop.status import (
	HTTPStatusException,
	CONTINUE, SWITCHING_PROTOCOLS, OK, CREATED, ACCEPTED, NON_AUTHORITATIVE_INFORMATION,
	NO_CONTENT, RESET_CONTENT, PARTIAL_CONTENT, MULTIPLE_CHOICES, MOVED_PERMANENTLY, FOUND,
	SEE_OTHER, NOT_MODIFIED, USE_PROXY, TEMPORARY_REDIRECT, BAD_REQUEST, UNAUTHORIZED, PAYMENT_REQUIRED,
	FORBIDDEN, NOT_FOUND, METHOD_NOT_ALLOWED, NOT_ACCEPTABLE, PROXY_AUTHENTICATION_REQUIRED,
	REQUEST_TIMEOUT, CONFLICT, GONE, LENGTH_REQUIRED, PRECONDITION_FAILED, REQUEST_ENTITY_TOO_LARGE,
	REQUEST_URI_TOO_LONG, UNSUPPORTED_MEDIA_TYPE, REQUEST_RANGE_NOT_SATISFIABLE, EXPECTATION_FAILED,
	I_AM_A_TEAPOT, INTERNAL_SERVER_ERROR, NOT_IMPLEMENTED, BAD_GATEWAY, SERVICE_UNAVAILABLE,
	GATEWAY_TIMEOUT, HTTP_VERSION_NOT_SUPPORTED
)

try:
	__import__('pkg_resources').declare_namespace(__name__)
except ImportError:
	__path___ = __import__('pkgutil').extend_path(__path__, __name__)
