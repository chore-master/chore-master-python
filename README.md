# Chore Master Python

## Development

```sh
poetry install
```

```sh
sudo docker compose -f ./deployments/docker-compose.infra.yml up -d
sudo docker compose -f ./deployments/docker-compose.infra.yml down
```

## Release

```sh
TAG="2024-05-31-v1" && \
git tag $TAG --force && \
sudo docker buildx build \
    --platform linux/amd64 \
    -f deployments/chore_master_api/Dockerfile \
    --build-arg SERVICE_NAME="chore_master_api" \
    --build-arg COMPONENT_NAME="web_server" \
    --build-arg COMMIT_SHORT_SHA="$(git rev-parse --short HEAD)" \
    --build-arg COMMIT_REVISION="$TAG" \
    --tag "gocreating/chore_master_api_web_server:$TAG" \
    ./ && \
docker push "gocreating/chore_master_api_web_server:$TAG"
```

## Deployment

```sh
sudo docker compose -f ./deployments/docker-compose.local.yml up -d --build
sudo docker compose -f ./deployments/docker-compose.local.yml down
```
