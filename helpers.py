'''Helper functions for the transcriber script'''

import datetime
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import logging
import os
from pathlib import Path
from sys import platform
import re
import yaml

# -------------------------------------------------------------------------------


class LabelError(Exception):
    '''Exception raised when dog, activitiy, or location name is not found in
    transcript'''

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

# -------------------------------------------------------------------------------


def custom_processor(s):
    '''Process string by
        -- stripping all non-letters and non-numbers
        -- forcing strings to lower-case '''
    regex = re.compile(r"(?ui)\W")
    return str.lower(regex.sub("", s))

# -------------------------------------------------------------------------------


def extract_activities_or_locations(
        identifier,
        transcript,
        label_dict,
        label_prons,
        threshold):
    '''Returns a string of the activities identified in the transcript
    Attributes:
        transcript - the transcript of the audiofile
        filename - the json file with the activities
        threshold - only scores over this threshold will be counted
    '''
    extracted_prons = process.extractBests(
        transcript,
        label_prons,
        scorer=fuzz.partial_ratio,
        score_cutoff=threshold,
        processor=custom_processor)
    if not extracted_prons:
        if identifier == "activities":
            raise LabelError(
                """No activities found in transcript. Please make sure the
                appropriate pronunciation is in the activities.json file""")
        elif identifier == "locations":
            raise LabelError(
                """No locations found in transcript. Please make sure the
                appropriate pronunciation is in the locations.json file""")
        else:
            raise LabelError(
                """Unknown identifier for labels. Can only be activities or
                locations""")
    extracted_names = [label_dict[pron] for pron, score in extracted_prons]
    extracted_string = " and ".join(extracted_names)
    return extracted_string

# -------------------------------------------------------------------------------


def extract_dogs(transcript, dogs_dict, dogs_prons):
    '''Returns a string of the dogs identified in the transcript
    Attributes:
        transcript - the transcript of the audiofile
        filename - the json file with the dogs' names
    '''
    transcript_without_spaces = transcript.replace(" ", "")
    extracted_prons = [
        pron for pron in dogs_prons if match_whole_word(
            pron, transcript_without_spaces)]
    if not extracted_prons:
        raise LabelError(
            """No dog names found in transcript. Please make sure the
            appropriate pronunciation is in the dogs.json file""")
    extracted_names = [dogs_dict[pron] for pron in extracted_prons]
    extracted_string = " and ".join(extracted_names)
    return extracted_string

# -------------------------------------------------------------------------------


def get_datestring(filename):
    '''Returns date string from file's mtime'''
    timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
    return timestamp.strftime("%m-%d-%Y")

# -------------------------------------------------------------------------------


def match_whole_word(word, transcript):
    match_output = re.search(word, transcript,
                             flags=re.IGNORECASE)
    return False if match_output is None else True

# -------------------------------------------------------------------------------


def read_yaml_as_dict(filename):
    '''Given a json file, this function reads it into a dict. It returns a
    dict and the dict's keys'''
    f = open(filename, 'r')
    return_dict = yaml.load(f)
    dict_keys = return_dict.keys()
    f.close()
    return return_dict, dict_keys

# -------------------------------------------------------------------------------


def rename_file(old, new, counter=0):
    '''Attempt to rename a file. If the file exists, try a numerical suffix'''
    if counter == 0:
        new_after_check = new
    else:
        suffix = str(counter)
        new_after_check = new[:-4] + ' (' + suffix + ')' + new[-4:]
    if os.path.isfile(new_after_check):
        rename_file(old, new, counter + 1)
    else:
        os.rename(old, new_after_check)

# -------------------------------------------------------------------------------


def setup_logger(logger_name, log_file, level=logging.INFO):
    '''Allows setting up different instances of loggers that will write to
    different files. On windows (embedded python), need to create files if
    they do not exist
    Attributes:
        logger_name - Name of the handle to the logger
        log_file - Output file
        level - INFO, DEBUG, ERROR etc'''
    if platform in ['win32', 'cygwin']:
        Path(log_file).touch()

    logger = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s : %(message)s)')
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)

# -------------------------------------------------------------------------------
