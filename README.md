# 📄 AI Resume Analyzer

A **beginner-friendly, production-ready** web app that lets users upload a PDF resume and receive instant AI-powered feedback — including a score out of 100, detected skills, missing keywords, improvement suggestions, career recommendations, and ATS tips.

Built with **Python**, **Streamlit**, and **Azure OpenAI (GPT-4)**.

---

## 🖥️ Live Demo Screenshot

```
┌─────────────────────────────────────────────────────────────────┐
│  📄 AI Resume Analyzer                                          │
│  Get instant, AI-powered feedback on your resume                │
├─────────────────────────┬───────────────────────────────────────┤
│  📂 Upload Your Resume  │  🎯 Target Job Role (optional)        │
│  [ Drop PDF here ]      │  [ Software Engineer... ]             │
│                         │  [ 🔍 Analyze Resume ]                │
├─────────────────────────┴───────────────────────────────────────┤
│  Score: 74/100  ●●●●●●●●○○  Good 👍                            │
│  Formatting 16/20  ████████████████░░░░                         │
│  Skills     18/20  ██████████████████░░                         │
│  …                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

| Feature | Detail |
|---|---|
| 📂 PDF Upload | Drag-and-drop or click to upload any text-based PDF |
| 🤖 AI Analysis | GPT-4 powered via Azure OpenAI |
| 📊 Resume Score | Weighted score out of 100 with category breakdown |
| 💡 Skill Detection | Automatically identifies technical & soft skills |
| 🔑 Missing Keywords | Role-specific keywords you should add |
| 🔧 Suggestions | Prioritized (High / Medium / Low) improvement tips |
| 🚀 Career Paths | Top matching job roles with % fit |
| ⚙️ ATS Tips | Tips to pass Applicant Tracking Systems |
| 🎨 Dark UI | Professional dark theme, mobile-responsive |

---

## 🗂️ Project Structure

```
resume_analyzer/
│
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── README.md               # This file
│
└── utils/
    ├── __init__.py         # Makes utils a Python package
    ├── pdf_reader.py       # PDF text extraction (pdfplumber + PyPDF2)
    └── analyzer.py         # Azure OpenAI integration & response parsing
```

---

## 🚀 Quick Start — Run Locally

### 1. Prerequisites
- Python **3.10+** installed ([download](https://python.org))
- An **Azure OpenAI** resource with a GPT-4 deployment
- `git` installed

### 2. Clone the repo

```bash
git clone https://github.com/YOUR-USERNAME/ai-resume-analyzer.git
cd ai-resume-analyzer
```

### 3. Create a virtual environment

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in your Azure OpenAI credentials:

```env
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_API_VERSION=2024-02-01
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### 6. Run the app

```bash
streamlit run app.py
```

Visit **http://localhost:8501** in your browser. 🎉

---

## ☁️ Deploy to GitHub

```bash
# 1. Initialise git (skip if already done)
git init
git add .
git commit -m "Initial commit — AI Resume Analyzer"

# 2. Create a new repo on github.com, then:
git remote add origin https://github.com/YOUR-USERNAME/ai-resume-analyzer.git
git branch -M main
git push -u origin main
```

> ⚠️ **Important**: Make sure `.env` is in `.gitignore` so your API key is never pushed.

```bash
echo ".env" >> .gitignore
```

---

## ☁️ Deploy to Azure App Service

### Option A — Azure CLI (recommended for beginners)

```bash
# 1. Login
az login

# 2. Create a resource group (skip if you have one)
az group create --name rg-resume-analyzer --location eastus

# 3. Create an App Service plan (free tier)
az appservice plan create \
    --name plan-resume-analyzer \
    --resource-group rg-resume-analyzer \
    --sku B1 \
    --is-linux

# 4. Create the web app
az webapp create \
    --resource-group rg-resume-analyzer \
    --plan plan-resume-analyzer \
    --name YOUR-APP-NAME \
    --runtime "PYTHON:3.11"

# 5. Set environment variables (replaces .env on Azure)
az webapp config appsettings set \
    --resource-group rg-resume-analyzer \
    --name YOUR-APP-NAME \
    --settings \
        AZURE_OPENAI_ENDPOINT="https://YOUR-RESOURCE.openai.azure.com/" \
        AZURE_OPENAI_API_KEY="your_key_here" \
        AZURE_OPENAI_API_VERSION="2024-02-01" \
        AZURE_OPENAI_DEPLOYMENT="gpt-4"

# 6. Set Streamlit startup command
az webapp config set \
    --resource-group rg-resume-analyzer \
    --name YOUR-APP-NAME \
    --startup-file "streamlit run app.py --server.port 8000 --server.address 0.0.0.0"

# 7. Deploy from local folder
az webapp up \
    --resource-group rg-resume-analyzer \
    --name YOUR-APP-NAME
```

Your app is live at: `https://YOUR-APP-NAME.azurewebsites.net`

### Option B — Deploy via GitHub Actions

1. In your GitHub repo go to **Settings → Secrets → Actions** and add:
   - `AZURE_WEBAPP_PUBLISH_PROFILE` (download from Azure Portal → your web app → Get publish profile)
2. Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Deploy to Azure Web App
        uses: azure/webapps-deploy@v2
        with:
          app-name: YOUR-APP-NAME
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| `EnvironmentError: Missing AZURE_OPENAI_ENDPOINT` | Check your `.env` file is in the project root and filled in |
| `Could not extract any text from this PDF` | The PDF is scanned. Use a text-based PDF |
| `openai.AuthenticationError` | Your API key is wrong or expired |
| `openai.NotFoundError` | Check `AZURE_OPENAI_DEPLOYMENT` matches your Azure deployment name exactly |
| App slow on first load | Normal — Streamlit cold-starts in ~3 s |

---

## 🔐 Security Notes

- Never commit your `.env` file
- Use Azure Key Vault for production secrets
- The app sends resume text to Azure OpenAI — ensure your Azure subscription has appropriate data governance settings

---

## 📄 License

MIT License — free to use, modify, and distribute.
