#!/bin/bash

VERSION=0.0.5

sed -i~ "s#SYSTEM_VERSION=.*#SYSTEM_VERSION=\"${VERSION}\" \\\\#" server/Dockerfile

sed -i~ "s#image: ncsa/criticalmaas-\([^:]*\):.*#image: ncsa/criticalmaas-\1:${VERSION}#" docker-compose.yml
sed -i~ "s#SYSTEM_VERSION: .*#SYSTEM_VERSION: \"${VERSION}\"#" docker-compose.yml
rm -f server/Dockerfile~ monitor/Dockerfile~ docker-compose.yml~
