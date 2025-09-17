# IDEN CHALLENGE 02- Atlassian Sync - Integration Engineer Assessment

## 📋 Project Overview

This project provides automation scripts for managing **users and groups** in Atlassian accounts using Python and Playwright.  
It includes:

- **`create_data.py`** – Automates the creation of test users and groups.
- **`extract_data.py`** – Extracts and parses users/groups data from Atlassian APIs.

## ✨ Features

- **Automated Login and test data creation** – Secure Atlassian authentication with robust error handling with automated group and user data creation
- **API Integration** – Uses API requests instead of HTML scraping for reliability
- **Pagination Support** – Handles large datasets across multiple pages
- **Comprehensive Extraction** – Fetches users, groups, and memberships
- **Error Resilience** – Multiple fallback strategies for UI interactions
- **JSON Output** – Structured outputs (`users.json`, `groups.json`)

---

## 🚀 Quick Start

### Prerequisites

- Python **3.8+**
- Git
- Atlassian account with **admin privileges**

### Installation

```bash
# Clone the repository
git clone https://github.com/Darshan-gowda-m/IDEN_CHALLENGE_2
cd IDEN_CHALLENGE_2

# Create a virtual environment
python -m venv venv

# Install dependencies
pip install -r requirements.txt
playwright install
```

### Configuration

Create a `config.json` file:

```json
{
  "email": "your-email@example.com",
  "password": "your-password",
  "num_users": 50,
  "num_groups": 25,
  "users_per_group": 2,
  "headless": false,
  "domain": "gmail.com",
  "slow_mo": 100,
  "timeout": 30000
}
```

---

## 📖 Usage

### 1. Create Test Data (Optional)

```bash
python create_data.py
```

Creates the specified number of users and groups in your Atlassian account.

### 2. Extract Data

```bash
python extract_data.py
```

- Logs in to Atlassian
- Fetches users and groups via API
- Extracts membership relationships
- Generates `users.json` and `groups.json`

---

## 📁 Project Structure

```
atlassian-sync/
├── create_data.py        # Script to create test users/groups
├── extract_data.py         # Script to extract users/groups
├── config.json           # Configurations
├── requirements.txt      # Dependencies
├── users.json            # Output: Users data
├── groups.json           # Output: Groups data
├── created_users.json    # Cache: Created users
├── created_groups.json   # Cache: Created groups
└── README.md             # Documentation
```

---

## 🔧 Configuration Parameters

| Parameter         | Description                  | Default   |
| ----------------- | ---------------------------- | --------- |
| `email`           | Atlassian admin email        | Required  |
| `password`        | Atlassian password           | Required  |
| `num_users`       | Number of test users to add  | 0         |
| `num_groups`      | Number of test groups to add | 0         |
| `users_per_group` | Users per group              | 2         |
| `headless`        | Run browser in background    | false     |
| `domain`          | Email domain for test users  | gmail.com |
| `slow_mo`         | Slow down interactions (ms)  | 100       |
| `timeout`         | Operation timeout (ms)       | 30000     |

---

## 📊 Output Format

### `users.json`

```json
[
  {
    "id": "user-account-id",
    "name": "User Name",
    "email": "user@gmail.com",
    "last_active": "2023-10-15T12:00:00Z",
    "status": "active",
    "groups": ["group-id-1", "group-id-2"]
  }
]
```

### `groups.json`

```json
[
  {
    "id": "group-id",
    "name": "Group Name",
    "description": "Group description",
    "members": ["user-id-1", "user-id-2"]
  }
]
```

---

## 🐛 Troubleshooting

### Common Issues

- **Login Failures**

  - Verify credentials in `config.json`
  - Disable 2FA for testing
  - Use `"headless": false` to debug

- **API Errors**

  - Ensure admin privileges
  - Check network connection

- **Element Not Found**
  - Increase `timeout`
  - Increase `slow_mo`

### Debug Mode

Enable debug mode by editing `config.json`:

```json
"headless": false,
"slow_mo": 500
```

---

---

## 📄 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file.

---
