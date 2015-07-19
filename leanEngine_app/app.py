# coding: utf-8

import os
import datetime
import time
from flask import Flask, request
import json

from config import *
import logging
from logentries import LogentriesHandler
import bugsnag
from bugsnag.flask import handle_exceptions

from event_analyzer_lib import core, utils
from leancloud.errors import LeanCloudError

# Configure Logentries
logger = logging.getLogger('logentries')
if APP_ENV == 'prod':
    logger.setLevel(logging.INFO)
else:
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s : %(levelname)s, %(message)s'))
    logger.addHandler(ch)
logentries_handler = LogentriesHandler(LOGENTRIES_TOKEN)
logger.addHandler(logentries_handler)

# Configure Bugsnag
bugsnag.configure(
    api_key=BUGSNAG_TOKEN,
    project_root=os.path.dirname(os.path.realpath(__file__))
)

app = Flask(__name__)

# Attach Bugsnag to Flask's exception handler
handle_exceptions(app)


@app.before_first_request
def init_before_first_request():
    init_tag = "[Initiation of Service Process]\n"
    logger.info('[init] enter init_before_first_request')

    log_init_time = "Initiation START at: \t%s\n" % (datetime.datetime.now())
    log_app_env = "Environment Variable: \t%s\n" % (APP_ENV)
    log_bugsnag_token = "Bugsnag Service TOKEN: \t%s\n" % (BUGSNAG_TOKEN)
    log_logentries_token = "Logentries Service TOKEN: \t%s\n" % (LOGENTRIES_TOKEN)
    logger.info(init_tag + log_init_time)
    logger.info(init_tag + log_app_env)
    logger.info(init_tag + log_bugsnag_token)
    logger.info(init_tag + log_logentries_token)

@app.route('/init/', methods=['POST'])
def rebuild_event():
    '''init specify event_type & tag model

    Parameters
    ----------
    data: JSON Obj
      e.g. {"event_type":"shopping#mall", "tag":"init_model"}
      event_type: string
      tag: string
      algo_type: string, optional, default "GMMHMM"

    Returns
    -------
    result: JSON Obj
      e.g. {"code":0, "message":"success", "result":""}
      code: int
        0 success, 1 fail
      message: string
      result: dict, optional
        model object id
    '''
    if request.headers.has_key('X-Request-Id') and request.headers['X-Request-Id']:
        x_request_id = request.headers['X-Request-Id']
    else:
        x_request_id = ''

    logger.info('<%s>, [rebuild event] enter' %(x_request_id))
    result = {'code': 1, 'message': ''}

    # params JSON validate
    try:
        incoming_data = json.loads(request.data)
    except ValueError, err_msg:
        logger.exception('<%s>, [rebuild event] [ValueError] err_msg: %s, params=%s' % (x_request_id, err_msg, request.data))
        result['message'] = 'Unvalid params: NOT a JSON Object'
        return json.dumps(result)

    # params key checking
    for key in ['event_type', 'tag']:
        if key not in incoming_data:
            logger.exception("<%s>, [rebuild event] [KeyError] params=%s, should have key: %s" % (x_request_id, incoming_data, key))
            result['message'] = "Params content Error: cant't find key=%s" % (key)
            return json.dumps(result)

    event_type = incoming_data['event_type']
    tag = incoming_data['tag']
    algo_type = incoming_data.get('algo_type', 'GMMHMM')

    model_id = core.rebuildEvent(event_type, algo_type, tag)
    result['code'] = 0
    result['message'] = 'success'
    result['result'] = {'modelObjectId': model_id}

    return json.dumps(result)


@app.route('/initAll/', methods=['POST'])
def init_all():
    '''init model and store in db with input tag

    Parameters
    ----------
    data: JSON Obj
      e.g. {}
      tag: string, optional, default 'init_model_timestamp'
      algo_type: string, optional, default "GMMHMM"

    Returns
    -------
    result: JSON Obj
      e.g. {"code":0, "message":"success", "result":""}
      code: int
        0 success, 1 fail
      message: string
      result:
    '''
    if request.headers.has_key('X-Request-Id') and request.headers['X-Request-Id']:
        x_request_id = request.headers['X-Request-Id']
    else:
        x_request_id = ''

    logger.info('<%s>, [init all] enter' %(x_request_id))
    result = {'code': 1, 'message': ''}

    # params JSON validate
    try:
        if request.data:
            incoming_data = json.loads(request.data)
        else:
            incoming_data = {}
    except ValueError, err_msg:
        logger.exception('<%s>, [init all] [ValueError] err_msg: %s, params=%s' % (x_request_id, err_msg, request.data))
        result['message'] = 'Unvalid params: NOT a JSON Object'
        return json.dumps(result)

    tag = incoming_data.get('tag', 'init_model_%s'%(int(time.time())))
    algo_type = incoming_data.get('algo_type', 'GMMHMM')

    core.initAll(tag, algo_type)
    result['message'] = 'success'
    result['code'] = 0
    return json.dumps(result)


