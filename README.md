# Chore Master Python

## Development

```sh
poetry install
```

## Deployment

```sh
sudo docker compose -f ./deployments/docker-compose.local.yml up -d --build
sudo docker compose -f ./deployments/docker-compose.local.yml down
```
