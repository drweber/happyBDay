#!/usr/bin/env bash

repository="drweber"
appname="happy"
branch="master"
version=""
commit=$(LC_ALL=C tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1| awk '{print tolower($0)}')
port="8080"

while getopts :r:a:b:v: o; do
    case "${o}" in
        r)
            repository=${OPTARG}
            ;;
        a)
            appname=${OPTARG}
            ;;
        b)
            branch=${OPTARG}
            ;;
        p)
            port=${OPTARG}
            ;;
        v)
            version=${OPTARG}
            ;;
    esac
done
shift $((OPTIND-1))

if [ -z "${version}" ]; then
    image="${repository}/${appname}:${branch}-${commit}"
else
    image="${repository}:${version}"
fi

echo ">>>> Building image ${image} <<<<"

docker build --build-arg build_expose_port=${port} -t ${image} -f Dockerfile .

docker push ${image}
