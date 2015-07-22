# -*- coding: utf-8 -*-

from dao.config import *
from dao.model import *
from algo.datasets import Dataset
import datetime
import logging
import json
from algo import trainer, classifier

logger = logging.getLogger('logentries')


ALGOMAP = {'GMMHMM': trainer.GMMHMMTrainer}  # algo_type to trainer class map


def rebuildEvent(
        event_type,
        algo_type="GMMHMM",
        new_tag="TAG_%s" % datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
):
    # Get events' info from db.
    events = getEventInfo()
    # Validation of existance of the event
    if event_type not in events:
        logger.debug("There is no event named %s in Config Class" % event_type)
        return None

    # Get Model's init params.
    init_params = events[event_type]["initParams"][algo_type]
    # # Get Sets of all kinds of status classification.
    sys_status_sets = getSystemStatusSets()

    logger.debug("Event %s's params is %s" % (event_type, init_params))
    logger.debug("And latest status classification are %s" % sys_status_sets)
    logger.debug("The generated model tag is %s" % new_tag)

    now = datetime.datetime.now()
    description = "Initiation of A new %s Model for event %s was made at %s" % (algo_type, event_type, now)
    return setModel(algo_type=algo_type, model_tag=new_tag, event_type=event_type,
                    model_param=init_params, status_sets=sys_status_sets, timestamp=now, description=description)


def initAll(new_tag, algo_type):
    # Get events' info from db.
    events = getEventInfo()

    for event in events:
        rebuildEvent(event, algo_type, new_tag)

    return True


def trainEvent(observations, event_type, source_tag, target_tag, algo_type):
    '''Train model by input observations
    '''
    model = getModel(algo_type, source_tag, event_type)
    model_param = model["modelParam"]
    status_sets = model["statusSets"]

    sound_set = status_sets["sound"]
    motion_set = status_sets["motion"]
    location_set = status_sets["location"]
    d = Dataset(event_type=getEventList(), motion_type=motion_set, sound_type=sound_set,
                location_type=location_set, event_prob_map=getEventProbMap())
    numerical_obs = d._convertObs2Dataset(observations)
    logger.debug('[trainEvent] numerical_obs=%s' % (numerical_obs))

    TRAINER = ALGOMAP[algo_type]
    my_trainer = TRAINER(model_param)
    my_trainer.fit(numerical_obs)
    description = '[source_tag=%s]Train model algo_type=%s for eventType=%s' % (
        source_tag, algo_type, event_type)

    return setModel(algo_type, target_tag, event_type, my_trainer.params_, status_sets,
                    datetime.datetime.now(), description, json.dumps(observations))


def trainEventRandomly(
        event_type,
        source_tag,
        target_tag,
        algo_type="GMMHMM"
):
    model = getModel(algo_type, source_tag, event_type)
    model_param = model["modelParam"]
    status_sets = model["statusSets"]

    sound_set = status_sets["sound"]
    motion_set = status_sets["motion"]
    location_set = status_sets["location"]

    train_obs_len = 10
    train_obs_count = 30
    d = Dataset(event_type=getEventList(), motion_type=motion_set, sound_type=sound_set,
                location_type=location_set, event_prob_map=getEventProbMap())
    logger.debug('[trainEventRandomly] Dataset: %s' % (d))
    #print('[trainEventRandomly] Dataset: %s' % (d))
    d.randomObservations(event_type, train_obs_len, train_obs_count)
    observations = d.obs
    logger.debug('[trainEventRandomly] obs: %s' % (observations))
    #print('[trainEventRandomly] obs: %s' % (observations))

    description = '[source_tag=%s]Random train algo_type=%s for eventType=%s, random train obs_len=%s, obs_count=%s' % (
        source_tag, algo_type, event_type, train_obs_len, train_obs_count)
    TRAINER = ALGOMAP[algo_type]
    my_trainer = TRAINER(model_param)
    my_trainer.fit(d.getDataset())

    return setModel(algo_type, target_tag, event_type, my_trainer.params_, status_sets,
                    datetime.datetime.now(), description, json.dumps(observations))

def trainAll(source_tag, target_tag, algo_type):
    '''train randomly all
    '''
    # Get events' info from db.
    events = getEventInfo()

    for event in events:
        trainEventRandomly(event, source_tag, target_tag, algo_type)

    return True


def predictEvent(seq, tag, algo_type, x_request_id=''):
    '''seq最可能属于一个tag下哪个label的model

    Parameters
    ----------
    seq: list
    tag: string
    algo_type: string

    Returns
    -------
    predict_result: dict
      e.g. {"shopping": 0.7, "sleeping": 0.3}
    '''
    algo_type2classifer_map = {"GMMHMM": classifier.GMMHMMClassifier}

    logger.info('<%s>, [predict event] start get Model by tag:%s' % (x_request_id, tag))
    models = {}
    for model in getModelByTag(algo_type, tag):
        models[model.get('eventType')] = {'status_set': model.get('statusSets'), 'param': model.get('param')}
    logger.info('<%s>, [predict event] end get Model by tag:%s' %(x_request_id, tag))

    if not models or len(models) == 0:
        logger.error("<%s>, [predict event] tag=%s don't have models" % (x_request_id, tag))
        raise ValueError("tag=%s don't have models" % (tag))

    logger.info('<%s>, [predict event] start predict, seq=%s' % (x_request_id, seq))
    CLASSIFER = algo_type2classifer_map[algo_type]
    my_classifer = CLASSIFER(models)
    predict_result = my_classifer.predict(seq)
    logger.info('<%s>, [predict event] end predict, seq=%s, predict_result=%s' %(x_request_id, seq, predict_result))

    return predict_result
