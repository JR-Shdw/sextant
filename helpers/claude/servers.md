# servers — démarrage / arrêt (IA)

Squelette générique. À copier dans `<projet>/claude/servers.md` et adapter
aux services tournant localement (workstation, lab, etc.).

## Services (exemple)

| Service | URL | Type | Container/process |
|---|---|---|---|
| sextant (CRUD) | http://127.0.0.1:8001 | python | `tools/server.py` |
| <service-a> | http://127.0.0.1:<port> | uvicorn | `module.app:obj` |
| <service-b> | http://127.0.0.1:<port> | container | `<container_name>` |

## Lancer

```bash
# sextant
cd <repo> && make serve

# autre service uvicorn
cd <repo> && nohup .venv/bin/uvicorn module.app:obj --host 127.0.0.1 --port <port> > /tmp/<service>.log 2>&1 & disown

# container
podman-compose -f <chemin>/docker-compose.yml up -d
```

## Vérifier

```bash
ss -tlnp | grep -E ":(<port-a>|<port-b>) "
podman ps --format "{{.Names}}\t{{.Ports}}"
```

## Arrêter

```bash
# python
make stop                                   # pour sextant
pkill -f "<repo>/.venv/bin/uvicorn"         # pour un autre uvicorn

# containers
podman-compose -f <chemin>/docker-compose.yml down
```
