# MSTY Debt Tracker

A comprehensive financial tracking application for MSTY investments with multiple tools:

- 📈 Compounding Simulator
- 📊 Cost Basis Tool
- 💸 Return on Debt
- 🛡️ Hedging Tool
- 📊 Simulated vs. Actual Performance
- 📉 Market Monitoring
- 📤 Export Center

## Features

- Real-time MSTR options data integration
- Dividend reinvestment tracking
- Cost basis calculation
- Hedging strategy analysis
- Performance comparison
- Market monitoring
- Data export capabilities

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/MSTY-Debt-Tracker-Tab.git
cd MSTY-Debt-Tracker-Tab
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run app.py
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:
```
EMAIL_FROM=your_email@example.com
EMAIL_PASSWORD=your_email_password
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
```

## Deployment

The application is deployed on Render and can be accessed at [your-app-url].

## Usage

1. Navigate to the desired tool using the sidebar
2. Enter your position details and preferences
3. View analysis, calculations, and visualizations
4. Export or save results as needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 