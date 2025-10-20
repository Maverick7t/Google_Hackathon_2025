# DevInsight Setup Guide

## Prerequisites

- **Python 3.9+** installed
- **Node.js 18+** and npm installed
- **Google Cloud Platform** account
- **Git** installed

## Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd googlehackathon
```

## Step 2: GCP Setup

### 2.1 Create GCP Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "devinsight-hackathon")
3. Note your Project ID

### 2.2 Enable APIs

Enable the following APIs:
- BigQuery API
- Vertex AI API
- Cloud Resource Manager API

```bash
gcloud services enable bigquery.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### 2.3 Create Service Account

```bash
gcloud iam service-accounts create devinsight-sa \
    --description="DevInsight service account" \
    --display-name="DevInsight SA"

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:devinsight-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/bigquery.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:devinsight-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Download key
gcloud iam service-accounts keys create service_account.json \
    --iam-account=devinsight-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

Move `service_account.json` to `backend/config/service_account.json`

## Step 3: Elasticsearch Setup

### Option A: Local Elasticsearch (Docker)

```bash
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  elasticsearch:8.11.0
```

### Option B: Elastic Cloud

1. Sign up at [Elastic Cloud](https://cloud.elastic.co/)
2. Create a deployment (free trial available)
3. Copy the Cloud ID and credentials
4. Update `.env` with connection details

## Step 4: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env .env.local
# Edit .env with your credentials
```

Update `backend/.env`:
```env
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./config/service_account.json
ELASTICSEARCH_URL=http://localhost:9200
GITHUB_TOKEN=your-github-token-optional
```

### Initialize BigQuery Tables

```bash
python -m src.bigquery_loader
```

### Initialize Elasticsearch Indices

```bash
python -m src.elasticsearch_indexer
```

## Step 5: Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run on `http://localhost:5173`

## Step 6: Run the Application

### Terminal 1: Backend
```bash
cd backend
python -m src.main
```

Backend API: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```

Frontend UI: `http://localhost:5173`

## Step 7: Test the System

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

### Test 2: Sync GitHub Data
```bash
# In Python
cd backend
python -m src.fivetran_connector
```

### Test 3: Query AI Agent
Open `http://localhost:5173` and ask:
- "What issues are blocking progress?"
- "Show me recent commits"
- "Which PRs need review?"

## Troubleshooting

### Issue: BigQuery permission denied
**Solution**: Ensure service account has `roles/bigquery.admin`

### Issue: Elasticsearch connection failed
**Solution**: Check if Elasticsearch is running:
```bash
curl http://localhost:9200
```

### Issue: Vertex AI quota exceeded
**Solution**: Check your GCP quota limits or use a different region

### Issue: Frontend can't connect to backend
**Solution**: Ensure backend is running on port 8000 and CORS is configured

## Optional: Docker Deployment

```bash
# Build backend
cd backend
docker build -t devinsight-backend .

# Run backend
docker run -p 8000:8000 \
  -e GCP_PROJECT_ID=your-project \
  -v $(pwd)/config:/app/config \
  devinsight-backend
```

## Next Steps

1. Load sample GitHub data
2. Test natural language queries
3. Customize for your specific repositories
4. Deploy to production (Vercel + GCP)

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Vertex AI Docs](https://cloud.google.com/vertex-ai/docs)
- [Elasticsearch Guide](https://www.elastic.co/guide/)
- [React Docs](https://react.dev/)
