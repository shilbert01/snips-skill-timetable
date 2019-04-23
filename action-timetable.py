#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import ConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
import io
import json
from datetime import datetime
#from timetable.timetable import SnipsTimetable

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

# each intent has a language associated with it
# extract language of first intent of assistant since there should only be one language per assistant
lang = json.load(open('/usr/share/snips/assistant/assistant.json'))['intents'][0]['language'] 

class SnipsConfigParser(ConfigParser.SafeConfigParser):
    def to_dict(self):
        return {section : {option_name : option for option_name, option in self.items(section)} for section in self.sections()}

def weekDay(year, month, day):
    """https://stackoverflow.com/questions/9847213/how-do-i-get-the-day-of-week-given-a-date-in-python"""
    offset = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    week   = ['Sunday', 
              'Monday', 
              'Tuesday', 
              'Wednesday', 
              'Thursday',  
              'Friday', 
              'Saturday']
    afterFeb = 1
    if month > 2: afterFeb = 0
    aux = int(year) - 1700 - afterFeb
    # dayOfWeek for 1700/1/1 = 5, Friday
    dayOfWeek  = 5
    # partial sum of days betweem current date and 1700/1/1
    dayOfWeek += (aux + afterFeb) * 365                  
    # leap year correction    
    dayOfWeek += aux / 4 - aux / 100 + (aux + 100) / 400     
    # sum monthly and day offsets
    dayOfWeek += offset[int(month) - 1] + (int(day) - 1)               
    dayOfWeek %= 7
    return dayOfWeek, week[dayOfWeek]


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
    if intentname in ["GetTimetableForDay"]:
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
	periods = ""

	for (slot_value, slot) in intentMessage.slots.items():
	    print('Slot {} -> \n\tRaw: {} \tValue: {}'.format(slot_value, slot[0].raw_value, slot[0].slot_value.value.value))

	print("day: %s %s" %(slot_value, slot[0].raw_value))
	datestring = slot[0].slot_value.value.value
	date = datetime.strptime(datestring.split('+')[0].rstrip(), "%Y-%m-%d %H:%M:%S")
	print("date: %s" %date)
	print type(date)
	print(date.strftime("%Y"),date.strftime("%m"),date.strftime("%d"))
	# get workweek
	wk = date.strftime("%V")
	print ttable["Week"]
	Awks = ttable["Week"]["a"].split(",")
	Bwks = ttable["Week"]["b"].split(",")
	print Awks
	if wk in Awks:
	    currwk = "A"
	elif wk in Bwks:
	    currwk = "B"
	x,y = weekDay(date.strftime("%Y"),date.strftime("%m"),date.strftime("%d"))
	print (x,y)
	#for key, value in sorted(ttable[y].items()):
	#    print(key, value)
	sorted_timetable = {int(k) : v for k, v in ttable[y].items()}
	print sorted_timetable
	# count number of school lessons
	lessons_count = len(sorted_timetable)
	# count number of periods and "free periods"
	freeperiods = 0
	for k,v in sorted_timetable.items():
	    if v == "":
		periods = periods + "Freistunde, "
		freeperiods = freeperiods + 1
	    else:
		# check for A | B week schedule
		if v.startswith("A:"):
		    if len(v.split("|")) != 2:
			result_sentence = "Irgendwas haut mit dem Stundenplan nicht hin. Es gibt offenbar A-Woche und B-Woche aber ich kann die Stunden nicht zuordnen. Schau dir die Stundenplan-Datei an."
		    else:
			ABperiods = v.split("|")
			for i in ABperiods:
			    if i.lstrip().startswith("A:"):
				Aperiod = i.split(":")[1].lstrip()
			    elif i.lstrip().startswith("B:"):
				Bperiod = i.split(":")[1].lstrip()
			#ABperiods = {v.split("|")[0].split(":")[0] : v.split("|")[0].split(":")[1] for v.split("|")[0].split(":")[0], v.split("|")[0].split(":")[1] in v.split("|")}
			if currwk == "A":
			    periods = periods + Aperiod + ", "
			elif currwk == "B":
			    periods = periods + Bperiod + ", "
		else:
		    periods = periods + v + ", "
	if lang == 'de':
	    result_sentence = "Es ist %s-Woche. Du hast %s Stunden, davon %s Freistunden. Du hast %s" %(currwk,len(sorted_timetable),freeperiods,periods)

    hermes.publish_end_session(intentMessage.session_id, result_sentence)

if __name__ == "__main__":
    with Hermes("localhost:1883") as h:
	h.subscribe_intents(subscribe_intent_callback).start()
