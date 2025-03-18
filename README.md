# Game Management System

## Overview
This is a Flask-based Game Management System that includes user authentication, game and team management, an admin panel, and profile management.

## Live Demo: https://gamemanagementsystem.glitch.me/

## Features
- User authentication (login, registration, logout)
- Admin panel to manage users, games, and teams
- Profile management for users
- Secure authentication using Flask-Login and Flask-WTF
- SQLite database for data storage

## Installation

### Prerequisites
Ensure you have Python installed (Python 3.7+ recommended).

### Steps
1. Clone the repository:
   ```sh
   git clone https://github.com/lovnishverma/game-management-system.git
   cd game-management-system
   ```
2. Create a virtual environment:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Set up the database:
   ```sh
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   ```
5. Run the application:
   ```sh
   flask run
   ```
6. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## Default Admin Credentials
- **Username:** admin  
- **Password:** Nielit@Games

## Usage
- Users can register and log in.
- Admins can add, edit, and remove users, games, and teams.
- Users can manage their profiles.

## Technologies Used
- Flask
- Flask-Login
- Flask-WTF
- SQLite
- Bootstrap (for frontend UI)

## License
This project is licensed under the MIT License. Feel free to use and modify it as needed.

## Contributing
Pull requests are welcome! If you find any issues, feel free to open an issue or contribute with a PR.

## Contact
For any questions or issues, please reach out at [princelv84@gmail.com].

