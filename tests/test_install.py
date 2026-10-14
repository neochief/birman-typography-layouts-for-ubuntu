"""Installer regressions with system writes and GSettings replaced by test doubles.

Run with: python3 -m unittest discover -s tests -v
"""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


INSTALLER = Path(__file__).resolve().parents[1] / 'install.sh'
SCHEMA = 'org.gnome.desktop.input-sources'


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name)
        self.state = self.path / 'settings.json'
        self.calls = self.path / 'calls.jsonl'
        self.env = dict(os.environ, PATH=str(self.path) + os.pathsep + os.environ['PATH'],
                        TEST_SETTINGS=str(self.state), TEST_CALLS=str(self.calls),
                        TEST_UID='1000')
        self.write_command('id', '#!/bin/sh\nprintf "%s\\n" "$TEST_UID"\n')
        self.write_command('sudo', '''#!/usr/bin/env python3
import json, os, sys
with open(os.environ['TEST_CALLS'], 'a') as log:
    log.write(json.dumps(['sudo'] + sys.argv[1:]) + '\\n')
''')
        # Do not read or modify the host's installed XKB files.
        self.write_command('grep', '#!/bin/sh\nexit 1\n')
        self.write_command('gsettings', '''#!/usr/bin/env python3
import ast, json, os, pathlib, sys
path = pathlib.Path(os.environ['TEST_SETTINGS'])
state = json.loads(path.read_text())
args = sys.argv[1:]
with open(os.environ['TEST_CALLS'], 'a') as log:
    log.write(json.dumps(['gsettings'] + args) + '\\n')
key = args[1] + '/' + args[2]
if args[0] == 'get':
    value = state[key]
    print(repr(value) if value else '@as []')
elif args[0] == 'set':
    if os.environ.get('TEST_FAIL_SET') == args[2]:
        sys.exit(1)
    state[key] = ast.literal_eval(args[3])
    path.write_text(json.dumps(state))
else:
    sys.exit(2)
''')

    def write_command(self, name, content):
        command = self.path / name
        command.write_text(content)
        command.chmod(0o755)

    def run_installer(self, options):
        self.state.write_text(json.dumps({SCHEMA + '/xkb-options': options}))
        result = subprocess.run(['bash', str(INSTALLER)], input='n\n',
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                universal_newlines=True, env=self.env)
        state = json.loads(self.state.read_text())
        calls = [json.loads(line) for line in self.calls.read_text().splitlines()] \
            if self.calls.exists() else []
        return result, state, calls

    def test_root_is_rejected_before_any_changes(self):
        self.env['TEST_UID'] = '0'
        result, state, calls = self.run_installer(['grp:alt_shift_toggle'])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('without sudo', result.stderr)
        self.assertEqual(calls, [])
        self.assertEqual(state[SCHEMA + '/xkb-options'], ['grp:alt_shift_toggle'])

    def test_existing_options_are_preserved(self):
        options = ['grp:alt_shift_toggle', 'compose:rwin', 'caps:escape']
        result, state, _ = self.run_installer(options)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state[SCHEMA + '/xkb-options'], options + ['lv3:ralt_switch'])
        self.assertEqual(state[SCHEMA + '/sources'],
                         [['xkb', 'us+typo-birman-en'], ['xkb', 'ru+typo-birman-ru']])

    def test_empty_typed_array_is_supported(self):
        result, state, _ = self.run_installer([])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state[SCHEMA + '/xkb-options'], ['lv3:ralt_switch'])

    def test_existing_altgr_is_not_duplicated_or_rewritten(self):
        options = ['lv3:ralt_switch', 'compose:rwin']
        result, state, calls = self.run_installer(options)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(state[SCHEMA + '/xkb-options'], options)
        self.assertFalse(any(call[:4] == ['gsettings', 'set', SCHEMA, 'xkb-options']
                             for call in calls))

    def test_failed_option_write_does_not_report_success(self):
        self.env['TEST_FAIL_SET'] = 'xkb-options'
        result, state, _ = self.run_installer(['compose:rwin'])
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Done!', result.stdout)
        self.assertEqual(state[SCHEMA + '/xkb-options'], ['compose:rwin'])


if __name__ == '__main__':
    unittest.main()
