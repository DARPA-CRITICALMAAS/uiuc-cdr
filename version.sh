#!/bin/bash

VERSION=0.3.0

sed -i~ "s#SYSTEM_VERSION=.*#SYSTEM_VERSION=\"${VERSION}\" \\\\#" cdrhook/Dockerfile

sed -i~ "s#SYSTEM_VERSION=.*#SYSTEM_VERSION=\"${VERSION}\"#" .env
sed -i~ "s#SYSTEM_VERSION=.*#SYSTEM_VERSION=\"${VERSION}\"#" env.example

rm -f server/Dockerfile~ .env~ env.example~
