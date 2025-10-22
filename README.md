# DevInsight 🔍

**AI-Powered GitHub Analytics with BigQuery, Elasticsearch & Gemini**

> Built for Google Cloud Hackathon 2025 - Transform raw GitHub data into actionable insights through natural language queries.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React 19](https://img.shields.io/badge/react-19-blue.svg)](https://react.dev/)

## 🌐 Live Demo

**🚀 Try it now:** [https://devinsight-a5gtwfjn3-moinaktar-shaikhs-projects.vercel.app](https://devinsight-a5gtwfjn3-moinaktar-shaikhs-projects.vercel.app)

**Backend API:** [https://google-hackathon-2025.onrender.com](https://google-hackathon-2025.onrender.com)

---

## 🚀 What is DevInsight?

DevInsight analyzes public GitHub repositories and answers natural language questions like:

- *"Who contributed the most?"*
- *"Show me issues from January 2025"*
- *"What's blocking us?"*
- *"Recent closed issues"*

### Demo Flow

1. **Data Pipeline**: GitHub API → BigQuery → Elasticsearch (with embeddings)
2. **AI Analysis**: Ask questions in natural language using RAG (Retrieval-Augmented Generation)
3. **Visual Insights**: Interactive charts + AI-powered answers

## 🏗️ Architecture

```
GitHub API → BigQuery (Data Warehouse) → Elasticsearch (Vector Store)
                ↓                              ↓
            Analytics API ← LangChain RAG → Vertex AI (Gemini)
                ↓
          React Frontend
```

**Key Components:**
- **GitHub REST API**: Direct data fetching (issues + contributors)
- **BigQuery**: Structured data warehouse with SQL analytics
- **Elasticsearch**: Vector search with dense embeddings (3072 dims)
- **Vertex AI**: Gemini Embedding Model + Gemini 2.5 Flash LLM
- **LangChain**: RAG pipeline orchestration
- **React + Vite**: Modern chat interface with Recharts visualizations

## 📦 Tech Stack

### Backend
- **Python 3.9+** - Programming language
- **FastAPI** - Modern API framework
- **LangChain** - RAG pipeline orchestration
- **Google Cloud BigQuery** - Data warehouse
- **Elasticsearch Cloud** - Vector search store
- **Vertex AI** - Gemini embeddings & LLM
- **GitHub REST API** - Data source

### Frontend
- **React 19** - UI framework
- **Vite 7** - Build tool & dev server
- **Recharts 3** - Data visualization
- **React Markdown** - Formatted AI responses
- **Lucide React** - Icon library
- **TailwindCSS 4** - Styling

### Cloud Services
- **Google Cloud Platform** - Vertex AI, BigQuery
- **Elasticsearch Cloud** - Managed vector store

## 🛠️ Complete Setup Guide

### Prerequisites

**Required:**
- **Python 3.9+** and **Node.js 18+**
- **Google Cloud Platform** account with billing enabled
- **Elasticsearch Cloud** account (free trial available)
- **GitHub** Personal Access Token

---

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/googlehackathon.git
cd googlehackathon
```

---

### Step 2: Google Cloud Platform Setup

#### 2.1 Create GCP Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project (e.g., `devinsight-ai`)
3. Note your **Project ID**

#### 2.2 Enable APIs
Enable these APIs in your GCP project:
- ✅ **Vertex AI API** (for embeddings and LLM)
- ✅ **BigQuery API** (for data warehouse)
- ✅ **Cloud Storage API** (for service accounts)

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable storage.googleapis.com
```

#### 2.3 Create Service Account
1. Go to **IAM & Admin → Service Accounts**
2. Click **"Create Service Account"**
3. Name: `devinsight-service-account`
4. Grant roles:
   - **BigQuery Admin**
   - **Vertex AI User**
   - **Storage Object Admin**
5. Generate **JSON key** and save as `backend/hackathon-github-ai-xxxxx.json`

#### 2.4 Create BigQuery Dataset
1. Go to **BigQuery Console**
2. Create dataset: `github_analytics`
3. Location: `US (multiple regions)`

---

### Step 3: Elasticsearch Cloud Setup

#### 3.1 Create Account & Deployment
1. Sign up at [Elastic Cloud](https://cloud.elastic.co/registration)
2. Create deployment:
   - Name: `devinsight-vector-store`
   - Provider: **Google Cloud Platform**
   - Region: `us-central1`
   - Version: Latest (8.x)
3. **Save credentials:**
   - Cloud ID
   - elastic password

---

### Step 4: GitHub Personal Access Token

1. Go to [GitHub Settings → Developer Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. Generate new token (classic)
3. Select scopes:
   - ✅ `repo` (Full control of repositories)
   - ✅ `read:org`
   - ✅ `read:user`
4. Copy token (starts with `ghp_`)

---

### Step 5: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 5.1 Configure Environment Variables

Create `backend/.env` file:

```env
# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=hackathon-github-ai-xxxxx.json
GCP_PROJECT_ID=your-gcp-project-id
VERTEX_AI_LOCATION=us-central1

# Elasticsearch
YOUR_CLOUD_ID=your-elastic-cloud-id
YOUR_PASSWORD=your-elastic-password
ELASTIC_INDEX=github_issues

# GitHub
GITHUB_TOKEN=ghp_your_github_token

# API
API_HOST=0.0.0.0
API_PORT=8000
```

---

### Step 6: Data Ingestion (Run Once)

Run these commands from `backend/src/` directory **in order**:

#### 6.1 Fetch GitHub Data
```bash
cd src
python github_connector.py
```
*Fetches issues and contributors from GitHub*

#### 6.2 Load into BigQuery
```bash
python bigquery_loader.py
```
*Creates table and inserts data in batches*

#### 6.3 Setup Elasticsearch Index
```bash
python rebuild_elasticindex.py
```
*Creates index with proper dense_vector mapping (3072 dims)*

#### 6.4 Generate Embeddings
```bash
python generate_embeddings.py
```
*Generates embeddings using Vertex AI and indexes in Elasticsearch*
⏱️ **This takes 10-20 minutes**

---

### Step 7: Start Backend Server

```bash
cd src
python main.py
```

**Server runs on:** `http://localhost:8000`

**Test it:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"DevInsight API"}
```

---

### Step 8: Frontend Setup

Open **new terminal**:

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
echo "VITE_API_URL=http://localhost:8000" > .env

# Start dev server
npm run dev
```

**Frontend runs on:** `http://localhost:5173`

---

### Step 9: Access Application

1. Open browser: **http://localhost:5173**
2. Try these queries in Chat:
   - "Who contributed the most?"
   - "Show me issues from January 2025"
   - "What's blocking us?"
3. Check **Reports** tab for analytics dashboard

---

## 📁 Project Structure

```
googlehackathon/
├── frontend/                         # React Frontend
│   ├── src/
│   │   ├── interface.jsx             # Main UI (Chat + Reports)
│   │   ├── App.jsx                   # App wrapper
│   │   ├── main.jsx                  # Entry point
│   │   ├── config.js                 # API config
│   │   └── assets/
│   │       └── logo.jpg.png          # Logo
│   ├── package.json
│   ├── vite.config.js
│   └── .env                          # VITE_API_URL
│
├── backend/                          # Python Backend
│   ├── src/
│   │   ├── main.py                   # FastAPI server (API endpoints)
│   │   ├── langchain_query.py        # RAG pipeline (LangChain + Vertex AI)
│   │   ├── github_connector.py       # GitHub API data fetching
│   │   ├── bigquery_loader.py        # BigQuery data loading
│   │   ├── rebuild_elasticindex.py   # Elasticsearch index setup
│   │   ├── generate_embeddings.py    # Embedding generation & indexing
│   │   └── utils.py                  # Helper functions
│   ├── requirements.txt
│   ├── .env                          # Environment variables
│   └── hackathon-github-ai-xxxxx.json # GCP service account key
│
├── docs/
│   ├── architecture.md               # System architecture
│   └── setup_guide.md                # Detailed setup
│
├── data_pipeline/
│   └── notebooks/
│       └── demo_notebook.ipynb       # Analysis demos
│
└── README.md                         # This file
```

## 🎯 Key Features

### Chat Interface
- 💬 **Natural Language Queries**: Ask questions in plain English
- 🤖 **AI-Powered Answers**: Gemini 2.5 Flash with RAG (Retrieval-Augmented Generation)
- 🔍 **Semantic Search**: Vector-based search using 3072-dim embeddings
- 📝 **Formatted Responses**: Markdown rendering with links, lists, and code blocks

### Analytics Dashboard
- 📊 **Issue Statistics**: Open vs Closed issues with pie charts
- 👥 **Top Contributors**: Bar chart showing commit counts
- ⚡ **Quick Stats**: Closed issues, avg resolution time, top contributor
- 🚨 **Blockers**: List of open issues requiring attention
- 📋 **Recent Activity**: Latest 20 issues with state and metadata

### Technology
- **Vector Search**: Elasticsearch with dense_vector field (cosine similarity)
- **Embeddings**: Vertex AI Gemini Embedding Model (3072 dimensions)
- **LLM**: Vertex AI Gemini 2.5 Flash for answer generation
- **Data Warehouse**: BigQuery with SQL analytics
- **Modern UI**: React 19 with Recharts visualizations

## 📚 API Documentation

When backend is running, access interactive API docs:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/ask` | POST | Natural language chat query (RAG) |
| `/query` | POST | Alias for /ask |
| `/chat` | POST | Alias for /ask |
| `/reports` | GET | Analytics dashboard data |
| `/issues/recent` | GET | Recent issues (last 20) |

**Example Request:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Who contributed the most?"}'
```

**Example Response:**
```json
{
  "answer": "Based on the data, the top contributor is john_doe with 1,247 commits across 156 issues.",
  "sources": [
    {
      "title": "Issue title",
      "contributor": "john_doe",
      "commit_count": 150,
      "created_at": "2025-01-15T10:00:00Z",
      "state": "closed"
    }
  ],
  "num_sources": 10
}
```

## �️ Troubleshooting

### Backend Issues

**Problem:** `ImportError: No module named 'fastapi'`
```bash
# Solution: Activate virtual environment and reinstall
cd backend
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

**Problem:** `google.auth.exceptions.DefaultCredentialsError`
```bash
# Solution: Check service account key path
# Ensure GOOGLE_APPLICATION_CREDENTIALS in .env points to correct JSON file
```

**Problem:** `elasticsearch.exceptions.ConnectionError`
```bash
# Solution: Verify Elasticsearch credentials
# Check YOUR_CLOUD_ID and YOUR_PASSWORD in .env
# Ensure Elasticsearch deployment is running
```

### Frontend Issues

**Problem:** `Failed to fetch` or CORS errors
```bash
# Solution: 
# 1. Ensure backend is running on port 8000
# 2. Check VITE_API_URL in frontend/.env
# 3. Verify CORS is enabled in main.py
```

**Problem:** Charts not displaying data
```bash
# Solution:
# 1. Check browser console for errors
# 2. Verify /reports endpoint returns data
# 3. Ensure BigQuery has data loaded
```

### Data Ingestion Issues

**Problem:** GitHub API rate limit errors
```bash
# Solution:
# 1. Wait a few minutes before retrying
# 2. Ensure GITHUB_TOKEN is set in .env
# 3. Authenticated requests have higher limits (5000/hour)
```

**Problem:** BigQuery permission errors
```bash
# Solution:
# 1. Verify service account has "BigQuery Admin" role
# 2. Check dataset "github_analytics" exists
# 3. Ensure billing is enabled on GCP project
```

---

## 💰 Cost Estimates

### Google Cloud Platform (Monthly)

**Free Tier:**
- BigQuery: First 10 GB storage + 1 TB queries/month FREE
- Vertex AI Embeddings: $0.0001 per 1K characters
- Vertex AI Gemini 2.5 Flash: $0.000125 per 1K characters

**Estimated for Small Project:**
- BigQuery: $0-5
- Vertex AI Embeddings: $1-10
- Vertex AI LLM: $2-15
- **Total GCP:** $5-30/month

### Elasticsearch Cloud
- Free trial: 14 days
- Basic deployment: ~$25/month after trial

**Total Estimated Cost:** $30-55/month

---

## 🚀 Deployment (Production)

### Backend Options

**1. Google Cloud Run (Recommended)**
```bash
cd backend
gcloud run deploy devinsight-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

**2. Google Compute Engine / AWS EC2**

### Frontend Options

**1. Vercel (Recommended)**
```bash
cd frontend
npm run build
vercel --prod
```

**2. Firebase Hosting**
```bash
npm run build
firebase deploy
```

**3. Netlify / GitHub Pages**

---

## 🚧 Future Enhancements

- [ ] Multi-repository support
- [ ] Real-time data sync
- [ ] Advanced filtering and search
- [ ] Export reports to PDF
- [ ] Email alerts for blockers
- [ ] Private repository support
- [ ] Team collaboration features

## 🤝 Contributing

This is a hackathon project! Contributions welcome:

1. Fork the repo
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 👨‍💻 Author

Built in 8 days for Google Cloud Hackathon 2025

## 🙏 Acknowledgments

- **Google Cloud Platform** - Vertex AI, BigQuery
- **Elastic** - Elasticsearch Cloud
- **LangChain** - RAG framework
- **GitHub** - Data source and API
- **FastAPI** - Backend framework
- **React & Vite** - Frontend tools

---

## 📧 Support

For issues and questions:
- 🐛 **Bug Reports:** Open an issue on GitHub
- 💡 **Feature Requests:** Submit via GitHub Issues
- 📖 **Documentation:** See [docs/](./docs/) folder

---

## 📖 Learning Resources

- [LangChain Documentation](https://python.langchain.com/docs/)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Elasticsearch Guide](https://www.elastic.co/guide/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [React Documentation](https://react.dev/)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)

---

## 🔐 Security Notes

**Never commit these files:**
- `.env` files (contain secrets)
- `*.json` (service account keys)
- `venv/` or `node_modules/`

**Add to `.gitignore`:**
```
.env
*.json
venv/
node_modules/
__pycache__/
dist/
build/
```

**Best Practices:**
- Rotate GitHub tokens every 90 days
- Use environment variables for all secrets
- Enable 2FA on all cloud accounts
- Review service account permissions regularly

---

**Built with ❤️ for Google Cloud Hackathon 2025**

**Version:** 1.0.0  
**Last Updated:** October 20, 2025

---


