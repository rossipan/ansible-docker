from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils.urls import open_url

import os

try:
    import json
except ImportError:
    import simplejson as json

ANSIBLE_ETCD_USER = os.getenv('ANSIBLE_ETCD_USER')
ANSIBLE_ETCD_PASSWORD = os.getenv('ANSIBLE_ETCD_PASSWORD')
ANSIBLE_ETCD_PREFIX = os.getenv('ANSIBLE_ETCD_PREFIX') or 'e3w_test'
ANSIBLE_ETCD_URL = os.getenv('ANSIBLE_ETCD_URL')

class Etcd:
    def __init__(self, url=ANSIBLE_ETCD_URL):
        self.url = url

    def get(self, key):
        try:
            value = os.popen('ETCDCTL_API=3 etcdctl get {prefix}/{key} --endpoints="{url}" --user="{user}:{password}" --print-value-only'.format(
                url=self.url,
                prefix=ANSIBLE_ETCD_PREFIX,
                key=key,
                user=ANSIBLE_ETCD_USER,
                password=ANSIBLE_ETCD_PASSWORD,
            )).read()
        except:
            return value

        if not value:
            raise RuntimeError('Key not found: %s' % key)  
        return value[0:-1] # replace value\n -> value

class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):
        etcd = Etcd()
        ret = []
        for term in terms:
            key = term.split()[0]
            value = etcd.get(key)
            ret.append(value)
        return ret