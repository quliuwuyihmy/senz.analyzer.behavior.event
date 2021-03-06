# coding: utf-8

import os

import leancloud
#from wsgiref import simple_server
from gevent.wsgi import WSGIServer

from app import app
from cloud import engine

from config import APP_ID, MASTER_KEY

from gevent import monkey
monkey.patch_all()

leancloud.init(APP_ID, master_key=MASTER_KEY)

application = engine


if __name__ == '__main__':
    # Be runnable locally.

    #here to test rnnrbm
    from event_analyzer_lib.core import trainRandomRnnRBM,predictByRnnRbm
    #trainRandomRnnRBM()
    predictByRnnRbm()

    app.debug = True
    #server = simple_server.make_server('0.0.0.0', 9010, application)
    server = WSGIServer(('0.0.0.0', 9010), application)
    server.serve_forever()
