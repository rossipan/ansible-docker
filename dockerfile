FROM centos:centos7
MAINTAINER Rossi Pan <rossipuc@gmail.com.tw>

ARG KUBE_VERSION=1.11.3
RUN yum clean all && \
    yum -y install epel-release && \
    yum -y install PyYAML python-jinja2 python-httplib2 python-keyczar python-paramiko python-setuptools git python-pip && \
    pip install ansible==2.7.8.0 && \
    mkdir /etc/ansible/ && \
    curl https://storage.googleapis.com/kubernetes-release/release/v${KUBE_VERSION}/bin/linux/amd64/kubectl -o ~/kubectl && \
    chmod +x ~/kubectl && \
    mv ~/kubectl /usr/bin/
COPY ansible.cfg /etc/ansible/
COPY ansible_plugins /usr/share/ansible_plugins/
COPY update.sh /bin/
COPY etcd* /bin/
WORKDIR /etc/ansible
