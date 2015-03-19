"""
WebSocket API

"""
import logging

import tornadoredis
import tornadoredis.pubsub
from sockjs.tornado import SockJSConnection, SockJSRouter


log = logging.getLogger(__name__)


subscriber = tornadoredis.pubsub.SockJSSubscriber(tornadoredis.Client())


class ChangesConnection(SockJSConnection):

    CHANNELS = [
        'model_changes',
        'monitoring',
    ]

    def on_open(self, info):
        log.info('on_open')
        subscriber.subscribe(self.CHANNELS, self)

    def on_close(self):
        log.info('on_close')
        subscriber.unsubscribe(self.CHANNELS, self)


router = SockJSRouter(ChangesConnection, '/realtime/changes')
urls = router.urls
