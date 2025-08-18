# Lab Automation API Reference

## Overview

The Lab Automation API is a modular, RESTful API that provides comprehensive functionality for network automation, configuration management, and deployment operations. The API is organized into logical modules with clear separation of concerns.

## Base URL

```
http://localhost:5000/api/v1
```

## Authentication

All API endpoints require authentication using JWT tokens.

### Headers

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

## API Modules

### 1. Authentication (`/auth`)

#### POST `/auth/register`
Register a new user account.

**Request Body:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user_id": 123
}
```

#### POST `/auth/login`
Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "username": "username",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "user": {
    "id": 123,
    "username": "username",
    "email": "user@example.com"
  }
}
```

#### POST `/auth/logout`
Logout user and invalidate tokens.

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

#### POST `/auth/refresh`
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "refresh_token_here"
}
```

**Response:**
```json
{
  "access_token": "new_jwt_token_here"
}
```

#### GET `/auth/me`
Get current user information.

**Response:**
```json
{
  "user": {
    "id": 123,
    "username": "username",
    "email": "user@example.com",
    "is_admin": false
  }
}
```

### 2. Bridge Domains (`/bridge-domains`)

#### POST `/bridge-domains/discover`
Discover bridge domain topology.

**Request Body:**
```json
{
  "bridge_domain_name": "bd1",
  "scan_depth": "full"
}
```

**Response:**
```json
{
  "message": "Bridge domain discovered successfully",
  "topology_data": {...},
  "scan_id": 456
}
```

#### GET `/bridge-domains/list`
List all bridge domains for the current user.

**Query Parameters:**
- `mine` (boolean): Filter to user's bridge domains only

**Response:**
```json
{
  "bridge_domains": [
    {
      "id": "bd1",
      "name": "Bridge Domain 1",
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

#### GET `/bridge-domains/{name}/details`
Get detailed information about a specific bridge domain.

**Response:**
```json
{
  "bridge_domain": {
    "id": "bd1",
    "name": "Bridge Domain 1",
    "topology_data": {...},
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### GET `/bridge-domains/{name}/visualize`
Get visualization data for a bridge domain.

**Response:**
```json
{
  "visualization": {
    "nodes": [...],
    "edges": [...],
    "layout": "hierarchical"
  }
}
```

### 3. Files (`/files`)

#### GET `/files/list`
List available files.

**Query Parameters:**
- `type` (string): Filter by file type
- `path` (string): Filter by directory path

**Response:**
```json
{
  "files": [
    {
      "name": "config.yaml",
      "path": "/configs/",
      "size": 1024,
      "modified": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### GET `/files/download/{filepath}`
Download a file.

**Response:** File download

#### GET `/files/content/{filepath}`
Get file content.

**Response:**
```json
{
  "content": "file content here",
  "encoding": "utf-8"
}
```

#### DELETE `/files/delete/{filepath}`
Delete a file.

**Response:**
```json
{
  "message": "File deleted successfully"
}
```

#### POST `/files/save-config`
Save configuration to file.

**Request Body:**
```json
{
  "filename": "new_config.yaml",
  "content": "configuration content",
  "path": "/configs/"
}
```

**Response:**
```json
{
  "message": "File saved successfully",
  "filepath": "/configs/new_config.yaml"
}
```

### 4. Dashboard (`/dashboard`)

#### GET `/dashboard/stats`
Get dashboard statistics.

**Response:**
```json
{
  "stats": {
    "total_configurations": 25,
    "total_deployments": 15,
    "active_deployments": 3,
    "total_users": 8
  }
}
```

#### GET `/dashboard/recent-activity`
Get recent user activity.

**Query Parameters:**
- `limit` (integer): Number of activities to return

**Response:**
```json
{
  "activities": [
    {
      "id": 1,
      "user": "username",
      "action": "Configuration created",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### GET `/dashboard/personal-stats`
Get personal statistics for current user.

**Response:**
```json
{
  "personal_stats": {
    "configurations_created": 5,
    "deployments_started": 3,
    "last_activity": "2024-01-01T00:00:00Z"
  }
}
```

### 5. Configurations (`/configurations`)

#### GET `/configurations`
List configurations for the current user.

**Query Parameters:**
- `mine` (boolean): Filter to user's configurations only

**Response:**
```json
{
  "configurations": [
    {
      "id": 123,
      "name": "Config 1",
      "status": "draft",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

#### GET `/configurations/{id}`
Get configuration details.

**Response:**
```json
{
  "configuration": {
    "id": 123,
    "name": "Config 1",
    "status": "draft",
    "content": {...},
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### POST `/configurations/{id}/validate`
Validate a configuration.

**Response:**
```json
{
  "configuration_id": 123,
  "is_valid": true,
  "errors": [],
  "warnings": [],
  "validated_at": "2024-01-01T00:00:00Z"
}
```

#### POST `/configurations/{id}/deploy`
Deploy a configuration.

**Request Body:**
```json
{
  "dry_run": false,
  "deployment_options": {...}
}
```

**Response:**
```json
{
  "message": "Configuration deployed successfully",
  "deployment_id": "dep_123",
  "dry_run": false
}
```

#### POST `/configurations/{id}/export`
Export configuration to file.

**Request Body:**
```json
{
  "format": "json",
  "filename": "exported_config.json"
}
```

**Response:** File download

#### POST `/configurations/import`
Import configuration from file.

**Request:** Multipart form data with file

**Response:**
```json
{
  "message": "Configuration imported successfully",
  "configuration_id": 124
}
```

#### POST `/configurations/{name}/scan`
Scan bridge domain topology.

**Request Body:**
```json
{
  "scan_depth": "full",
  "parameters": {...}
}
```

**Response:**
```json
{
  "message": "Topology scan completed successfully",
  "scan_id": 789,
  "topology_data": {...}
}
```

#### POST `/configurations/{name}/reverse-engineer`
Reverse engineer configuration from existing bridge domain.

**Request Body:**
```json
{
  "include_metadata": true
}
```

**Response:**
```json
{
  "message": "Configuration reverse engineered successfully",
  "configuration_id": 125,
  "bridge_domain": "bd1"
}
```

### 6. Deployments (`/deployments`)

#### GET `/deployments/list`
List deployments for the current user.

**Response:**
```json
{
  "deployments": [
    {
      "id": "dep_123",
      "configuration_id": 123,
      "status": "completed",
      "started_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

#### POST `/deployments/start`
Start a new deployment.

**Request Body:**
```json
{
  "configuration_id": 123,
  "deployment_type": "standard",
  "dry_run": false
}
```

**Response:**
```json
{
  "message": "Deployment started successfully",
  "deployment_id": "dep_123",
  "status": "started"
}
```

#### GET `/deployments/{id}/status`
Get deployment status.

**Response:**
```json
{
  "deployment_id": "dep_123",
  "status": {
    "current_phase": "deploying",
    "progress": 75,
    "estimated_completion": "2024-01-01T01:00:00Z"
  }
}
```

#### POST `/deployments/{config_id}/pause`
Pause an active deployment.

**Response:**
```json
{
  "message": "Deployment paused successfully",
  "status": "paused"
}
```

#### POST `/deployments/{config_id}/resume`
Resume a paused deployment.

**Response:**
```json
{
  "message": "Deployment resumed successfully",
  "status": "deploying"
}
```

#### POST `/deployments/{config_id}/cancel`
Cancel an active deployment.

**Request Body:**
```json
{
  "reason": "User requested cancellation"
}
```

**Response:**
```json
{
  "message": "Deployment cancelled successfully",
  "status": "cancelled"
}
```

### 7. Devices (`/devices`)

#### POST `/devices/scan`
Scan network devices.

**Request Body:**
```json
{
  "scan_range": "192.168.1.0/24",
  "scan_type": "ping"
}
```

**Response:**
```json
{
  "message": "Device scan completed",
  "devices_found": 5,
  "scan_results": [...]
}
```

#### GET `/devices/scan/preview`
Preview device scan without executing.

**Response:**
```json
{
  "scan_preview": {
    "targets": ["192.168.1.1", "192.168.1.2"],
    "estimated_duration": "30s"
  }
}
```

### 8. Admin (`/admin`)

#### GET `/admin/users`
Get all users (admin only).

**Response:**
```json
{
  "users": [
    {
      "id": 123,
      "username": "username",
      "email": "user@example.com",
      "is_admin": false,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### POST `/admin/users`
Create a new user (admin only).

**Request Body:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password",
  "is_admin": false
}
```

**Response:**
```json
{
  "message": "User created successfully",
  "user_id": 124
}
```

#### PUT `/admin/users/{id}`
Update user information (admin only).

**Request Body:**
```json
{
  "email": "updated@example.com",
  "is_admin": true
}
```

**Response:**
```json
{
  "message": "User updated successfully"
}
```

#### DELETE `/admin/users/{id}`
Delete a user (admin only).

**Response:**
```json
{
  "message": "User deleted successfully"
}
```

## Error Handling

All API endpoints return consistent error responses:

### Error Response Format

```json
{
  "error": true,
  "message": "Error description",
  "status_code": 400,
  "details": {
    "field": "Additional error information"
  }
}
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Authentication endpoints**: 10 requests per minute
- **Deployment endpoints**: 20 requests per minute
- **Admin endpoints**: 50 requests per minute
- **General endpoints**: 100 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Caching

The API implements intelligent caching for improved performance:

- **Dashboard data**: 60 seconds TTL
- **Configuration data**: 300 seconds TTL
- **Topology data**: 600 seconds TTL

Cache can be invalidated using the `/api/cache/clear` endpoint.

## Monitoring

The API provides comprehensive monitoring endpoints:

- `/api/health` - Basic health check
- `/api/health/detailed` - Detailed health check with metrics
- `/api/metrics` - Current API metrics
- `/api/metrics/clear` - Clear collected metrics

## WebSocket Events

Real-time updates are available via WebSocket:

### Connection
```javascript
const socket = io('http://localhost:5000');
```

### Events

#### `deployment_progress`
Receive deployment progress updates:
```javascript
socket.on('deployment_progress', (data) => {
  console.log('Deployment progress:', data);
});
```

#### `deployment_complete`
Receive deployment completion notifications:
```javascript
socket.on('deployment_complete', (data) => {
  console.log('Deployment completed:', data);
});
```

#### `deployment_error`
Receive deployment error notifications:
```javascript
socket.on('deployment_error', (data) => {
  console.log('Deployment error:', data);
});
```

## SDK and Client Libraries

### Python Client

```python
from lab_automation_client import LabAutomationClient

client = LabAutomationClient(
    base_url="http://localhost:5000/api/v1",
    username="username",
    password="password"
)

# List configurations
configs = client.configurations.list()

# Deploy configuration
deployment = client.configurations.deploy(config_id=123)
```

### JavaScript/Node.js Client

```javascript
const { LabAutomationClient } = require('lab-automation-client');

const client = new LabAutomationClient({
  baseUrl: 'http://localhost:5000/api/v1',
  username: 'username',
  password: 'password'
});

// List configurations
const configs = await client.configurations.list();

// Deploy configuration
const deployment = await client.configurations.deploy(123);
```

## Support and Documentation

For additional support and documentation:

- **API Documentation**: This document
- **Code Examples**: See `/examples` directory
- **Issue Reporting**: GitHub issues
- **Community**: GitHub discussions

## Versioning

The API follows semantic versioning. Current version: `v1`

- **v1**: Current stable version
- **v2**: Future version with enhanced features (in development)

To use a specific version, include it in the URL:
```
http://localhost:5000/api/v1/...  # Current version
http://localhost:5000/api/v2/...  # Future version
```
