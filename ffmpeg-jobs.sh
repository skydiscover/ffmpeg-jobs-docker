#!/bin/sh

if [ "$#" -ne 0 ] ; then
  exec $@
fi

JOBS_DIR="/jobs"
JOBS_INPUT_DIR="${JOBS_DIR}/input"
JOBS_DONE_DIR="${JOBS_DIR}/done"
JOBS_WORKING_DIR="${JOBS_DIR}/working"
VSTAT_FILE="/tmp/vstats"

display () # Calculate/collect progress 
{
START=$(date +%s); FR_CNT=0; ETA=0; ELAPSED=0
while [ -e /proc/$FF_PID ]; do
    sleep $DISPLAY_REFRESH_RATE
    VSTATS=$(tail -n 2 "$VSTAT_FILE" | sed -rn "s/.*frame= *([0-9]+).*/\1/p")
    if [ $VSTATS -gt $FR_CNT ]; then
        FR_CNT=$VSTATS
        PERCENTAGE=$(echo "scale=2; 100 * $FR_CNT / $TOT_FR" | bc)
        
    fi
    ELAPSED=$(echo "$(date +%s) - $START" | bc)
    ETA=$(date -d @$(awk 'BEGIN{print int(('$ELAPSED' / '$FR_CNT') * ('$TOT_FR' - '$FR_CNT'))}') -u +%H:%M:%S)
    FPS=$(echo "scale=2; $FR_CNT / $ELAPSED" | bc)
    echo "Frame:$FR_CNT of $TOT_FR Time:$(date -d @$ELAPSED -u +%H:%M:%S) FPS:$FPS ETA:$ETA Percent:$PERCENTAGE"
done
}

mkdir -p $JOBS_INPUT_DIR 2> /dev/null
mkdir -p $JOBS_DONE_DIR 2> /dev/null
mkdir -p $JOBS_WORKING_DIR 2> /dev/null
mkdir -p $(dirname "$VSTAT_FILE") 2> /dev/null

for FAILED_JOB in $JOBS_WORKING_DIR/*; do
  BASENAME=$(basename "$FAILED_JOB")
  if [ "$BASENAME" != "*" ]; then
    mv "$FAILED_JOB" "$JOBS_DONE_DIR/FAILED_$BASENAME"
  fi
done

while true ; do
  while [ -z "$(ls ${JOBS_INPUT_DIR})" ] ; do
    sleep $PULL_REFRESH_RATE
  done
  FILE=$(ls ${JOBS_INPUT_DIR} | head -n 1)
  mv "${JOBS_INPUT_DIR}/${FILE}" "${JOBS_WORKING_DIR}/."
  
  FF_OPTS=$(perl -ne 'print "$1\n" if /\b *ffmpeg +(.*)/' "${JOBS_WORKING_DIR}/${FILE}")
  VIDEOINPUT=$(echo "${FF_OPTS}" | perl -ne 'print "$1\n" if /\b(?:.* )?-i +\"([^\"]*)\"/')
  FPS=$(ffprobe "${VIDEOINPUT}" 2>&1 | sed -n "s/.*, \(.*\) tbr.*/\1/p")
  DUR=$(ffprobe "${VIDEOINPUT}" 2>&1 | sed -n "s/.* Duration: \([^,]*\), .*/\1/p")
  HRS=$(echo $DUR | cut -d":" -f1)
  MIN=$(echo $DUR | cut -d":" -f2)
  SEC=$(echo $DUR | cut -d":" -f3)
  TOT_FR=$(echo "($HRS*3600+$MIN*60+$SEC)*$FPS" | bc | cut -d"." -f1)
  
  if [ ! "$TOT_FR" -gt "0" ]; then 
    echo "ERROR, could not compute total frame number for file ${FILE}"
  exit; fi
  
  echo "Launching command: ffmpeg -vstats_file '${VSTAT_FILE}' ${FF_OPTS} 2>/dev/null"
  /bin/sh -c "ffmpeg -vstats_file '${VSTAT_FILE}' ${FF_OPTS}" 2>/dev/null &
  FF_PID=$!
  echo "Starting new instance of ffmpeg with pid: $FF_PID"
  echo "Encoding file: '$VIDEOINPUT'"
  echo "Length: $DUR - Frames: $TOT_FR"
  display
  echo "Finished encoding file: '$VIDEOINPUT'"
  rm -f "${VSTAT_FILE}"
  mv "${JOBS_WORKING_DIR}/${FILE}" "${JOBS_DONE_DIR}/${FILE}"
done
