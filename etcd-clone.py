#!/usr/bin/env python

import sys
import os
import re

STAGE = os.getenv('STAGE') or 'dev'
CI_PROJECT_NAME = os.getenv('CI_PROJECT_NAME')
CI_COMMIT_REF_NAME = os.getenv('CI_COMMIT_REF_NAME')
ANSIBLE_ETCD_USER = os.getenv('ANSIBLE_ETCD_USER')
ANSIBLE_ETCD_PASSWORD = os.getenv('ANSIBLE_ETCD_PASSWORD')
ANSIBLE_ETCD_PREFIX = os.getenv('ANSIBLE_ETCD_PREFIX') or 'e3w_test'
ANSIBLE_ETCD_URL = os.getenv('ANSIBLE_ETCD_URL')
DEFAULT_VALUE = 'etcdv3_dir_$2H#%gRe3*t'

#error messages
older_version_not_found = 'older version not found at : {stage}/groupvars/{project}, nothing to do..'.format(
        stage=STAGE,
        project=CI_PROJECT_NAME
    )

version_format_not_match = 'CI_COMMIT_REF_NAME: {CI_COMMIT_REF_NAME} format not like x.x.x.xxxx, nothing to do..'.format(
        CI_COMMIT_REF_NAME=CI_COMMIT_REF_NAME,
    )

version_exists = 'CI_COMMIT_REF_NAME: {CI_COMMIT_REF_NAME} is exists at etcd, nothing to do..'.format(
        CI_COMMIT_REF_NAME=CI_COMMIT_REF_NAME,
    )

def get_all_key():
    try:
        result = os.popen("ETCDCTL_API=3 etcdctl --endpoints='{url}' --user='{user}:{password}' get --sort-by key --prefix {prefix}/{stage}/groupvars/{project} --keys-only".format(
            url=ANSIBLE_ETCD_URL,
            prefix=ANSIBLE_ETCD_PREFIX,
            stage=STAGE,
            project=CI_PROJECT_NAME,
            user=ANSIBLE_ETCD_USER,
            password=ANSIBLE_ETCD_PASSWORD
        )).readlines()

        if not result:
            print(older_version_not_found), sys.exc_info()[0]
            os._exit(0)

    except IOError, (errno, strerror):
        print "I/O error(%s): %s" % (errno, strerror)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise

    return result

def create_key(etcd_path, etcd_value):
    try:
        result = os.popen("ETCDCTL_API=3 etcdctl --endpoints='{url}' --user='{user}:{password}' put -- {prefix}/{etcd_path} '{value}' ".format(
            url=ANSIBLE_ETCD_URL,
            prefix=ANSIBLE_ETCD_PREFIX,
            etcd_path=etcd_path,
            value=etcd_value,
            user=ANSIBLE_ETCD_USER,
            password=ANSIBLE_ETCD_PASSWORD
        )).read()

        if not result:
            raise RuntimeError

        if etcd_value == DEFAULT_VALUE:
            print('create directory: "%s" is %s' % (etcd_path, result))
        else:
            print('create key: "%s" is %s' % (etcd_path, result))

    except IOError, (errno, strerror):
        print "I/O error(%s): %s" % (errno, strerror)
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise

def get_value(etcd_path):
    try:
        value = os.popen("ETCDCTL_API=3 etcdctl --endpoints='{url}' --user='{user}:{password}' get {prefix}/{etcd_path} --print-value-only ".format(
            url=ANSIBLE_ETCD_URL,
            prefix=ANSIBLE_ETCD_PREFIX,
            etcd_path=etcd_path,
            user=ANSIBLE_ETCD_USER,
            password=ANSIBLE_ETCD_PASSWORD
        )).read()

    except:
        return value

    if not value:
        raise RuntimeError('Key not found: %s' % etcd_path)  
    return value[0:-1] # replace value\n -> value

def get_older_version(data):
    release_version_list = []
    hit_release_pattern = r"^e3w_test\/" + re.escape(STAGE) + r"\/groupvars\/" + re.escape(CI_PROJECT_NAME) + r"\/[\d.]+$"

    for v in data:
        if re.match(hit_release_pattern, v):
            release_version = v.split('/')[4].replace('\n', '')

            if CI_COMMIT_REF_NAME >= release_version:
                release_version_list.append(release_version)

    #older version not found at etcd
    if len(release_version_list) == 0:
        print(older_version_not_found), sys.exc_info()[0]
        os._exit(0)

    ##release version is exists at etcd
    elif CI_COMMIT_REF_NAME in release_version_list:
        print(version_exists), sys.exc_info()[0]
        os._exit(0)

    else:
        older_version = sorted(release_version_list, reverse=True)[0]
        return older_version

def cloen_dir():

    all_key = get_all_key()
    older_version = get_older_version(all_key)
    create_dir = create_key(STAGE + '/groupvars/' + CI_PROJECT_NAME + '/' + CI_COMMIT_REF_NAME, DEFAULT_VALUE)

    hit_key_pattern = r"^e3w_test\/" + re.escape(STAGE) + r"\/groupvars\/" + re.escape(CI_PROJECT_NAME) + r"\/" + re.escape(older_version) + r"\/[\w]+$"
    for k in all_key:
        if re.match(hit_key_pattern, k):
            new_key = k.split('/')[5].replace('\n', '')
            new_value = get_value(STAGE + '/groupvars/' + CI_PROJECT_NAME + '/' + older_version + '/' + new_key)
            put_key = create_key(STAGE + '/groupvars/' + CI_PROJECT_NAME + '/' + CI_COMMIT_REF_NAME + '/' + new_key, new_value)


def main():
    print('## Run etcd-clone.py..')
    r = re.compile('^[\d.]+$')
    if r.match(CI_COMMIT_REF_NAME) is not None:
        cloen_dir()
    else:
        #release version format is not right
        print(version_format_not_match), sys.exc_info()[0]

if __name__ == "__main__":
    main()