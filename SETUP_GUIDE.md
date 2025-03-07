# Complete Beginner's Guide: Setting Up the Receipt Management Backend

Welcome to the Receipt Management project! This guide will walk you through setting up the entire backend environment including the main server, parsing service, and MongoDB database. This guide is especially focused on Windows setup, since that's what many team members use.

## What You'll Be Setting Up

1. MongoDB database - Stores user data and receipts
2. Django main backend server - Handles authentication and core functionality
3. Django parsing server - Processes receipt images
4. Connections between all components

## Prerequisites

- Python 3.9 or higher
- Git
- A terminal/command prompt

## Step 1: Clone the Repository

First, let's get the code on your machine:

```bash
# Clone the repository
git clone https://github.com/your-org/receipt-management.git

# Navigate to the project directory
cd receipt-management
```

## Step 2: Setting Up MongoDB on Windows

### Installing MongoDB

1. Download the MongoDB Community Server installer (.msi) from the [MongoDB website](https://www.mongodb.com/try/download/community)
2. Run the installer as administrator
3. Follow the installation wizard:
   - Accept the license agreement
   - Choose "Complete" setup type
   - Uncheck "Install MongoDB as a Service" if you prefer to start it manually
   - Keep the default data directory (`C:\Program Files\MongoDB\Server\4.4\data`) or change it
   - Complete the installation

### Adding MongoDB to Your PATH

To run MongoDB commands from any directory:

1. Right-click on "This PC" or "My Computer" and select "Properties"
2. Click on "Advanced system settings"
3. Click on "Environment Variables"
4. Find "Path" in the "System variables" section and click "Edit"
5. Click "New" and add the path to the MongoDB bin directory:
   ```
   C:\Program Files\MongoDB\Server\4.4\bin
   ```
6. Click "OK" to close all dialogs

### Verify MongoDB Installation

Open a new Command Prompt and type:
```
mongod --version
```

You should see the MongoDB version information.

### Using the Configuration File

The repository includes a configuration file for MongoDB:

1. Navigate to the backend directory in File Explorer
2. Look at the `server/mongodb.conf` file to understand its settings

To start MongoDB with this configuration:

```bash
# Navigate to the backend directory
cd backend

# Create necessary directories if they don't exist
mkdir -p server\db\data
mkdir -p server\logs

# Start MongoDB with the configuration file
mongod --config server\mongodb.conf
```

The configuration file specifies:
- Data storage location
- Log file location
- Socket path for local connections
- Port number (default: 27017)

Keep this Command Prompt window open while you're working.

## Step 3: Setting Up Python Environment

Let's create a virtual environment to keep our Python packages isolated:

```bash
# Create a virtual environment
python -m venv .env

# Activate the virtual environment on Windows
.env\Scripts\activate

# Your command prompt should now show (.env) at the beginning
```

## Step 4: Installing Dependencies

Now let's install the Python packages we need:

```bash
# Make sure you're in the backend directory
cd backend  # Skip if you're already here

# Install required packages
pip install -r requirements.txt
```

## Step 5: Setting Up the Main Django Backend

Now let's set up the main Django backend:

```bash
# Navigate to the general backend directory
cd general

# Create database tables (SQLite is used only for Django's internal mechanisms)
python manage.py migrate

# Create an admin user
python manage.py createsuperuser
```

Follow the prompts to create a username, email, and password.

## Step 6: Setting Up the Parser Service

The parser service is a separate Django application that processes receipt images:

```bash
# Open a new Command Prompt window
# Navigate to the project directory and activate the virtual environment
cd path\to\receipt-management
.env\Scripts\activate

# Navigate to the parser directory
cd backend\parser

# Set up the parser database
python manage.py migrate

# Start the parser service (use a different port from the main server)
python manage.py runserver 8001
```

Keep this Command Prompt window open too.

## Step 7: Starting the Main Backend Server

Now let's start the Django main server (in the original Command Prompt window or a new one):

```bash
# Make sure you're in the backend/general directory
cd backend\general

# Start the Django development server
python manage.py runserver
```

You should see output like:
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
March 07, 2025 - 10:30:00
Django version 4.1.13, using settings 'general.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

## Step 8: Verifying Your Setup

Let's make sure everything is running correctly:

1. **MongoDB**: You should have a Command Prompt window showing MongoDB running
2. **Parser Service**: You should have a Command Prompt window showing the parser service running on port 8001
3. **Main Backend**: You should have a Command Prompt window showing the main Django server running on port 8000

To summarize, you should have 3 separate Command Prompt windows open, each running a different component.

## Step 9: Accessing the Admin Interface

1. Open your web browser and go to http://127.0.0.1:8000/admin/
2. Log in with the superuser credentials you created earlier
3. You should see the admin interface with various MongoDB collections like Users, Receipts, etc.

## Step 10: Testing with an Example Flow

Let's test a complete workflow to make sure everything is connected properly:

### 1. Register a User

```bash
# Open a new Command Prompt
curl -X POST http://127.0.0.1:8000/api/auth/register/ -H "Content-Type: application/json" -d "{\"email\":\"test@example.com\", \"password\":\"testpassword123\", \"first_name\":\"Test\", \"last_name\":\"User\"}"
```

If you don't have curl, you can use PowerShell:
```powershell
$body = @{
    email = "test@example.com"
    password = "testpassword123"
    first_name = "Test"
    last_name = "User"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/register/" -Method Post -Body $body -ContentType "application/json"
```

### 2. Login to Get Access Token

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ -H "Content-Type: application/json" -d "{\"email\":\"test@example.com\", \"password\":\"testpassword123\"}"
```

PowerShell:
```powershell
$body = @{
    email = "test@example.com"
    password = "testpassword123"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login/" -Method Post -Body $body -ContentType "application/json"
$token = $response.access
```

Copy the access token from the response (it starts with "eyJ" and is quite long).

### 3. Upload a Receipt Image for Parsing

First, find a sample receipt image to test with.

```bash
curl -X POST http://127.0.0.1:8000/api/parser/upload/ -H "Authorization: Bearer YOUR_ACCESS_TOKEN" -F "file=@path\to\receipt.jpg"
```

PowerShell:
```powershell
$token = "YOUR_ACCESS_TOKEN"  # Replace with the actual token
$filePath = "C:\path\to\receipt.jpg"  # Replace with actual path

$headers = @{
    "Authorization" = "Bearer $token"
}

$form = @{
    file = Get-Item -Path $filePath
}

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/parser/upload/" -Method Post -Headers $headers -Form $form
$jobId = $response.job_id
```

### 4. Check Parsing Job Status

```bash
curl -X GET http://127.0.0.1:8000/api/parser/jobs/JOB_ID/ -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

PowerShell:
```powershell
$jobId = "JOB_ID"  # Replace with actual job_id from previous response
$token = "YOUR_ACCESS_TOKEN"  # Same token as before

$headers = @{
    "Authorization" = "Bearer $token"
}

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/parser/jobs/$jobId/" -Method Get -Headers $headers
```

If everything is working correctly, you should see the job status and any parsed data.

## Key API Endpoints for Frontend Development

Here are the main endpoints you'll use in your frontend development:

### Authentication
```
POST /api/auth/register/
{
  "email": "user@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}

POST /api/auth/login/
{
  "email": "user@example.com",
  "password": "securepassword"
}
Response:
{
  "access": "eyJ0eXAi...",
  "refresh": "eyJ0eXAi..."
}
```

### Using Authentication in JavaScript
```javascript
// Example of how to use the access token in JavaScript fetch
async function getReceipts() {
  const response = await fetch('http://localhost:8000/api/receipts/', {
    method: 'GET',
    headers: {
      'Authorization': 'Bearer eyJ0eXAi...',  // Replace with your access token
      'Content-Type': 'application/json'
    }
  });
  
  if (response.ok) {
    const data = await response.json();
    console.log(data);
    return data;
  } else {
    console.error('Failed to fetch receipts');
  }
}
```

### User Profile
```
GET /api/profiles/me/
Authorization: Bearer <your_access_token>

Response:
{
  "employee_id": "EMP001",
  "first_name": "John",
  "last_name": "Doe",
  "department": "Engineering",
  "position": "Developer"
}
```

### Receipts
```
GET /api/receipts/
Authorization: Bearer <your_access_token>

POST /api/receipts/
Authorization: Bearer <your_access_token>
{
  "merchant_name": "Grocery Store",
  "transaction_time": "2025-03-01T12:30:00Z",
  "total_amount": "45.67",
  "currency": "USD",
  "category": "Groceries"
}
```

### Receipt Parsing
```
POST /api/parser/upload/
Authorization: Bearer <your_access_token>
Content-Type: multipart/form-data
file: <receipt_image.jpg>

Response:
{
  "job_id": "67c88ab866c34cb3c6e7ee98",
  "status": "pending"
}

GET /api/parser/jobs/67c88ab866c34cb3c6e7ee98/
Authorization: Bearer <your_access_token>
```

## Troubleshooting Common Issues on Windows

### MongoDB Won't Start
If MongoDB doesn't start properly:
```
# Check if MongoDB is already running
tasklist | findstr mongod

# If it's running but you can't connect, you might need to kill the process
taskkill /F /IM mongod.exe

# Check if the data directory exists and is writable
# Make sure the path in mongodb.conf is correct

# Try starting MongoDB manually with verbose logging
mongod --dbpath server\db\data --logpath server\logs\mongodb.log --logappend
```

### "Command not found" Errors
If Windows can't find the `mongod` command:
```
# Try using the full path
"C:\Program Files\MongoDB\Server\4.4\bin\mongod.exe" --config server\mongodb.conf

# Make sure MongoDB is properly added to your PATH
# Restart your Command Prompt after updating PATH
```

### Path Issues
Windows paths use backslashes (`\`) rather than forward slashes (`/`). Make sure to use the correct path format:
```
# Correct Windows path
cd backend\general

# Not
cd backend/general  # This might work sometimes but can cause issues
```

### Django Server Port Already in Use
If you see "Port 8000 is already in use":
```
# Find what's using the port
netstat -ano | findstr :8000

# Kill the process (replace PID with the process ID from above)
taskkill /F /PID <PID>

# Or use a different port
python manage.py runserver 8005
```

### Virtual Environment Activation Issues
If you see an error about running scripts being disabled:
```
# Open PowerShell as Administrator and run
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Try activating the environment again
.env\Scripts\activate
```

## Daily Development Workflow

Once everything is set up, here's your daily workflow:

1. **Start MongoDB**:
   ```
   cd backend
   mongod --config server\mongodb.conf
   ```

2. **Start Parser Service**:
   ```
   cd backend\parser
   .env\Scripts\activate
   python manage.py runserver 8001
   ```

3. **Start Main Backend**:
   ```
   cd backend\general
   .env\Scripts\activate
   python manage.py runserver
   ```

4. **Start Your Frontend Development Server**:
   ```
   cd frontend
   npm start  # or whatever command launches your frontend
   ```

5. When you're done, just press Ctrl+C in each Command Prompt window to stop the services.

## Next Steps

Now that you have the complete backend environment running, you can:

1. Explore the admin interface to understand the data structure
2. Test API endpoints using the examples provided
3. Begin integrating your frontend with these endpoints
4. Ask for help if you encounter any issues

Happy coding!