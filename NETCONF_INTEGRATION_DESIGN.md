# NETCONF Integration Design for Bridge Domain Topology Editor

## **Overview**

Instead of parsing SSH CLI output, using NETCONF (Network Configuration Protocol) would provide a standardized, structured approach to configuration management. NETCONF offers XML-based configuration data, standardized operations, and better error handling compared to CLI parsing.

## **Current SSH CLI vs. NETCONF Comparison**

### **Current SSH CLI Approach:**
```bash
# SSH to device and execute commands
ssh admin@DNAAS-LEAF-B13
show running-config bridge-domain
show running-config interface bundle-60000.255
show running-config vlan

# Parse unstructured text output
bridge-domain g_visaev_v255
 admin-state enable
 interface bundle-60000.255
 interface ge100-0/0/34
```

### **NETCONF Approach:**
```xml
<!-- NETCONF get-config request -->
<rpc message-id="101" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <get-config>
    <source>
      <running/>
    </source>
    <filter type="subtree">
      <bridge-domains xmlns="http://drivenets.com/ns/yang/dnos-bridge-domain">
        <bridge-domain>
          <name>g_visaev_v255</name>
          <admin-state/>
          <interfaces/>
        </bridge-domain>
      </bridge-domains>
    </filter>
  </get-config>
</rpc>

<!-- Structured XML response -->
<rpc-reply message-id="101" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <data>
    <bridge-domains xmlns="http://drivenets.com/ns/yang/dnos-bridge-domain">
      <bridge-domain>
        <name>g_visaev_v255</name>
        <admin-state>enabled</admin-state>
        <interfaces>
          <interface>
            <name>bundle-60000.255</name>
            <type>subinterface</type>
            <vlan-id>255</vlan-id>
          </interface>
          <interface>
            <name>ge100-0/0/34</name>
            <type>physical</type>
          </interface>
        </interfaces>
      </bridge-domain>
    </bridge-domains>
  </data>
</rpc-reply>
```

## **NETCONF Architecture for Bridge Domain Management**

### **1. NETCONF Client Implementation**

