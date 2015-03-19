#!/usr/bin/env python
"""
Cointrol server entry point

"""
import tornado.web
import tornado.wsgi
import tornado.ioloop
import tornado.httpserver
from tornado.options import options, define, parse_command_line
import django.core.handlers.wsgi
import django.contrib.staticfiles.handlers
from django.conf import settings

from . import realtime


define('port', type=int, default=8000)


def main():
    parse_command_line()
    tornado_app = tornado.web.Application(
        debug=settings.DEBUG,
        handlers=realtime.urls + [

            # Django fallback (for admin, static files, etc.)
            ('.*', tornado.web.FallbackHandler, {
                'fallback': tornado.wsgi.WSGIContainer(
                    django.contrib.staticfiles.handlers.StaticFilesHandler(
                        django.core.handlers.wsgi.WSGIHandler()))

            }),

        ]
    )
    server = tornado.httpserver.HTTPServer(tornado_app)
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
