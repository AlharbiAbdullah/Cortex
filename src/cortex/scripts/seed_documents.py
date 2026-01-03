"""
Seed Script for Sample Documents.

Seeds the database with sample documents for testing Cortex services.
Only runs if no documents exist in ChromaDB (prevents duplicate seeding).

Usage:
    python -m cortex.scripts.seed_documents

Or programmatically:
    from cortex.scripts.seed_documents import seed_sample_documents
    await seed_sample_documents()
"""

import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)


# ==================== Sample Documents ====================
# These match the test files described in TESTING.md

SAMPLE_DOCUMENTS = [
    # Financial Documents
    {
        "filename": "invoice_sample.txt",
        "content": """INVOICE #INV-2024-001
Date: January 15, 2024
Due Date: February 15, 2024

Bill To: Acme Corporation
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
Bank: First National Bank
Account: 1234567890

Thank you for your business!
""",
    },
    {
        "filename": "expense_report_q4.txt",
        "content": """EXPENSE REPORT - Q4 2024
Employee: Sarah Johnson
Department: Sales
Period: October 1 - December 31, 2024

Travel Expenses:
- Client Visit NYC (Oct 15-17): $1,250
  - Flights: $450
  - Hotel (2 nights): $520
  - Meals: $180
  - Ground Transport: $100

- Conference Atlanta (Nov 8-10): $1,890
  - Flights: $380
  - Hotel (3 nights): $780
  - Registration: $500
  - Meals: $230

- Client Meeting Chicago (Dec 5): $650
  - Flights: $320
  - Meals: $130
  - Transportation: $200

Total Travel: $3,790

Office Supplies: $245
Software Subscriptions: $180
Client Entertainment: $420

TOTAL EXPENSES: $4,635
Approved By: Michael Chen (Manager)
""",
    },
    # Meeting Documents
    {
        "filename": "board_meeting_minutes.txt",
        "content": """BOARD MEETING MINUTES
Date: January 20, 2024
Location: Conference Room A
Time: 10:00 AM - 12:30 PM

Attendees:
- John Smith (CEO)
- Sarah Johnson (CFO)
- Michael Brown (CTO)
- Emily Davis (COO)
- Board Members: Robert Wilson, Lisa Chen, David Park

Agenda:
1. Q4 2023 Financial Review
2. 2024 Strategic Plan
3. Technology Roadmap
4. Budget Approval

Key Decisions:
- Approved $5M budget for R&D expansion
- Authorized hiring of 25 new engineers
- Set Q1 revenue target at $15M
- Approved new office lease in Austin

Action Items:
- Sarah to finalize 2024 budget by Feb 1
- Michael to present tech roadmap next meeting
- Emily to complete hiring plan by Jan 31
- John to negotiate vendor contracts

Next Meeting: February 17, 2024 at 10:00 AM

Minutes recorded by: Administrative Assistant
""",
    },
    {
        "filename": "project_status_update.txt",
        "content": """PROJECT STATUS UPDATE
Project: CRM Implementation
Date: January 25, 2024
Project Manager: Alex Thompson

Executive Summary:
The CRM implementation project is currently on track with 65% completion.
Major milestones have been met according to schedule.

Current Phase: Development (Phase 3 of 5)

Completed Milestones:
[x] Requirements Gathering - Dec 1
[x] System Design - Dec 15
[x] Database Setup - Jan 5
[x] Core API Development - Jan 20

In Progress:
[ ] User Interface Development - 60% complete
[ ] Integration with ERP - 40% complete
[ ] Data Migration Scripts - 30% complete

Upcoming Milestones:
- User Acceptance Testing: Feb 15
- Training Sessions: March 1-5
- Go Live: March 15

Budget Status:
- Allocated: $450,000
- Spent to Date: $285,000 (63%)
- Projected Final: $440,000 (2% under budget)

Risks:
1. Data migration complexity - MEDIUM
   Mitigation: Additional QA resources allocated

2. User adoption - LOW
   Mitigation: Training program developed

Team:
- 3 Senior Developers
- 2 Junior Developers
- 1 QA Engineer
- 1 Business Analyst
""",
    },
    # HR Documents
    {
        "filename": "employee_handbook_excerpt.txt",
        "content": """EMPLOYEE HANDBOOK - 2024 EDITION
Chapter 4: Time Off and Leave Policies

4.1 Vacation Leave
Full-time employees accrue vacation based on years of service:
- 0-2 years: 15 days per year
- 3-5 years: 20 days per year
- 6+ years: 25 days per year

Vacation requests must be submitted at least 2 weeks in advance.
Maximum carryover: 5 days to the following year.

4.2 Sick Leave
All employees receive 10 sick days per year.
Sick leave can be used for personal illness or caring for immediate family.
Doctor's note required for absences exceeding 3 consecutive days.

4.3 Personal Days
Employees receive 3 personal days per year.
Personal days do not carry over to the next year.

4.4 Holidays
The company observes 11 paid holidays:
- New Year's Day
- Martin Luther King Jr. Day
- Presidents' Day
- Memorial Day
- Independence Day
- Labor Day
- Thanksgiving Day
- Day after Thanksgiving
- Christmas Eve
- Christmas Day
- New Year's Eve

4.5 Parental Leave
- Maternity Leave: 12 weeks paid
- Paternity Leave: 6 weeks paid
- Adoption Leave: 8 weeks paid

Contact HR at hr@company.com for questions.
""",
    },
    {
        "filename": "performance_review_template.txt",
        "content": """ANNUAL PERFORMANCE REVIEW
Review Period: January 1 - December 31, 2024

Employee Information:
Name: [Employee Name]
Department: Engineering
Position: Senior Software Engineer
Manager: [Manager Name]
Review Date: [Date]

Performance Ratings Scale:
5 - Exceptional
4 - Exceeds Expectations
3 - Meets Expectations
2 - Needs Improvement
1 - Unsatisfactory

Core Competencies Assessment:

1. Technical Skills: [Rating]
   Comments: [Feedback]

2. Communication: [Rating]
   Comments: [Feedback]

3. Teamwork: [Rating]
   Comments: [Feedback]

4. Problem Solving: [Rating]
   Comments: [Feedback]

5. Initiative: [Rating]
   Comments: [Feedback]

Goals Achievement (from previous review):
- Goal 1: [Status]
- Goal 2: [Status]
- Goal 3: [Status]

Strengths:
- [List key strengths]

Areas for Improvement:
- [List development areas]

Goals for Next Review Period:
1. [Goal 1]
2. [Goal 2]
3. [Goal 3]

Overall Rating: [1-5]

Employee Signature: ________________ Date: ________
Manager Signature: _________________ Date: ________
""",
    },
    # Technical Documents
    {
        "filename": "api_documentation.txt",
        "content": """API DOCUMENTATION
Service: User Management API
Version: 2.0.0
Base URL: https://api.company.com/v2

Authentication:
All endpoints require Bearer token authentication.
Header: Authorization: Bearer <token>

Rate Limiting:
- 1000 requests per minute per API key
- Rate limit headers included in response

Endpoints:

1. GET /users
   Description: List all users (paginated)
   Parameters:
   - page (int): Page number (default: 1)
   - limit (int): Items per page (default: 20, max: 100)
   - status (string): Filter by status (active, inactive)
   Response: 200 OK
   {
     "data": [...],
     "pagination": {
       "page": 1,
       "total_pages": 10,
       "total_items": 195
     }
   }

2. GET /users/{id}
   Description: Get user by ID
   Parameters:
   - id (uuid): User ID
   Response: 200 OK
   {
     "id": "uuid",
     "email": "string",
     "name": "string",
     "created_at": "timestamp",
     "status": "active"
   }

3. POST /users
   Description: Create new user
   Body:
   {
     "email": "user@example.com",
     "name": "John Doe",
     "role": "member"
   }
   Response: 201 Created

4. PUT /users/{id}
   Description: Update user
   Body: (partial update supported)
   Response: 200 OK

5. DELETE /users/{id}
   Description: Delete user (soft delete)
   Response: 204 No Content

Error Codes:
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Rate Limited
- 500: Server Error
""",
    },
    {
        "filename": "security_policy.txt",
        "content": """INFORMATION SECURITY POLICY
Document ID: SEC-POL-001
Version: 3.0
Effective Date: January 1, 2024
Classification: Internal Use Only

1. PURPOSE
This policy establishes information security requirements for all employees,
contractors, and third parties who access company systems and data.

2. SCOPE
Applies to all company information assets, systems, and personnel.

3. PASSWORD REQUIREMENTS
- Minimum length: 12 characters
- Must include: uppercase, lowercase, numbers, special characters
- Password rotation: Every 90 days
- No reuse of last 12 passwords
- Account lockout after 5 failed attempts

4. MULTI-FACTOR AUTHENTICATION (MFA)
MFA is required for:
- All remote access
- VPN connections
- Cloud service access
- Administrative accounts

5. DATA CLASSIFICATION
- Public: No restrictions
- Internal: Employee access only
- Confidential: Need-to-know basis
- Restricted: Explicitly authorized only

6. ACCEPTABLE USE
Prohibited activities:
- Unauthorized software installation
- Sharing credentials
- Accessing unauthorized systems
- Storing sensitive data on personal devices

7. INCIDENT REPORTING
All security incidents must be reported within 1 hour to:
- Security Team: security@company.com
- Help Desk: ext. 5000

8. REMOTE WORK
- Use company VPN for all work activities
- Secure home network required
- Lock screens when away from device
- No public WiFi for sensitive work

9. COMPLIANCE
Violations may result in disciplinary action up to termination.

Approved by: Chief Information Security Officer
Last Review: December 15, 2023
Next Review: December 15, 2024
""",
    },
]

