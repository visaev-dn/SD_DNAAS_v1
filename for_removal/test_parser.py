#!/usr/bin/env python3

def parse_lacp_xml_debug(xml_content):
    """Debug version of LACP XML parser."""
    bundles = []
    
    lines = xml_content.split('\n')
    current_bundle = None
    in_members_section = False
    in_member_section = False
    
    print("=== DEBUG PARSING ===")
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Find bundle interface start
        if '<interface>' in line and 'bundle-' in line:
            print(f"Line {i}: Found bundle interface start: {line}")
            current_bundle = {
                'name': '',
                'members': [],
                'lacp_mode': 'unknown',
                'period': 'unknown'
            }
            in_members_section = False
            in_member_section = False
        
        # Find bundle name
        elif '<name>' in line and 'bundle-' in line and current_bundle:
            bundle_name = line.replace('<name>', '').replace('</name>', '').strip()
            current_bundle['name'] = bundle_name
            print(f"Line {i}: Found bundle name: {bundle_name}")
        
        # Start of members section
        elif '<members>' in line and current_bundle:
            in_members_section = True
            print(f"Line {i}: Entered members section")
        
        # End of members section
        elif '</members>' in line and current_bundle:
            in_members_section = False
            print(f"Line {i}: Exited members section")
        
        # Start of member section
        elif '<member>' in line and current_bundle and in_members_section:
            in_member_section = True
            print(f"Line {i}: Entered member section")
        
        # End of member section
        elif '</member>' in line and current_bundle and in_members_section:
            in_member_section = False
            print(f"Line {i}: Exited member section")
        
        # Find member interfaces (inside member tags)
        elif '<interface>' in line and 'ge' in line and current_bundle and in_member_section:
            member = line.replace('<interface>', '').replace('</interface>', '').strip()
            if member and member not in current_bundle['members']:
                current_bundle['members'].append(member)
                print(f"Line {i}: Found member: {member}")
        
        # Find LACP mode
        elif '<lacp-mode>' in line and current_bundle:
            mode = line.replace('<lacp-mode>', '').replace('</lacp-mode>', '').strip()
            current_bundle['lacp_mode'] = mode
            print(f"Line {i}: Found LACP mode: {mode}")
        
        # Find period
        elif '<period>' in line and current_bundle:
            period = line.replace('<period>', '').replace('</period>', '').strip()
            current_bundle['period'] = period
            print(f"Line {i}: Found period: {period}")
        
        # End of bundle interface
        elif '</interface>' in line and current_bundle and current_bundle['name'] and not in_members_section:
            if current_bundle['name'] and current_bundle['name'] not in [b['name'] for b in bundles]:
                bundles.append(current_bundle)
                print(f"Line {i}: Completed bundle: {current_bundle}")
            current_bundle = None
    
    print(f"=== FINAL RESULT: {len(bundles)} bundles ===")
    for bundle in bundles:
        print(f"Bundle: {bundle['name']}, Members: {bundle['members']}")
    
    return bundles

# Test with a small sample
test_xml = """<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
	<drivenets-top xmlns="http://drivenets.com/ns/yang/dn-top">
		<protocols xmlns="http://drivenets.com/ns/yang/dn-protocol">
			<lacp xmlns="http://drivenets.com/ns/yang/dn-lacp">
				<interfaces>
					<interface>
						<name>bundle-60000</name>
						<members>
							<member>
								<interface>ge100-0/0/36</interface>
								<config-items>
									<interface>ge100-0/0/36</interface>
								</config-items>
							</member>
							<member>
								<interface>ge100-0/0/37</interface>
								<config-items>
									<interface>ge100-0/0/37</interface>
								</config-items>
							</member>
						</members>
						<config-items>
							<name>bundle-60000</name>
							<period>short</period>
							<lacp-mode>active</lacp-mode>
						</config-items>
					</interface>
				</interfaces>
			</lacp>
		</protocols>
	</drivenets-top>
</config>"""

if __name__ == "__main__":
    parse_lacp_xml_debug(test_xml) 