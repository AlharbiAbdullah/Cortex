# Cortex Testing Guide

This guide provides test scenarios and sample questions for validating Cortex services through the frontend and API.

---

## Table of Contents

1. [Quick Start Testing](#quick-start-testing)
2. [Document Upload & Smart Routing](#document-upload--smart-routing)
3. [RAG Chat Testing](#rag-chat-testing)
4. [Summarization Service](#summarization-service)
5. [Comparison Service](#comparison-service)
6. [Report Generation](#report-generation)
7. [Data Quality Assessment](#data-quality-assessment)
8. [API Testing with cURL](#api-testing-with-curl)

---

## Quick Start Testing

### Prerequisites

1. Start all services:
   ```bash
   docker compose up -d
   ```

2. Verify services are running:
   ```bash
   curl http://localhost:8000/health
   ```

3. Access the frontend at: http://localhost:3000

---

## Document Upload & Smart Routing

The Smart Router automatically classifies uploaded documents into 100 categories across 9 domains.

### Test Files to Upload

Create or use these sample documents to test classification:

| Document Type | Sample Content | Expected Category |
|---------------|----------------|-------------------|
| **Invoice** | "Invoice #12345, Amount Due: $5,000, Payment Terms: Net 30" | `invoice` |
| **Meeting Minutes** | "Board Meeting Minutes - Q4 Review, Attendees: CEO, CFO, CTO..." | `meeting_minutes` |
| **Technical Spec** | "API Specification v2.0, Endpoints: /users, /orders, Authentication: OAuth2" | `api_documentation` |
| **Resume/CV** | "John Doe, Software Engineer, 5 years experience, Skills: Python, AWS" | `resume_cv` |
| **Security Report** | "Threat Assessment: Critical vulnerabilities found in network infrastructure" | `threat_assessment` |

### Frontend Testing Steps

1. **Drag & Drop Upload**
   - Go to http://localhost:3000
   - Drag a PDF/DOCX file onto the landing page
   - Watch for "Uploaded!" confirmation

2. **Click to Upload**
   - Click "Upload Files" button
   - Select a file (PDF, DOCX, Excel, TXT, Markdown)
   - File is stored in Bronze layer and processed in background

3. **Check Processing Status**
   - API: `GET http://localhost:8000/api/upload/jobs`
   - Verify job status changes from `queued` → `processing` → `completed`

### Expected Routing Results

After upload, documents are:
1. Stored in **Bronze** (raw)
2. Extracted and stored in **Silver** (processed)
3. Indexed in **ChromaDB** for RAG
4. Classified with confidence score

---

## RAG Chat Testing

The chat interface supports RAG (Retrieval Augmented Generation) with different expert personas.

### Persona-Specific Test Questions

#### General Persona
| Question | Expected Behavior |
|----------|-------------------|
| "What documents have been uploaded?" | Lists recent documents from Silver layer |
| "Summarize the main topics in my documents" | Aggregates themes across documents |
| "What is the total amount on all invoices?" | Extracts and sums financial data |

#### Political/Geopolitical Persona
| Question | Expected Behavior |
|----------|-------------------|
| "What are the geopolitical risks mentioned in the reports?" | Focuses on political analysis |
| "Summarize the international relations context" | Emphasizes diplomatic aspects |
| "What regional tensions are discussed?" | Highlights geopolitical insights |

#### Intelligence (Intel) Persona
| Question | Expected Behavior |
|----------|-------------------|
| "What security threats are identified?" | Focuses on threat assessment |
| "List all mentioned vulnerabilities" | Extracts security-relevant information |
| "What are the key intelligence findings?" | Summarizes intel-related content |

#### Analytics Persona
| Question | Expected Behavior |
|----------|-------------------|
| "Create a breakdown of expenses by category" | Generates structured data analysis |
| "What are the KPI trends?" | Focuses on metrics and performance |
| "Compare Q1 vs Q2 performance metrics" | Analytical comparison with data |

#### Media Persona
| Question | Expected Behavior |
|----------|-------------------|
| "What press releases are in the documents?" | Focuses on communications content |
| "Summarize the brand messaging" | Extracts marketing/PR information |
| "What are the key announcements?" | Highlights media-relevant content |

### Chat Testing Steps

1. Navigate to http://localhost:3000/chat
2. Select a **Persona** (General, Political, Intel, Analytics, Media)
3. Select a **Model** (Qwen 2.5, Qwen 3, Gemma 2, Mistral)
4. Type your question and press Enter

### Sample Conversation Flow

```
User: What financial documents have been uploaded?
Assistant: [Lists invoices, budgets, expense reports from Silver layer]

User: What is the total amount across all invoices?
Assistant: [Calculates and returns sum with breakdown]

User: Generate an Excel report of these invoices
Assistant: [Creates Excel file, provides download link]
```

---

## Summarization Service

Generate summaries of documents with key points, entities, and action items.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/summarize` | POST | Summarize raw text |
| `/api/summarize/document` | POST | Summarize a Silver document |
| `/api/summarize/quick` | POST | Quick summary (shorter) |

### Test Scenarios

#### 1. Text Summarization
```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quarterly financial report shows revenue increased by 15% compared to last year. Operating expenses decreased by 8% due to cost optimization initiatives. The company launched three new products in the Asia-Pacific region. Customer satisfaction scores improved to 4.5 out of 5. The board approved a new strategic partnership with TechCorp for AI development. Next quarter focus will be on expanding European operations and hiring 50 new engineers.",
    "include_entities": true,
    "include_actions": true
  }'
```

**Expected Output:**
- Executive summary (2-3 sentences)
- Key points (bullet list)
- Entities (companies, people, locations)
- Action items (tasks to be done)

#### 2. Document Summarization
```bash
curl -X POST http://localhost:8000/api/summarize/document \
  -H "Content-Type: application/json" \
  -d '{
    "silver_key": "documents/2024/01/invoice_12345.json"
  }'
```

### Questions to Ask in Chat

| Question | Tests |
|----------|-------|
| "Summarize the uploaded quarterly report" | Document retrieval + summarization |
| "What are the key action items from the meeting minutes?" | Action item extraction |
| "List the main entities mentioned in the contract" | Entity extraction |
| "Give me a quick summary of the last 3 uploads" | Multi-document summarization |

---

## Comparison Service

Compare two documents for similarities, differences, and semantic alignment.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/compare` | POST | Compare two text strings |
| `/api/compare/documents` | POST | Compare two Silver documents |
| `/api/compare/versions` | POST | Compare document versions |
| `/api/compare/similarity` | POST | Get similarity score only |

### Test Scenarios

#### 1. Text Comparison
```bash
curl -X POST http://localhost:8000/api/compare \
  -H "Content-Type: application/json" \
  -d '{
    "text1": "The project deadline is March 15, 2024. Budget is $50,000. Team size is 5 developers.",
    "text2": "The project deadline is April 1, 2024. Budget is $75,000. Team size is 8 developers.",
    "generate_summary": true
  }'
```

**Expected Output:**
- Similarity score (0.0 - 1.0)
- Diff changes (added, removed, modified)
- Change summary

#### 2. Document Version Comparison
```bash
curl -X POST http://localhost:8000/api/compare/versions \
  -H "Content-Type: application/json" \
  -d '{
    "silver_key": "contracts/nda_v1.json",
    "version_count": 3
  }'
```

### Questions to Ask in Chat

| Question | Tests |
|----------|-------|
| "Compare the two uploaded contracts" | Document comparison |
| "What changed between v1 and v2 of the policy?" | Version comparison |
| "How similar are the two reports?" | Similarity scoring |
| "List the differences between the two proposals" | Diff generation |

---

## Report Generation

Generate formatted reports from templates in HTML, PDF, or DOCX format.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/reports/templates` | GET | List available templates |
| `/api/reports/generate` | POST | Generate a report |
| `/api/reports/download/{filename}` | GET | Download generated report |
| `/api/reports/chart` | POST | Create a chart image |
| `/api/reports/preview` | POST | Preview without saving |

### Available Templates

| Template ID | Description | Required Fields |
|-------------|-------------|-----------------|
| `executive_summary` | Executive summary report | `title`, `summary`, `key_findings`, `recommendations` |
| `data_analysis` | Data analysis with charts | `title`, `analysis_summary`, `data_table`, `insights` |
| `comparison` | Document comparison report | `title`, `document1_name`, `document2_name`, `similarities`, `differences` |

### Test Scenarios

#### 1. Generate Executive Summary
```bash
curl -X POST http://localhost:8000/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "executive_summary",
    "data": {
      "title": "Q4 2024 Performance Review",
      "summary": "Strong quarterly performance with 15% revenue growth.",
      "key_findings": [
        "Revenue exceeded targets by 12%",
        "Customer acquisition cost reduced by 20%",
        "Market share increased to 23%"
      ],
      "recommendations": [
        "Expand into European markets",
        "Increase R&D investment by 10%",
        "Launch customer loyalty program"
      ]
    },
    "output_format": "pdf"
  }'
```

#### 2. Create Chart
```bash
curl -X POST http://localhost:8000/api/reports/chart \
  -H "Content-Type: application/json" \
  -d '{
    "chart_type": "bar",
    "title": "Monthly Revenue",
    "data": {
      "labels": ["Jan", "Feb", "Mar", "Apr"],
      "values": [45000, 52000, 48000, 61000]
    }
  }'
```

### Questions to Ask in Chat

| Question | Tests |
|----------|-------|
| "Generate a summary report of Q4 performance" | Report generation |
| "Create a comparison report of the two contracts" | Template selection + data |
| "What report templates are available?" | Template listing |
| "Generate a PDF report with charts" | Multi-format output |

---

## Data Quality Assessment

Assess data quality with profiling, anomaly detection, and quality scores.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/quality/assess` | POST | Assess uploaded file |
| `/api/quality/assess/gold` | POST | Assess Gold layer document |
| `/api/quality/quick-check` | POST | Quick quality check (JSON data) |
| `/api/quality/quick-check/file` | POST | Quick check on uploaded file |
| `/api/quality/thresholds` | GET | Get quality thresholds |

### Test Scenarios

#### 1. Assess CSV File Quality
```bash
curl -X POST http://localhost:8000/api/quality/assess \
  -F "file=@sample_data.csv" \
  -F "dataset_name=Sales Data Q4"
```

**Sample CSV for Testing:**
```csv
id,name,email,amount,date,status
1,John Doe,john@example.com,1500.00,2024-01-15,completed
2,Jane Smith,,2300.50,2024-01-16,pending
3,Bob Wilson,bob@test.com,-500.00,invalid-date,completed
4,Alice Brown,alice@example.com,1800.00,2024-01-18,
5,John Doe,john@example.com,1500.00,2024-01-15,completed
```

**Expected Quality Issues:**
- Missing values in `email` and `status`
- Negative amount (anomaly)
- Invalid date format
- Duplicate row (id 1 and 5)

#### 2. Quick Check JSON Data
```bash
curl -X POST http://localhost:8000/api/quality/quick-check \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"id": 1, "name": "Product A", "price": 29.99, "stock": 100},
      {"id": 2, "name": null, "price": -5.00, "stock": 50},
      {"id": 3, "name": "Product C", "price": 49.99, "stock": null}
    ]
  }'
```

### Quality Metrics Explained

| Metric | Description | Threshold |
|--------|-------------|-----------|
| **Completeness** | % of non-null values | > 95% good |
| **Uniqueness** | % of unique values (for IDs) | > 99% good |
| **Consistency** | Data format consistency | > 90% good |
| **Validity** | Values within expected range | > 95% good |

### Questions to Ask in Chat

| Question | Tests |
|----------|-------|
| "What is the data quality of the uploaded Excel file?" | Quality assessment |
| "Are there any anomalies in the sales data?" | Anomaly detection |
| "Which columns have the most missing values?" | Column profiling |
| "Is the customer data consistent?" | Consistency checking |

---

## API Testing with cURL

### Complete Test Script

Save as `test_cortex.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

echo "=== Health Check ==="
curl -s "$BASE_URL/health" | jq

echo -e "\n=== Upload Test File ==="
echo "Invoice #12345, Amount: \$5,000, Due: 2024-02-01" > /tmp/test_invoice.txt
curl -s -X POST "$BASE_URL/api/upload" \
  -F "file=@/tmp/test_invoice.txt" | jq

echo -e "\n=== List Jobs ==="
sleep 2
curl -s "$BASE_URL/api/upload/jobs" | jq

echo -e "\n=== Chat Test ==="
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What documents have been uploaded?",
    "use_rag": true,
    "model_name": "qwen2.5:14b",
    "expert": "general",
    "conversation_history": []
  }' | jq

echo -e "\n=== Summarization Test ==="
curl -s -X POST "$BASE_URL/api/summarize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The company reported Q4 revenue of $10M, a 20% increase. New products launched in Europe. Plans to hire 100 engineers next quarter.",
    "include_entities": true,
    "include_actions": true
  }' | jq

echo -e "\n=== Report Templates ==="
curl -s "$BASE_URL/api/reports/templates" | jq

echo -e "\n=== Quality Thresholds ==="
curl -s "$BASE_URL/api/quality/thresholds" | jq

echo -e "\n=== All Tests Complete ==="
```

Run with:
```bash
chmod +x test_cortex.sh
./test_cortex.sh
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Connection refused" | Ensure `docker compose up -d` is running |
| "Job stuck in queued" | Check Ollama is running: `curl http://localhost:11434/api/tags` |
| "No documents found" | Upload a document first before querying |
| "Model not found" | Pull the model: `ollama pull qwen2.5:14b` |

### Checking Logs

```bash
# Backend logs
docker compose logs -f backend

# All service logs
docker compose logs -f

# Specific service
docker compose logs -f minio
```

### Resetting Data

```bash
# Stop and remove volumes
docker compose down -v

# Restart fresh
docker compose up -d
```

---

## Test Data Files

### Sample Invoice (invoice_sample.txt)
```
INVOICE

Invoice Number: INV-2024-001
Date: January 15, 2024
Due Date: February 15, 2024

Bill To:
Acme Corporation
123 Business Street
New York, NY 10001

Items:
1. Consulting Services - 40 hours @ $150/hr = $6,000
2. Software License - Annual subscription = $2,400
3. Training Session - 2 days = $1,600

Subtotal: $10,000
Tax (8%): $800
Total Due: $10,800

Payment Terms: Net 30
```

### Sample Meeting Minutes (meeting_sample.txt)
```
MEETING MINUTES

Board of Directors Meeting
Date: January 20, 2024
Location: Conference Room A

Attendees:
- John Smith (CEO)
- Sarah Johnson (CFO)
- Michael Brown (CTO)
- Lisa Davis (COO)

Agenda:
1. Q4 Financial Review
2. 2024 Strategic Planning
3. New Product Launch

Key Decisions:
- Approved $5M budget for R&D expansion
- Authorized hiring of 25 new engineers
- Set Q1 revenue target at $15M

Action Items:
- Sarah to finalize budget allocation by Feb 1
- Michael to present tech roadmap next meeting
- Lisa to schedule product launch for March 15

Next Meeting: February 15, 2024
```

### Sample Data Quality Test (quality_test.csv)
```csv
customer_id,name,email,order_amount,order_date,status,country
1001,John Doe,john.doe@email.com,150.00,2024-01-15,completed,USA
1002,Jane Smith,jane.smith@email.com,275.50,2024-01-16,completed,UK
1003,Bob Wilson,,89.99,2024-01-17,pending,USA
1004,Alice Brown,alice@email.com,-50.00,2024-01-18,completed,Canada
1005,Charlie Davis,charlie@email.com,320.00,invalid,completed,Germany
1006,,,200.00,2024-01-20,shipped,France
1007,Eva Green,eva@email.com,450.00,2024-01-21,,Spain
1001,John Doe,john.doe@email.com,150.00,2024-01-15,completed,USA
```

This file contains:
- Missing values (rows 3, 6, 7)
- Negative amount (row 4)
- Invalid date (row 5)
- Duplicate row (rows 1 and 8)
