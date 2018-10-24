from shutil import copyfile
import fileinput

def is_word_in_file(word, filename):
    return word in open(filename).read()

def copy(filename, new_filename):
    copyfile(filename, new_filename)

def replace_in_file(filename, to_replace, replacement):
    with fileinput.FileInput(filename, inplace=True, backup='.bak') as f:
        for line in f:
            print(line.replace(to_replace, replacement), end='')
