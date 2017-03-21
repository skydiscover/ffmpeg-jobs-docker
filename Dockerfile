FROM jrottenberg/ffmpeg:latest

WORKDIR /

ENV DISPLAY_REFRESH_RATE=5 \
    PULL_REFRESH_RATE=5

RUN apt-get update && apt-get install -y bc

VOLUME /jobs
COPY "./ffmpeg-jobs.sh" "/ffmpeg-jobs.sh"
ENTRYPOINT ["/ffmpeg-jobs.sh"]
CMD [""]







