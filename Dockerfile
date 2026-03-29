# Builder builds a debian package.
FROM ubuntu:25.10 AS builder
RUN apt-get update
RUN apt-get --assume-yes install \
    build-essential \
    debhelper \
    devscripts \
    dh-virtualenv \
    equivs \
    libssl-dev \
    pipx \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-venv
RUN pipx install uv
WORKDIR /build/server
COPY uv.lock /build/server
COPY pyproject.toml README.md /build/server/
COPY debian /build/server/debian
COPY server /build/server/server
COPY config /build/server/config
RUN dpkg-buildpackage -us -uc -b

# This builds a runnable development server.
FROM ubuntu:25.10
WORKDIR /tmp
RUN apt-get update
RUN apt-get --assume-yes install \
    python3 \
    sudo
COPY --from=builder /build/* /tmp
RUN dpkg -i /tmp/server_0.1-1_*.deb
CMD service server restart && tail -F /opt/server/var/log/server.log