```python
import xml.etree.ElementTree as ET
from ncclient import manager
from ncclient.xml_ import to_ele, to_xml
import logging

class DNOSNetconfClient:
    """
    NETCONF client for DNOS devices
    """
    
    def __init__(self, host: str, username: str, password: str, port: int = 830):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.logger = logging.getLogger(__name__)
        
        # DNOS-specific YANG namespaces
        self.namespaces = {
            'nc': 'urn:ietf:params:xml:ns:netconf:base:1.0',
            'dnos-bd': 'http://drivenets.com/ns/yang/dnos-bridge-domain',
            'dnos-if': 'http://drivenets.com/ns/yang/dnos-interfaces',
            'dnos-vlan': 'http://drivenets.com/ns/yang/dnos-vlan'
        }
    
    def connect(self) -> manager.Manager:
        """
        Establish NETCONF connection to device
        
        Returns:
            NETCONF manager connection
        """
        try:
            connection = manager.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                hostkey_verify=False,
                device_params={'name': 'default'},
                allow_agent=False,
                look_for_keys=False
            )
            self.logger.info(f"NETCONF connection established to {self.host}")
            return connection
        except Exception as e:
            self.logger.error(f"Failed to connect to {self.host}: {e}")
            raise
    
    def get_bridge_domains(self, connection: manager.Manager) -> Dict:
        """
        Retrieve all bridge domain configurations via NETCONF
        
        Args:
            connection: NETCONF manager connection
            
        Returns:
            Dictionary of bridge domain configurations
        """
        # Build NETCONF get-config request
        filter_xml = f"""
        <filter type="subtree">
            <bridge-domains xmlns="{self.namespaces['dnos-bd']}">
                <bridge-domain>
                    <name/>
                    <admin-state/>
                    <interfaces>
                        <interface>
                            <name/>
                            <type/>
                            <vlan-id/>
                        </interface>
                    </interfaces>
                </bridge-domain>
            </bridge-domains>
        </filter>
        """
        
        try:
            # Send get-config request
            response = connection.get_config(source='running', filter=filter_xml)
            
            # Parse XML response
            bridge_domains = self.parse_bridge_domains_response(response)
            
            self.logger.info(f"Retrieved {len(bridge_domains)} bridge domains from {self.host}")
            return bridge_domains
            
        except Exception as e:
            self.logger.error(f"Failed to get bridge domains from {self.host}: {e}")
            raise
    
    def get_interface_configs(self, connection: manager.Manager) -> Dict:
        """
        Retrieve interface configurations via NETCONF
        
        Args:
            connection: NETCONF manager connection
            
        Returns:
            Dictionary of interface configurations
        """
        filter_xml = f"""
        <filter type="subtree">
            <interfaces xmlns="{self.namespaces['dnos-if']}">
                <interface>
                    <name/>
                    <type/>
                    <admin-state/>
                    <subinterfaces>
                        <subinterface>
                            <index/>
                            <vlan-id/>
                        </subinterface>
                    </subinterfaces>
                </interface>
            </interfaces>
        </filter>
        """
        
        try:
            response = connection.get_config(source='running', filter=filter_xml)
            interfaces = self.parse_interfaces_response(response)
            
            self.logger.info(f"Retrieved {len(interfaces)} interfaces from {self.host}")
            return interfaces
            
        except Exception as e:
            self.logger.error(f"Failed to get interfaces from {self.host}: {e}")
            raise
    
    def parse_bridge_domains_response(self, response) -> Dict:
        """
        Parse NETCONF response for bridge domains
        
        Args:
            response: NETCONF response XML
            
        Returns:
            Parsed bridge domain configurations
        """
        bridge_domains = {}
        
        # Parse XML response
        root = ET.fromstring(response.xml)
        
        # Find bridge domains in response
        for bridge_domain in root.findall('.//dnos-bd:bridge-domain', self.namespaces):
            name_elem = bridge_domain.find('dnos-bd:name', self.namespaces)
            if name_elem is not None:
                name = name_elem.text
                
                # Extract admin state
                admin_state_elem = bridge_domain.find('dnos-bd:admin-state', self.namespaces)
                admin_state = admin_state_elem.text if admin_state_elem is not None else 'unknown'
                
                # Extract interfaces
                interfaces = []
                for interface in bridge_domain.findall('.//dnos-bd:interface', self.namespaces):
                    if_name_elem = interface.find('dnos-bd:name', self.namespaces)
                    if_type_elem = interface.find('dnos-bd:type', self.namespaces)
                    vlan_elem = interface.find('dnos-bd:vlan-id', self.namespaces)
                    
                    if if_name_elem is not None:
                        interface_info = {
                            'name': if_name_elem.text,
                            'type': if_type_elem.text if if_type_elem is not None else 'unknown',
                            'vlan_id': int(vlan_elem.text) if vlan_elem is not None else None
                        }
                        interfaces.append(interface_info)
                
                bridge_domains[name] = {
                    'name': name,
                    'admin_state': admin_state,
                    'interfaces': interfaces,
                    'device': self.host,
                    'retrieved_via': 'netconf'
                }
        
        return bridge_domains
    
    def parse_interfaces_response(self, response) -> Dict:
        """
        Parse NETCONF response for interfaces
        
        Args:
            response: NETCONF response XML
            
        Returns:
            Parsed interface configurations
        """
        interfaces = {}
        
        root = ET.fromstring(response.xml)
        
        for interface in root.findall('.//dnos-if:interface', self.namespaces):
            name_elem = interface.find('dnos-if:name', self.namespaces)
            if name_elem is not None:
                name = name_elem.text
                
                type_elem = interface.find('dnos-if:type', self.namespaces)
                admin_state_elem = interface.find('dnos-if:admin-state', self.namespaces)
                
                # Extract subinterfaces
                subinterfaces = []
                for subif in interface.findall('.//dnos-if:subinterface', self.namespaces):
                    index_elem = subif.find('dnos-if:index', self.namespaces)
                    vlan_elem = subif.find('dnos-if:vlan-id', self.namespaces)
                    
                    if index_elem is not None:
                        subinterface_info = {
                            'index': int(index_elem.text),
                            'vlan_id': int(vlan_elem.text) if vlan_elem is not None else None
                        }
                        subinterfaces.append(subinterface_info)
                
                interfaces[name] = {
                    'name': name,
                    'type': type_elem.text if type_elem is not None else 'unknown',
                    'admin_state': admin_state_elem.text if admin_state_elem is not None else 'unknown',
                    'subinterfaces': subinterfaces
                }
        
        return interfaces
```

### **2. Enhanced Bridge Domain Discovery with NETCONF**

