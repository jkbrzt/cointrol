import logging

from tornado.ioloop import IOLoop
from tornado.gen import coroutine
from tornado import autoreload
from django.conf import settings

from .workers import (TickerWatcher, TransactionsWatcher,
                      OrdersWatcher, Monitoring)


log = logging.getLogger(__name__)


@coroutine
def main_loop():
    log.info('starting main loop')

    workers = [
        Monitoring(),
        TickerWatcher(),
        TransactionsWatcher(),
        OrdersWatcher()
    ]

    # First run them sequentially to avoid race conditions.
    for worker in workers:
        yield worker.run_once()

    # Then forever in parallel.
    yield [worker.run_forever() for worker in workers]


def main():

    if settings.DEBUG:
        log.info('starting Tornado autoreload')
        autoreload.start()

    log.info('*** main() ***')
    try:
        IOLoop.instance().run_sync(main_loop)
    except KeyboardInterrupt:
        log.info('^C, quitting')


if __name__ == '__main__':
    main()
