#!/usr/bin/env python
"""Check difference in time between two objects,
where an object may be:

- a file
- a systemd unit

Result will contain:

- newer: true if src is newer than dest
- older: true if src is older than dest
"""

import os
import subprocess
# import getpass
from ansible.module_utils.basic import AnsibleModule


def get_systemd_time(name):
    command = [
        'systemctl',
        'show',
        '--property', 'ExecMainStartTimestamp',
    ]

    components = name.split(':', 2)
    if components[0] == 'systemd':
        components = components[1:]
    if components[0] == 'user':
        components = components[1:]
        command.append('--user')

    command.append(':'.join(components))

    output = subprocess.check_output(command)

    timestamp = output.split('=')[1]
    if not timestamp:
        return None

    # Use GNU date to translate to seconds since epoch
    secs_str = subprocess.check_output([
        'date',
        '-d', timestamp,
        '+%s',
    ])
    return int(secs_str)


def get_file_time(name):
    components = name.split(':', 1)
    if components[0] == 'file':
        name = components[1]
    stat = os.stat(name)
    return stat.st_mtime


def get_time(name):
    if name.startswith('systemd:'):
        return get_systemd_time(name)
    elif name.startswith('file:') or name.startswith('/'):
        return get_file_time(name)
    raise ValueError("Cannot interpret '%s'" % name)


def update_result(result, module):
    src = module.params['src']
    dest = module.params['dest']

    src_time = get_time(src)
    dest_time = get_time(dest)

    delta = dest_time - src_time

    result['src_time'] = src_time
    result['dest_time'] = dest_time
    result['delta'] = delta

    if delta < 0:
        result['newer'] = True
    elif delta > 0:
        result['older'] = True


def run_module():
    module_args = dict(
        src=dict(type='str', required=True),
        dest=dict(type='str', required=True),
    )

    result = dict(
        changed=False,
        newer=False,
        older=False,
    )
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    update_result(result, module)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
