# Makefile
BASE_PATH = /path/to/module
PREFIX = /usr/bin
SUDO = $(PREFIX)/sudo
DNF = $(SUDO) $(PREFIX)/dnf
VENV = $(PREFIX)/virtualenv
SERVICE = $(SUDO) $(PREFIX)/systemctl

install:
	@echo "Install base environment <--"
	@$(DNF) install -y mariadb-server mariadb nginx uwsgi \
		python-virtualenv python-pip python-devel gcc

	@echo "Create virtualenv and install packages <--"
	@$(VENV) venv; \
	source venv/bin/activate; \
	pip install -r requirements/prod.txt; \
	$(SUDO) pip install uwsgi

deploy: install
	@echo "Copy configuration files <--"
	@sed -i "s|<BASE_PATH>|"$(BASE_PATH)"|g" \
		deploy/uwsgi/nginx.conf \
		deploy/uwsgi/uwsgi.ini; \
	$(SUDO) cp deploy/uwsgi/nginx.conf /etc/nginx/conf.d/app.conf; \
	$(SUDO) cp deploy/uwsgi/uwsgi.ini /etc/uwsgi.d/; \
	$(SUDO) cp deploy/uwsgi/uwsgi.service /usr/lib/systemd/system/; \
	$(SERVICE) daemon-reload

	@echo "Deploy flask app <--"
	@source venv/bin/activate; \
	python manage.py deploy

run_server:
	@echo "Running services <--"
	@$(SERVICE) restart mariadb uwsgi nginx; \
	$(SERVICE) enable mariadb uwsgi nginx

stop_server:
	@echo "Stopping services <--"
	@$(SERVICE) stop nginx uwsgi mariadb

test:
	@echo "Running unit tests <--"
	@source venv/bin/activate; \
	python manage.py test
