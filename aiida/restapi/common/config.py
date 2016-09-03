## Pagination defaults
LIMIT_DEFAULT = 400
PERPAGE_DEFAULT = 20

##Version prefix for all the URLs
PREFIX="/api/v2"

## Flask app configs.
#DEBUG: True/False. enables debug mode N.B.
#!!!For production run use ALWAYS False!!!
#PROPAGATE_EXCEPTIONS: True/False serve REST exceptions to the client (and not a
# generic 500: Internal Server Error exception)
APP_CONFIG = {
              'DEBUG': False,
              'PROPAGATE_EXCEPTIONS': True,
              }

## Caching
#memcached: backend caching system
cache_config={'CACHE_TYPE': 'memcached'}
#Caching TIMEOUTS (in seconds)
TIMEOUT_NODES = 10
TIMEOUT_COMPUTERS = 10*60
TIMEOUT_DATAS = 10*60
TIMEOUT_GROUPS = 10*60
TIMEOUT_CODES = 10*60


# Database
import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, '../database/mcloud.db')
SECRET_KEY = "\xb7\x9c:\xca\xa3\x9f\x8a;\xa6_\x96\xc7\xd2?\x82\xa6\x9d;'\xe2W\xe1\xc8\xc2"
