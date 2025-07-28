# Lovable Code Generation Prompt
# Lab Automation Framework - Web GUI Interface

## Project Overview

Create a modern, responsive web application for a Network Lab Automation Framework that provides a web-based interface for network configuration management, bridge domain deployment, and device monitoring. The application should serve as a centralized platform where multiple users can access network automation tools through their browsers.

## Core Requirements

### 1. User Authentication & Management
- **Login/Logout System**: Clean, secure authentication interface
- **User Roles**: Admin, Operator, Viewer with different access levels
- **Session Management**: Persistent user sessions with timeout
- **User Profile**: Personal settings and workspace preferences

### 2. Main Dashboard
- **Overview Cards**: 
  - Total devices managed
  - Active deployments
  - Recent configurations
  - System health status
- **Quick Actions**: 
  - Start new bridge domain configuration
  - View recent deployments
  - Access file management
  - System monitoring
- **Real-time Updates**: Live status indicators and notifications

### 3. Bridge Domain Builder Interface
- **Configuration Wizard**:
  - Step 1: Select configuration type (P2P/P2MP)
  - Step 2: Choose source device and interface
  - Step 3: Select destination devices
  - Step 4: Configure VLAN and service parameters
  - Step 5: Review and generate configuration
- **Device Selection**: 
  - Tree view of network topology
  - Search and filter devices
  - Device status indicators
  - Interface availability display
- **Real-time Validation**: 
  - Path calculation results
  - Configuration validation
  - Error highlighting and suggestions

### 4. File Management System
- **File Browser**:
  - Hierarchical directory tree
  - File upload/download capabilities
  - File preview and editing
  - Search and filter files
- **Configuration Files**:
  - Pending configurations
  - Deployed configurations
  - Configuration history
  - Version control indicators
- **Inventory Management**:
  - Device inventory files
  - Topology data
  - Bundle mappings
  - Import/export functionality

### 5. Deployment Management
- **Configuration Deployment**:
  - List of pending configurations
  - Deployment status tracking
  - Real-time deployment progress
  - Success/failure notifications
- **SSH Push Interface**:
  - Device selection for deployment
  - Configuration preview
  - Deployment options (dry-run, validation)
  - Deployment logs and history
- **Configuration Removal**:
  - List of deployed configurations
  - Removal confirmation
  - Rollback capabilities

### 6. Network Discovery & Topology
- **Device Discovery**:
  - Probe and parse network devices
  - LACP and LLDP data collection
  - Device status monitoring
  - Connection health indicators
- **Topology Visualization**:
  - Interactive network topology map
  - Device hierarchy (Superspine → Spine → Leaf)
  - Connection status and bandwidth
  - Device type indicators
- **ASCII Topology Trees**:
  - Detailed topology view
  - Minimized topology view
  - Export topology diagrams

### 7. Bridge Domain Discovery & Visualization
- **Bridge Domain Discovery**:
  - Discover existing bridge domains
  - Mapping and consolidation
  - Confidence scoring
  - Pattern detection
- **Bridge Domain Visualization**:
  - Interactive bridge domain diagrams
  - Device and interface mapping
  - Bandwidth and path information
  - Export visualization files

### 8. Monitoring & Analytics
- **System Monitoring**:
  - Real-time system status
  - User activity tracking
  - Performance metrics
  - Error logging and alerting
- **Deployment Analytics**:
  - Success/failure rates
  - Deployment time tracking
  - User productivity metrics
  - Configuration error analysis

## Technical Specifications

### Frontend Technology Stack
- **Framework**: React with TypeScript
- **Styling**: Tailwind CSS with custom design system
- **State Management**: React Context or Redux Toolkit
- **Real-time**: WebSocket connections for live updates
- **Charts**: Chart.js or D3.js for analytics
- **Terminal**: xterm.js for terminal emulation