```python
class NetconfBridgeDomainDiscovery(BridgeDomainDiscovery):
    """
    Bridge domain discovery using NETCONF instead of SSH CLI
    """
    
    def __init__(self):
        super().__init__()
        self.netconf_clients = {}
        self.device_credentials = self.load_device_credentials()
    
    def load_device_credentials(self) -> Dict[str, Dict]:
        """
        Load device credentials for NETCONF connections
        
        Returns:
            Dictionary mapping device names to credentials
        """
        # Load from configuration file or environment
        credentials = {
            'DNAAS-LEAF-B13': {
                'host': '192.168.1.13',
                'username': 'admin',
                'password': 'password123',
                'port': 830
            },
            'DNAAS-SPINE-A08': {
                'host': '192.168.1.8',
                'username': 'admin',
                'password': 'password123',
                'port': 830
            }
            # Add all devices...
        }
        return credentials
    
    def get_netconf_client(self, device_name: str) -> DNOSNetconfClient:
        """
        Get or create NETCONF client for device
        
        Args:
            device_name: Name of the device
            
        Returns:
            NETCONF client instance
        """
        if device_name not in self.netconf_clients:
            if device_name not in self.device_credentials:
                raise ValueError(f"No credentials found for device {device_name}")
            
            creds = self.device_credentials[device_name]
            self.netconf_clients[device_name] = DNOSNetconfClient(
                host=creds['host'],
                username=creds['username'],
                password=creds['password'],
                port=creds['port']
            )
        
        return self.netconf_clients[device_name]
    
    def discover_bridge_domains_netconf(self) -> Dict:
        """
        Discover bridge domains using NETCONF
        
        Returns:
            Enhanced bridge domain mapping with NETCONF data
        """
        logger.info("Starting NETCONF-based Bridge Domain Discovery...")
        
        all_bridge_domains = {}
        all_interfaces = {}
        
        # Discover from each device
        for device_name in self.device_credentials.keys():
            try:
                logger.info(f"Discovering bridge domains from {device_name} via NETCONF...")
                
                # Get NETCONF client
                client = self.get_netconf_client(device_name)
                
                # Establish connection
                with client.connect() as connection:
                    # Get bridge domain configurations
                    bridge_domains = client.get_bridge_domains(connection)
                    
                    # Get interface configurations
                    interfaces = client.get_interface_configs(connection)
                    
                    # Store results
                    all_bridge_domains[device_name] = bridge_domains
                    all_interfaces[device_name] = interfaces
                    
                    logger.info(f"Retrieved {len(bridge_domains)} bridge domains and {len(interfaces)} interfaces from {device_name}")
                    
            except Exception as e:
                logger.error(f"Failed to discover from {device_name}: {e}")
                continue
        
        # Create enhanced mapping
        enhanced_mapping = self.create_netconf_enhanced_mapping(all_bridge_domains, all_interfaces)
        
        return enhanced_mapping
    
    def create_netconf_enhanced_mapping(self, bridge_domains: Dict, interfaces: Dict) -> Dict:
        """
        Create enhanced mapping from NETCONF data
        
        Args:
            bridge_domains: Bridge domain data from all devices
            interfaces: Interface data from all devices
            
        Returns:
            Enhanced bridge domain mapping
        """
        enhanced_mapping = {
            'discovery_metadata': {
                'timestamp': datetime.now().isoformat(),
                'devices_scanned': len(bridge_domains),
                'discovery_method': 'netconf',
                'structured_data': True,
                'xml_based': True
            },
            'bridge_domains': {},
            'device_interfaces': interfaces,
            'discovery_summary': {
                'total_bridge_domains': 0,
                'total_interfaces': 0,
                'devices_with_netconf': len(bridge_domains),
                'devices_failed': 0
            }
        }
        
        # Process bridge domains from each device
        for device_name, device_bridge_domains in bridge_domains.items():
            device_type = self.detect_device_type(device_name)
            
            for bridge_domain_name, bridge_domain_data in device_bridge_domains.items():
                # Analyze service name pattern
                service_analysis = self.service_analyzer.extract_service_info(bridge_domain_name)
                
                # Create enhanced bridge domain entry
                if bridge_domain_name not in enhanced_mapping['bridge_domains']:
                    enhanced_mapping['bridge_domains'][bridge_domain_name] = {
                        'service_name': bridge_domain_name,
                        'detected_username': service_analysis.get('username'),
                        'detected_vlan': service_analysis.get('vlan_id'),
                        'confidence': service_analysis.get('confidence', 0),
                        'detection_method': 'netconf_structured',
                        'devices': {},
                        'total_interfaces': 0,
                        'structured_config': True
                    }
                
                # Add device-specific configuration
                enhanced_mapping['bridge_domains'][bridge_domain_name]['devices'][device_name] = {
                    'device_type': device_type,
                    'admin_state': bridge_domain_data['admin_state'],
                    'interfaces': bridge_domain_data['interfaces'],
                    'structured_data': True,
                    'netconf_retrieved': True,
                    'xml_source': True
                }
                
                # Update summary
                enhanced_mapping['bridge_domains'][bridge_domain_name]['total_interfaces'] += len(
                    bridge_domain_data['interfaces']
                )
                enhanced_mapping['discovery_summary']['total_bridge_domains'] += 1
        
        return enhanced_mapping
```

