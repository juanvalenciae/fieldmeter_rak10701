INSTALL_DIR ?= /opt
PREFIX ?= /usr/local
APP_NAME := fieldmeter_rak10701

APP_DIR := ${INSTALL_DIR}/${APP_NAME}
ENV_DIR := ${APP_DIR}/${APP_NAME}.pyenv

install:
	mkdir -p "${APP_DIR}"
	python3 -m venv "${ENV_DIR}"
	${ENV_DIR}/bin/python -m pip install -r requirements.txt
	install -Dm755 main.py ${APP_DIR}/
	cp -r lib ${APP_DIR}/
	sed -i "s;/usr/bin/python3;${ENV_DIR}/bin/python -W ignore;" ${APP_DIR}/main.py
	ln -sf "${APP_DIR}/main.py" "${PREFIX}/bin/${APP_NAME}"

uninstall:
	rm ${PREFIX}/bin/${APP_NAME}
	rm -rf ${APP_DIR}
