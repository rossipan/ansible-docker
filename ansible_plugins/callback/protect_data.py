from ansible.plugins.callback.default import CallbackModule as CallbackModule_default
from ansible.utils.display import Display
from ansible.playbook.task_include import TaskInclude
from ansible import constants as C
import os, collections, re


class CallbackModule(CallbackModule_default):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'protect_data'

    def __init__(self):
        # From CallbackModule
        self._display = Display()
        self.disabled = False
        self.super_ref = super(CallbackModule, self)
        self.super_ref.__init__()

    def _get_item(self, result):
        if result.get('_ansible_no_log', False):
            item = "(censored due to no_log)"
        elif result.get('_ansible_item_label', False):
            item = result.get('_ansible_item_label')
        else:
            item = result.get('item', None)

        if not isinstance(item,dict):
            item = re.sub(r'(.*)\s--token\s([\w.-]+)\s(.*)', r'\1 --token **** \3', item)
        return item

    def v2_runner_item_on_ok(self, result):
        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        self._clean_results(result._result, result._task.action)
        if isinstance(result._task, TaskInclude):
            return
        elif result._result.get('changed', False):
            msg = 'changed'
            color = C.COLOR_CHANGED
        else:
            msg = 'ok'
            color = C.COLOR_OK

        if delegated_vars:
            msg += ": [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
        else:
            msg += ": [%s]" % result._host.get_name()

        msg += " => (item=%s)" % (self._get_item(result._result),)

        if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and '_ansible_verbose_override' not in result._result:
            msg += " => %s" % self._dump_results(result._result)
        self._display.display(msg, color=color)

    def v2_runner_item_on_failed(self, result):

        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        self._clean_results(result._result, result._task.action)
        self._handle_exception(result._result)

        msg = "failed: "
        if delegated_vars:
            msg += "[%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
        else:
            msg += "[%s]" % (result._host.get_name())

        self._handle_warnings(result._result)
        self._display.display(msg + " (item=%s) => %s" % (self._get_item(result._result), self._dump_results(result._result)), color=C.COLOR_ERROR)

    def hide_keyword(self, result):
        ret = {}
        for key, value in result.iteritems():
            if isinstance(value,str) or isinstance(value,unicode):
                ret[key] = re.sub(r'(.*)\s--token\s([\w.-]+)\s(.*)', r'\1 --token **** \3', value)
            else:
                ret[key] = value
        return ret

    def _dump_results(self, result, indent=None, sort_keys=True, keep_invocation=False):
        return super(CallbackModule, self)._dump_results(self.hide_keyword(result), indent, sort_keys, keep_invocation)