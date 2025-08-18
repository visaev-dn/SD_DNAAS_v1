#!/usr/bin/env python3
"""
Test Consolidated Configuration Facade
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))


def main():
    from config_engine.configuration import ConfigurationManager

    mgr = ConfigurationManager()

    # Minimal builder_config mock
    builder_config = {
        'bridge_domain_name': 'test_bd',
        'topology_type': 'p2p',
        'devices': {
            'leaf1': {},
            'leaf2': {},
        },
        'interfaces': {
            'leaf1_ge100-0/0/1': {'name': 'ge100-0/0/1', 'device_name': 'leaf1', 'interface_type': 'access'},
            'leaf2_ge100-0/0/1': {'name': 'ge100-0/0/1', 'device_name': 'leaf2', 'interface_type': 'access'},
        },
        'vlans': {
            'vlan_251': {'vlan_id': 251, 'name': 'VLAN251', 'interfaces': []}
        }
    }

    gen = mgr.generate(builder_config, user_id=1)
    print(f"Generate: success={gen.success}, errors={gen.errors}")

    # Use a tiny config for diff/validate
    current_config = {}
    new_config = gen.config or {}

    diff = mgr.diff(current_config, new_config)
    print(f"Diff: added={diff.added_devices}, modified={diff.modified_devices}, removed={diff.removed_devices}, risk={diff.risk_level}")

    rep = mgr.validate(new_config)
    print(f"Validate: valid={rep.valid}, issues={len(rep.issues)}, warnings={len(rep.warnings)}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
