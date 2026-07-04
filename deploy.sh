#!/bin/bash
# WanderSoul — Google Cloud Run Deployment Script
# Run this once after setting up gcloud CLI
#
# Prerequisites:
#   1. Install gcloud CLI: https://cloud.google.com/sdk/docs/install
#   2. Run: gcloud auth login
#   3. Run: gcloud projects create wandersoul-app --name="WanderSoul" (or use existing project)
#   4. Set your project: gcloud config set project wandersoul-app
#   5. Fill in your API keys below or pass as env vars

# ── Config ────────────────────────────────────────────────────────
PROJECT_ID="wandersoul-app"          # Your GCP project ID
SERVICE_NAME="wandersoul"
REGION="us-central1"                 # Free tier region
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# ── Enable required GCP APIs ──────────────────────────────────────
echo "Enabling GCP APIs..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com --project=$PROJECT_ID

# ── Build and push Docker image via Cloud Build (free) ───────────
echo "Building and pushing image..."
gcloud builds submit --tag $IMAGE --project=$PROJECT_ID

# ── Deploy to Cloud Run ───────────────────────────────────────────
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2 \
  --set-env-vars "GROQ_API_KEY=$GROQ_API_KEY,TAVILY_API_KEY=$TAVILY_API_KEY,LLM_MODEL=llama-3.3-70b-versatile,LLM_TEMPERATURE=0.7,LLM_TIMEOUT_SECONDS=15" \
  --project=$PROJECT_ID

echo ""
echo "✅ Deployment complete!"
echo "Your app URL:"
gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID --format="value(status.url)"
