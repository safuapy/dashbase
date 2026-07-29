FROM phusion/baseimage:bionic-1.0.0
LABEL maintainer="Dashbase Developers"
LABEL description="Dockerised Dashbase Core, built from CI"

ARG USER_ID
ARG GROUP_ID

ENV HOME /home/dashbase

# add user with specified (or default) user/group ids
ENV USER_ID ${USER_ID:-1000}
ENV GROUP_ID ${GROUP_ID:-1000}
RUN groupadd -g ${GROUP_ID} dashbase && \
    useradd -u ${USER_ID} -g dashbase -s /bin/bash -m -d /home/dashbase dashbase && \
    mkdir /home/dashbase/.dashbase && \
    chown ${USER_ID}:${GROUP_ID} -R /home/dashbase

COPY bin/* /usr/local/bin/

RUN chmod a+x /usr/local/bin/*

USER dashbase

VOLUME ["/home/dashbase"]

EXPOSE 9998 9999 19998 19999

WORKDIR /home/dashbase