### Design System
- **Color Palette**: 
  - Primary: Blue (#3B82F6)
  - Success: Green (#10B981)
  - Warning: Yellow (#F59E0B)
  - Error: Red (#EF4444)
  - Neutral: Gray (#6B7280)
- **Typography**: 
  - Headings: Inter or system font
  - Body: System font stack
  - Monospace: For terminal and code
- **Components**: 
  - Cards for dashboard items
  - Modals for wizards and forms
  - Tables for data display
  - Trees for hierarchical data
  - Progress indicators
  - Status badges

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Header: Logo, User Menu, Notifications, Search                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────────────────────────────────────────────┐ │
│  │             │  │                                                     │ │
│  │   Sidebar   │  │                Main Content Area                   │ │
│  │  Navigation │  │                                                     │ │
│  │             │  │  - Dashboard                                        │ │
│  │  - Dashboard│  │  - Bridge Domain Builder                            │ │
│  │  - Builder  │  │  - File Management                                 │ │
│  │  - Files    │  │  - Deployment Management                           │ │
│  │  - Deploy   │  │  - Network Discovery                               │ │
│  │  - Monitor  │  │  - Bridge Domain Discovery                         │ │
│  │  - Settings │  │  - Analytics                                       │ │
│  │             │  │                                                     │ │
│  └─────────────┘  └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
│  Footer: Status Bar, Connection Info, Version                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Features to Implement

### 1. Responsive Design
- Mobile-first approach
- Tablet and desktop optimization
- Touch-friendly controls
- Adaptive layouts

### 2. Real-time Updates
- WebSocket connections for live data
- Auto-refresh for status updates
- Push notifications for important events
- Live progress indicators

### 3. Accessibility
- WCAG 2.1 AA compliance
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode

### 4. Performance
- Lazy loading for large datasets
- Virtual scrolling for long lists
- Optimized image loading
- Efficient state management

### 5. Security
- Input validation and sanitization
- CSRF protection
- XSS prevention
- Secure file uploads

## Component Specifications

### 1. Dashboard Components
- **Status Cards**: Device count, deployments, health
- **Quick Action Buttons**: Start builder, view files, deploy
- **Recent Activity**: Latest deployments and configurations
- **System Health**: Performance metrics and alerts

### 2. Bridge Domain Builder Components
- **Configuration Wizard**: Multi-step form with progress
- **Device Selector**: Tree view with search and filters
- **Interface Picker**: Dropdown with availability status
- **Path Calculator**: Visual path representation
- **Configuration Preview**: Generated config display

### 3. File Management Components
- **File Browser**: Tree structure with icons
- **Upload Zone**: Drag-and-drop file upload
- **File Preview**: Syntax highlighting for configs
- **File Actions**: Download, delete, rename

### 4. Deployment Components
- **Deployment List**: Table with status and actions
- **Progress Tracker**: Real-time deployment progress
- **Log Viewer**: Scrollable log display
- **Configuration Selector**: Dropdown with metadata

### 5. Monitoring Components
- **Status Dashboard**: Real-time system status
- **Activity Feed**: User actions and system events
- **Performance Charts**: Metrics visualization
- **Alert Center**: Notifications and warnings

## Data Models

### User
```typescript
interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'operator' | 'viewer';
  lastLogin: Date;
  preferences: UserPreferences;
}
```

### Device
```typescript
interface Device {
  name: string;
  type: 'superspine' | 'spine' | 'leaf';
  status: 'online' | 'offline' | 'error';
  interfaces: Interface[];
  location: string;
}
```

### Configuration
```typescript
interface Configuration {
  id: string;
  name: string;
  type: 'p2p' | 'p2mp';
  status: 'pending' | 'deployed' | 'failed';
  devices: string[];
  vlanId: number;
  createdAt: Date;
  deployedAt?: Date;
}
```

### Deployment
```typescript
interface Deployment {
  id: string;
  configurationId: string;
  status: 'running' | 'completed' | 'failed';
  progress: number;
  devices: DeploymentDevice[];
  logs: DeploymentLog[];
  startedAt: Date;
  completedAt?: Date;
}
```

## API Integration Points

### 1. Authentication
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- PUT /api/auth/preferences

### 2. Bridge Domain Builder
- POST /api/builder/validate
- POST /api/builder/generate
- GET /api/builder/devices
- GET /api/builder/interfaces

### 3. File Management
- GET /api/files/list
- POST /api/files/upload
- GET /api/files/download/:id
- DELETE /api/files/:id

### 4. Deployment
- GET /api/deployments/list
- POST /api/deployments/start
- GET /api/deployments/:id/status
- GET /api/deployments/:id/logs

### 5. Monitoring
- GET /api/monitoring/status
- GET /api/monitoring/metrics
- GET /api/monitoring/alerts
- WebSocket /ws/monitoring

## User Experience Flow

### 1. First-time User
1. Login with credentials
2. View welcome tutorial
3. Explore dashboard
4. Start first configuration

### 2. Bridge Domain Creation
1. Click "New Bridge Domain" on dashboard
2. Select configuration type
3. Choose source device and interface
4. Add destination devices
5. Configure VLAN parameters
6. Review and generate configuration
7. Deploy or save for later

### 3. File Management
1. Navigate to Files section
2. Browse directory structure
3. Upload inventory files
4. View and edit configurations
5. Download generated files

### 4. Deployment Process
1. Select configuration to deploy
2. Review deployment settings
3. Start deployment
4. Monitor real-time progress
5. View deployment logs
6. Verify deployment success

## Success Criteria

### 1. Usability
- Users can complete bridge domain creation in <5 minutes
- File operations complete in <2 seconds
- Deployment monitoring provides real-time feedback
- Interface is intuitive for network engineers

### 2. Performance
- Page load times <2 seconds
- Real-time updates <500ms latency
- Support for 50+ concurrent users
- Mobile responsiveness on all devices

### 3. Reliability
- 99.9% uptime
- Graceful error handling
- Data persistence across sessions
- Secure file operations

## Additional Considerations

### 1. Internationalization
- Support for multiple languages
- RTL language support
- Localized date/time formats
- Currency and number formatting

### 2. Customization
- User-configurable dashboard
- Customizable themes
- Personal workspace settings
- Saved searches and filters

### 3. Integration
- REST API for external tools
- Webhook support for notifications
- Export capabilities (PDF, CSV)
- Third-party tool integration

### 4. Documentation
- In-app help system
- Contextual tooltips
- Video tutorials
- User guide integration

This web GUI should transform the existing command-line Lab Automation Framework into a modern, accessible, and powerful web application that maintains all existing functionality while providing an enhanced user experience for network automation tasks. 