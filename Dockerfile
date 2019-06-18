FROM python:3.6-slim

WORKDIR /usr/src/app

ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100
ENV POETRY_VERSION=0.12.16
ENV PATH=$PATH:/usr/src/app

COPY pyproject.toml poetry.lock ./

ENV RUN_DEPS libyaml-dev

RUN set -ex ; \
    apt-get update ; \
    # Install run dependencies
    apt-get install -y --no-install-recommends \
      $RUN_DEPS ; \
    # Install poetry
    pip install "poetry==$POETRY_VERSION" ; \
    poetry config settings.virtualenvs.create false ; \
    # Install python dependencies
    poetry install --no-interaction --no-ansi ; \
    # Clean apt
    apt-get autoremove -y ; \
    apt-get clean -y ; \
    rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["poetry", "run", "sb"]
