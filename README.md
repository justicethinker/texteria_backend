# Texteria Backend (Medinnovate)

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688)
![Database](https://img.shields.io/badge/ORM-SQLAlchemy-red)
![License](https://img.shields.io/badge/license-MIT-green)

## About
Texteria is a robust backend infrastructure designed specifically for tracking, managing, and analyzing malaria cases. By providing secure API endpoints for data collection, authentication, and seamless database management, this service supports healthcare initiatives in monitoring and combating the spread of the disease efficiently.

## Features
* **Secure Authentication:** Built-in user authentication and authorization logic to protect sensitive health data.
* **Data Validation:** Strict input validation and serialization using Pydantic schemas.
* **Relational Database Modeling:** Comprehensive data models managed via SQLAlchemy.
* **Automated Migrations:** Database schema version control and migrations handled out-of-the-box with Alembic.

## Prerequisites
Before running the project, ensure you have the following installed:
* **Python** (v3.9 or higher)
* **pip** (Python package installer)
* A running SQL database (e.g., PostgreSQL or SQLite depending on your database URL)

## Installation
Run the following commands to get your local development environment set up:

```bash
# 1. Clone the repository
git clone [https://github.com/justicethinker/texteria_backend.git](https://github.com/justicethinker/texteria_backend.git)
cd texteria_backend

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# 3. Install the dependencies
pip install -r requirements.txt

# 4. Configure Environment Variables
# Create a .env file for your database credentials and secret keys
cat <<EOT >> .env
DATABASE_URL=sqlite:///./texteria.db  # Replace with your actual DB URL
SECRET_KEY="your_super_secret_key"
ALGORITHM="HS256"
EOT

# 5. Run Database Migrations
alembic upgrade head
```

## Usage

### Running the Server
To start the development server with live reloading:
```bash
uvicorn main:app --reload
```

Once the server is running, you can access the interactive API documentation natively provided by FastAPI at:
* **Swagger UI:** `http://127.0.0.1:8000/docs`
* **ReDoc:** `http://127.0.0.1:8000/redoc`

## Contributing
We welcome contributions to help improve health-tech infrastructure!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/NewEndpoint`)
3. Commit your Changes (`git commit -m 'Add some NewEndpoint'`)
4. Push to the Branch (`git push origin feature/NewEndpoint`)
5. Open a Pull Request

## License
Distributed under the MIT License. See `LICENSE` for more information.

---
**Contact:** justicethinker2@gmail.com | [GitHub](https://github.com/justicethinker)
