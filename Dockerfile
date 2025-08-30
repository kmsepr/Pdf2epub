# Use Debian Trixie base image
FROM debian:trixie

# Set environment variables to avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TERM=xterm

# Update and install packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        xz-utils \
        fonts-dejavu-core \
        fonts-dejavu-mono \
        libexpat1 \
        libunistring5 \
        libidn2-0 \
        libp11-kit0 \
        libtasn1-6 \
        libgnutls30 \
        libpsl5 \
        libbrotli1 \
        libpng16-16 \
        libfreetype6 \
        libfontconfig1 \
        libglvnd0 \
        libopengl0 \
        libglu1-mesa \
        x11-common \
        libice6 \
        libsm6 \
        libxau6 \
        libxdmcp6 \
        libxcb1 \
        libx11-data \
        libx11-6 \
        libxext6 \
        libxrender1 \
        publicsuffix \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set a default command
CMD ["bash"]