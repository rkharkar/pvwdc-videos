import tkinter as tk
import tkinter.filedialog as fd
import os
import subprocess
import platform


class UserWindow:
    '''
    Creates the window for interacting with the user
    '''
    def __init__(self, config, renaming_method):
        '''
        :param config:
        The config file required for the program
        '''
        self.__root = tk.Tk()
        self.__renaming_method = renaming_method
        self.create_window(config)
        self.create_buttons(config)
        self.place_buttons()
        self.__root.mainloop()

    def create_window(self, config):
        '''Create the window according to specs in the config'''
        self.__root.title(config['DEFAULT']['window_title'])
        self.__root.geometry(config['DEFAULT']['window_props'])

    def open_file(self, filename):
        if platform.system() == 'Darwin':       # macOS
            subprocess.call(('open', filename))
        elif platform.system() == 'Windows':    # Windows
            os.startfile(filename)
        else:                                   # linux variants
            subprocess.call(('xdg-open', filename))

    def browse_folders(self, config):
        '''Browse and select folder with videos'''
        folderpath = fd.askdirectory(
            initialdir=config['DEFAULT']['videos_folder']
        )
        try:
            config['DEFAULT']['videos_folder'] = folderpath
            with open('settings.ini', 'w') as settingsfile:
                config.write(settingsfile)
        except TypeError:
            # Do nothing - user probably pressed cancel
            pass

    def create_buttons(self, config):
        '''Initializes the buttons in the UI'''
        self.__open_dogs_button = tk.Button(
            self.__root,
            text="Review dog names",
            command=lambda: self.open_file(
                os.path.abspath(config['DEFAULT']['dogs_file'])
            )
        )
        self.__open_activities_button = tk.Button(
            self.__root,
            text="Review activities",
            command=lambda: self.open_file(
                os.path.abspath(config['DEFAULT']['activities_file'])
            )
        )
        self.__open_locations_button = tk.Button(
            self.__root,
            text="Review Locations",
            command=lambda: self.open_file(
                os.path.abspath(config['DEFAULT']['locations_file'])
            )
        )
        self.__working_directory_button = tk.Button(
            self.__root,
            text="Set videos folder",
            command=lambda: self.browse_folders(config)
        )
        self.__runButton = tk.Button(
            self.__root, text="Rename",
            command=lambda: self.__renaming_method(self)
        )

    def place_buttons(self):
        self.__working_directory_button.pack(pady=10)
        self.__open_dogs_button.pack(pady=10)
        self.__open_activities_button.pack(pady=10)
        self.__open_locations_button.pack(pady=10)
        self.__runButton.pack(pady=10)

    def disable_ui(self):
        self.__runButton["state"] = "disabled"

    def enable_ui(self):
        self.__runButton["state"] = "normal"
