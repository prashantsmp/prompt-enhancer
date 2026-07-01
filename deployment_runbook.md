# Cloud Run Deployment & Wiring Runbook

This runbook details the `gcloud` commands and provisioning steps required to build, deploy, and wire the **PromptEnhancer** agent and dashboard services to Google Cloud Run.

---

## 🛠️ Step 1: Authentication & Project Setup

1. **Authenticate the deployment**:
   ```bash
   gcloud auth login
   ```

2. **Set your active project**:
   ```bash
   gcloud config set project [PROJECT_ID]
   ```

3. **Enable necessary Google Cloud APIs**:
   ```bash
   gcloud services enable \
     run.googleapis.com \
     pubsub.googleapis.com \
     artifactregistry.googleapis.com \
     aiplatform.googleapis.com
   ```

---

## 📬 Step 2: Provision Pub/Sub Topics

1. **Create the Dead-Letter Queue (DLQ) topic**:
   ```bash
   gcloud pubsub topics create prompt-events-dlq
   ```

2. **Create the main `prompt-events` topic**:
   ```bash
   gcloud pubsub topics create prompt-events
   ```

3. **Create the DLQ subscription**:
   ```bash
   gcloud pubsub subscriptions create prompt-events-dlq-sub \
     --topic=prompt-events-dlq
   ```

4. **Create the main event subscription with the dead-letter policy wired**:
   ```bash
   gcloud pubsub subscriptions create prompt-events-sub \
     --topic=prompt-events \
     --dead-letter-topic=prompt-events-dlq \
     --max-delivery-attempts=5
   ```

---

## 🛡️ Step 3: Identity & IAM Role Binding

1. **Create the Dashboard Service Account**:
   ```bash
   gcloud iam service-accounts create prompt-enhancer-dashboard-sa \
     --display-name="PromptEnhancer Dashboard Service Account"
   ```

2. **Grant the service account permissions to query/resume sessions on Agent Runtime (Vertex AI)**:
   ```bash
   gcloud projects add-iam-policy-binding [PROJECT_ID] \
     --member="serviceAccount:prompt-enhancer-dashboard-sa@[PROJECT_ID].iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

---

## 🚀 Step 4: Build & Deploy to Cloud Run

We deploy both services to Google Cloud Run as Knative services.

### 1. Deploy the Agent Service
Deploy the core ADK agent service:
```bash
gcloud run deploy prompt-enhancer-agent \
  --source=. \
  --region=us-east1 \
  --memory=4Gi \
  --cpu=1 \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=[PROJECT_ID],GOOGLE_CLOUD_LOCATION=global"
```
*Note the generated Service URL (e.g., `https://prompt-enhancer-agent-xxxx-uc.a.run.app`).*

### 2. Deploy the Web Dashboard Service
Deploy the glassmorphic manager dashboard and wire it to the Agent service:
```bash
gcloud run deploy prompt-enhancer-dashboard \
  --source=. \
  --region=us-east1 \
  --port=8080 \
  --service-account="prompt-enhancer-dashboard-sa@[PROJECT_ID].iam.gserviceaccount.com" \
  --allow-unauthenticated \
  --set-env-vars="AGENT_SERVICE_URL=https://prompt-enhancer-agent-xxxx-uc.a.run.app"
```