@app.route('/trainRandomly/', methods=['POST'])
def train_randomly():
    '''Randomly train a `source_tag` model.

    After train, model params will be saved in db and taged `target_tag`

    Parameters
    ----------
    data: JSON Obj
      e.g. {"event_type":"shopping#mall", "source_tag":"init_model"}
      event_type: string
      source_tag: string
      target_tag: string, optional, default "random_train"
      algo_type: string, optional, default "GMMHMM"

    Returns
    -------
    result: JSON Obj
      e.g. {"code":0, "message":"success", "result":""}
      code: int
        0 success, 1 fail
      message: string
      result: dict, optional
        model object id
    '''
    if request.headers.has_key('X-Request-Id') and request.headers['X-Request-Id']:
        x_request_id = request.headers['X-Request-Id']
    else:
        x_request_id = ''

    logger.info('<%s>, [train randomly] enter' %(x_request_id))
    result = {'code': 1, 'message': ''}

    # params JSON validate
    try:
        incoming_data = json.loads(request.data)
    except ValueError, err_msg:
        logger.exception('<%s>, [tran randomly] [ValueError] err_msg: %s, params=%s' % (x_request_id, err_msg, request.data))
        result['message'] = 'Unvalid params: NOT a JSON Object'
        return json.dumps(result)

    # params key checking
    for key in ['event_type', 'source_tag']:
        if key not in incoming_data:
            logger.exception("<%s>, [rebuild event] [KeyError] params=%s, should have key: %s" % (x_request_id, incoming_data, key))
            result['message'] = "Params content Error: cant't find key=%s" % (key)
            return json.dumps(result)

    event_type = incoming_data['event_type']
    source_tag = incoming_data['source_tag']
    target_tag = incoming_data.get('target_tag', 'random_train')
    algo_type = incoming_data.get('algo_type', 'GMMHMM')

    model_id = core.trainEventRandomly(event_type, source_tag, target_tag, algo_type)
    result['code'] = 0
    result['message'] = 'success'
    result['result'] = {'modelObjectId': model_id}

    return json.dumps(result)


@app.route('/trainRandomlyAll/', methods=['POST'])
def train_randomly_all():
    '''Randomly train a `source_tag` model of all event labels.

    After train, model params will be saved in db and taged `target_tag`

    Parameters
    ----------
    data: JSON Obj
      e.g. {"source_tag":"init_model"}
      source_tag: string
      target_tag: string, optional, default "random_train"
      algo_type: string, optional, default "GMMHMM"

    Returns
    -------
    result: JSON Obj
      e.g. {"code":0, "message":"success", "result":""}
      code: int
        0 success, 1 fail
      message: string
      result: dict, optional
        model object id
    '''
    if request.headers.has_key('X-Request-Id') and request.headers['X-Request-Id']:
        x_request_id = request.headers['X-Request-Id']
    else:
        x_request_id = ''

    logger.info('<%s>, [train randomly all] enter' %(x_request_id))
    result = {'code': 1, 'message': ''}

    # params JSON validate
    try:
        incoming_data = json.loads(request.data)
    except ValueError, err_msg:
        logger.exception('<%s>, [tran randomly all] [ValueError] err_msg: %s, params=%s' % (x_request_id, err_msg, request.data))
        result['message'] = 'Unvalid params: NOT a JSON Object'
        return json.dumps(result)

    # params key checking
    for key in ['source_tag']:
        if key not in incoming_data:
            logger.exception("<%s>, [train randomly all] [KeyError] params=%s, should have key: %s" % (x_request_id, incoming_data, key))
            result['message'] = "Params content Error: cant't find key=%s" % (key)
            return json.dumps(result)

    source_tag = incoming_data['source_tag']
    target_tag = incoming_data.get('target_tag', 'random_train')
    algo_type = incoming_data.get('algo_type', 'GMMHMM')

    core.trainAll(source_tag, target_tag, algo_type)
    result['code'] = 0
    result['message'] = 'success'

    return json.dumps(result)

