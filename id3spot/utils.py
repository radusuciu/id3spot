from colorama import Fore, Back, Style, init
from eyed3.id3.tag import Tag
from eyed3.utils.console import getTtySize, printMsg
from eyed3.plugins.classic import ClassicPlugin as DummyPlugin
from contextlib import redirect_stdout
import eyed3.plugins.classic as classic
import difflib
import io
import os


# hack to use eyed3.classic.ClassicPlugin to print tag info for us without having to provide args
class Dummy(object):
    def __getattr__(self, _): return None

DummyPlugin.args = Dummy()
DummyPlugin.terminal_width = getTtySize()[1] - 2

printTag = lambda tag: DummyPlugin.printTag(DummyPlugin, tag)

def printAudioInfo(info):
    if isinstance(info, classic.mp3.Mp3AudioInfo):
        printMsg(classic.boldText('  Time: ') +
                 '%s\tMPEG%d, Layer %s\t[ %s @ %s Hz - %s ]' %
                 (classic.utils.formatTime(info.time_secs),
                  info.mp3_header.version,
                  'I' * info.mp3_header.layer,
                  info.bit_rate_str,
                  info.mp3_header.sample_freq, info.mp3_header.mode))
        printMsg('-' * DummyPlugin.terminal_width)

def printHeader(file_path, new_name=None):
    file_len = len(file_path)
    from stat import ST_SIZE
    file_size = os.stat(file_path)[ST_SIZE]
    size_str = classic.utils.formatSize(file_size)
    size_len = len(size_str) + 5
    if file_len + size_len >= DummyPlugin.terminal_width:
        file_path = '...' + file_path[-(75 - size_len):]
        file_len = len(file_path)
    pat_len = DummyPlugin.terminal_width - file_len - size_len
    printMsg('%s%s%s[ %s ]%s' %
             (classic.boldText(file_path, c=classic.HEADER_COLOR()),
              classic.HEADER_COLOR(), ' ' * pat_len, size_str, classic.Fore.RESET))

def capture_fn_stdout(fn, *args):
    f = io.StringIO()
    with redirect_stdout(f):
        fn(*args)
    return f.getvalue()

def tag_to_string(tag):
    return capture_fn_stdout(printTag, tag or Tag())

def file_info_to_string(audio_file, tag, new_name=None):
    separator = '-' * DummyPlugin.terminal_width
    header = capture_fn_stdout(printHeader, audio_file.path, new_name)
    audio_info = capture_fn_stdout(printAudioInfo, audio_file.info)
    tag_string = tag_to_string(tag)
    return '\n{}{sep}{}{}{sep}'.format(header, audio_info, tag_string, sep=separator)

def color_diff(diff):
    for line in diff:
        if line.startswith('+'):
            yield Fore.GREEN + line + Fore.RESET
        elif line.startswith('-'):
            yield Fore.RED + line + Fore.RESET
        elif line.startswith('^'):
            yield Fore.BLUE + line + Fore.RESET
        else:
            yield line

def diff(first, second):
    return list(color_diff(difflib.ndiff(
        first.splitlines(keepends=True), second.splitlines(keepends=True)
    )))
