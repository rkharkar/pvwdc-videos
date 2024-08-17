'''This takes mp4 files in the given location, transcribes the first 15
seconds, and writes the transcripts to a file. Along the way, it creates
wav files and deletes them in order to accomplish transcription'''

# -------------------------------------------------------------------------------
from helpers import setup_logger
import logging
from helpers import LabelError
from helpers import rename_file
from helpers import read_yaml_as_dict
from helpers import get_datestring
from helpers import extract_dogs
from helpers import extract_activities_or_locations
import speech_recognition as sr
from moviepy.editor import VideoFileClip
import os
import re
import configparser
import tkinter as tk

# -------------------------------------------------------------------------------
# Read settings
config = configparser.ConfigParser()
config.read('settings.ini')
settings = config.defaults()


# -------------------------------------------------------------------------------
def setup_loggers():
    '''Setup loggers to write debug info to'''
    logs_vids_folder = settings['videos_folder']
    setup_logger(
        'matched',
        os.path.join(
            logs_vids_folder,
            'matched.log'),
        level=logging.INFO)
    setup_logger(
        'unmatched',
        os.path.join(
            logs_vids_folder,
            'unmatched.log'),
        level=logging.DEBUG)
    setup_logger(
        'unsuccessful',
        os.path.join(
            logs_vids_folder,
            'unsuccessful.log'),
        level=logging.DEBUG)


# -------------------------------------------------------------------------------
def rename_files(button_handle):
    '''Rename files found in the specified folder'''
    button_handle["state"] = "disabled"
    setup_loggers()
    matched = logging.getLogger('matched')
    unmatched = logging.getLogger('unmatched')
    unsuccessful = logging.getLogger('unsuccessful')
    supported_file_types = settings.get('supported_file_types').split(',')

    # ---------------------------------------------------------------------------
    # Find all mp4 files (case insensitive) in the specified directory
    # some constants
    # capitalized for uniformity (original etension is capital)
    mov_pattern = re.compile(
        "|".join(supported_file_types),
        re.IGNORECASE)  # look for the movie extensions

    logs_vids_folder = settings['videos_folder']
    # Create list of mp4's
    all_files = [
        os.path.join(
            logs_vids_folder,
            filename)
        for filename in os.listdir(logs_vids_folder) if os.path.isfile(
                os.path.join(
                    logs_vids_folder,
                    filename))]  # first, list all files
    # and then filter (case insensitive)
    mov_files = [filename
                 for filename in all_files
                 if mov_pattern.search(filename)]
    print(mov_files)

    # ---------------------------------------------------------------------------
    # Create audio files
    aud_ext = 'wav'
    # extent of video to transcribe (in seconds)
    extent = int(settings.get('audio_duration'))

    for filename in mov_files:
        try:
            # the subclip method specifies how much of the file to read
            clip = VideoFileClip(filename).subclip(0)
            if clip.duration < extent:
                raise Exception()
            clip15Seconds = clip.subclip(0, extent)
            audio_file_name = os.path.join(
                logs_vids_folder, mov_pattern.sub(
                    aud_ext, filename))
            clip15Seconds.audio.write_audiofile(audio_file_name)
            clip15Seconds.close()
            clip.close()
        except BaseException:
            unsuccessful.debug(filename)
            unsuccessful.error(
                """Could not convert video to audio. Video possibly not long
                enough""")
    # ---------------------------------------------------------------------------
    # Here is where all the heavy lifting will happen. wav files will be
    # transcribed, labels will be determined, and files renamed. Will look for
    # exact matches for dog names and approximate matches for the other fields
    # ---------------------------------------------------------------------------
    # Read in the yamls and create lists of pronunciations (dictionary keys)
    # distance threshold for activities and locations
    # filenames and paths
    dogs_dict, dogs_prons = read_yaml_as_dict(settings.get('dogs_file'))
    activities_dict, activites_prons = read_yaml_as_dict(
        settings.get('activities_file')
    )
    locations_dict, locations_prons = read_yaml_as_dict(
        settings.get('locations_file')
    )

    # Initialize the recognizer
    aud_files = [mov_pattern.sub(aud_ext, filename) for filename in mov_files]
    r = sr.Recognizer()  # define the recognizer

    acts_locs_threshold = int(settings.get('matching_threshold'))
    noise_duration = int(settings.get('noise_duration'))
    # Loop through all the wav files, transcribe, determine labels, rename
    for aud_file, mov_file in zip(aud_files, mov_files):
        extension = mov_file[-3::]
        aud_clip = sr.AudioFile(aud_file)
        try:
            with aud_clip as source:
                r.adjust_for_ambient_noise(
                    source, duration=noise_duration)  # getting rid of noise
                # this converts the audiofile into compatible audio data
                recording = r.record(source)
            # need to 'try except' because if the recognizer doesn't recognize
            # anything, it errors out. Also, extraction functions raise an
            # error if they can't match
            transcript = r.recognize_google(recording)
            # determine dogs' names, activities, and locations
            dog_names = extract_dogs(transcript, dogs_dict, dogs_prons)
            activity_labels = extract_activities_or_locations(
                "activities",
                transcript,
                activities_dict,
                activites_prons,
                acts_locs_threshold
            )
            location_labels = extract_activities_or_locations(
                "locations",
                transcript,
                locations_dict,
                locations_prons,
                acts_locs_threshold
            )
            datestring = get_datestring(mov_file)
            final_filename = dog_names + ", " + activity_labels + ", " + \
                location_labels + ", " + datestring + "." + extension
            # logging to files for debugging purposes. matched is if the final
            # name determined via transcription is the same as the original,
            # unmatched is if the names do not match up, and unsuccessful is
            # if no name could be finalized
            if final_filename.lower() == mov_file.lower:
                matched.info(mov_file)
            else:
                unmatched.debug(mov_file + " - " + final_filename)
                unmatched.debug("Transcript: " + transcript)
            os.remove(aud_file)
            rename_file(
                mov_file,
                os.path.join(logs_vids_folder, final_filename)
            )
        except sr.UnknownValueError:
            unsuccessful.error(
                mov_file + " : " + "Nothing could be transcribed"
            )
            os.remove(aud_file)
        except LabelError as e:
            unsuccessful.debug(mov_file)
            unsuccessful.debug("Transcript: " + transcript)
            unsuccessful.debug("Reason: " + e.message)
            os.remove(aud_file)
        except BaseException:
            unsuccessful.debug(mov_file)
            unsuccessful.debug("Reason: Possibly could not access file")
    # ---------------------------------------------------------------------------

    button_handle["state"] = "normal"


# -------------------------------------------------------------------------------
def create_gui():
    root = tk.Tk()
    root.title(settings.get('window_title'))
    root.geometry(settings.get('window_props'))
    button = tk.Button(
        root, text="Rename",
        command=lambda: rename_files(button)
    )
    button.pack(pady=20)
    root.mainloop()


create_gui()