### **3. NETCONF Configuration Management**

```python
class NetconfConfigurationManager:
    """
    Manage bridge domain configurations via NETCONF
    """
    
    def __init__(self, device_credentials: Dict):
        self.device_credentials = device_credentials
        self.logger = logging.getLogger(__name__)
    
    def create_bridge_domain(self, device_name: str, bridge_domain_config: Dict) -> bool:
        """
        Create bridge domain via NETCONF
        
        Args:
            device_name: Target device name
            bridge_domain_config: Bridge domain configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = DNOSNetconfClient(**self.device_credentials[device_name])
            
            # Build NETCONF edit-config request
            config_xml = self.build_bridge_domain_config_xml(bridge_domain_config)
            
            with client.connect() as connection:
                # Send edit-config request
                response = connection.edit_config(
                    target='running',
                    config=config_xml
                )
                
                self.logger.info(f"Successfully created bridge domain on {device_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to create bridge domain on {device_name}: {e}")
            return False
    
    def modify_bridge_domain(self, device_name: str, bridge_domain_name: str, 
                           changes: Dict) -> bool:
        """
        Modify bridge domain via NETCONF
        
        Args:
            device_name: Target device name
            bridge_domain_name: Name of bridge domain to modify
            changes: Configuration changes to apply
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = DNOSNetconfClient(**self.device_credentials[device_name])
            
            # Build NETCONF edit-config request for modifications
            config_xml = self.build_modification_config_xml(bridge_domain_name, changes)
            
            with client.connect() as connection:
                response = connection.edit_config(
                    target='running',
                    config=config_xml
                )
                
                self.logger.info(f"Successfully modified bridge domain {bridge_domain_name} on {device_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to modify bridge domain on {device_name}: {e}")
            return False
    
    def delete_bridge_domain(self, device_name: str, bridge_domain_name: str) -> bool:
        """
        Delete bridge domain via NETCONF
        
        Args:
            device_name: Target device name
            bridge_domain_name: Name of bridge domain to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client = DNOSNetconfClient(**self.device_credentials[device_name])
            
            # Build NETCONF edit-config request for deletion
            config_xml = self.build_deletion_config_xml(bridge_domain_name)
            
            with client.connect() as connection:
                response = connection.edit_config(
                    target='running',
                    config=config_xml
                )
                
                self.logger.info(f"Successfully deleted bridge domain {bridge_domain_name} on {device_name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to delete bridge domain on {device_name}: {e}")
            return False
    
    def build_bridge_domain_config_xml(self, bridge_domain_config: Dict) -> str:
        """
        Build XML configuration for bridge domain creation
        
        Args:
            bridge_domain_config: Bridge domain configuration
            
        Returns:
            XML configuration string
        """
        service_name = bridge_domain_config['service_name']
        admin_state = bridge_domain_config.get('admin_state', 'enabled')
        interfaces = bridge_domain_config.get('interfaces', [])
        
        # Build XML configuration
        config_xml = f"""
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
            <bridge-domains xmlns="http://drivenets.com/ns/yang/dnos-bridge-domain">
                <bridge-domain>
                    <name>{service_name}</name>
                    <admin-state>{admin_state}</admin-state>
                    <interfaces>
        """
        
        for interface in interfaces:
            config_xml += f"""
                        <interface>
                            <name>{interface['name']}</name>
                            <type>{interface.get('type', 'unknown')}</type>
            """
            
            if interface.get('vlan_id'):
                config_xml += f"""
                            <vlan-id>{interface['vlan_id']}</vlan-id>
                """
            
            config_xml += """
                        </interface>
            """
        
        config_xml += """
                    </interfaces>
                </bridge-domain>
            </bridge-domains>
        </config>
        """
        
        return config_xml
```

