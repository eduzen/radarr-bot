FROM python:3.11-slim-bullseye as production

WORKDIR /code

RUN echo 'alias ll="ls -l"' >> ~/.bashrc

RUN apt-get update && \
  apt-get upgrade -y && \
  pip install --user --upgrade \
  pip \
  pip-tools \
  build \
  wheel

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
COPY . ./

CMD ["python", "/code/rbot"]


FROM production as development

COPY requirements-dev.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements-dev.txt

RUN pip install -e .


CMD ["python", "/code/rbot"]
