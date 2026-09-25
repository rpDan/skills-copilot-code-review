# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View active announcements, and (for signed-in teachers) create, edit and delete them

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| GET    | `/announcements/active`                                           | Get announcements currently within their active date range          |
| GET    | `/announcements?teacher_username=...`                             | Get all announcements (requires teacher authentication)              |
| POST   | `/announcements?teacher_username=...`                             | Create an announcement (requires teacher authentication)             |
| PUT    | `/announcements/{announcement_id}?teacher_username=...`           | Update an announcement (requires teacher authentication)             |
| DELETE | `/announcements/{announcement_id}?teacher_username=...`           | Delete an announcement (requires teacher authentication)             |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

3. **Announcements** - Uses a generated id as identifier:
   - Message
   - Optional start date (defaults to immediately active)
   - Required expiration date
   - Teacher who created it

All data is stored in memory, which means data will be reset when the server restarts.
