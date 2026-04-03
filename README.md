# MASO Project
# Project Setup & Running

## 1. Clone the Repository

```bash
git clone https://github.com/angelmj21/MASO.git
cd MASO/Ossomis
```
---

# Backend Setup

## 2. Navigate to Backend

```bash
cd backend
```

## 3. Install Dependencies

Make sure Python is installed (Python 3.8+ recommended).

```bash
pip install fastapi uvicorn
```

If a requirements file exists:

```bash
pip install -r requirements.txt
```

---

## 4. Start the Backend Server

Run the FastAPI application using **Uvicorn**:

```bash
uvicorn api:app --reload --port 8000
```

If successful, you should see:

```
Uvicorn running on http://127.0.0.1:8000
Application startup complete.
```

---

# Frontend Setup

Open another terminal and navigate to the project root:

```bash
cd Ossomis
```

Start the frontend by opening the HTML file:

```bash
start frontend/index.html
```

This will open the frontend in your default browser.

---

# Testing the Project

1. Ensure the **backend server is running on port 8000**.
2. Open the **frontend in the browser**.
3. Perform actions from the UI which will call the backend APIs. (INITIATE ANALYSIS, ROGUE_MODE (SIMULATE ATTACK))

# Stopping the Server

Press:

```
CTRL + C
```

in the backend terminal to stop the server.

---
