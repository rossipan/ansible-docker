#!/usr/bin/env python

import yaml
import sys
import os

FILENAME = sys.argv[1]
STAGE = os.getenv('STAGE') or 'dev'
CI_PROJECT_NAME = os.getenv('CI_PROJECT_NAME')
CI_COMMIT_REF_NAME = os.getenv('CI_COMMIT_REF_NAME')
ANSIBLE_ETCD_USER = os.getenv('ANSIBLE_ETCD_USER')
ANSIBLE_ETCD_PASSWORD = os.getenv('ANSIBLE_ETCD_PASSWORD')
ANSIBLE_ETCD_PREFIX = os.getenv('ANSIBLE_ETCD_PREFIX') or 'e3w_test'
ANSIBLE_ETCD_URL = os.getenv('ANSIBLE_ETCD_URL')
DEFAULT_VALUE = 'etcdv3_dir_$2H#%gRe3*t'

with open(FILENAME, 'rb') as f:
    conf = yaml.load(f.read())    # load the config file

def process(**params):
    for key, value in params.items():
        path = '%s/groupvars/%s/%s/%s' % ( STAGE, CI_PROJECT_NAME, CI_COMMIT_REF_NAME, key)
        put(path, value)


def put(etcd_path, etcd_value):
    try:
        result = os.popen("ETCDCTL_API=3 etcdctl --endpoints='{url}' --user='{user}:{password}' put -- {prefix}/{etcd_path} '{value}' ".format(
            url=ANSIBLE_ETCD_URL,
            prefix=ANSIBLE_ETCD_PREFIX,
            etcd_path=etcd_path,
            stage=STAGE,
            tag=CI_COMMIT_REF_NAME,
            project=CI_PROJECT_NAME,
            value=etcd_value,
            user=ANSIBLE_ETCD_USER,
            password=ANSIBLE_ETCD_PASSWORD,
        )).read()

        if not result:
            raise RuntimeError

        if etcd_value == DEFAULT_VALUE:
            print('set directory: "%s" is %s' % (etcd_path, result))
        else:
            print('set key "%s" "%s" is %s' % (etcd_path, etcd_value, result))

    except IOError, (errno, strerror):
        print "I/O error(%s): %s" % (errno, strerror)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise

create_stage = put(STAGE, DEFAULT_VALUE)
create_groupvars = put(STAGE + '/groupvars', DEFAULT_VALUE)
create_project = put(STAGE + '/groupvars/' + CI_PROJECT_NAME, DEFAULT_VALUE)

list_pathlist =''
for path in CI_COMMIT_REF_NAME.split('/'):
    list_pathlist = (list_pathlist + '/' + path)
    put(STAGE + '/groupvars/' + CI_PROJECT_NAME + list_pathlist, DEFAULT_VALUE)

process(**conf)
