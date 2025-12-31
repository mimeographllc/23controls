# SecureAuth API - Postman Collection Guide

## 📦 Collection Overview

This Postman collection provides complete API coverage for the SecureAuth SSO Application, including:

- **Authentication** - Signup, Login, Token Refresh, Logout
- **MFA (Multi-Factor Authentication)** - Setup and Verification
- **OAuth** - Google and Amazon OAuth flows
- **User Management** - Profile management and admin operations
- **RBAC** - Roles and Permissions management
- **Health & Status** - API health and documentation

## 🚀 Quick Start

### 1. Import Collection into Postman

#### Option A: Import from File
1. Open Postman
2. Click **Import** button (top left)
3. Select **SecureAuth_API.postman_collection.json**
4. Click **Import**

#### Option B: Import from URL
1. Open Postman
2. Click **Import** → **Link**
3. Paste the raw GitHub URL or file path
4. Click **Continue** → **Import**

### 2. Configure Collection Variables

The collection uses variables for easy configuration:

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8000` | Backend API base URL |
| `access_token` | (empty) | JWT access token (auto-populated) |
| `refresh_token` | (empty) | JWT refresh token (auto-populated) |
| `user_id` | (empty) | User ID (auto-populated) |

**To change variables:**
1. Click on the collection name
2. Go to **Variables** tab
3. Update `base_url` if needed (e.g., for production)
4. Save changes

### 3. Test Connection

Run the **Health Check** request:
```
GET {{base_url}}/health
```

**Expected Response:**
```json
{
  "status": "healthy"
}
```

## 🔑 Authentication Flow

### Step 1: Login

**Request:** `POST /auth/login`

**Body:**
```json
{
  "email": "admin@example.com",
  "password": "Admin123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

✅ **Tokens automatically saved to collection variables!**

### Step 2: Make Authenticated Requests

All endpoints marked with 🔒 require authentication. The collection automatically includes the `access_token` in the Authorization header.

**Example:** `GET /auth/me`

The request automatically includes:
```
Authorization: Bearer {{access_token}}
```

### Step 3: Refresh Token (When Expired)

**Request:** `POST /auth/refresh`

**Body:**
```json
{
  "refresh_token": "{{refresh_token}}"
}
```

New `access_token` is automatically saved!

## 📋 Collection Structure

### 1️⃣ Authentication (6 requests)

| Request | Method | Auth Required | Description |
|---------|--------|---------------|-------------|
| Sign Up | POST | ❌ | Register new user |
| Login | POST | ❌ | Get JWT tokens |
| Get Current User | GET | ✅ | User info with roles |
| Refresh Token | POST | ❌ | Refresh access token |
| Logout | POST | ✅ | Invalidate session |

### 2️⃣ MFA (2 requests)

| Request | Method | Auth Required | Description |
|---------|--------|---------------|-------------|
| Setup MFA | POST | ✅ | Get QR code & secret |
| Verify MFA Token | POST | ✅ | Verify TOTP code |

### 3️⃣ OAuth (2 requests)

| Request | Method | Auth Required | Description |
|---------|--------|---------------|-------------|
| Initiate Google OAuth | GET | ❌ | Start Google login |
| Initiate Amazon OAuth | GET | ❌ | Start Amazon login |

⚠️ **Note:** OAuth requests redirect to provider login pages. Use browser for OAuth flows.

### 4️⃣ User Management (8 requests)

| Request | Method | Auth Required | Admin Only | Description |
|---------|--------|---------------|------------|-------------|
| Get My Profile | GET | ✅ | ❌ | Current user profile |
| Update My Profile | PUT | ✅ | ❌ | Update own profile |
| Change Password | POST | ✅ | ❌ | Change own password |
| List All Users | GET | ✅ | ✅ | List all users |
| Get User by ID | GET | ✅ | ✅ | Get specific user |
| Update User | PUT | ✅ | ✅ | Update any user |
| Delete User | DELETE | ✅ | ✅ | Delete user |

### 5️⃣ Roles & Permissions (12 requests)

| Request | Method | Auth Required | Admin Only | Description |
|---------|--------|---------------|------------|-------------|
| Create Role | POST | ✅ | ✅ | Create new role |
| List Roles | GET | ✅ | ❌ | View all roles |
| Get Role by ID | GET | ✅ | ❌ | View specific role |
| Assign Role to User | POST | ✅ | ✅ | Grant role |
| Remove Role from User | DELETE | ✅ | ✅ | Revoke role |
| Create Permission | POST | ✅ | ✅ | Create permission |
| List Permissions | GET | ✅ | ❌ | View permissions |
| Get Permission by ID | GET | ✅ | ❌ | View specific permission |
| Assign Permission to Role | POST | ✅ | ✅ | Add permission to role |
| Remove Permission from Role | DELETE | ✅ | ✅ | Remove from role |
| Assign Permission to User | POST | ✅ | ✅ | Grant directly to user |
| Remove Permission from User | DELETE | ✅ | ✅ | Revoke from user |

### 6️⃣ Health & Status (3 requests)

| Request | Method | Auth Required | Description |
|---------|--------|---------------|-------------|
| Root | GET | ❌ | API info |
| Health Check | GET | ❌ | Health status |
| API Documentation | GET | ❌ | Swagger docs |

## 🧪 Testing Scenarios

### Scenario 1: New User Registration

1. **Sign Up** - Create account
2. **Login** - Get tokens
3. **Get Current User** - Verify account

### Scenario 2: User Profile Management

1. **Login** - Authenticate
2. **Get My Profile** - View current info
3. **Update My Profile** - Change details
4. **Change Password** - Update password

### Scenario 3: MFA Setup

1. **Login** - Authenticate
2. **Setup MFA** - Get QR code
3. Scan QR code with authenticator app
4. **Verify MFA Token** - Test TOTP code

### Scenario 4: Admin User Management

1. **Login** as admin
2. **List All Users** - View users
3. **Get User by ID** - View specific user
4. **Update User** - Modify user details
5. **Assign Role to User** - Grant permissions

### Scenario 5: RBAC Configuration

1. **Login** as admin
2. **Create Role** - Define new role
3. **Create Permission** - Define permission
4. **Assign Permission to Role** - Connect them
5. **Assign Role to User** - Grant to user
6. **Get My Profile** - Verify permissions

## 🔐 Security Types

The application supports three security types:

### PASSWORD
Standard email/password authentication
```json
{
  "security_type": "PASSWORD",
  "password": "SecurePass123!"
}
```

### MFA_TOTP
TOTP-based multi-factor authentication
```json
{
  "security_type": "MFA_TOTP"
}
```

### MFA_PASSKEY
WebAuthn/FIDO2 passkey authentication
```json
{
  "security_type": "MFA_PASSKEY"
}
```

## 👥 User Tiers

| Tier | Value | Description |
|------|-------|-------------|
| Free | `FREE` | Basic features |
| Basic | `BASIC` | Standard features |
| Premium | `PREMIUM` | Advanced features |
| Enterprise | `ENTERPRISE` | All features |

## 📝 Request Body Examples

### Sign Up
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "organization": "Acme Corp",
  "division": "Engineering",
  "security_type": "PASSWORD",
  "password": "SecurePass123!"
}
```

### Login
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

### Update Profile
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "organization": "New Company",
  "division": "Marketing"
}
```

