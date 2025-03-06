# Chore Master Python

## Development

```sh
poetry install
poetry run python -m patchright install-deps chromium
poetry run python -m patchright install chromium
```

```sh
# it may take a while to start
sudo docker compose -f ./apps/chore_master_api/deployments/docker-compose.infra.yml -p chore_master_infra up -d
sudo docker compose -f ./apps/chore_master_api/deployments/docker-compose.infra.yml -p chore_master_infra down
```

## Release

```sh
export TAG="2025-03-07-v1"
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
docker push "gocreating/chore_master_api_web_server:$TAG" \
git push --tag
```

## Deployment

```sh
sudo docker compose -f ./apps/chore_master_api/deployments/docker-compose.local.yml up -d --build
sudo docker compose -f ./apps/chore_master_api/deployments/docker-compose.local.yml down
```
