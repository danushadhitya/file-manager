# File Manager API

A containerized file management REST API built with Flask, PostgreSQL, and LocalStack (S3-compatible storage). This application provides endpoints for uploading, listing, downloading, and deleting files with API key authentication.

## Architecture Overview

The application consists of three main components running in Docker containers:

1. **Web Application (Flask)**: Handles API requests and serves the optional web interface.
2. **PostgreSQL Database**: Stores file metadata including filename, file size, upload date and status.
3. **LocalStack**: Provides S3-compatible object storage for actual file data

### Data Flow

- **File Upload**: Files are uploaded to the S3 bucket (LocalStack), and metadata is stored in PostgreSQL
- **File Listing**: Metadata is retrieved from PostgreSQL with pagination support
- **File Download**: Generates a pre-signed URL from S3 (valid for 5 minutes) for secure temporary access
- **File Deletion**: Marks the file record as deleted in PostgreSQL and deletes the file in S3 bucket.

## Prerequisites

- Docker and Docker Compose installed on your system
- Git (to clone the repository)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/danushadhitya/file-manager.git
cd file-manager
```

### 2. Create Environment File

Create a `.env` file in the project root directory with the following configuration:

```properties
# AWS/LocalStack Configuration
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
S3_BUCKET_NAME=uploadedfiles
AWS_ENDPOINT_URL=http://localstack:4566

# API Authentication
API_KEY=test-api-key

# PostgreSQL Database Configuration
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=filedb
```

**Note**: These are default values for local development. 

### 3. Start the Application

```bash
docker-compose up --build
```

This command will:
- Build the Flask application container
- Pull PostgreSQL and LocalStack images
- Create a Docker network for inter-container communication
- Initialize the database schema
- Create the S3 bucket in LocalStack
- Start all services

The application will be accessible at `http://localhost:8000`

### 4. Access the Web Interface (Optional)

Open your browser and navigate to:
```
http://localhost:8000
```

Enter your API key and use the web interface to upload, list, download, and delete files.

## API Endpoints

All API endpoints require authentication using the `X-API-KEY` header.

### 1. Upload File

Upload a single file to the system. The file is stored in S3 (LocalStack) and metadata is saved in PostgreSQL.

**Endpoint**: `POST /api/upload`



**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/upload \
  -H "X-API-KEY: test-api-key" \
  -F "file=@/path/to/your/file.pdf"
```



### 2. List Files (with Pagination)

Retrieve a paginated list of uploaded files. Default is 10 items per page.

**Endpoint**: `GET /api/list`


**Query Parameters**:
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 10, max: 20)

**cURL Examples**:

Default (page 1, 10 items):
```bash
curl -X GET http://localhost:8000/api/list \
  -H "X-API-KEY: test-api-key"
```

Custom pagination:
```bash
curl -X GET "http://localhost:8000/api/list?page=2&per_page=20" \
  -H "X-API-KEY: test-api-key"
```



### 3. Download File

Generate a pre-signed URL for downloading a file. The URL is valid for 5 minutes only.

**Endpoint**: `GET /api/download/<file_id>`



**cURL Example**:
```bash
curl -X GET http://localhost:8000/api/download/1 \
  -H "X-API-KEY: test-api-key"
```



**Usage**: Copy the `download_url` and paste it in your browser.

### 4. Delete File

Mark a file record as deleted in the database's status field and remove it from S3 bucket.

**Endpoint**: `DELETE /api/files/<file_id>`



**cURL Example**:
```bash
curl -X DELETE http://localhost:8000/api/files/1 \
  -H "X-API-KEY: test-api-key"


