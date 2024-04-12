#!/bin/bash

VERSION=0.0.4

sed -i~ "s#SYSTEM_VERSION=.*#SYSTEM_VERSION=\"${VERSION}\" \\\\#" Dockerfile
sed -i~ "s#image: ncsa/criticalmaas-cdr:.*#image: ncsa/criticalmaas-cdr:${VERSION}#" docker-compose.yml
sed -i~ "s#SYSTEM_VERSION: .*#SYSTEM_VERSION: \"${VERSION}\"#" docker-compose.yml
rm Dockerfile~ docker-compose.yml~

docker build -t ncsa/criticalmaas-cdr:${VERSION} .
