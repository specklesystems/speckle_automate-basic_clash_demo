FROM debian:bullseye-slim

# Install basic packages
RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  gnupg \
  netbase \
  wget; \
  rm -rf /var/lib/apt/lists/*

# Install version control systems and procps
RUN apt-get update && apt-get install -y --no-install-recommends \
  git \
  mercurial \
  openssh-client \
  subversion \
  procps; \
  rm -rf /var/lib/apt/lists/*

# Install various development tools and libraries
RUN set -ex; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
  autoconf \
  automake \
  bzip2 \
  dpkg-dev \
  file \
  g++ \
  gcc \
  imagemagick \
  libbz2-dev \
  libc6-dev \
  libcurl4-openssl-dev \
  libdb-dev \
  libevent-dev \
  libffi-dev \
  libgdbm-dev \
  libglib2.0-dev \
  libgmp-dev \
  libjpeg-dev \
  libkrb5-dev \
  liblzma-dev \
  libmagickcore-dev \
  libmagickwand-dev \
  libmaxminddb-dev \
  libncurses5-dev \
  libncursesw5-dev \
  libpng-dev \
  libpq-dev \
  libreadline-dev \
  libsqlite3-dev \
  libssl-dev \
  libtool \
  libwebp-dev \
  libxml2-dev \
  libxslt-dev \
  libyaml-dev \
  make \
  patch \
  unzip \
  xz-utils \
  zlib1g-dev \
  $(if apt-cache show 'default-libmysqlclient-dev' 2>/dev/null | grep -q '^Version:'; then \
  echo 'default-libmysqlclient-dev'; \
  else \
  echo 'libmysqlclient-dev'; \
  fi); \
  rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV LANG=C.UTF-8

# Install additional libraries
RUN /bin/sh -c set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
  libbluetooth-dev \
  tk-dev \
  uuid-dev; \
  rm -rf /var/lib/apt/lists/*

# Set GPG key and Python version
ENV GPG_KEY=A035C8C19219BA821ECEA86B64E628F8D684696D
ENV PYTHON_VERSION=3.10.13

# Install Python from source
RUN /bin/sh -c set -eux; \
  wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz"; \
  wget -O python.tar.xz.asc "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc"; \
  GNUPGHOME="$(mktemp -d)"; export GNUPGHOME; \
  gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys "$GPG_KEY"; \
  gpg --batch --verify python.tar.xz.asc python.tar.xz; \
  gpgconf --kill all; \
  rm -rf "$GNUPGHOME" python.tar.xz.asc; \
  mkdir -p /usr/src/python; \
  tar --extract --directory /usr/src/python --strip-components=1 --file python.tar.xz; \
  rm python.tar.xz; \
  cd /usr/src/python; \
  gnuArch="$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)"; \
  ./configure \
  --build="$gnuArch" \
  --enable-loadable-sqlite-extensions \
  --enable-optimizations \
  --enable-option-checking=fatal \
  --enable-shared \
  --with-lto \
  --with-system-expat \
  --without-ensurepip; \
  nproc="$(nproc)"; \
  EXTRA_CFLAGS="$(dpkg-buildflags --get CFLAGS)"; \
  LDFLAGS="$(dpkg-buildflags --get LDFLAGS)"; \
  make -j "$nproc" \
  "EXTRA_CFLAGS=${EXTRA_CFLAGS:-}" \
  "LDFLAGS=${LDFLAGS:-}" \
  "PROFILE_TASK=${PROFILE_TASK:-}"; \
  rm python; \
  make -j "$nproc" \
  "EXTRA_CFLAGS=${EXTRA_CFLAGS:-}" \
  "LDFLAGS=${LDFLAGS:--Wl},-rpath='\$\$ORIGIN/../lib'" \
  "PROFILE_TASK=${PROFILE_TASK:-}" \
  python; \
  make install; \
  bin="$(readlink -ve /usr/local/bin/python3)"; \
  dir="$(dirname "$bin")"; \
  mkdir -p "/usr/share/gdb/auto-load/$dir"; \
  cp -vL Tools/gdb/libpython.py "/usr/share/gdb/auto-load/$bin-gdb.py"; \
  cd /; \
  rm -rf /usr/src/python; \
  find /usr/local -depth \
  \( \
  \( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
  -o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \) \
  \) -exec rm -rf '{}' +; \
  ldconfig; \
  python3 --version

# Create symlinks for Python tools
RUN /bin/sh -c set -eux; \
  for src in idle3 pydoc3 python3 python3-config; do \
  dst="$(echo "$src" | tr -d 3)"; \
  [ -s "/usr/local/bin/$src" ]; \
  [ ! -e "/usr/local/bin/$dst" ]; \
  ln -svT "$src" "/usr/local/bin/$dst"; \
  done

# Set Python pip and setuptools versions and install pip
ENV PYTHON_PIP_VERSION=23.0.1
ENV PYTHON_SETUPTOOLS_VERSION=65.5.1
ENV PYTHON_GET_PIP_URL=https://github.com/pypa/get-pip/raw/c6add47b0abf67511cdfb4734771cbab403af062/public/get-pip.py
ENV PYTHON_GET_PIP_SHA256=22b849a10f86f5ddf7ce148ca2a31214504ee6c83ef626840fde6e5dcd809d11
RUN /bin/sh -c set -eux; \
  wget -O get-pip.py "$PYTHON_GET_PIP_URL"; \
  echo "$PYTHON_GET_PIP_SHA256 *get-pip.py" | sha256sum -c -; \
  export PYTHONDONTWRITEBYTECODE=1; \
  python get-pip.py \
  --disable-pip-version-check \
  --no-cache-dir \
  --no-compile \
  "pip==$PYTHON_PIP_VERSION" \
  "setuptools==$PYTHON_SETUPTOOLS_VERSION"; \
  rm -f get-pip.py; \
  pip --version


# Set working directory
WORKDIR /root/

# Set build arguments
ARG BRANCH=main
ARG NUM_CORES=10

# Clone a git repository
RUN /bin/sh -c "git clone --single-branch --depth 1 -b $BRANCH https://github.com/nuvolos-cloud/PyMesh.git"

# Set environment variables
ENV PYMESH_PATH=/root/PyMesh
ENV NUM_CORES=10

# Install additional packages
RUN echo "deb http://ftp.us.debian.org/debian unstable main contrib non-free" >> /etc/apt/sources.list.d/unstable.list && \
  apt-get update && apt-get install -y \
  gcc-9 \
  g++-9 \
  git \
  cmake \
  libgmp-dev \
  libmpfr-dev \
  libgmpxx4ldbl \
  libboost-dev \
  libboost-thread-dev \
  zip unzip patchelf && \
  apt-get clean

# Build and install PyMesh
WORKDIR /root/PyMesh

RUN git clone --depth 1 https://github.com/PyMesh/cgal.git $PYMESH_PATH/third_party/cgal
RUN git clone --depth 1 https://github.com/PyMesh/libigl.git $PYMESH_PATH/third_party/libigl
RUN git clone --depth 1 https://github.com/PyMesh/carve.git $PYMESH_PATH/third_party/carve
RUN git clone --depth 1 https://github.com/PyMesh/cork.git $PYMESH_PATH/third_party/cork
RUN git clone --depth 1 https://github.com/PyMesh/tetgen.git $PYMESH_PATH/third_party/tetgen
RUN git clone --depth 1 https://github.com/PyMesh/qhull.git $PYMESH_PATH/third_party/qhull
RUN git clone --depth 1 https://github.com/PyMesh/Clipper.git $PYMESH_PATH/third_party/Clipper
RUN git clone --depth 1 https://github.com/PyMesh/eigen.git $PYMESH_PATH/third_party/eigen
RUN git clone --depth 1 https://github.com/PyMesh/pybind11.git $PYMESH_PATH/third_party/pybind11
RUN git clone --depth 1 https://github.com/PyMesh/geogram.git $PYMESH_PATH/third_party/geogram
RUN git clone --depth 1 https://github.com/PyMesh/draco.git $PYMESH_PATH/third_party/draco
RUN git clone --depth 1 https://github.com/PyMesh/TetWild.git $PYMESH_PATH/third_party/TetWild
RUN git clone --depth 1 https://github.com/PyMesh/WindingNumber.git $PYMESH_PATH/third_party/WindingNumber
RUN git clone --depth 1 https://github.com/PyMesh/tbb.git $PYMESH_PATH/third_party/tbb
RUN git clone --depth 1 https://github.com/PyMesh/jigsaw.git $PYMESH_PATH/third_party/jigsaw
RUN git clone --depth 1 https://github.com/fmtlib/fmt.git $PYMESH_PATH/third_party/fmt
RUN git clone --depth 1 https://github.com/gabime/spdlog.git $PYMESH_PATH/third_party/spdlog

RUN git submodule update --init third_party/triangle
RUN git submodule update --init third_party/quartet
RUN git submodule update --init third_party/mmg
RUN git submodule update --init third_party/json

RUN pip install -r $PYMESH_PATH/python/requirements.txt
RUN ./setup.py bdist_wheel
RUN rm -rf build_3.7 third_party/build 
RUN python $PYMESH_PATH/docker/patches/patch_wheel.py dist/pymesh2*.whl
RUN pip install --upgrade pip
RUN pip install dist/pymesh2*.whl

# Build third-party libraries for PyMesh
WORKDIR /root/PyMesh/third_party
RUN /bin/sh -c "python ./build.py mmg && python ./build.py tetgen"

# We install poetry to generate a list of dependencies which will be required by our application
RUN pip install poetry

# We set the working directory to be the /home/speckle directory; all of our files will be copied here.
WORKDIR /home/speckle

# Copy all of our code and assets from the local directory into the /home/speckle directory of the container.
# We also ensure that the user 'speckle' owns these files, so it can access them
# This assumes that the Dockerfile is in the same directory as the rest of the code
COPY . /home/speckle

# Using poetry, we generate a list of requirements, save them to requirements.txt, and then use pip to install them
RUN poetry export --format requirements.txt --output /home/speckle/requirements.txt --without-hashes && \
    pip install --requirement /home/speckle/requirements.txt