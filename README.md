FFmpeg jobs and enhanced progress display
=========================================

This project just adds a shell script for jobs management and enhanced progress display to [Jrottenberg's FFmpeg container](https://github.com/jrottenberg/ffmpeg)
The added script is inspired from [this script](https://gist.github.com/pruperting/397509)

How to use it
-------------

First of all you can pull the image by running `docker pull skydiscover/ffmpeg-jobs` then run it like this:

```
docker run
    --name=ffmpeg-jobs
    -d \
    -v <my/jobs/dir>:/jobs \
    skydiscover/ffmpeg-jobs
```

Then the conainer will monitor files that are added in `/jobs/input` and process those jobs.
A job file contains only a ffmpeg command, like `ffmpeg -i "my-movie" -c:v libx264 -c:a copy "my_new_movie"`.

Obviously, files have to be accessible by the container, so add as many mounted volumes as you need to.
And for file in the job file, I highly advise you to just use double quotes `""` if filenames are complex.

Others variables can be passed to the container like this: `-e KEY=VALUE`.
Possible variables are:
```
DISPLAY_REFRESH_RATE - Time in seconds between log updates (default is 5 seconds)
PULL_REFRESH_RATE    - Time in seconds between job files search (default is 5 seconds)
```
