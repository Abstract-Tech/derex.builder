FROM ubuntu:18.04

RUN apt-get update -y
RUN apt-get -y install software-properties-common
RUN apt-add-repository -y ppa:projectatomic/ppa
RUN apt-get -y -qq update
RUN apt-get -y install buildah
RUN apt-get install -y libapparmor-dev libdevmapper-dev
COPY registries.conf /etc/containers/registries.conf

RUN apt-get update -y
RUN apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -

RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

RUN apt-get install -y docker-ce docker-ce-cli containerd.io

# Use with:
# docker run --rm --privileged --security-opt="seccomp=unconfined" --cap-add=ALL -v /var/lib/containers/:/var/lib/containers/:rw,Z -ti buildah
