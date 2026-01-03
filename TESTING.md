# Cortex Testing Guide

This guide provides test scenarios and sample questions for validating Cortex AI services using the auto-seeded sample data.

---

## Table of Contents

1. [Quick Start Testing](#quick-start-testing)
2. [Seeded Sample Data](#seeded-sample-data)
3. [Chat Service](#chat-service)
4. [Conversational Analytics](#conversational-analytics)
5. [Summarize Service](#summarize-service)
6. [Data Quality Service](#data-quality-service)
7. [Extract Service](#extract-service)
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

3. Access the frontend:
   - Landing Page: http://localhost:3000
   - AI Platform: http://localhost:3000/ai
   - BI Platform: http://localhost:3000/bi

### Auto-Seeding

On first startup, the system automatically seeds:
- **43 predefined contexts** for document classification
- **9 sample documents** across various categories

No manual setup required - just run `docker compose up -d` and start testing!

---

## Seeded Sample Data

The following documents are automatically seeded on first startup:

### Financial Documents

**invoice_sample.txt** (Category: `invoice`)
- Invoice #INV-2024-001 to Acme Corporation
- Date: January 15, 2024 | Due: February 15, 2024
- Items: Consulting ($6,000), Software License ($2,400), Training ($1,600)
- Total: $10,800 (including 8% tax)

**expense_report_q4.txt** (Category: `expense_report`)
- Employee: Sarah Johnson, Department: Sales
- Q4 2024 expenses totaling $4,635
- Travel: NYC ($1,250), Atlanta Conference ($1,890), Chicago ($650)
- Other: Office Supplies ($245), Software ($180), Entertainment ($420)

### Meeting & Project Documents

**board_meeting_minutes.txt** (Category: `meeting_minutes`)
- Date: January 20, 2024
- Attendees: John Smith (CEO), Sarah Johnson (CFO), Michael Brown (CTO), Emily Davis (COO)
- Key Decisions: $5M R&D budget, 25 new engineers, Q1 target $15M, Austin office lease
- Action Items: Budget by Feb 1 (Sarah), Tech roadmap (Michael), Hiring plan (Emily)

**project_status_update.txt** (Category: `project_management`)
- Project: CRM Implementation (65% complete)
- Budget: $450,000 allocated, $285,000 spent (63%)
- Milestones: Requirements, Design, Database, API complete
- Upcoming: UAT (Feb 15), Training (Mar 1-5), Go Live (Mar 15)

### HR Documents

**employee_handbook_excerpt.txt** (Category: `employee_handbook`)
- Vacation: 15-25 days based on tenure
- Sick Leave: 10 days/year
- Personal Days: 3 days/year
- 11 paid holidays
- Parental Leave: 6-12 weeks

**performance_review_template.txt** (Category: `performance_evaluation`)
- Rating scale 1-5
- Core competencies: Technical, Communication, Teamwork, Problem Solving, Initiative
- Goal tracking structure

### Technical Documents

**api_documentation.txt** (Category: `api_documentation`)
- Service: User Management API v2.0.0
- Base URL: https://api.company.com/v2
- Endpoints: GET/POST/PUT/DELETE /users
- Rate Limit: 1000 requests/minute
- Authentication: Bearer token

**security_policy.txt** (Category: `security_policy`)
- Document ID: SEC-POL-001, Version 3.0
- Password: 12+ chars, 90-day rotation, MFA required
- Data Classification: Public, Internal, Confidential, Restricted
- Incident reporting: 1 hour to security@company.com

### Sales Data

**sales_data.csv** (Category: `sales_report`)
```csv
customer_id,name,email,order_amount,order_date,status,country
1001,John Doe,john@email.com,150.00,2024-01-15,completed,USA
1002,Jane Smith,jane@email.com,275.50,2024-01-16,completed,UK
1003,Bob Wilson,,89.99,2024-01-17,pending,USA
1004,Alice Brown,alice@email.com,-50.00,2024-01-18,completed,Canada
1005,Charlie Davis,charlie@email.com,320.00,invalid,completed,Germany
1006,,,200.00,2024-01-20,shipped,France
1007,Eva Green,eva@email.com,450.00,2024-01-21,,Spain
1008,John Doe,john@email.com,150.00,2024-01-15,completed,USA
1009,Frank Miller,frank@email.com,175.25,2024-01-22,completed,Italy
1010,Grace Lee,grace@email.com,520.00,2024-01-23,pending,Japan
1011,Henry Wang,henry@email.com,89.00,2024-01-24,completed,China
1012,Iris Martinez,iris@email.com,340.75,2024-01-25,shipped,Mexico
```

**Data Quality Issues (intentional for testing):**
- Missing email: rows 3, 6
- Missing name: row 6
- Negative amount: row 4 (-$50.00)
- Invalid date: row 5 ("invalid")
- Missing status: row 7
- Duplicate record: rows 1 and 8 (John Doe)

---

## Chat Service

**URL:** http://localhost:3000/ai/chat

### Test Questions - Invoice & Financial

| Question | Expected Response Contains |
|----------|---------------------------|
| "What is the total on invoice INV-2024-001?" | $10,800 |
| "Who is the invoice billed to?" | Acme Corporation |
| "What are the line items on the invoice?" | Consulting, Software License, Training |
| "What are the payment terms?" | Net 30 |
| "How much was spent on consulting?" | $6,000 (40 hours @ $150/hr) |

### Test Questions - Expense Report

| Question | Expected Response Contains |
|----------|---------------------------|
| "What were Sarah Johnson's Q4 expenses?" | $4,635 total |
| "How much was spent on the Atlanta conference?" | $1,890 |
| "What travel expenses were incurred?" | NYC, Atlanta, Chicago trips |
| "Who approved the expense report?" | Michael Chen (Manager) |

### Test Questions - Meeting Minutes

| Question | Expected Response Contains |
|----------|---------------------------|
| "Who attended the board meeting?" | John Smith, Sarah Johnson, Michael Brown, Emily Davis |
| "What budget was approved for R&D?" | $5M |
| "How many engineers will be hired?" | 25 |
| "What is the Q1 revenue target?" | $15M |
| "What are Sarah's action items?" | Finalize budget by Feb 1 |
| "When is the next board meeting?" | February 17, 2024 |

### Test Questions - Project Status

| Question | Expected Response Contains |
|----------|---------------------------|
| "What is the CRM project status?" | 65% complete, on track |
| "What is the project budget?" | $450,000 allocated, $285,000 spent |
| "When is the CRM go-live date?" | March 15 |
| "What milestones are completed?" | Requirements, Design, Database, API |
| "What are the project risks?" | Data migration (MEDIUM), User adoption (LOW) |

### Test Questions - HR Policies

| Question | Expected Response Contains |
|----------|---------------------------|
| "How many vacation days do new employees get?" | 15 days (0-2 years) |
| "What is the parental leave policy?" | Maternity 12 weeks, Paternity 6 weeks |
| "How many sick days per year?" | 10 days |
| "What holidays does the company observe?" | 11 paid holidays |

### Test Questions - Security Policy

| Question | Expected Response Contains |
|----------|---------------------------|
| "What are the password requirements?" | 12+ characters, 90-day rotation |
| "Is MFA required?" | Yes, for remote access, VPN, cloud |
| "How quickly must security incidents be reported?" | Within 1 hour |
| "What are the data classification levels?" | Public, Internal, Confidential, Restricted |

### Test Questions - API Documentation

| Question | Expected Response Contains |
|----------|---------------------------|
| "What is the API rate limit?" | 1000 requests per minute |
| "What authentication does the API use?" | Bearer token |
| "What endpoints are available?" | GET/POST/PUT/DELETE /users |
| "What HTTP status codes are returned?" | 400, 401, 403, 404, 429, 500 |

---

## Conversational Analytics

**URL:** http://localhost:3000/ai/analytics

### Chart & Visualization Requests

| Request | Expected Behavior |
|---------|-------------------|
| "Create a bar chart of sales by country" | Chart with USA, UK, Canada, Germany, France, Spain, Italy, Japan, China, Mexico |
| "Show pie chart of order status" | completed, pending, shipped segments |
| "Graph order amounts over time" | Time series from Jan 15-25, 2024 |

### Analytics Queries

| Question | Expected Response |
|----------|-------------------|
| "What are the top 3 countries by order volume?" | USA (3), then others with 1 each |
| "What is the total revenue?" | ~$2,710.49 (excluding negative) |
| "What is the average order amount?" | ~$226 |
| "How many orders are pending?" | 2 (rows 3 and 10) |
| "How many orders are completed?" | 7 |
| "Which customer has the highest order?" | Grace Lee - $520.00 |

### Data Analysis

| Question | Expected Response |
|----------|-------------------|
| "Show me orders from USA" | 3 orders totaling $389.99 |
| "What orders are over $300?" | Charlie Davis ($320), Eva Green ($450), Grace Lee ($520), Iris Martinez ($340.75) |
| "List customers with pending orders" | Bob Wilson, Grace Lee |

---

## Summarize Service

**URL:** http://localhost:3000/ai/summarize

### Document Summaries

| Request | Key Points Expected |
|---------|---------------------|
| "Summarize the invoice" | Acme Corp, $10,800, consulting/software/training |
| "Summarize the board meeting" | $5M R&D, 25 engineers, $15M Q1 target, Austin office |
| "Summarize the expense report" | Sarah Johnson, Q4, $4,635 total, travel expenses |
| "Summarize the CRM project" | 65% complete, $450K budget, March 15 go-live |
| "Summarize the security policy" | Password rules, MFA, data classification, incident reporting |

### Cross-Document Summaries

| Request | Expected Behavior |
|---------|-------------------|
| "Summarize all financial documents" | Invoice ($10,800), Expense report ($4,635), Budget decisions ($5M R&D) |
| "What decisions were made?" | R&D expansion, hiring, revenue targets, office lease |
| "List all action items" | Budget (Sarah), Tech roadmap (Michael), Hiring plan (Emily) |
| "Summarize HR policies" | Vacation, sick leave, holidays, parental leave |

### Quick Summaries

| Request | Expected Behavior |
|---------|-------------------|
| "TL;DR of the board meeting" | Brief 2-3 sentence summary |
| "Key takeaways from project status" | Status, timeline, budget, risks |
| "Executive summary of Q4 expenses" | Total, major categories, approval |

---

## Data Quality Service

**URL:** http://localhost:3000/ai/quality

### Quality Assessment

| Question | Expected Response |
|----------|-------------------|
| "Check quality of the sales data" | Missing values, invalid data, duplicates detected |
| "What percentage of records are complete?" | ~58% (7 of 12 fully complete) |
| "Are there any data quality issues?" | Yes - nulls, negative amounts, invalid dates, duplicates |

### Missing Value Detection

| Question | Expected Response |
|----------|-------------------|
| "How many missing emails?" | 2 (rows 3 and 6) |
| "Which records have missing names?" | Row 6 |
| "Find records with missing status" | Row 7 (Eva Green) |
| "List all incomplete records" | Rows 3, 4, 5, 6, 7 |

### Invalid Data Detection

| Question | Expected Response |
|----------|-------------------|
| "Are there any negative amounts?" | Yes - row 4: -$50.00 |
| "Find invalid dates" | Row 5: "invalid" instead of date |
| "Detect outliers in order amounts" | -$50.00 (negative outlier) |

### Duplicate Detection

| Question | Expected Response |
|----------|-------------------|
| "Are there duplicate records?" | Yes - rows 1 and 8 (John Doe, same order) |
| "Find duplicate customers" | John Doe appears twice with identical data |

### Quality Metrics

| Question | Expected Response |
|----------|-------------------|
| "What is the completeness score?" | ~83% field completeness |
| "Data validity score?" | ~92% (2 invalid values out of ~84 fields) |
| "Overall data quality score?" | Combined assessment |

---

## Extract Service

**URL:** http://localhost:3000/ai/extract

### Format Conversion

| Request | Expected Output |
|---------|-----------------|
| "Give me sales data as JSON" | JSON array of customer orders |
| "Export orders as CSV" | CSV formatted data |
| "Convert invoice to JSON" | Structured invoice data |

### Specific Extractions

| Request | Expected Output |
|---------|-----------------|
| "Extract all customer emails" | List of 10 emails (excluding nulls) |
| "Get invoice line items" | Consulting, Software License, Training with amounts |
| "Extract attendees from meeting" | John Smith, Sarah Johnson, Michael Brown, Emily Davis |
| "Pull action items from meeting" | 3 items with owners and deadlines |

### Filtered Extractions

| Request | Expected Output |
|---------|-----------------|
| "Extract completed orders only" | 7 orders with status=completed |
| "Get orders from USA" | 3 orders |
| "Extract orders over $200" | 6 orders |

### Entity Extraction

| Request | Expected Output |
|---------|-----------------|
| "Extract all dates from documents" | Invoice dates, meeting dates, deadlines |
| "Pull all monetary amounts" | $10,800, $6,000, $2,400, etc. |
| "Extract all person names" | John Smith, Sarah Johnson, Michael Brown, etc. |
| "Get all company names" | Acme Corporation, First National Bank |

---

## API Testing with cURL

### Health Check
```bash
curl http://localhost:8000/health
```

### List Seeded Documents
```bash
curl http://localhost:8000/api/documents
```

### Chat Query
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the total on the invoice?",
    "use_rag": true,
    "model_name": "qwen2.5:14b",
    "expert": "general",
    "conversation_history": []
  }'
```

### Test Specific Questions
```bash
# Invoice query
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Who is the invoice billed to?", "use_rag": true, "model_name": "qwen2.5:14b", "expert": "general", "conversation_history": []}'

# Meeting query
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What decisions were made at the board meeting?", "use_rag": true, "model_name": "qwen2.5:14b", "expert": "general", "conversation_history": []}'

# Security policy query
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the password requirements?", "use_rag": true, "model_name": "qwen2.5:14b", "expert": "general", "conversation_history": []}'
```

### Complete Test Script

Save as `test_cortex.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"

echo "=== Health Check ==="
curl -s "$BASE_URL/health" | jq

echo -e "\n=== List Documents ==="
curl -s "$BASE_URL/api/documents" | jq '.documents | length' | xargs echo "Documents seeded:"

echo -e "\n=== Test Invoice Query ==="
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the total on invoice INV-2024-001?",
    "use_rag": true,
    "model_name": "qwen2.5:14b",
    "expert": "general",
    "conversation_history": []
  }' | jq '.response'

echo -e "\n=== Test Meeting Query ==="
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Who attended the board meeting?",
    "use_rag": true,
    "model_name": "qwen2.5:14b",
    "expert": "general",
    "conversation_history": []
  }' | jq '.response'

echo -e "\n=== Test Security Query ==="
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the password requirements in the security policy?",
    "use_rag": true,
    "model_name": "qwen2.5:14b",
    "expert": "general",
    "conversation_history": []
  }' | jq '.response'

echo -e "\n=== All Tests Complete ==="
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" | Run `docker compose up -d` |
| "No documents found" | Wait for seeding to complete (~30 seconds) |
| "Model not found" | Run `ollama pull qwen2.5:14b` |
| Chat not responding | Check backend logs: `docker compose logs -f backend` |
| Seeding failed | Check logs: `docker compose logs backend \| grep -i seed` |

### Verify Seeding
```bash
# Check document count
curl -s http://localhost:8000/api/documents | jq '.documents | length'
# Expected: 9

# Check specific categories
curl -s http://localhost:8000/api/documents | jq '.documents[].primary_category'
```

### Checking Logs
```bash
# All logs
docker compose logs -f

# Backend only
docker compose logs -f backend

# Seeding logs
docker compose logs backend | grep -E "(SEEDING|Seeded|contexts saved)"
```

### Reset Data
```bash
# Full reset (removes all data, triggers re-seeding)
docker compose down -v
docker compose up -d
```
