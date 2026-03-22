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
WORKDIR /build/backend-learnify
COPY uv.lock /build/backend-learnify
COPY pyproject.toml README.md /build/backend-learnify/
COPY debian /build/backend-learnify/debian
COPY backendlearnify /build/backend-learnify/backendlearnify
COPY config /build/backend-learnify/config
RUN dpkg-buildpackage -us -uc -b

# This builds a runnable development server.
FROM ubuntu:25.10
WORKDIR /tmp
RUN apt-get update
RUN apt-get --assume-yes install \
    python3 \
    sudo
COPY --from=builder /build/* /tmp
RUN dpkg -i /tmp/backend-learnify_0.1-1_*.deb
CMD service backend-learnify restart && tail -F /opt/backend-learnify/var/log/backend-learnify.log
