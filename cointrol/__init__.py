import logging
import os


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cointrol.conf')

import django
django.setup()


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.propagate = False
console = logging.StreamHandler()
console.setFormatter(
    logging.Formatter('[%(asctime)s %(levelname)1.1s] %(name)s: %(message)s'))
log.addHandler(console)



