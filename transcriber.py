'''This takes mp4 files in the given location, transcribes the first 15 seconds, and writes the transcripts to a file. Along the way, it creates wav files and deletes them in order to accomplish transcription'''

#-------------------------------------------------------------------------------
# Libraries for globbing mp4 files
import os
import sys
import re
file_dir = os.path.dirname(__file__)       #required for embedded python
sys.path.append(file_dir)

# Libraries for dealing with movies and speech
from moviepy.editor import *
import speech_recognition as sr

# Label and date extraction functions
from helpers import extract_activities_or_locations
from helpers import extract_dogs
from helpers import get_datestring
from helpers import read_json_as_dict

# Custom errors for not being able to identify labels
from helpers import LabelError
import logging
from helpers import setup_logger

#-------------------------------------------------------------------------------
# Setup loggers to write debug info to
folder = '.'                                  #for now, everything in the working dir
setup_logger('matched', os.path.join(folder, 'matched.log'), level = logging.INFO)
setup_logger('unmatched', os.path.join(folder, 'unmatched.log'), level = logging.DEBUG)
setup_logger('unsuccessful', os.path.join(folder, 'unsuccessful.log'), level = logging.DEBUG)
matched = logging.getLogger('matched')
unmatched = logging.getLogger('unmatched')
unsuccessful = logging.getLogger('unsuccessful')

#-------------------------------------------------------------------------------
# Find all mp4 files (case insensitive) in the specified directory
#some constants
mov_exts = ['MP4', 'MTS']                           #capitalized for uniformity (original etension is capital)
mov_pattern = re.compile("|".join(mov_exts), re.IGNORECASE)    #look for the movie extensions

# Create list of mp4's
all_files = [filename
             for filename in os.listdir(folder)
             if os.path.isfile(os.path.join(folder, filename))]                                                         #first, list all files
mov_files = [filename
             for filename in all_files
             if mov_pattern.search(filename)]                                                                               #and then filter (case insensitive)

#-------------------------------------------------------------------------------
# Create audio files
aud_ext = 'wav'      #apparently the speech recognition works well with wav, so going with that
aud_pattern = re.compile(aud_ext, re.IGNORECASE)
extent = 15          #extent of video to transcribe (in seconds)

for filename in mov_files:
    try:
        clip = VideoFileClip(filename).subclip(0, extent)    #the subclip method specifies how much of the file to read
        clip.audio.write_audiofile(os.path.join(folder, mov_pattern.sub(aud_ext, filename)))
    except:
        unsuccessful.error("Could not convert video to audio. Video possibly not long enough")

#-------------------------------------------------------------------------------
# Here is where all the heavy lifting will happen. wav files will be transcribed, labels will be determined, and files renamed. Will look for exact matches for dog names and approximate matches for the other fields
#-------------------------------------------------------------------------------
# Read in the jsons and create lists of pronunciations (dictionary keys)
#distance threshold for activities and locations
acts_locs_threshold = 90

#how long to listen for noise (in seconds)
noise_duration = 1

#filenames and paths
dogs_dict, dogs_pros = read_json_as_dict(os.path.join(file_dir, 'dogs.json'))
activities_dict, activities_pros = read_json_as_dict(os.path.join(file_dir, 'activities.json'))
locations_dict, locations_pros = read_json_as_dict(os.path.join(file_dir, 'locations.json'))

# Initialize the recognizer
aud_files = [mov_pattern.sub(aud_ext, filename) for filename in mov_files]
r = sr.Recognizer()      #define the recognizer

# Loop through all the wav files, transcribe, determine labels, rename
for aud_file, mov_file in zip(aud_files, mov_files):
    extension = mov_file[-3::]
    aud_clip = sr.AudioFile(aud_file)
    with aud_clip as source:
        r.adjust_for_ambient_noise(source, duration = noise_duration)      #getting rid of noise
        recording = r.record(source)                          #this converts the audiofile into compatible audio data
    #need to 'try except' because if the recognizer doesn't recognize anything, it errors out. Also, extraction functions raise an error if they can't match
    try:
        transcript = r.recognize_google(recording)
        #determine dogs' names, activities, and locations
        dog_names = extract_dogs(transcript, dogs_dict, dogs_pros)
        activity_labels = extract_activities_or_locations("activities", transcript, activities_dict, activities_pros, acts_locs_threshold)
        location_labels = extract_activities_or_locations("locations", transcript, locations_dict, locations_pros, acts_locs_threshold)
        datestring = get_datestring(mov_file)
        final_filename = dog_names + ", " + activity_labels + ", " + location_labels + ", " + datestring + "." + extension
        #logging to files for debugging purposes. matched is if the final name determined via transcription is the same as the original, unmatched is if the names do not match up, and unsuccessful is if no name could be finalized
        if final_filename.lower() == mov_file.lower:
            matched.info(mov_file + " - " + final_filename)
        else:
            unmatched.debug(mov_file + " - " + final_filename)
            unmatched.debug("Transcript: " + transcript)
    except sr.UnknownValueError:
        unsuccessful.error(mov_file + " : " + "Nothing could be transcribed")
    except LabelError as e:
        unsuccessful.debug(mov_file)
        unsuccessful.debug("Transcript: " + transcript)
        unsuccessful.debug("Reason: " + e.message)

#-------------------------------------------------------------------------------
