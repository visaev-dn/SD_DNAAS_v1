#!/usr/bin/env python3
"""
Test the bundle parser with actual output
"""

import sys
import os

# Add the parent directory to the path so we can import from utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.cli_parser import DNOSCLIParser

def test_bundle_parser():
    """Test the bundle parser with sample output"""
    
    # Sample output from 'show interfaces' command
    sample_output = """
DNAAS-LEAF-B14(06-Jul-2025-17:00:53)# show interfaces

Legend: i - inner vlan, u - unnumbered interface, b - interface disabled due to breakout, L2 - l2 service interface, s - suspended IPv6 address, p - primary IP address (has secondaries), d - obtained via DHCP, v - VLAN list or range (only lowest VID is displayed), m - VLAN manipulation or L2-originated-vlans configuration is configured


| Interface                |  Admin   | Operational     | IPv4 Address           | IPv6 Address
                   | VLAN          | MTU  | Network-Service                             | Bundle-Id  |
+--------------------------+----------+-----------------+------------------------+--------------------------
-------------------+---------------+------+---------------------------------------------+------------+
| bundle-445 (L2)          | enabled  | down            |                        |
                   | (m)           | 1518 | BD (g_rgorlovsky_v445_NCP3-TO-CL16)         |            |
| bundle-447               | enabled  | up              |                        |
                   |               | 1514 | VRF (default)                               |            |
| bundle-447.447 (L2)      | enabled  | up              |                        |
                   | 447           | 1518 | BD (g_rgorlovsky_v447_NCP3-TO-CL16)         |            |
| bundle-60000             | enabled  | up              |                        |
                   |               | 9288 | VRF (default)                               |            |
| bundle-60000.150 (L2)    | enabled  | up              |                        |
                   | 150           | 9292 | BD (g_zkeiserman_v150_to_wan)               |            |
| bundle-60000.151 (L2)    | enabled  | up              |                        |
                   | 151           | 9292 | BD (g_zkeiserman_v150_to_wan)               |            |
| bundle-60000.210 (L2)    | enabled  | up              |                        |
                   | 210           | 9292 | BD (g_yor_v210_PE-3-WAN_v13)                |            |
| bundle-60000.211 (L2)    | enabled  | up              |                        |
                   | 211           | 9292 | BD (g_yor_v211_EVPN-v11_CE)                 |            |
| bundle-60000.251 (L2)    | enabled  | up              |                        |
                   | 251           | 9292 | BD (g_visaev_v251_to_Spirent)               |            |
| bundle-60000.253 (L2)    | enabled  | up              |                        |
                   | 253           | 9292 | BD (g_visaev_v253_Spirent)                  |            |
| bundle-60000.431 (L2)    | enabled  | up              |                        |
                   | 433           | 9292 | VRF (default)                               |            |
| bundle-60000.432 (L2)    | enabled  | up              |                        |
                   | 434           | 9292 | VRF (default)                               |            |
| bundle-60000.441 (L2)    | enabled  | up              |                        |
                   | 441           | 9292 | VRF (default)                               |            |
| bundle-60000.442 (L2)    | enabled  | up              |                        |
                   | 442           | 9292 | BD (g_rgorlovsky_v442_NCP3-TO-CL16)         |            |
| bundle-60000.443 (L2)    | enabled  | up              |                        |
                   | 443           | 9292 | BD (g_rgorlovsky_v443_NCP3-TO-CL16)         |            |
| bundle-60000.444 (L2)    | enabled  | up              |                        |
                   | 444           | 9292 | BD (g_rgorlovsky_v444_NCP3-TO-CL16)         |            |
| bundle-60000.445 (L2)    | enabled  | up              |                        |
                   | 445           | 9292 | BD (g_rgorlovsky_v445_NCP3-TO-CL16)         |            |
-- More -- (Press q to quit)
"""
    
    parser = DNOSCLIParser()
    bundles = parser.parse_bundle_interfaces(sample_output)
    
    print("Bundle parsing test results:")
    print(f"Found {len(bundles)} bundles:")
    
    for bundle_name, bundle in bundles.items():
        print(f"  - {bundle_name}: status={bundle.status}, interfaces={bundle.interfaces}")

def test_lacp_counters_parser():
    """Test the LACP counters parser with sample output"""
    
    # Sample output from 'show lacp counters' command
    sample_output = """
DNAAS-LEAF-B14(06-Jul-2025-17:00:56)# show lacp counters

| Interface                |  Admin   | Operational     | IPv4 Address           | IPv6 Address
                   | VLAN          | MTU  | Network-Service                             | Bundle-Id  |
+--------------------------+----------+-----------------+------------------------+--------------------------
-------------------+---------------+------+---------------------------------------------+------------+
| bundle-445 (L2)          | enabled  | down            |                        |
                   | (m)           | 1518 | BD (g_rgorlovsky_v445_NCP3-TO-CL16)         |            |
| ge100-0/0/9              | enabled  | down            |                        |
                   |               | 1514 | VRF (default)                               | 445        |
| ge100-0/0/10             | enabled  | down            |                        |
                   |               | 1514 | VRF (default)                               | 445        |
| bundle-60000             | enabled  | up              |                        |
                   |               | 9288 | VRF (default)                               |            |
| ge100-0/0/36             | enabled  | up              |                        |
                   |               | 9288 | VRF (default)                               | 60000      |
| ge100-0/0/37             | enabled  | up              |                        |
                   |               | 9288 | VRF (default)                               | 60000      |
| ge100-0/0/38             | enabled  | up              |                        |
                   |               | 9288 | VRF (default)                               | 60000      |
| ge100-0/0/39             | enabled  | up              |                        |
                   |               | 9288 | VRF (default)                               | 60000      |
-- More -- (Press q to quit)
"""
    
    parser = DNOSCLIParser(debug=True)
    bundles = parser.parse_lacp_counters(sample_output)
    
    print("\nLACP counters parsing test results:")
    print(f"Found {len(bundles)} bundles:")
    
    for bundle_name, bundle in bundles.items():
        print(f"  - {bundle_name}: status={bundle.status}, interfaces={bundle.interfaces}")

if __name__ == "__main__":
    test_bundle_parser()
    test_lacp_counters_parser() 