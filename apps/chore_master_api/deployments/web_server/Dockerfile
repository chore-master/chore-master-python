FROM python:3.11-bookworm

ARG SERVICE_NAME
ARG COMPONENT_NAME
ARG COMMIT_SHORT_SHA
ARG COMMIT_REVISION

ENV SERVICE_NAME=${SERVICE_NAME}
ENV COMPONENT_NAME=${COMPONENT_NAME}
ENV COMMIT_SHORT_SHA=${COMMIT_SHORT_SHA}
ENV COMMIT_REVISION=${COMMIT_REVISION}

RUN pip install poetry==1.8.3 && \
    poetry config virtualenvs.create false

WORKDIR /app/chore-master-python

COPY ./apps/chore_master_api/deployments/web_server/pyproject.toml /app/chore-master-python/pyproject.toml
COPY ./apps/chore_master_api/deployments/web_server/poetry.toml /app/chore-master-python/poetry.toml
RUN poetry install

COPY ./modules/ /app/chore-master-python/modules
COPY ./apps/chore_master_api/ /app/chore-master-python/apps/chore_master_api

CMD [ "poetry", "run", "python", "-m", "apps.chore_master_api.entrypoints.web_server" ]