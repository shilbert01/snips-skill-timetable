#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import ConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import io
import json
import datetime
#from timetable.timetable import SnipsTimetable

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

# each intent has a language associated with it
# extract language of first intent of assistant since there should only be one language per assistant
lang = json.load(open('/usr/share/snips/assistant/assistant.json'))['intents'][0]['language'] 

class SnipsConfigParser(ConfigParser.SafeConfigParser):
    def to_dict(self):
        return {section : {option_name : option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, ConfigParser.Error) as e:
        return dict()


class TimetableConfigParser(ConfigParser.SafeConfigParser):
    def to_dict(self):
        return {section : {option_name : option for option_name, option in self.items(section)} for section in self.sections()}

def read_timetable_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = TimetableConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, ConfigParser.Error) as e:
        return dict()

def subscribe_intent_callback(hermes, intentMessage):
    user,intentname = intentMessage.intent.intent_name.split(':')  # the user can fork the intent with this method
    if intentname in ["GetTimetable"]:
	conf = read_configuration_file(CONFIG_INI)
	ttable = read_configuration_file(conf["global"]["source"])
	action_wrapper(hermes, intentMessage, conf, ttable)
    else:
	pass


def action_wrapper(hermes, intentMessage, conf, ttable):
    """ Write the body of the function that will be executed once the intent is recognized. 
    In your scope, you have the following objects : 
    - intentMessage : an object that represents the recognized intent
    - hermes : an object with methods to communicate with the MQTT bus following the hermes protocol. 
    - conf : a dictionary that holds the skills parameters you defined 

    Refer to the documentation for further details. 
    """
    intentname = intentMessage.intent.intent_name.split(':')[1]

    if intentname == "GetTimetableForDay":
	#now = datetime.datetime.now()
	#day = now.day

	#for i < 9:
	    
	#timetable = ttable["Monday"][""]
	

	if lang == 'de':
	    result_sentence = u'Heute hast du %s '% ("Deutsch")


    hermes.publish_end_session(intentMessage.session_id, result_sentence)

if __name__ == "__main__":
    with Hermes("localhost:1883") as h:
	h.subscribe_intents(subscribe_intent_callback).start()