@app.route('/predict/', methods=['POST'])
def predict():
    '''Predict seq belong to which event

    Parameters
    ----------
    data: JSON obj
      e.g. {
            "seq" : [{"motion": "sitting", "sound": "unknown", "location": "chinese_restaurant"},
                     {"motion": "sitting", "sound": "shop", "location": "chinese_restaurant"},
                     {"motion": "walking", "sound": "shop", "location": "night_club"}],
            "tag":"init_model"
           }
      seq: list
      tag: string
      algo_type: string, optional, default "GMMHMM"

    Returns
    -------
    result: JSON Obj
      e.g. {"code":0, "message":"success", "result":{"shopping":0.7,"walking":0.3}}
      code: int
        0 success, 1 fail
      message: string
      result: dict
    '''
    if request.headers.has_key('X-Request-Id') and request.headers['X-Request-Id']:
        x_request_id = request.headers['X-Request-Id']
    else:
        x_request_id = ''

    logger.info('<%s>, [predict] enter' %(x_request_id))
    result = {'code': 1, 'message': ''}

    # params JSON validate
    try:
        incoming_data = json.loads(request.data)
    except ValueError, err_msg:
        logger.exception('<%s>, [predict] [ValueError] err_msg: %s, params=%s' % (x_request_id, err_msg, request.data))
        result['message'] = 'Unvalid params: NOT a JSON Object'
        return json.dumps(result)

    # params key checking
    for key in ['seq', 'tag']:
        if key not in incoming_data:
            logger.exception("<%s>, [predict] [KeyError] params=%s, should have key: %s" % (x_request_id, incoming_data, key))
            result['message'] = "Params content Error: cant't find key=%s" % (key)
            return json.dumps(result)

    seq = incoming_data['seq']
    tag = incoming_data['tag']
    algo_type = incoming_data.get('algo_type', "GMMHMM")

    try:
        # data clean for seq
        seq_cleaned = []
        for elem in seq:
            seq_cleaned.append({
                'location': elem['location'],
                'motion': elem['motion'],
                'sound': elem['sound'],
            })

        result['result'] = core.predictEvent(seq_cleaned, tag, algo_type)
        result['code'] = 0
        result['message'] = 'success'
    except LeanCloudError, err_msg:
        result['message'] = "[LeanCloudError] Maybe can't find source_tag=%s, event_type=%s" % (source_tag, event_type)
        logger.info('<%s> [predict] [LeanCloudError] %s' % (x_request_id, err_msg))

    return json.dumps(result)


@app.route('/train/', methods=['POST'])
def train():
    '''Train a `source_tag` model of `event_type` by `obs`.

    After train, model params will be saved in db and taged `target_tag`

    Parameters
    ----------
    data: JSON Obj
      e.g. {
            "obs" : [{"motion": "sitting", "sound": "unknown", "location": "chinese_restaurant"},
                     {"motion": "sitting", "sound": "shop", "location": "chinese_restaurant"},
                     {"motion": "walking", "sound": "shop", "location": "night_club"}],
            "source_tag": "init_model",
            "event_type": "dining_in_restaurant"
           }
      obs: list, must be 2-dimension list
      event_type: string
      source_tag: string
      target_tag: string, optional, default equal to `source_tag`
      algo_type: string, optional, default "GMMHMM"

    Returns
    -------
    result: JSON Obj
      e.g. {"code":0, "message":"success", "result":""}
      code: int
        0 success, 1 fail
      message: string
      result: dict, optional
        model object id
    '''
    if request.headers.has_key('X-Request-Id') and request.headers['X-Request-Id']:
        x_request_id = request.headers['X-Request-Id']
    else:
        x_request_id = ''

    logger.info('<%s>, [train] enter' %(x_request_id))
    result = {'code': 1, 'message': ''}

    # params JSON validate
    try:
        incoming_data = json.loads(request.data)
    except ValueError, err_msg:
        logger.exception('<%s>, [train] [ValueError] err_msg: %s, params=%s' % (x_request_id, err_msg, request.data))
        result['message'] = 'Unvalid params: NOT a JSON Object'
        return json.dumps(result)

    # params key checking
    for key in ['obs', 'event_type', 'source_tag']:
        if key not in incoming_data:
            logger.exception("<%s>, [train] [KeyError] params=%s, should have key: %s" % (x_request_id, incoming_data, key))
            result['message'] = "Params content Error: cant't find key=%s" % (key)
            return json.dumps(result)

    event_type = incoming_data['event_type']
    source_tag = incoming_data['source_tag']
    obs = incoming_data['obs']
    target_tag = incoming_data.get('target_tag', source_tag)
    algo_type = incoming_data.get('algo_type', 'GMMHMM')

    if not utils.check_2D_list(obs):
        result['message'] = 'input obs=%s is not 2-dimension' % (obs)
        return json.dumps(result)
    # TODO: wrapper for obs
    cleaned_obs = []
    for seq in obs:
        seq_cleaned = []
        for elem in seq:
            seq_cleaned.append({
                'location': elem['location'],
                'motion': elem['motion'],
                'sound': elem['sound'],
            })
        cleaned_obs.append(seq_cleaned)

    try:
        model_id = core.trainEvent(obs, event_type, source_tag, target_tag, algo_type)
        result['code'] = 0
        result['message'] = 'success'
        result['result'] = {'modelObjectId': model_id}
    except LeanCloudError, err_msg:
        result['message'] = "[LeanCloudError] Maybe can't find source_tag=%s, event_type=%s" % (source_tag, event_type)
        logger.info('<%s> [train] [LeanCloudError] %s' % (x_request_id, err_msg))

    return json.dumps(result)