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
WORKDIR /build/backend
COPY uv.lock /build/backend
COPY pyproject.toml README.md /build/backend/
COPY debian /build/backend/debian
COPY backendlearnify /build/backend/backendlearnify
COPY config /build/backend/config
RUN dpkg-buildpackage -us -uc -b

# This builds a runnable development server.
FROM ubuntu:25.10
WORKDIR /tmp
RUN apt-get update
RUN apt-get --assume-yes install \
    python3 \
    sudo
COPY --from=builder /build/* /tmp
RUN dpkg -i /tmp/backend_0.1-1_*.deb
CMD service backend restart && tail -F /opt/backend/var/log/backend.log
