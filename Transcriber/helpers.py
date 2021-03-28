'''Helper functions for the transcriber script'''

import datetime
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import json
import logging
import os
import re

#-------------------------------------------------------------------------------
class LabelError(Exception):
    '''Exception raised when dog, activitiy, or location name is not found in transcript'''

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

#-------------------------------------------------------------------------------
def custom_processor(s):
    '''Process string by
        -- stripping all non-letters and non-numbers
        -- forcing strings to lower-case '''
    regex = re.compile(r"(?ui)\W")
    return str.lower(regex.sub("", s))

#-------------------------------------------------------------------------------
def extract_activities_or_locations(identifier, transcript, label_dict, label_pros, threshold):
    '''Returns a string of the activities identified in the transcript
    Attributes:
        transcript - the transcript of the audiofile
        filename - the json file with the activities
        threshold - only scores over this threshold will be counted
    '''
    extracted_pros = process.extractBests(transcript, label_pros, scorer = fuzz.partial_ratio, score_cutoff = threshold, processor = custom_processor)
    if not extracted_pros:
        if identifier == "activities":
            raise LabelError("No activities found in transcript. Please make sure the appropriate pronunciation is in the activities.json file")
        elif identifier == "locations":
            raise LabelError("No locations found in transcript. Please make sure the appropriate pronunciation is in the locations.json file")
        else:
            raise LabelError("Unknown identifier for labels. Can only be activities or locations")
    extracted_names = [label_dict[pro] for pro, score in extracted_pros]
    extracted_string = " and ".join(extracted_names)
    return extracted_string

#-------------------------------------------------------------------------------
def extract_dogs(transcript, dogs_dict, dogs_pros):
    '''Returns a string of the dogs identified in the transcript
    Attributes:
        transcript - the transcript of the audiofile
        filename - the json file with the dogs' names
    '''
    extracted_pros = [pro for pro in dogs_pros if pro in transcript]
    if not extracted_pros:
        raise LabelError("No dog names found in transcript. Please make sure the appropriate pronunciation is in the dogs.json file")
    extracted_names = [dogs_dict[pro] for pro in extracted_pros]
    extracted_string = " and ".join(extracted_names)
    return extracted_string

#-------------------------------------------------------------------------------
def get_datestring(filename):
    '''Returns date string from file's mtime'''
    timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
    return timestamp.strftime("%m-%d-%Y")

#-------------------------------------------------------------------------------
def read_json_as_dict(filename):
    '''Given a json file, this function reads it into a dict. It returns a dict and the dict's keys'''
    f = open(filename, 'r')
    return_dict = json.load(f)
    dict_keys = return_dict.keys()
    f.close()
    return return_dict, dict_keys

#-------------------------------------------------------------------------------
def setup_logger(logger_name, log_file, level = logging.INFO):
    '''Allows setting up different instances of loggers that will write to different files
    Attributes:
        logger_name - Name of the handle to the logger
        log_file - Output file
        level - INFO, DEBUG, ERROR etc'''
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s : %(message)s)')
    fileHandler = logging.FileHandler(log_file, mode = 'w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    l.addHandler(streamHandler)

#-------------------------------------------------------------------------------
