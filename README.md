# 🍰 Fantasy Great British Bake Off

<img width="1430" height="379" alt="image" src="https://github.com/user-attachments/assets/34089df2-b520-44ed-b87f-013cdf843909" />

## 🧁 Great Fantasy Bake Off League

A self-hosted web application built with Streamlit and powered by a PostgreSQL database for running a fantasy league based on The Great British Bake Off. Perfect for friend groups, families, or colleagues who want to add extra excitement to their Bake Off viewing experience with predictions, scoring, and leaderboards!

## ✨ Features

### 👥 For Players

- **🆔 Simple Registration**: Join with just your name and email
- **🔒 Email Allow-List**: Optional restriction to invited participants only
- **📝 Weekly Predictions**: Submit picks for each episode:
  - ⭐ **Star Baker** - Who will excel this week?
  - 🏆 **Technical Winner** - First place in the technical challenge
  - 😢 **Baker Eliminated** - Who goes home?
  - 🤝 **Hollywood Handshake** - Will anyone earn the coveted handshake?
- **🎯 Season-Long Predictions**: Update your finale predictions each week:
  - 👑 **Season Winner** - Who will take the title?
  - 🥈🥉 **Two Finalists** - Who else makes the final?
- **⚠️ Smart Validation**: Real-time warnings prevent contradictory picks
- **📧 Email Confirmations**: Automatic summary of your submissions
- **🏆 Live Leaderboard**: See current standings with detailed score breakdowns
- **📊 Advanced Scoring**:
  - **Weekly Points** for episode predictions (3-10 points each)
  - **Foresight Points** for season predictions (higher rewards for earlier correct picks!)
- **📋 Picks History**: Review past predictions after deadlines pass
- **📖 Info Page**: Complete scoring rules and strategy guide

### 🎛️ For Commissioners (Admin Panel)

- **🔐 Password Protection**: Secure access to all admin functions
- **🎪 Admin Override**: Temporarily allow picks for any week regardless of deadlines
- **📊 Enter Weekly Results**: Input official episode outcomes to update scores
- **👥 Baker Management**: Add new contestants, track eliminations automatically
- **👤 Player Management**: View, edit, or remove player accounts
- **🏁 Final Scoring Tool**: Enter finale results to calculate all foresight points
- **💾 Data Management**:
  - **📥 Database Backups**: Export all data as JSON
  - **📈 Real-time Stats**: View league metrics and participation
  - **🔄 Full Reset**: Start fresh for a new season
- **🌐 Cloud Database**: Powered by Neon PostgreSQL for reliability and scalability

## ⚙️ Setup and Installation

### 🗄️ Database Setup (Neon PostgreSQL)

