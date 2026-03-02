# Commands Reference

This file lists git and docker commands used across this project (from docs/scripts and normal project workflow).

## Git Commands

```bash
git status
git status --short
git diff
git diff -- <path>
git add <path>
git add .
git commit -m "<message>"
git push
git pull
git checkout <branch>
git checkout -b codex/<branch-name>
git branch
git log --oneline --decorate --graph
```

## Docker / Docker Compose Commands

### Compose lifecycle
```bash
docker compose up
docker-compose up --build
docker-compose up -d
docker-compose build
docker-compose ps
docker-compose logs
docker-compose logs -f
docker-compose logs -f backend
docker-compose restart
docker-compose down
docker-compose down -v
```

### Compose exec
```bash
docker compose exec backend python seed_users.py
docker-compose exec backend python -c "<python_code>"
```

### Image build/push/login
```bash
docker build -t YOUR_DOCKERHUB_USERNAME/cable-ticketing-backend:latest ./backend
docker build -t YOUR_DOCKERHUB_USERNAME/cable-ticketing-frontend:latest ./frontend
docker push YOUR_DOCKERHUB_USERNAME/cable-ticketing-backend:latest
docker push YOUR_DOCKERHUB_USERNAME/cable-ticketing-frontend:latest
echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin
```

### Backup/restore helpers (used by ops scripts)
```bash
docker exec cable-ticketing-postgres pg_dump -U ticketing -d ticketing -Fc > <target>/ticketing.dump
docker exec -i cable-ticketing-postgres dropdb -U ticketing --if-exists ticketing
docker exec -i cable-ticketing-postgres createdb -U ticketing ticketing
cat <backup_path> | docker exec -i cable-ticketing-postgres pg_restore -U ticketing -d ticketing --clean --if-exists
```
