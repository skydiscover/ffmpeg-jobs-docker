import os
import time
import shlex
import logging
import subprocess
import pexpect
import argparse
import io
import re
from tqdm import tqdm

JOBS_DIR="/jobs"
JOBS_INPUT_DIR="%s/input" % JOBS_DIR
JOBS_DONE_DIR="%s/done" % JOBS_DIR
JOBS_WORKING_DIR="%s/working" % JOBS_DIR
VSTAT_FILE="/tmp/vstats"
PULL_REFRESH_RATE=1
DISPLAY_REFRESH_RATE=1

class TqdmToLogger(io.StringIO):
    """
        Output stream for TQDM which will output to logger module instead of
        the StdOut.
    """
    logger = None
    level = None
    buf = ''
    def __init__(self,logger,level=None):
        super(TqdmToLogger, self).__init__()
        self.logger = logger
        self.level = level or logging.INFO
    def write(self,buf):
        self.buf = buf.strip('\r\n\t ')
    def flush(self):
        self.logger.log(self.level, self.buf)

def monitor_ffmpeg_cmd(ffmpeg_cmd):
    ffargs = shlex.split(ffmpeg_cmd)
    input_file = ffargs[ffargs.index("-i") + 1]
    logger.info("analysing for frame count")
    # video_fps = eval(
        # re.findall(
            # r'r_frame_rate="([^"]+)"',
            # str(subprocess.check_output([u"ffprobe", input_file.encode("utf-8"), u"-v", u"0", u"-select_streams", u"v:0", u"-print_format", u"flat", u"-show_entries", u"stream=r_frame_rate"])))[0])
    # logging.debug("Video framerate is %5.02f" % video_fps)
    # tmp = subprocess.check_output([u"ffprobe", input_file.encode("utf-8"), u"-v", u"0", u"-select_streams", u"v:0", u"-print_format", u"flat", u"-show_entries", u"stream=duration"])
    # duration = re.findall(
            # r'duration="([^"]+)"',
            # str(subprocess.check_output([u"ffprobe", input_file.encode("utf-8"), u"-v", u"0", u"-select_streams", u"v:0", u"-print_format", u"flat", u"-show_entries", u"stream=duration"])))[0]
    # if duration != "N/A":
        # logging.debug("Video duration is %5.02f sec" % duration)
        # frame_count = int(video_fps * float(duration))
    # else:
        # logging.warning("Could not fetch duration with ffprobe, emulating a Video lenght of 3 hours")
        # frame_count = int(video_fps * 10800.)
    frame_count = int(subprocess.check_output([u"mediainfo", u"--Language=raw", u"-f", u"--Inform=Video;%FrameCount%", input_file.encode("utf-8")]))
    logger.info("frame count is %d" % frame_count)
    
    logger.info("launching command %s" % ffmpeg_cmd)
    pbar = tqdm(total=frame_count, file=tqdm_out, mininterval=args.display_refresh_rate, desc=os.path.basename(ffargs[-1]), ncols=200, unit='frame', smoothing=0)
    old_frame = 0
    # thread = pexpect.spawn(ffmpeg_cmd.encode("utf-8"), encoding='utf-8')
    thread = pexpect.spawn(u"ffmpeg", shlex.split(ffmpeg_cmd)[1:], encoding='utf-8')
    cpl = thread.compile_pattern_list([pexpect.EOF, "frame= *\d+", '(.+)'])
    while True:
        i = thread.expect_list(cpl, timeout=None)
        if i == 0: # EOF
            logger.debug("the sub process exited")
            pbar.close()
            break
        elif i == 1:
            frame_number = int(re.findall(r"frame= *(\d+)", thread.match.group(0))[0])
            pbar.update(frame_number - old_frame)
            old_frame = frame_number
            # thread.close
        elif i == 2:
            #unknown_line = thread.match.group(0)
            #print unknown_line
            pass

argparser = argparse.ArgumentParser()
argparser.add_argument('--pull-refresh-rate', dest='pull_refresh_rate', metavar='number',
                       type=int, default=10,
                       help='interval in seconds between two check of input folder')
argparser.add_argument('--display-refresh-rate', dest='display_refresh_rate', metavar='number',
                       type=int, default=10,
                       help='interval in seconds between two display refresh')
args = argparser.parse_args()
            
logging.basicConfig(format='[%(levelname)s] %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

tqdm_out = TqdmToLogger(logger,level=logging.INFO)
            
if not os.path.exists(JOBS_INPUT_DIR):
    os.makedirs(JOBS_INPUT_DIR)
if not os.path.exists(JOBS_DONE_DIR):
    os.makedirs(JOBS_DONE_DIR)
if not os.path.exists(JOBS_WORKING_DIR):
    os.makedirs(JOBS_WORKING_DIR)
if not os.path.exists(os.path.dirname(VSTAT_FILE)):
    os.makedirs(os.path.dirname(VSTAT_FILE))
    
for file in os.listdir(JOBS_WORKING_DIR):
    logger.warning("Found older processing file: %s" % file)
    os.rename("%s/%s" % (JOBS_WORKING_DIR, file), "%s/FAILED_%s" % (JOBS_DONE_DIR, file))
    
    
while True:
    files = os.listdir(JOBS_INPUT_DIR)
    logger.debug("files: %s" % str(files))
    if len(files) == 0:
        time.sleep(args.pull_refresh_rate)
        continue
        
    for file in files:
        with open("%s/%s" % (JOBS_INPUT_DIR, file), 'r', encoding='utf-8') as ifile:
            ffmpeg_cmd = ifile.read()
            
        nb_input = shlex.split(ffmpeg_cmd).count("-i")
        if nb_input == 1:
            # Normal use
            os.rename("%s/%s" % (JOBS_INPUT_DIR, file), "%s/%s" % (JOBS_WORKING_DIR, file))
            monitor_ffmpeg_cmd(ffmpeg_cmd)
            os.rename("%s/%s" % (JOBS_WORKING_DIR, file), "%s/%s" % (JOBS_DONE_DIR, file))
        elif nb_input > 1:
            # Anormal, but still valid use
            pass
        else:
            # 0 occurence ?
            logger.warning("No input file in ffmpeg command ?")
            continue