### Change Password
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass123!"
}
```

### Create Role
```json
{
  "name": "Editor",
  "description": "Can edit content",
  "tier_required": "FREE"
}
```

### Create Permission
```json
{
  "name": "edit_posts",
  "module": "posts",
  "action": "edit",
  "description": "Permission to edit posts",
  "tier_required": "FREE"
}
```

## 🎯 Response Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created |
| 204 | No Content | Deleted successfully |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Invalid/missing token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 500 | Internal Server Error | Server error |
| 501 | Not Implemented | Feature not configured |

## ⚡ Pro Tips

### 1. Use Collection Runner
Run entire folder at once:
1. Right-click folder (e.g., "Authentication")
2. Select **Run folder**
3. See all tests execute in sequence

### 2. Use Pre-request Scripts
The collection includes scripts that:
- Auto-save tokens from login
- Auto-save user IDs from signup
- Set up test data

### 3. Use Test Scripts
Some requests include tests:
- Login → Saves tokens automatically
- Sign Up → Saves user_id automatically

### 4. Create Environments
For different deployments:
1. Click **Environments** (left sidebar)
2. Create **Development**, **Staging**, **Production**
3. Set different `base_url` for each
4. Switch environments easily

Example environments:
```
Development: http://localhost:8000
Staging: https://staging-api.example.com
Production: https://api.example.com
```

### 5. Export Collection Variables
Save your current session:
1. Click collection → **Variables**
2. Copy token values
3. Store securely for later use

## 🐛 Troubleshooting

### Issue: 401 Unauthorized

**Problem:** Token expired or invalid

**Solution:**
1. Run **Login** request again
2. Or run **Refresh Token** request
3. Tokens auto-update in variables

### Issue: 403 Forbidden

**Problem:** Insufficient permissions

**Solution:**
1. Check user roles: **Get My Profile**
2. Contact admin to assign role
3. Login as admin for admin operations

### Issue: Connection Refused

**Problem:** Backend not running

**Solution:**
```bash
# Check if backend is running
docker-compose ps

# Start backend
docker-compose up -d backend

# Check logs
docker-compose logs -f backend
```

### Issue: OAuth Redirects Don't Work

**Problem:** OAuth requires browser interaction

**Solution:**
1. Use OAuth requests in browser, not Postman
2. Or use frontend application for OAuth
3. Postman can't handle OAuth redirects properly

### Issue: Invalid Request Body

**Problem:** Wrong JSON format

**Solution:**
1. Check **Body** → **raw** → **JSON** is selected
2. Validate JSON syntax
3. Check example request bodies above

## 📊 Monitoring Requests

### View Request Details
1. Click **Console** (bottom left in Postman)
2. See full request/response logs
3. Debug headers, body, status codes

### Save Responses
1. Send request
2. Click **Save Response** → **Save as example**
3. Document expected responses

## 🔄 Automated Testing

### Collection Tests
Some requests include automated tests:

**Login Request:**
```javascript
if (pm.response.code === 200) {
    var jsonData = pm.response.json();
    pm.collectionVariables.set('access_token', jsonData.access_token);
    pm.collectionVariables.set('refresh_token', jsonData.refresh_token);
}
```

**Sign Up Request:**
```javascript
if (pm.response.code === 201) {
    var jsonData = pm.response.json();
    pm.collectionVariables.set('user_id', jsonData.id);
}
```

These run automatically after each request!

## 📚 Additional Resources

- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

## 🎉 Summary

This Postman collection provides:
- ✅ **30+ API endpoints** fully documented
- ✅ **Automatic token management** via test scripts
- ✅ **Pre-configured examples** for all requests
- ✅ **RBAC support** with roles and permissions
- ✅ **MFA testing** with TOTP verification
- ✅ **OAuth integration** endpoints
- ✅ **Admin operations** for user management

**Quick start:**
1. Import collection
2. Run "Login" request
3. Tokens auto-saved
4. All authenticated requests work!

Happy testing! 🚀
