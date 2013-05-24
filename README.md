httoop
======

An object oriented HTTP library.

Httoop can be used to parse, compose and work with HTTP-Request- and Response-Messages.

It provides an powerful interface using the vocabularity used in RFC 2616 and focuses on implementing HTTP "compliant" as defined in RFC 2616 Section 1.2.

"An implementation is not compliant if it fails to satisfy one or more of the MUST or REQUIRED level requirements for the protocols it implements."
[RFC 2616 Section 1.2](http://tools.ietf.org/html/rfc2616#section-1.2)

On top of the object oriented abstraction of HTTP httoop provides an easy way to support WSGI.


HTTP and extensions are defined in the following RFC's:

* Hypertext Transfer Protocol -- HTTP/1.1 (RFC 2616)

* HTTP Authentication: Basic and Digest Access Authentication (RFC 2617)

* Additional HTTP Status Codes (RFC 6585)

* PATCH Method for HTTP (RFC 5789)

* Use of the Content-Disposition Header Field in the Hypertext Transfer Protocol (HTTP) (RFC 6266)

* Upgrading to TLS Within HTTP/1.1 (RFC 2817)

* Transparent Content Negotiation in HTTP (RFC 2295)

* HTTP Remote Variant Selection Algorithm -- RVSA/1.0 (RFC 2296)

* HTTP Extensions for Web Distributed Authoring and Versioning (WebDAV) (RFC 4918)

* Hyper Text Coffee Pot Control Protocol (HTCPCP/1.0) (RFC 2324)

Extended information about hypermedia, WWW and how HTTP is meant to be used:

* Web Linking (RFC 5988)

* Representational State Transfer [REST](http://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)

Httoop is inspired by the following MIT-Licensed software:

* [cherrypy](http://cherrypy.org)
* [http-parser](https://github.com/benoitc/http-parser)
* [circuits.web](http://circuitsweb.com)
* [url-parse] (TODO)
