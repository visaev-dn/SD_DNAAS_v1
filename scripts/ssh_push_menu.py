#!/usr/bin/env python3
"""
Interactive SSH Push Menu
Provides user-friendly interface for configuration deployment and removal.
"""
import sys
from pathlib import Path

# Add config_engine to path
sys.path.append(str(Path(__file__).parent.parent / "config_engine"))
# Add parent directory to path for database_manager
sys.path.append(str(Path(__file__).parent.parent))

from ssh_push_manager import SSHPushManager

class SSHPushMenu:
    def __init__(self):
        self.push_manager = SSHPushManager()
    
    def show_main_menu(self):
        """Display the main SSH push menu."""
        while True:
            print("\n" + "=" * 60)
            print("=== SSH Configuration Push Menu ===")
            print("=" * 60)
            
            # Show available configurations
            available_configs = self.push_manager.get_available_configs()
            if available_configs:
                print("\n📁 Available Configurations:")
                for i, config in enumerate(available_configs, 1):
                    print(f"{i}. {config['name']} ({config['type']})")
            else:
                print("\n📁 No available configurations found.")
                print("   Run bridge domain builder first to generate configs.")
            
            # Show deployed configurations
            deployed_configs = self.push_manager.get_deployed_configs()
            if deployed_configs:
                print("\n📋 Currently Deployed:")
                for i, config in enumerate(deployed_configs, 1):
                    deployed_date = config['deployed_at'][:16].replace('T', ' ') if config['deployed_at'] else 'Unknown'
                    vlan_info = f" (VLAN {config.get('vlan_id', 'N/A')})" if config.get('vlan_id') else ""
                    print(f"{i}. {config['name']}{vlan_info} (Deployed: {deployed_date})")
            
            # Show deleted configurations
            deleted_configs = self.push_manager.get_removed_configs()
            if deleted_configs:
                print("\n🗑️  Deleted Configurations:")
                for i, config in enumerate(deleted_configs, 1):
                    deleted_date = config['deleted_at'][:16].replace('T', ' ') if config['deleted_at'] else 'Unknown'
                    vlan_info = f" (VLAN {config.get('vlan_id', 'N/A')})" if config.get('vlan_id') else ""
                    print(f"{i}. {config['name']}{vlan_info} (Deleted: {deleted_date})")
            
            print("\nOptions:")
            if available_configs:
                print("- [P]ush selected config")
                print("- [V]alidate selected config")
                print("- [C]LI preview selected config")
            if deployed_configs:
                print("- [R]emove selected deployed config")
                print("- [X] CLI preview deletion for selected config")
            if deleted_configs:
                print("- [S]Restore selected deleted config")
            print("- [B]ack to main menu")
            
            choice = input("\nSelect an option: ").strip().upper()
            
            if choice == 'P' and available_configs:
                self.push_selected_config(available_configs)
            elif choice == 'V' and available_configs:
                self.validate_selected_config(available_configs)
            elif choice == 'C' and available_configs:
                self.cli_preview_selected_config(available_configs)
            elif choice == 'R' and deployed_configs:
                self.remove_selected_config(deployed_configs)
            elif choice == 'X' and deployed_configs:
                self.deletion_preview_selected_config(deployed_configs)
            elif choice == 'S' and deleted_configs:
                self.restore_selected_config(deleted_configs)
            elif choice == 'B':
                print("Returning to main menu...")
                break
            else:
                print("❌ Invalid choice. Please select a valid option.")
    
    def push_selected_config(self, available_configs):
        """Push a selected configuration."""
        print("\n" + "-" * 40)
        print("📤 Push Configuration")
        print("-" * 40)
        
        # Show available configs
        for i, config in enumerate(available_configs, 1):
            print(f"{i}. {config['name']}")
        
        try:
            choice = int(input("\nSelect configuration to push (0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(available_configs):
                selected_config = available_configs[choice - 1]
                self._push_config(selected_config['name'])
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    def validate_selected_config(self, available_configs):
        """Validate a selected configuration."""
        print("\n" + "-" * 40)
        print("🔍 Validate Configuration")
        print("-" * 40)
        
        # Show available configs
        for i, config in enumerate(available_configs, 1):
            print(f"{i}. {config['name']}")
        
        try:
            choice = int(input("\nSelect configuration to validate (0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(available_configs):
                selected_config = available_configs[choice - 1]
                self._validate_config(selected_config['name'])
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    def cli_preview_selected_config(self, available_configs):
        """Preview CLI commands for a selected configuration."""
        print("\n" + "-" * 40)
        print("🔍 CLI Command Preview")
        print("-" * 40)
        
        # Show available configs
        for i, config in enumerate(available_configs, 1):
            print(f"{i}. {config['name']}")
        
        try:
            choice = int(input("\nSelect configuration to preview (0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(available_configs):
                selected_config = available_configs[choice - 1]
                self._cli_preview_config(selected_config['name'])
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    def remove_selected_config(self, deployed_configs):
        """Remove a selected deployed configuration."""
        print("\n" + "-" * 40)
        print("🗑️  Remove Deployed Configuration")
        print("-" * 40)
        
        # Show deployed configs
        for i, config in enumerate(deployed_configs, 1):
            deployed_date = config['deployed_at'][:16].replace('T', ' ') if config['deployed_at'] else 'Unknown'
            vlan_info = f" (VLAN {config.get('vlan_id', 'N/A')})" if config.get('vlan_id') else ""
            print(f"{i}. {config['name']}{vlan_info} (Deployed: {deployed_date})")
        
        try:
            choice = int(input("\nSelect configuration to remove (0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(deployed_configs):
                selected_config = deployed_configs[choice - 1]
                self._remove_config(selected_config['name'])
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    def deletion_preview_selected_config(self, deployed_configs):
        """Preview deletion CLI commands for a selected configuration."""
        print("\n" + "-" * 40)
        print("🔍 Deletion CLI Preview")
        print("-" * 40)
        
        # Show deployed configs
        for i, config in enumerate(deployed_configs, 1):
            deployed_date = config['deployed_at'][:16].replace('T', ' ') if config['deployed_at'] else 'Unknown'
            vlan_info = f" (VLAN {config.get('vlan_id', 'N/A')})" if config.get('vlan_id') else ""
            print(f"{i}. {config['name']}{vlan_info} (Deployed: {deployed_date})")
        
        try:
            choice = int(input("\nSelect configuration to preview deletion (0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(deployed_configs):
                selected_config = deployed_configs[choice - 1]
                self._cli_preview_deletion(selected_config['name'])
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    def restore_selected_config(self, deleted_configs):
        """Restore a selected deleted configuration."""
        print("\n" + "-" * 40)
        print("🔄 Restore Deleted Configuration")
        print("-" * 40)
        
        # Show deleted configs
        for i, config in enumerate(deleted_configs, 1):
            deleted_date = config['deleted_at'][:16].replace('T', ' ') if config['deleted_at'] else 'Unknown'
            vlan_info = f" (VLAN {config.get('vlan_id', 'N/A')})" if config.get('vlan_id') else ""
            print(f"{i}. {config['name']}{vlan_info} (Deleted: {deleted_date})")
        
        try:
            choice = int(input("\nSelect configuration to restore (0 to cancel): "))
            if choice == 0:
                return
            if 1 <= choice <= len(deleted_configs):
                selected_config = deleted_configs[choice - 1]
                self._restore_config(selected_config['name'])
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Please enter a valid number.")
    
    def _push_config(self, config_name: str):
        """Push a configuration with confirmation."""
        print(f"\n📤 Pushing configuration: {config_name}")
        
        # Show config details
        details = self.push_manager.get_config_details(config_name)
        if details:
            print(f"   📱 Devices: {', '.join(details['devices'])}")
            print(f"   🏷️  VLAN ID: {details['vlan_id']}")
            print(f"   📊 Device count: {details['device_count']}")
        
        # Validate first
        print("\n🔍 Validating configuration...")
        is_valid, errors = self.push_manager.validate_config(config_name)
        if not is_valid:
            print("❌ Validation failed:")
            for error in errors:
                print(f"   • {error}")
            return
        
        print("✅ Validation passed!")
        
        # Preview CLI commands
        print("\n🔍 Previewing CLI commands that will be deployed:")
        success, errors, device_commands = self.push_manager.preview_cli_commands(config_name)
        if not success:
            print("❌ Failed to preview CLI commands:")
            for error in errors:
                print(f"   • {error}")
            return
        
        # Show CLI commands for each device
        for device_name, cli_commands in device_commands.items():
            print(f"\n📱 {device_name}:")
            for i, command in enumerate(cli_commands, 1):
                print(f"   {i:2d}. {command}")
        
        # Confirm deployment
        confirm = input(f"\nDeploy {config_name} to {details['device_count']} devices? (y/N): ").strip().lower()
        if confirm == 'y':
            print(f"\n🚀 Deploying {config_name}...")
            success, errors = self.push_manager.deploy_config(config_name)
            if success:
                print(f"✅ {config_name} deployed successfully!")
            else:
                print(f"❌ Failed to deploy {config_name}:")
                for error in errors:
                    print(f"   • {error}")
        else:
            print("❌ Deployment cancelled.")
    
    def _validate_config(self, config_name: str):
        """Validate a configuration."""
        print(f"\n🔍 Validating configuration: {config_name}")
        
        is_valid, errors = self.push_manager.validate_config(config_name)
        if is_valid:
            print("✅ Configuration is valid!")
            
            # Show additional details
            details = self.push_manager.get_config_details(config_name)
            if details:
                print(f"   📱 Devices: {', '.join(details['devices'])}")
                print(f"   🏷️  VLAN ID: {details['vlan_id']}")
                print(f"   📊 Device count: {details['device_count']}")
        else:
            print("❌ Configuration validation failed:")
            for error in errors:
                print(f"   • {error}")
    
    def _cli_preview_config(self, config_name: str):
        """Preview CLI commands for a configuration."""
        print(f"\n🔍 CLI Preview for: {config_name}")
        
        # Show config details
        details = self.push_manager.get_config_details(config_name)
        if details:
            print(f"   📱 Devices: {', '.join(details['devices'])}")
            print(f"   🏷️  VLAN ID: {details['vlan_id']}")
            print(f"   📊 Device count: {details['device_count']}")
        
        # Preview CLI commands
        print("\n🔍 CLI Commands that would be deployed:")
        success, errors, device_commands = self.push_manager.preview_cli_commands(config_name)
        if not success:
            print("❌ Failed to preview CLI commands:")
            for error in errors:
                print(f"   • {error}")
            return
        
        # Show CLI commands for each device
        for device_name, cli_commands in device_commands.items():
            print(f"\n📱 {device_name}:")
            for i, command in enumerate(cli_commands, 1):
                print(f"   {i:2d}. {command}")
        
        print(f"\n📋 Summary: {len(device_commands)} devices, {sum(len(cmds) for cmds in device_commands.values())} total commands")
    
    def _remove_config(self, config_name: str):
        """Remove a deployed configuration."""
        print(f"\n🗑️  Removing configuration: {config_name}")
        
        # Show config details
        details = self.push_manager.get_config_details(config_name)
        if details:
            print(f"   📱 Devices: {', '.join(details['devices'])}")
            print(f"   🏷️  VLAN ID: {details['vlan_id']}")
        
        # Preview deletion CLI commands
        print("\n🔍 Previewing CLI deletion commands:")
        success, errors, device_commands = self.push_manager.preview_deletion_commands(config_name)
        if not success:
            print("❌ Failed to preview deletion CLI commands:")
            for error in errors:
                print(f"   • {error}")
            return
        
        # Show CLI commands for each device
        for device_name, cli_commands in device_commands.items():
            print(f"\n📱 {device_name}:")
            for i, command in enumerate(cli_commands, 1):
                print(f"   {i:2d}. {command}")
        
        print(f"\n⚠️  These commands will REMOVE the configuration from {details['device_count']} devices!")
        print("   Verification will check that the configuration is no longer present.")
        
        # Confirm removal
        confirm = input(f"\nRemove {config_name} from {details['device_count']} devices? (y/N): ").strip().lower()
        if confirm == 'y':
            print(f"\n🗑️  Removing {config_name}...")
            success, errors = self.push_manager.remove_config(config_name)
            if success:
                print(f"✅ {config_name} removed successfully!")
            else:
                print(f"❌ Failed to remove {config_name}:")
                for error in errors:
                    print(f"   • {error}")
        else:
            print("❌ Removal cancelled.")
    
    def _cli_preview_deletion(self, config_name: str):
        """Preview CLI deletion commands for a configuration."""
        print(f"\n🗑️  CLI Deletion Preview for: {config_name}")
        
        # Show config details
        details = self.push_manager.get_config_details(config_name)
        if details:
            print(f"   📱 Devices: {', '.join(details['devices'])}")
            print(f"   🏷️  VLAN ID: {details['vlan_id']}")
            print(f"   📊 Device count: {details['device_count']}")
        
        # Preview deletion CLI commands
        print("\n🔍 CLI Deletion Commands that would be executed:")
        success, errors, device_commands = self.push_manager.preview_deletion_commands(config_name)
        if not success:
            print("❌ Failed to preview deletion CLI commands:")
            for error in errors:
                print(f"   • {error}")
            return
        
        # Show CLI commands for each device
        for device_name, cli_commands in device_commands.items():
            print(f"\n📱 {device_name}:")
            for i, command in enumerate(cli_commands, 1):
                print(f"   {i:2d}. {command}")
        
        print(f"\n📋 Summary: {len(device_commands)} devices, {sum(len(cmds) for cmds in device_commands.values())} total deletion commands")
        print("\n⚠️  Note: These commands will REMOVE the configuration from devices!")
        print("   Verification will check that the configuration is no longer present.")

    def _restore_config(self, config_name: str):
        """Restore a deleted configuration."""
        print(f"\n🔄 Restoring configuration: {config_name}")
        
        # Show config details
        details = self.push_manager.get_config_details(config_name)
        if details:
            print(f"   📱 Devices: {', '.join(details['devices'])}")
            print(f"   🏷️  VLAN ID: {details['vlan_id']}")
            device_count = details['device_count']
        else:
            print(f"   ⚠️  Could not load configuration details")
            device_count = "unknown"
        
        # Preview deployment CLI commands
        print("\n🔍 Previewing CLI deployment commands:")
        success, errors, device_commands = self.push_manager.preview_cli_commands(config_name)
        if not success:
            print("❌ Failed to preview deployment CLI commands:")
            for error in errors:
                print(f"   • {error}")
            return
        
        # Show CLI commands for each device
        for device_name, cli_commands in device_commands.items():
            print(f"\n📱 {device_name}:")
            for i, command in enumerate(cli_commands, 1):
                print(f"   {i:2d}. {command}")
        
        # Confirm deployment
        confirm = input(f"\nDeploy {config_name} to {device_count} devices? (y/N): ").strip().lower()
        if confirm == 'y':
            print(f"\n🚀 Deploying {config_name} to {device_count} devices...")
            success, errors = self.push_manager.deploy_config(config_name)
            if success:
                print(f"✅ {config_name} restored successfully!")
            else:
                print(f"❌ Failed to restore {config_name}:")
                for error in errors:
                    print(f"   • {error}")
        else:
            print("❌ Deployment cancelled.")

def main():
    """Main function to run the SSH push menu."""
    menu = SSHPushMenu()
    menu.show_main_menu()

if __name__ == "__main__":
    main() 