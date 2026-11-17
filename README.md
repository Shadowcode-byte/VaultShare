# 🛡️ VaultShare
### Secure Student File & Document Sharing System

**A security-focused document-sharing platform designed to give students control over their files, permissions, and privacy.**

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![React](https://img.shields.io/badge/Frontend-React-61DAFB)
![Docker](https://img.shields.io/badge/Containerization-Docker-2496ED)
![License](https://img.shields.io/badge/License-Not%20Specified-lightgrey)

---

## 📌 Overview

VaultShare is a full-stack web application designed for secure document storage and controlled file sharing among students.

Students regularly exchange assignments, notes, presentations, and academic documents. However, conventional sharing workflows may not provide the application-specific authorization, integrity verification, and security auditing required for sensitive academic material.

VaultShare addresses these challenges by combining **AES-256-GCM encryption, SHA-256 integrity verification, permission-based file sharing, secure authentication, and administrative audit logging** in a single platform.

The application is built using React, FastAPI, and SQLAlchemy, with Docker-based containerization.

## ✨ Key Features

### 🔐 Authentication & Authorization
- Student registration and login.
- Argon2 password hashing.
- HttpOnly session cookies.
- Secure and SameSite cookie settings for HTTPS deployment.
- Server-side session validation and logout revocation.
- Role-based access control for students and administrators.
- Disabled-account enforcement.

### 📁 Secure File Management
- Upload and manage academic documents.
- Supported formats: PDF, DOCX, PPTX, XLSX, TXT, JPG, JPEG, and PNG.
- Maximum upload size of 15 MB.
- File extension and content validation.
- Filename sanitization.
- Encrypted document storage.
- Authorized file downloads.
- Owner-controlled file deletion.

### 🔒 AES-256-GCM Encryption
VaultShare encrypts uploaded files before saving them.

AES-256-GCM provides authenticated encryption, protecting file confidentiality while detecting unauthorized ciphertext modifications.

Encryption keys are supplied through environment configuration rather than hardcoded into the application.

### 🔍 SHA-256 Integrity Verification
Each uploaded document is associated with a SHA-256 fingerprint.

The integrity verification feature helps detect whether document contents have changed unexpectedly.

### 🤝 Permission-Based File Sharing
Students can share documents with other registered users using controlled permissions.

- **View Only:** Access file information without download permission.
- **Download:** Download the shared document.
- **Revocation:** File owners can revoke previously granted access.

Permission checks are enforced by the backend.

### 🛡️ Administrator Dashboard
Administrators can:
- View registered users and their account statuses.
- Disable and re-enable student accounts.
- Review security-related audit events.
- Monitor successful and failed logins.
- Review unauthorized access attempts.
- Inspect file-sharing and integrity-related activity.

---

## 🧰 Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| ORM | SQLAlchemy |
| Database | SQLite (local demonstration) |
| Database migrations | Alembic |
| Password hashing | Argon2 |
| File encryption | AES-256-GCM |
| Integrity verification | SHA-256 |
| Containerization | Docker |
| HTTPS demonstration | Cloudflare Tunnel |
| Version control | Git & GitHub |

The backend also supports PostgreSQL connection configuration for future cloud deployment.

---

## 🏗️ System Architecture

```text
                 STUDENT / ADMIN
                        |
                        v
                REACT FRONTEND
                        |
                        v
                 FASTAPI BACKEND
                        |
          +-------------+-------------+
          |             |             |
          v             v             v
    AUTHENTICATION   FILE SECURITY   ADMINISTRATION
          |             |             |
          v             v             v
      SESSIONS      AES-256-GCM     AUDIT LOGS
      USER ROLES    SHA-256         USER MANAGEMENT
      PASSWORDS     PERMISSIONS
          |             |
          v             v
     SQL DATABASE   ENCRYPTED STORAGE
```

### File Upload Workflow

1. The user authenticates.
2. The backend validates the uploaded document.
3. A SHA-256 fingerprint is calculated.
4. The file is encrypted using AES-256-GCM.
5. Encrypted content is saved to protected storage.
6. File metadata is recorded in the database.

### File Download Workflow

1. The backend validates the user's session.
2. File access permissions are checked.
3. Encrypted content is retrieved.
4. Decryption and integrity checks are performed.
5. The original file is returned to an authorized user.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js and npm
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Shadowcode-byte/VaultShare.git
cd VaultShare
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Create a local environment file from the example:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Configure the required database, session, encryption, and storage settings in `.env`.

Generate an encryption key using the project's key-generation script:

```bash
python scripts/generate_key.py
```

Keep all secrets private. Never commit `.env` or encryption keys.

Run database migrations:

```bash
python -m alembic upgrade head
```

Start FastAPI:

```bash
python -m uvicorn app.main:app --reload
```

Backend API:

`http://127.0.0.1:8000`

API documentation:

`http://127.0.0.1:8000/docs`

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

`http://localhost:5173`

---

## 🐳 Docker Deployment

VaultShare includes Docker configuration on the `deployment` branch.

```bash
git switch deployment
docker build -t vaultshare .
```

The Docker configuration builds the React frontend and packages it with the FastAPI application.

A container requires appropriate environment variables for database connectivity, encryption keys, session configuration, and file storage.

For the current demonstration, a persistent host-mounted directory is used to retain the local SQLite database and encrypted files between container restarts.

**Note:** A Docker image alone does not provide persistent storage. Production deployments require separately managed persistent storage and secure secret configuration.

---

## 🌐 Public Demonstration

VaultShare has been demonstrated using **Docker and Cloudflare Tunnel**.

The tunnel provides a temporary public HTTPS address that forwards requests to the application running on the developer's machine.

This setup allows remote demonstration without migrating the entire application to permanent cloud infrastructure.

**Deployment status:** Temporary public HTTPS demonstration.

The application is not currently guaranteed to be available 24/7. The tunnel and host machine must remain running.

For security reasons, the demonstration should use fictional accounts and synthetic documents only.

---

## 🧪 Security Testing

VaultShare includes automated checks covering:

- Database constraints and relationships.
- Registration and authentication.
- Session revocation.
- File validation and upload restrictions.
- AES-256-GCM encryption and tampering detection.
- SHA-256 integrity verification.
- Sharing permissions and access revocation.
- Administrator authorization.
- User account disabling.
- File deletion and audit-history preservation.

The project's standalone Python test scripts are located in the `backend` directory.

Example:

```bash
cd backend
python test_phase3_auth.py
python test_phase5_crypto.py
python test_phase6_integrity.py
python test_phase7_sharing.py
python test_phase8_admin.py
```

**Testing note:** The HTTP storage-permission test includes a Windows-specific adaptation. Owner-only NTFS ACL security has not been independently verified. Automated test success does not constitute a complete production security audit.

---

## 🔮 Future Enhancements

- Permanent cloud deployment with independently hosted backend services.
- PostgreSQL production database integration.
- Persistent cloud object storage for encrypted documents.
- Email verification and password recovery.
- Multi-factor authentication.
- Enhanced administrative analytics.
- Automated backups and recovery procedures.
- Continuous integration and deployment.
- Additional security hardening and penetration testing.
- Improved accessibility and mobile experience.

---

## 📂 Repository Structure

```text
VaultShare/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── db/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   └── services/
│   ├── alembic/
│   ├── scripts/
│   ├── requirements.txt
│   └── test_phase*.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── context/
│   │   └── pages/
│   └── package.json
├── Dockerfile
├── .dockerignore
├── deployment/
└── .gitignore
```

**Note:** Docker and deployment configuration files are available on the `deployment` branch.

---

## ⚠️ Security & Deployment Disclaimer

VaultShare is an educational cybersecurity project and working prototype.

Although it implements multiple security controls and has undergone functional and automated testing, it has not undergone a comprehensive independent security audit.

Do not use the demonstration deployment for sensitive or confidential documents.

Production use requires additional infrastructure hardening, access controls, backups, monitoring, and security validation.

---

## 👨‍💻 Development

Developed as a student cybersecurity project.

**Project Repository:** [Shadowcode-byte/VaultShare](https://github.com/Shadowcode-byte/VaultShare)

**GitHub:** [@Shadowcode-byte](https://github.com/Shadowcode-byte)

---

### VaultShare — Your Documents. Your Control.

*Secure storage. Controlled sharing. Verifiable integrity.*
