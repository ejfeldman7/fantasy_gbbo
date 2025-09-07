# fantasy_gbbo

<img width="1430" height="379" alt="image" src="https://github.com/user-attachments/assets/34089df2-b520-44ed-b87f-013cdf843909" />

## 🧁 Great Fantasy Bake Off League
This is a self-hosted web application built with Streamlit for running a fantasy league based on The Great British Bake Off. It allows a group of friends or colleagues to make weekly and season-long predictions, automatically calculates scores, and provides a full suite of admin tools for the league commissioner.

## Features
### For Players
- Profile Creation: Join the league by creating a simple profile with your name and email.
- Email Allow-List: (Optional) Restrict registration to a pre-approved list of emails for private leagues.
- Weekly Picks: Each week, submit predictions for:
  - ⭐ Star Baker
  - 🏆 Technical Challenge Winner
  - 😢 Baker Sent Home
  - 🤝 Hollywood Handshake (Yes/No)
- Season Predictions: Alongside weekly picks, update your predictions for the ultimate Season Winner and the two other Finalists.
- Live Validation: The app provides real-time warnings to prevent contradictory picks (e.g., picking a baker to be eliminated and also win the season).
- Email Confirmations: Automatically receive an email summary of your picks upon submission.
- Dynamic Leaderboard: View the current league standings, with scores updated as the commissioner enters official results.
- Picks History: Review all predictions from past weeks after the submission deadline has passed, ensuring picks remain secret until they are locked in.
- Info Page: A dedicated page explaining the scoring system, rules, and deadlines.

### For the Commissioner (Admin Panel)
- Password Protected: Simple password protection for all admin functions.
- Enter Weekly Results: Easily input the official results after each episode to calculate weekly points.
- Manage Bakers: Add the new cast of bakers at the start of the season and remove them as they are eliminated.
- Manage Players: View, edit, or remove player profiles.
- Final Scoring Tool: After the finale, enter the official winner and finalists to automatically calculate and apply the weighted "Foresight Points" to the leaderboard.
- Data Management:
  - Backup: Download all league data (users, picks, results) into a single JSON file at any time.
  - Reset: Completely wipe all data to easily start a fresh season.

## ⚙️ Setup and Installation
Follow these steps to get the application running on your local machine or server.

### 1. Prerequisites
-  Python 3.8+
- pip

### 2. Clone the Repository
Clone this repository to your local machine:
```
git clone [https://github.com/your-username/fantasy-bake-off.git](https://github.com/your-username/fantasy-bake-off.git)
cd fantasy-bake-off
```

### 3. Install Dependencies
Install the required Python libraries from the requirements.txt file:

```pip install -r requirements.txt```

### 4. Create the Secrets File
This app uses Streamlit's secrets management to handle email credentials securely.
In the root of your project folder, create a new folder named .streamlit.
Inside the .streamlit folder, create a new file named secrets.toml.
Your project structure should look like this:
```
# .streamlit/secrets.toml

# Credentials for sending confirmation emails (e.g., Gmail)
# NOTE: You must use a Google "App Password", not your regular password.
[email_credentials]
sender_name = "Fantasy Bake Off Commissioner"
sender_email = "your_email@gmail.com"
sender_password = "your_16_character_app_password"

# Password to access the Admin Panel in the app
[admin_panel]
admin_password = "a_secure_password_of_your_choice"

# (Optional) Email Allow-List for registration
# If this section is omitted, anyone can register.
[allowed_emails]
emails = [
    "player.one@example.com",
    "player.two@example.com",
    "another-player@domain.org"
]
```

### 5. Generate a Gmail "App Password"
For security, you cannot use your regular Gmail password. You must generate a special App Password.
Go to your Google Account settings: myaccount.google.com.
Navigate to the Security tab.
Ensure 2-Step Verification is turned On. You cannot create an App Password without it.
At the bottom of the 2-Step Verification page, click on App passwords.
Give the app a name (e.g., "Streamlit Bake Off") and click Create.
Google will generate a 16-character password.  Copy this password (without spaces) and paste it as the sender_password value in your secrets.toml file.

### 6. Run the Application
In your terminal, from the root directory of the project, run the following command:
```streamlit run app.py```
The application should now be running in your web browser!

## 🗓️ Configuring for a New Season
### To reset the app for a new season of Bake Off, follow these steps:
- Update Dates in app.py:
- Modify the WEEK_DATES dictionary to reflect the new season's schedule.
- Modify the REVEAL_DATES_UTC dictionary with the new submission deadlines.
- Reset All Data:
  - Log in to the Admin Panel.
  - Go to the "Data Management" tab.
  - Use the "RESET ALL LEAGUE DATA" button to clear all old users, picks, and results.

### Add New Bakers:
- In the Admin Panel, go to the "Manage Bakers" tab.
- Add each of the new season's contestants to the list.

The league is now ready for a new season!

## 📁 Project Structure
```
.
├── .github/workflows/        # GitHub Actions for CI/CD
│   └── static_analysis.yml
├── .streamlit/
│   └── secrets.toml          # Secure credentials (not committed)
├── src/
│   ├── pages/                # Each page of the Streamlit app
│   │   ├── admin.py
│   │   ├── info.py
│   │   ├── leaderboard.py
│   │   └── submit_picks.py
│   ├── auth.py               # Email validation logic
│   ├── config.py             # Season-specific dates and constants
│   ├── data_manager.py       # OOP class for handling data files
│   ├── email_utils.py        # Email sending functions
│   └── scoring.py            # Scoring calculation logic
├── app.py                    # Main entry point for the app
├── requirements.txt          # Project dependencies
└── README.md                 # This file
```
