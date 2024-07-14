# Chore Master Python

## Development

```sh
poetry install
```

```sh
sudo docker compose -f ./apps/chore_master_api/deployments/docker-compose.infra.yml up -d
sudo docker compose -f ./apps/chore_master_api/deployments/docker-compose.infra.yml down
```

## Release

```sh
export TAG="2024-07-14-v2"
git tag $TAG --force
sudo docker buildx build \
    --platform linux/amd64 \
    -f apps/chore_master_api/deployments/web_server/Dockerfile \
    --build-arg SERVICE_NAME="chore_master_api" \
    --build-arg COMPONENT_NAME="web_server" \
    --build-arg COMMIT_SHORT_SHA="$(git rev-parse --short HEAD)" \
    --build-arg COMMIT_REVISION="$TAG" \
    --tag "gocreating/chore_master_api_web_server:$TAG" \
    ./
docker push "gocreating/chore_master_api_web_server:$TAG"
```

## Deployment

```sh
sudo docker compose -f ./apps/chore_master_api/deployments/docker-compose.local.yml up -d --build
sudo docker compose -f ./apps/chore_master_api/deployments/docker-compose.local.yml down
```
