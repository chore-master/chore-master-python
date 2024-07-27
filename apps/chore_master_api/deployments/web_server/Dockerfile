FROM python:3.10-alpine

ARG SERVICE_NAME
ARG COMPONENT_NAME
ARG COMMIT_SHORT_SHA
ARG COMMIT_REVISION

ENV ENV=${ENV}
ENV SERVICE_NAME=${SERVICE_NAME}
ENV COMPONENT_NAME=${COMPONENT_NAME}
ENV COMMIT_SHORT_SHA=${COMMIT_SHORT_SHA}
ENV COMMIT_REVISION=${COMMIT_REVISION}

RUN apk --update --upgrade add \
    gcc musl-dev jpeg-dev zlib-dev libffi-dev cairo-dev pango-dev gdk-pixbuf-dev \
    git
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry config experimental.system-git-client true

WORKDIR /app/chore-master-python

COPY ./apps/chore_master_api/deployments/web_server/pyproject.toml /app/chore-master-python/pyproject.toml
RUN poetry install

COPY ./modules/ /app/chore-master-python/modules
COPY ./apps/chore_master_api/ /app/chore-master-python/apps/chore_master_api

CMD [ "poetry", "run", "python", "-m", "apps.chore_master_api.entrypoints.web_server" ]