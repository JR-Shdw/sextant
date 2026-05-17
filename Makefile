PY := .venv/bin/python
PIP := .venv/bin/pip
RUFF := .venv/bin/ruff
HOST := 127.0.0.1
PORT := 8001
LOG := /tmp/sextant_server.log
PIDFILE := /tmp/sextant_server.pid

.PHONY: help install lint scan leak-scan serve stop restart status ruff clean

help:
	@echo "Targets:"
	@echo "  install     creer .venv + installer deps"
	@echo "  lint        valider les YAML (catalog_lint.py)"
	@echo "  scan        regenerer catalog/files.yaml + _index.tsv"
	@echo "  leak-scan   chasser les IP RFC1918 hors allowlist"
	@echo "  serve       demarrer le serveur CRUD ($(HOST):$(PORT)) en background"
	@echo "  stop        arreter le serveur"
	@echo "  restart     stop + serve"
	@echo "  status      pid + port du serveur"
	@echo "  ruff        ruff check tools/"
	@echo "  clean       supprimer __pycache__ et fichiers generes"

install:
	python3 -m venv .venv
	$(PIP) install -q -r tools/requirements.txt

lint:
	$(PY) tools/catalog_lint.py

scan:
	$(PY) tools/catalog_scan.py

leak-scan:
	$(PY) tools/leak_scan.py

serve:
	@if [ -f $(PIDFILE) ] && kill -0 $$(cat $(PIDFILE)) 2>/dev/null; then \
	   echo "deja lance (pid $$(cat $(PIDFILE)))"; \
	else \
	   nohup $(PY) tools/server.py --host $(HOST) > $(LOG) 2>&1 & echo $$! > $(PIDFILE); \
	   sleep 1; \
	   ss -tlnp 2>/dev/null | grep $(PORT) || tail $(LOG); \
	fi

stop:
	@if [ -f $(PIDFILE) ] && kill -0 $$(cat $(PIDFILE)) 2>/dev/null; then \
	   kill $$(cat $(PIDFILE)) && echo "stoppe (pid $$(cat $(PIDFILE)))"; \
	   rm -f $(PIDFILE); \
	else echo "rien a stopper"; rm -f $(PIDFILE); fi

restart: stop serve

status:
	@if [ -f $(PIDFILE) ] && kill -0 $$(cat $(PIDFILE)) 2>/dev/null; then \
	   echo "pid $$(cat $(PIDFILE))"; \
	   ss -tlnp 2>/dev/null | grep $(PORT) || true; \
	else echo "serveur down"; fi

ruff:
	$(RUFF) check tools/

clean:
	find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} +
	rm -f catalog/files.yaml catalog/_index.tsv
