import sys
from python_utils import file_utils
from python_utils import file_locations
import os

class SchemeConfig:
    def __init__(self, src_dir, extra_args=None):
        self.simple_name = "pcc_test_scheme"
        self.pantheon_dir = file_locations.pantheon_dir
        self.ld_library_path = src_dir + "core/"
        self.extra_args = extra_args
        self.recv_command = src_dir + "app/pccserver recv"
        self.send_command = src_dir + "app/pccclient send"
        self.pantheon_color = "blue"
        self.pantheon_marker = "*"

def is_scheme_in_pantheon(scheme_config):
    return file_utils.is_word_in_file(scheme_config.simple_name,
        os.path.join(scheme_config.pantheon_dir, TRAVIS_FILENAME))

def add_scheme_to_pantheon(src_dir, extra_args=None):
    scheme_config = SchemeConfig(src_dir, extra_args=extra_args)
    create_scheme_running_script(scheme_config)
    add_scheme_to_config(scheme_config)
    add_scheme_to_travis(scheme_config)
    return "pcc_test_scheme"

##
#   Setup for the script that is used to run the pcc senders/receivers.
##

RUNNING_SCRIPT_CLEAN_FILENAME = "run_scheme_clean.py"
RUNNING_SCRIPT_RECV_COMMAND_KEYWORD = "RUN_RECEIVER"
RUNNING_SCRIPT_SEND_COMMAND_KEYWORD = "RUN_SENDER"
RUNNING_SCRIPT_LD_LIBRARY_KEYWORD = "# Replaced with LD_LIBRARY_PATH if needed"
RUNNING_SCRIPT_LD_LIBRARY_FORMAT = "os.environ['LD_LIBRARY_PATH'] = '%s'"
RUNNING_SCRIPT_EXTRA_ARGS_KEYWORD = "# Replaced with extra args if needed"

def get_script_name(scheme_config):
    pantheon_src = os.path.join(scheme_config.pantheon_dir, "src")
    return os.path.join(pantheon_src, scheme_config.simple_name + ".py")

def copy_clean_running_script(scheme_config):
    file_utils.copy(os.path.join(scheme_config.pantheon_dir, RUNNING_SCRIPT_CLEAN_FILENAME),
        get_script_name(scheme_config))

def fill_in_running_script(scheme_config):
    script = get_script_name(scheme_config)
    file_utils.replace_in_file(script, RUNNING_SCRIPT_RECV_COMMAND_KEYWORD,
        "'%s'" % scheme_config.recv_command)
    file_utils.replace_in_file(script, RUNNING_SCRIPT_SEND_COMMAND_KEYWORD,
        "'%s'" % scheme_config.send_command)

def add_ld_library_path_to_running_script(scheme_config):
    script = get_script_name(scheme_config)
    file_utils.replace_in_file(script, RUNNING_SCRIPT_LD_LIBRARY_KEYWORD,
        RUNNING_SCRIPT_LD_LIBRARY_FORMAT % scheme_config.ld_library_path)

def add_extra_args_to_running_script(scheme_config):
    script = get_script_name(scheme_config)
    file_utils.replace_in_file(script, RUNNING_SCRIPT_EXTRA_ARGS_KEYWORD,
        "+ " + str(scheme_config.extra_args))

def create_scheme_running_script(scheme_config):
    copy_clean_running_script(scheme_config)
    fill_in_running_script(scheme_config)

    if (scheme_config.ld_library_path is not None):
        add_ld_library_path_to_running_script(scheme_config)
    
    if (scheme_config.extra_args is not None):
        add_extra_args_to_running_script(scheme_config)

##
#   Config setup. Copies a clean version of the Pantheon config file and adds the new scheme to
#   the file.
##

CONFIG_FILENAME = os.path.join("src", "config.yml")
CONFIG_CLEAN_FILENAME = os.path.join("src", "config.clean.yml")
CONFIG_FILE_NAME_KEYWORD = "EXPERIMENTAL_NAME_PLACEHOLDER"
CONFIG_FILE_COLOR_KEYWORD = "EXPERIMENTAL_COLOR_PLACEHOLDER"
CONFIG_FILE_MARKER_KEYWORD = "EXPERIMENTAL_MARKER_PLACEHOLDER"

def copy_clean_config_file(pantheon_dir):
    file_utils.copy(os.path.join(pantheon_dir, CONFIG_CLEAN_FILENAME),
        os.path.join(pantheon_dir, CONFIG_FILENAME))

def add_scheme_to_config(scheme_config):
    copy_clean_config_file(scheme_config.pantheon_dir)
    file_utils.replace_in_file(os.path.join(scheme_config.pantheon_dir, CONFIG_FILENAME),
        CONFIG_FILE_NAME_KEYWORD, scheme_config.simple_name)
    file_utils.replace_in_file(os.path.join(scheme_config.pantheon_dir, CONFIG_FILENAME),
        CONFIG_FILE_COLOR_KEYWORD, scheme_config.pantheon_color)
    file_utils.replace_in_file(os.path.join(scheme_config.pantheon_dir, CONFIG_FILENAME),
        CONFIG_FILE_MARKER_KEYWORD, "'%s'" % scheme_config.pantheon_marker)

##
#   Travis setup. Copies a clean version of the Pantheon travis script and adds the new scheme
#   to the script.
##

TRAVIS_FILENAME = ".travis.yml"
TRAVIS_CLEAN_FILENAME = ".travis.clean.yml"
TRAVIS_FILE_KEYWORD = "EXPERIMENTAL_NAME_PLACEHOLDER"

def copy_clean_travis_file(pantheon_dir):
    file_utils.copy(os.path.join(pantheon_dir, TRAVIS_CLEAN_FILENAME),
        os.path.join(pantheon_dir, TRAVIS_FILENAME))

def add_scheme_to_travis(scheme_config):
    print("adding scheme to travis")
    copy_clean_travis_file(scheme_config.pantheon_dir)
    file_utils.replace_in_file(os.path.join(scheme_config.pantheon_dir, TRAVIS_FILENAME),
        TRAVIS_FILE_KEYWORD, scheme_config.simple_name)
