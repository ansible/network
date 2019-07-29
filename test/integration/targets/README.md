## Running the tests

Note: These were run using `ansible 2.9.0.dev0`
Note: Update the `test/integration/targets/inventory.yml` file to reflect your appliance name/user/password etc.

```
$ cd test/integration/targets
$ ansible-playbook -i inventory.yml test.yml
```

## Test output

```
(venv) ➜  targets git:(bt_test_check) ✗ ansible-playbook -i inventory.yml test.yml

PLAY [all] ***********************************************************************************

TASK [vyos_interfaces : Collect all cli test cases] ******************************************
ok: [vyos101 -> localhost]

TASK [vyos_interfaces : Set test_items] ******************************************************
ok: [vyos101]

TASK [vyos_interfaces : Run test case (connection=network_cli)] ******************************
included: /home/bthornto/github/vyos_merge/network/test/integration/targets/vyos_interfaces/tests/cli/deleted.yaml for vyos101
included: /home/bthornto/github/vyos_merge/network/test/integration/targets/vyos_interfaces/tests/cli/overridden.yaml for vyos101
included: /home/bthornto/github/vyos_merge/network/test/integration/targets/vyos_interfaces/tests/cli/replaced.yaml for vyos101
included: /home/bthornto/github/vyos_merge/network/test/integration/targets/vyos_interfaces/tests/cli/merged.yaml for vyos101

TASK [vyos_interfaces : debug] ***************************************************************
ok: [vyos101] =>
  msg: Start vyos_interfaces deleted integration tests ansible_connection=network_cli

TASK [vyos_interfaces : include_tasks] *******************************************************
included: /home/bthornto/github/vyos_merge/network/test/integration/targets/vyos_interfaces/tests/cli/_populate.yaml for vyos101

TASK [vyos_interfaces : Setup] ***************************************************************
changed: [vyos101] => (item=eth1)
changed: [vyos101] => (item=eth2)
[DEPRECATION WARNING]: Distribution fedora 29 on host vyos101 should use /usr/bin/python3,
but is using /usr/bin/python for backward compatibility with prior Ansible releases. A future
 Ansible release will default to using the discovered platform python for this host. See
https://docs.ansible.com/ansible/devel/reference_appendices/interpreter_discovery.html for
more information. This feature will be removed in version 2.12. Deprecation warnings can be
disabled by setting deprecation_warnings=False in ansible.cfg.

TASK [vyos_interfaces : Delete attributes of given interfaces] *******************************
changed: [vyos101]

TASK [vyos_interfaces : Assert that the before dicts were correctly generated] ***************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Assert that the correct set of commands were generated] **************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Assert that the after dicts were correctly generated] ****************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Delete attributes of given interfaces (IDEMPOTENT)] ******************
ok: [vyos101]

TASK [vyos_interfaces : Assert that the previous task was idempotent] ************************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Assert that the before dicts were correctly generated] ***************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : include_tasks] *******************************************************
included: /home/bthornto/github/vyos_merge/network/test/integration/targets/vyos_interfaces/tests/cli/_remove_config.yaml for vyos101

TASK [vyos_interfaces : Remove Config] *******************************************************
ok: [vyos101] => (item=eth1)
ok: [vyos101] => (item=eth2)

TASK [vyos_interfaces : debug] ***************************************************************
ok: [vyos101] =>
  msg: START vyos_interfaces overridden integration tests on connection=network_cli

TASK [vyos_interfaces : include_tasks] *******************************************************
included: /home/bthornto/github/vyos_merge/network/test/integration/targets/vyos_interfaces/tests/cli/_populate.yaml for vyos101

TASK [vyos_interfaces : Setup] ***************************************************************
changed: [vyos101] => (item=eth1)
changed: [vyos101] => (item=eth2)

TASK [vyos_interfaces : Overrides all device configuration with provided configuration] ******
changed: [vyos101]

TASK [vyos_interfaces : Assert that before dicts were correctly generated] *******************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Assert that correct commands were generated] *************************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Assert that after dicts were correctly generated] ********************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Overrides all device configuration with provided configurations (IDEMPOTENT)] ***
ok: [vyos101]

TASK [vyos_interfaces : Assert that the previous task was idempotent] ************************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Assert that before dicts were correctly generated] *******************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : include_tasks] *******************************************************
included: /home/bthornto/github/vyos_merge/network/test/integration/targets/vyos_interfaces/tests/cli/_remove_config.yaml for vyos101

TASK [vyos_interfaces : Remove Config] *******************************************************
ok: [vyos101] => (item=eth1)
changed: [vyos101] => (item=eth2)

TASK [vyos_interfaces : debug] ***************************************************************
ok: [vyos101] =>
  msg: START vyos_interfaces replaced integration tests on connection=network_cli

TASK [vyos_interfaces : include_tasks] *******************************************************
included: /home/bthornto/github/vyos_merge/network/test/integration/targets/vyos_interfaces/tests/cli/_populate.yaml for vyos101

TASK [vyos_interfaces : Setup] ***************************************************************
changed: [vyos101] => (item=eth1)
changed: [vyos101] => (item=eth2)

TASK [vyos_interfaces : Replace device configurations of listed interfaces with provided configurations] ***
 [WARNING]: The value 100 (type int) in a string field was converted to u'100' (type string).
If this does not look like what you expect, quote the entire value to ensure it does not
change.

changed: [vyos101]

TASK [vyos_interfaces : Assert that correct set of commands were generated] ******************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Assert that before dicts are correctly generated] ********************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Assert that after dict is correctly generated] ***********************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Replace device configurations of listed interfaces with provided configurarions (IDEMPOTENT)] ***
ok: [vyos101]

TASK [vyos_interfaces : Assert that task was idempotent] *************************************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Assert that before dict is correctly generated] **********************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : include_tasks] *******************************************************
included: /home/bthornto/github/vyos_merge/network/test/integration/targets/vyos_interfaces/tests/cli/_remove_config.yaml for vyos101

TASK [vyos_interfaces : Remove Config] *******************************************************
changed: [vyos101] => (item=eth1)
changed: [vyos101] => (item=eth2)

TASK [vyos_interfaces : debug] ***************************************************************
ok: [vyos101] =>
  msg: START vyos_interfaces merged integration tests on connection=network_cli

TASK [vyos_interfaces : include_tasks] *******************************************************
included: /home/bthornto/github/vyos_merge/network/test/integration/targets/vyos_interfaces/tests/cli/_remove_config.yaml for vyos101

TASK [vyos_interfaces : Remove Config] *******************************************************
ok: [vyos101] => (item=eth1)
ok: [vyos101] => (item=eth2)

TASK [vyos_interfaces : Merge the provided configuration with the exisiting running configuration] ***
 [WARNING]: The value 101 (type int) in a string field was converted to u'101' (type string).
If this does not look like what you expect, quote the entire value to ensure it does not
change.

changed: [vyos101]

TASK [vyos_interfaces : Assert that before dicts were correctly generated] *******************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Assert that correct set of commands were generated] ******************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Assert that after dicts was correctly generated] *********************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Merge the provided configuration with the existing running configuration (IDEMPOTENT)] ***
ok: [vyos101]

TASK [vyos_interfaces : Assert that the previous task was idempotent] ************************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : Assert that before dicts were correctly generated] *******************
ok: [vyos101] => changed=false
  msg: All assertions passed

TASK [vyos_interfaces : include_tasks] *******************************************************
included: /home/bthornto/github/vyos_merge/network/test/integration/targets/vyos_interfaces/tests/cli/_remove_config.yaml for vyos101

TASK [vyos_interfaces : Remove Config] *******************************************************
changed: [vyos101] => (item=eth1)
changed: [vyos101] => (item=eth2)

PLAY RECAP ***********************************************************************************
vyos101                    : ok=54   changed=10   unreachable=0    failed=0    skipped=0    rescued=0    ignored=0

(venv) ➜  targets git:(bt_test_check) ✗
```