## **Benefits of NETCONF Integration**

### **1. Structured Data**
- **XML-based configuration** instead of unstructured text
- **Standardized data models** via YANG schemas
- **Type-safe configuration** with validation
- **Hierarchical data structure** for complex configurations

### **2. Reliable Operations**
- **Atomic transactions** for configuration changes
- **Rollback capabilities** with commit/rollback operations
- **Error handling** with structured error responses
- **Validation** at the protocol level

### **3. Enhanced Discovery**
- **Precise data retrieval** with targeted filters
- **No parsing ambiguity** - structured XML responses
- **Complete configuration** access without command limitations
- **Real-time state** monitoring capabilities

### **4. Better Integration**
- **Standard protocol** supported by all major vendors
- **Programmatic access** with consistent APIs
- **Multi-vendor support** with vendor-specific YANG models
- **Future-proof** technology

## **Implementation Considerations**

### **1. DNOS YANG Models**
```xml
<!-- Example DNOS bridge domain YANG model -->
module dnos-bridge-domain {
  namespace "http://drivenets.com/ns/yang/dnos-bridge-domain";
  prefix "dnos-bd";
  
  container bridge-domains {
    list bridge-domain {
      key "name";
      leaf name {
        type string;
        description "Bridge domain name";
      }
      leaf admin-state {
        type enumeration {
          enum enabled;
          enum disabled;
        }
        default enabled;
      }
      container interfaces {
        list interface {
          key "name";
          leaf name {
            type string;
          }
          leaf type {
            type enumeration {
              enum physical;
              enum subinterface;
              enum bundle;
            }
          }
          leaf vlan-id {
            type uint16;
          }
        }
      }
    }
  }
}
```

### **2. Error Handling**
```python
# NETCONF error handling
try:
    response = connection.edit_config(target='running', config=config_xml)
    if response.ok:
        logger.info("Configuration applied successfully")
    else:
        logger.error(f"Configuration failed: {response.error}")
except Exception as e:
    logger.error(f"NETCONF operation failed: {e}")
    # Handle specific NETCONF errors
    if "access-denied" in str(e):
        logger.error("Insufficient privileges")
    elif "invalid-value" in str(e):
        logger.error("Invalid configuration value")
```

### **3. Performance Considerations**
- **Connection pooling** for multiple devices
- **Batch operations** for multiple configurations
- **Caching** of frequently accessed data
- **Asynchronous operations** for large deployments

## **Migration Strategy**

### **Phase 1: NETCONF Discovery (2-3 weeks)**
1. **Implement NETCONF client** for DNOS devices
2. **Create YANG model mappings** for bridge domains
3. **Replace SSH discovery** with NETCONF discovery
4. **Validate data accuracy** against existing system

### **Phase 2: NETCONF Configuration Management (2-3 weeks)**
1. **Implement configuration operations** (create/modify/delete)
2. **Add transaction support** with commit/rollback
3. **Integrate with topology editor** for configuration changes
4. **Add error handling** and validation

### **Phase 3: Enhanced Features (1-2 weeks)**
1. **Real-time monitoring** via NETCONF notifications
2. **Configuration validation** using YANG schemas
3. **Performance optimization** with connection pooling
4. **Multi-vendor support** preparation

## **Comparison Summary**

| Aspect | SSH CLI | NETCONF |
|--------|---------|---------|
| **Data Format** | Unstructured text | Structured XML |
| **Parsing** | Regex/string parsing | XML parsing |
| **Validation** | Limited | Schema-based |
| **Error Handling** | Text-based | Structured errors |
| **Transactions** | Manual | Built-in |
| **Rollback** | Manual | Automatic |
| **Performance** | Slower | Faster |
| **Reliability** | Lower | Higher |
| **Standards** | Vendor-specific | RFC standard |
| **Future-proof** | Limited | Excellent |

NETCONF integration would significantly improve the reliability, maintainability, and capabilities of the bridge domain topology editor while providing a more robust foundation for future enhancements. 