# CSV Sample - Sales Data
SALES_DATA_CSV = {
    "filename": "sales_data.csv",
    "content": """customer_id,name,email,order_amount,order_date,status,country
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
""",
}


async def seed_sample_documents() -> tuple[int, int]:
    """
    Seed sample documents into the system.

    Directly uploads documents to Silver layer and ingests into ChromaDB,
    bypassing the full processing pipeline for faster startup.

    Returns:
        Tuple of (success_count, error_count).
    """
    from cortex.services.document_service import get_document_service
    from cortex.services.minio import get_minio_service

    logger.info("=" * 60)
    logger.info("SEEDING SAMPLE DOCUMENTS")
    logger.info("=" * 60)

    minio = get_minio_service()
    doc_service = get_document_service()

    all_documents = SAMPLE_DOCUMENTS + [SALES_DATA_CSV]
    success_count = 0
    error_count = 0

    # Category mapping for sample documents
    category_map = {
        "invoice_sample.txt": "invoice",
        "expense_report_q4.txt": "expense_report",
        "board_meeting_minutes.txt": "meeting_minutes",
        "project_status_update.txt": "project_management",
        "employee_handbook_excerpt.txt": "employee_handbook",
        "performance_review_template.txt": "performance_evaluation",
        "api_documentation.txt": "api_documentation",
        "security_policy.txt": "security_policy",
        "sales_data.csv": "sales_report",
    }

    for doc in all_documents:
        try:
            filename = doc["filename"]
            content = doc["content"]
            document_id = uuid.uuid4().hex
            file_type = filename.split(".")[-1].lower()
            category = category_map.get(filename, "unclassified")

            # Upload directly to Bronze then Silver
            bronze_key = minio.upload_bytes_to_bronze(
                data=content.encode("utf-8"),
                filename=filename,
                document_id=document_id,
            )

            # Copy to Silver with predefined category
            silver_key = minio.copy_to_silver(
                bronze_key=bronze_key,
                document_id=document_id,
                filename=filename,
                file_type=file_type,
                primary_category=category,
                categories=[category],
                confidence=1.0,
                reasoning="Seeded sample document",
                status="seeded",
                feed_the_brain=1,
            )

            # Ingest directly into ChromaDB
            result = await doc_service.ingest_text(
                doc_key=silver_key,
                filename=filename,
                text=content,
                file_type=file_type,
            )

            if result.get("status") == "success":
                logger.info(f"  Seeded: {filename} -> {category}")
                success_count += 1
            else:
                logger.warning(f"  Failed to ingest: {filename}")
                error_count += 1

        except Exception as e:
            logger.error(f"  Error seeding {doc['filename']}: {e}")
            error_count += 1

    logger.info("=" * 60)
    logger.info(f"SEEDING COMPLETE: {success_count} documents, {error_count} errors")
    logger.info("=" * 60)

    return success_count, error_count


def check_documents_exist() -> bool:
    """
    Check if any documents exist in ChromaDB.

    Returns:
        True if documents exist, False otherwise.
    """
    try:
        from cortex.services.document_service import get_document_service

        doc_service = get_document_service()
        documents = doc_service.list_documents()
        return len(documents) > 0
    except Exception as e:
        logger.warning(f"Could not check for existing documents: {e}")
        return False


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Seed sample documents")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force seeding even if documents exist",
    )
    args = parser.parse_args()

    if not args.force and check_documents_exist():
        print("Documents already exist. Use --force to seed anyway.")
    else:
        asyncio.run(seed_sample_documents())