This app uses [Neon](https://neon.tech) as a managed PostgreSQL database. It's free and perfect for this application!

1. **Create a Neon Account**: Sign up at [neon.tech](https://neon.tech)
2. **Create a Database**: Create a new project with a database named `neondb`
3. **Get Connection String**: Copy your connection string from the Neon dashboard

### 💻 Local Development Setup

#### Prerequisites

- **Python 3.8+**
- **pip** or **uv** (recommended)

#### 1. Clone the Repository

```bash
git clone https://github.com/your-username/fantasy-gbbo.git
cd fantasy-gbbo
```

#### 2. Create Virtual Environment & Install Dependencies

```bash
# Using uv (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Or using uv (faster)
uv sync
```

#### 3. Configure Secrets

Create `.streamlit/secrets.toml` with your configuration:

```toml
# Database connection (from your Neon dashboard)
[connections.neon]
url = "postgresql://username:password@host/neondb?sslmode=require"

# Email settings for confirmations (Gmail App Password required)
[email_credentials]
sender_name = "Fantasy Bake Off Commissioner"
sender_email = "your_email@gmail.com"
sender_password = "your_16_character_app_password"

# Admin panel access
[admin_panel]
admin_password = "your_secure_admin_password"

# Optional: Restrict registration to specific emails
[allowed_emails]
emails = [
    "player1@example.com",
    "player2@example.com"
]
```

#### 4. Gmail App Password Setup

1. Go to [Google Account Settings](https://myaccount.google.com)
2. Enable **2-Factor Authentication** (required)
3. Go to **Security** → **App passwords**
4. Create new app password for "Fantasy Bake Off"
5. Use the 16-character password in your `secrets.toml`

#### 5. Run the Application

```bash
streamlit run app.py
```

Open your browser to `http://localhost:8501` 🎉

### ☁️ Deployment Options

- **Streamlit Community Cloud**: Connect your GitHub repo for free hosting
- **Railway**: Easy PostgreSQL + Streamlit deployment
- **Heroku**: Classic platform with PostgreSQL add-ons
- **Self-hosted**: Any server with Python and PostgreSQL access

## 🎬 Setting Up for a New Season

### 📅 Update Season Configuration

Edit `src/config.py` to match the new season:

```python
# Update week dates and deadlines
WEEK_DATES = {
    "2": "Week 2 (Date)",
    "3": "Week 3 (Date)",
    # ... add all weeks
}

REVEAL_DATES_UTC = {
    "2": datetime(2025, 9, 19, 7, 0, 0, tzinfo=timezone.utc),
    # ... submission deadlines for each week
}
```

### 🧹 Reset League Data

1. **Admin Panel** → **Data Management** tab
2. **Create Backup** (optional but recommended!)
3. **RESET ALL LEAGUE DATA** to clear old season

### 👨‍🍳 Add New Contestants

1. **Admin Panel** → **Manage Bakers** tab
2. Add each new baker to the roster
3. Bakers are automatically tracked as eliminated during the season

### 🚀 Season Ready!

Your league is now configured for the new season of Bake Off!

## 📁 Project Structure

```
fantasy-gbbo/
├── 📂 src/
│   ├── 📂 pages/             # Streamlit app pages
│   │   ├── admin.py          # 🎛️ Admin panel with all management tools
│   │   ├── info.py           # 📖 Rules and scoring explanation
│   │   ├── leaderboard.py    # 🏆 Live scoring and standings
│   │   └── submit_picks.py   # 📝 Weekly prediction submission
│   ├── auth.py               # 🔐 Email validation and normalization
│   ├── config.py             # 📅 Season dates and deadlines
│   ├── data_manager.py       # 🗄️ Database abstraction layer
│   ├── database.py           # 🐘 PostgreSQL database operations
│   ├── email_utils.py        # 📧 Email confirmation system
│   └── scoring.py            # 🧮 Points calculation engine
├── 📂 .streamlit/
│   └── secrets.toml          # 🔐 Database & email credentials
├── 📂 .github/workflows/     # 🤖 CI/CD automation
├── app.py                    # 🚀 Main application entry point
├── requirements.txt          # 📦 Python dependencies
└── README.md                 # 📖 This documentation
```

## 🎯 Key Technologies

- **🎨 Frontend**: Streamlit with beautiful UI components
- **🗄️ Database**: Neon PostgreSQL (managed, serverless)
- **📊 Data Processing**: Pandas for scoring calculations
- **📧 Email**: SMTP integration for confirmations
- **🔐 Security**: Streamlit secrets management
- **🚀 Deployment**: Streamlit Community Cloud ready

## 📊 Scoring System Details

### Weekly Points (per episode)

| Prediction             | Correct | Penalty                |
| ---------------------- | ------- | ---------------------- |
| 🤝 Hollywood Handshake | +10 pts | -10 pts                |
| ⭐ Star Baker          | +5 pts  | -5 pts (if eliminated) |
| 😢 Eliminated Baker    | +5 pts  | -5 pts (if star baker) |
| 🏆 Technical Winner    | +3 pts  | None                   |

### Foresight Points (season finale)

- **👑 Season Winner**: `(11 - week_number) × 10` points
- **🥈🥉 Finalists**: `(11 - week_number) × 5` points each
- **Strategy**: Earlier correct predictions = exponentially more points!

Example: Correctly picking the winner in Week 2 = **90 points**, but waiting until Week 9 = only **20 points**

## 🛠️ Contributing

Pull requests welcome! Please ensure your code:

- ✅ Follows the existing code style
- 📝 Includes proper docstrings
- 🧪 Doesn't break existing functionality
- 🎨 Maintains the fun, baking-themed UI

## 📄 License

This project is open source and available under the MIT License.

---

<div align="center">

**🍰 Happy Baking and May the Best Predictions Win! 🏆**

_Built with ❤️ for fans of The Great British Bake Off_

</div>
