"""
Seed Script for Metadata Context Store.

This script initializes the database with predefined category contexts.
Run this once on initial setup or when adding new categories.

Supports 100 categories with NO "general" catch-all.
Documents that don't match any category become "unclassified" for human review.

Usage:
    python -m cortex.scripts.seed_contexts

Or programmatically:
    from cortex.scripts.seed_contexts import seed_predefined_contexts
    seed_predefined_contexts()
"""

from cortex.database.connection import DatabaseService

# ==================== Predefined Contexts (100 Categories) ====================
# Organized by domain - NO "general" catch-all category

PREDEFINED_CONTEXTS = [
    # ==================== BUSINESS & OPERATIONS (15) ====================
    {
        "category": "operations_report",
        "context_text": """Operational reports including daily/weekly/monthly operations summaries,
status updates, operational metrics, business unit performance, and operational KPIs.""",
        "sample_content": """Monthly Operations Report - Q4 2024
Operations Summary:
- Uptime: 99.7%
- Incidents resolved: 45
- SLA compliance: 98.2%
- Staff utilization: 87%
Next month priorities: System upgrade, staff training.""",
    },
    {
        "category": "kpi_dashboard",
        "context_text": """KPI dashboards showing key performance indicators, metrics visualization,
performance scorecards, executive dashboards, and business metrics tracking.""",
        "sample_content": """Executive KPI Dashboard - December 2024
Revenue: $4.5M (↑12% YoY)
Customer Satisfaction: 4.6/5
Employee NPS: 72
On-time Delivery: 94.2%
Cost per Unit: $23.50 (↓8%)""",
    },
    {
        "category": "inventory_management",
        "context_text": """Inventory documents including stock levels, inventory counts, warehouse reports,
material tracking, SKU management, and stock movement records.""",
        "sample_content": """Warehouse Inventory Report
Location: Warehouse A
Total SKUs: 2,450
Low Stock Items: 23 (requires reorder)
Overstock Items: 15
Inventory Value: $1.2M
Last Count Date: Dec 10, 2024""",
    },
    {
        "category": "supply_chain",
        "context_text": """Supply chain documents including logistics, shipping, procurement,
vendor management, distribution, lead times, and supply chain analytics.""",
        "sample_content": """Supply Chain Status Report
Supplier Performance:
- On-time delivery rate: 91%
- Quality acceptance rate: 98.5%
Lead Times:
- Raw materials: 14 days
- Components: 21 days
Shipping costs YTD: $450K""",
    },
    {
        "category": "project_management",
        "context_text": """Project management documents including project plans, timelines, milestones,
resource allocation, Gantt charts, project status, and risk registers.""",
        "sample_content": """Project Status Report - CRM Implementation
Phase: Development (60% complete)
Timeline: On track
Budget: $45K of $80K spent
Milestones:
✓ Requirements gathering
✓ Design approval
○ Development (in progress)
○ Testing
○ Deployment""",
    },
    {
        "category": "meeting_minutes",
        "context_text": """Meeting minutes from board meetings, team meetings, stakeholder meetings,
including attendees, agenda, discussion points, decisions, and action items.""",
        "sample_content": """Board Meeting Minutes - December 5, 2024
Attendees: CEO, CFO, COO, Board Members
Agenda:
1. Q3 Financial Review
2. 2025 Strategic Plan
3. Capital Expenditure Approval
Decisions:
- Approved $2M expansion budget
- Q1 hiring freeze lifted
Action Items:
- CFO to present detailed budget Jan 15""",
    },
    {
        "category": "standard_operating_procedure",
        "context_text": """SOPs and standard operating procedures including work instructions,
operational protocols, step-by-step processes, and compliance procedures.""",
        "sample_content": """SOP-2024-045: Customer Complaint Handling
Purpose: Standardize customer complaint resolution
Scope: All customer-facing departments
Procedure:
1. Log complaint in CRM within 2 hours
2. Assign to appropriate department
3. Initial response within 24 hours
4. Resolution within 5 business days
5. Follow-up satisfaction survey""",
    },
    {
        "category": "compliance_report",
        "context_text": """Compliance reports including regulatory compliance, policy adherence,
audit findings, corrective actions, and compliance certifications.""",
        "sample_content": """Compliance Audit Report - ISO 27001
Audit Date: November 2024
Auditor: External - CompliancePro
Findings:
- 2 Minor non-conformities
- 5 Observations for improvement
Corrective Actions Required: Yes
Certification Status: Maintained""",
    },
    # ==================== FINANCIAL (15) ====================
    {
        "category": "invoice",
        "context_text": """Invoices including billing documents, payment requests, itemized charges,
service invoices, product invoices, and invoice records.""",
        "sample_content": """INVOICE #INV-2024-0892
Date: December 10, 2024
Bill To: ABC Corporation
Items:
- Consulting Services (40 hrs): $8,000
- Travel Expenses: $1,250
Subtotal: $9,250
Tax (8%): $740
Total Due: $9,990
Payment Terms: Net 30""",
    },
    {
        "category": "purchase_order",
        "context_text": """Purchase orders including POs, order requests, requisitions,
buying orders, and procurement documents.""",
        "sample_content": """PURCHASE ORDER #PO-2024-0456
Date: December 8, 2024
Vendor: Industrial Supplies Co.
Ship To: Warehouse B
Items:
- Steel Rods (100 units): $5,000
- Fasteners (500 pcs): $750
- Safety Equipment: $1,200
Total: $6,950
Required Delivery: Dec 20, 2024""",
    },
    {
        "category": "expense_report",
        "context_text": """Expense reports including reimbursement requests, travel expenses,
cost claims, business expenses, and expense documentation.""",
        "sample_content": """Expense Report - John Smith
Period: December 1-15, 2024
Purpose: Client Visit - Chicago
Expenses:
- Airfare: $450
- Hotel (3 nights): $540
- Meals: $180
- Ground Transport: $95
Total: $1,265
Receipts Attached: Yes""",
    },
    {
        "category": "profit_loss",
        "context_text": """P&L statements including profit and loss, income statements,
earnings reports, revenue reports, and financial performance summaries.""",
        "sample_content": """Profit & Loss Statement - Q3 2024
Revenue: $12,500,000
Cost of Goods Sold: $7,500,000
Gross Profit: $5,000,000
Operating Expenses: $3,200,000
Operating Income: $1,800,000
Net Income: $1,350,000
EPS: $2.15""",
    },
    {
        "category": "budget",
        "context_text": """Budgets including financial plans, budget allocations, spending plans,
cost estimates, department budgets, and capital budgets.""",
        "sample_content": """2025 Annual Budget - Marketing Department
Total Budget: $2,400,000
Allocation:
- Digital Marketing: $800,000 (33%)
- Events & Trade Shows: $400,000 (17%)
- Content Creation: $350,000 (15%)
- Advertising: $500,000 (21%)
- Personnel: $350,000 (14%)
Variance from 2024: +8%""",
    },
    {
        "category": "tax_document",
        "context_text": """Tax documents including tax returns, tax filings, tax assessments,
withholding records, tax certificates, and tax compliance documents.""",
        "sample_content": """Tax Filing Summary - FY 2024
Entity: XYZ Corporation
Tax ID: 12-3456789
Filing Type: Corporate Income Tax
Gross Income: $15,000,000
Deductions: $4,500,000
Taxable Income: $10,500,000
Tax Liability: $2,205,000
Filing Status: Submitted""",
    },
    {
        "category": "audit_report",
        "context_text": """Audit reports including financial audits, internal audits, external audits,
audit findings, management letters, and audit recommendations.""",
        "sample_content": """Financial Audit Report - FY 2024
Auditor: Big Four Accounting LLP
Opinion: Unqualified (Clean)
Material Misstatements: None
Key Findings:
- Internal controls adequate
- Revenue recognition compliant
- Inventory valuation accurate
Recommendations: 3 minor improvements""",
    },
    # ==================== LEGAL & REGULATORY (12) ====================
    {
        "category": "legal_contract",
        "context_text": """Legal contracts including binding agreements, service contracts,
partnership agreements, vendor contracts, and commercial agreements.""",
        "sample_content": """SERVICE AGREEMENT
Between: ABC Corp ("Client") and XYZ Services ("Provider")
Effective Date: January 1, 2025
Term: 24 months
Services: IT Infrastructure Management
Monthly Fee: $15,000
SLA: 99.9% uptime guarantee
Termination: 90 days written notice""",
    },
    {
        "category": "nda",
        "context_text": """Non-disclosure agreements including confidentiality agreements,
secrecy contracts, mutual NDAs, and proprietary information protection.""",
        "sample_content": """NON-DISCLOSURE AGREEMENT
Parties: Acme Inc. and Beta Technologies
Purpose: Exploring potential partnership
Confidential Information: Technical specifications, pricing, customer data
Duration: 3 years from disclosure
Permitted Use: Evaluation purposes only
Governing Law: State of Delaware""",
    },
    {
        "category": "privacy_policy",
        "context_text": """Privacy policies including data protection policies, GDPR documents,
privacy notices, cookie policies, and data handling procedures.""",
        "sample_content": """PRIVACY POLICY
Last Updated: December 2024
Data Controller: Our Company Inc.
Data Collected: Name, email, usage data
Purpose: Service delivery, improvements
Retention: 3 years after account closure
Rights: Access, rectification, erasure
Contact: privacy@company.com""",
    },
    {
        "category": "court_document",
        "context_text": """Court documents including legal filings, court orders, judgments,
legal proceedings, motions, and litigation documents.""",
        "sample_content": """CASE NO: 2024-CV-12345
IN THE DISTRICT COURT
Plaintiff: Smith Corporation
Defendant: Jones LLC
Document: Motion for Summary Judgment
Filed: December 10, 2024
Judge: Honorable A. Johnson
Hearing Date: January 15, 2025""",
    },
    # ==================== HUMAN RESOURCES (12) ====================
    {
        "category": "resume_cv",
        "context_text": """Resumes and CVs including job applications, career histories,
professional profiles, qualifications, and candidate documents.""",
        "sample_content": """RESUME
Name: Jane Doe
Position: Senior Software Engineer
Experience: 8 years
Education: MS Computer Science, Stanford
Skills: Python, AWS, Machine Learning
Recent Role: Tech Lead at BigTech Inc.
- Led team of 8 engineers
- Delivered $2M cost savings project""",
    },
    {
        "category": "job_description",
        "context_text": """Job descriptions including role definitions, position requirements,
job postings, responsibilities, and qualifications.""",
        "sample_content": """JOB POSTING
Title: Data Analyst
Department: Business Intelligence
Location: Remote
Experience: 3-5 years
Requirements:
- SQL proficiency
- Python/R experience
- Visualization tools (Tableau, Power BI)
Salary Range: $85,000 - $110,000""",
    },
    {
        "category": "performance_evaluation",
        "context_text": """Performance evaluations including employee reviews, appraisals,
feedback forms, 360 reviews, and performance improvement plans.""",
        "sample_content": """ANNUAL PERFORMANCE REVIEW
Employee: Michael Chen
Period: 2024
Overall Rating: Exceeds Expectations
Goals Achievement: 95%
Key Accomplishments:
- Led successful product launch
- Mentored 3 junior team members
Development Areas: Strategic thinking
Next Year Goals: Team leadership role""",
    },
    {
        "category": "training_material",
        "context_text": """Training materials including learning content, course materials,
skill development, e-learning modules, and certification training.""",
        "sample_content": """TRAINING MODULE: Leadership Fundamentals
Duration: 4 hours
Learning Objectives:
1. Communication skills for leaders
2. Team motivation techniques
3. Conflict resolution
4. Performance management basics
Assessment: Quiz + Case Study
Certificate: Upon 80% completion""",
    },
    {
        "category": "employee_handbook",
        "context_text": """Employee handbooks including company policies, workplace rules,
HR guidelines, code of conduct, and employee benefits guide.""",
        "sample_content": """EMPLOYEE HANDBOOK - 2024 Edition
Chapter 5: Time Off Policies
- Vacation: 15 days/year
- Sick Leave: 10 days/year
- Personal Days: 3 days/year
- Holidays: 11 company holidays
Carryover: Max 5 days vacation
Request Process: Submit via HR portal""",
    },
    # ==================== MARKETING & SALES (12) ====================
    {
        "category": "marketing_campaign",
        "context_text": """Marketing campaigns including campaign plans, promotional strategies,
marketing initiatives, campaign analytics, and marketing ROI reports.""",
        "sample_content": """Campaign Brief: Spring Product Launch
Campaign Name: "New Horizons"
Duration: March 1 - April 30, 2025
Channels: Social, Email, Paid Search
Target Audience: SMB Decision Makers
Budget: $150,000
Goals:
- 5,000 MQLs
- 15% conversion rate
- 300% ROI target""",
    },
    {
        "category": "sales_report",
        "context_text": """Sales reports including sales performance, revenue tracking,
sales metrics, pipeline reports, and territory analysis.""",
        "sample_content": """Monthly Sales Report - November 2024
Total Revenue: $2.8M
New Deals Closed: 45
Average Deal Size: $62,000
Win Rate: 28%
Pipeline Value: $12.5M
Top Performers:
- Region A: $980K (Sarah Johnson)
- Region B: $720K (Mike Williams)""",
    },
    {
        "category": "market_research",
        "context_text": """Market research including market analysis, consumer studies,
market surveys, industry reports, and competitive landscape.""",
        "sample_content": """Market Research Report: Cloud Services 2025
Market Size: $450B (projected)
Growth Rate: 18% CAGR
Key Players: AWS (32%), Azure (22%), GCP (10%)
Trends:
- Multi-cloud adoption increasing
- Edge computing growth
- AI integration expanding
Opportunity: Mid-market segment underserved""",
    },
    {
        "category": "customer_feedback",
        "context_text": """Customer feedback including reviews, surveys, satisfaction scores,
testimonials, NPS data, and customer sentiment analysis.""",
        "sample_content": """Customer Satisfaction Survey Results - Q4 2024
Response Rate: 34%
Overall Satisfaction: 4.4/5
NPS Score: 52
Top Positives:
- Product quality (4.6/5)
- Customer support (4.5/5)
Areas for Improvement:
- Delivery speed (3.8/5)
- Mobile app (3.5/5)""",
    },
    # ==================== TECHNICAL & IT (12) ====================
    {
        "category": "technical_specification",
        "context_text": """Technical specifications including system specs, requirements documents,
design specs, functional specifications, and technical requirements.""",
        "sample_content": """Technical Specification: API Gateway v2.0
Version: 2.0.0
Author: Platform Team
Requirements:
- Handle 10,000 requests/second
- 99.99% availability SLA
- OAuth 2.0 authentication
- Rate limiting per client
- Real-time logging to ELK stack
Compatibility: Kubernetes 1.25+""",
    },
    {
        "category": "api_documentation",
        "context_text": """API documentation including API references, integration guides,
endpoint documentation, SDK guides, and developer documentation.""",
        "sample_content": """API Reference: User Service
Base URL: https://api.example.com/v1
Authentication: Bearer Token

GET /users/{id}
Description: Retrieve user by ID
Response: 200 OK
{
  "id": "uuid",
  "email": "string",
  "created_at": "timestamp"
}""",
    },
    {
        "category": "system_architecture",
        "context_text": """System architecture including architecture diagrams, system designs,
infrastructure plans, microservices design, and data flow diagrams.""",
        "sample_content": """Architecture Overview: E-Commerce Platform
Components:
- Frontend: React SPA (CloudFront CDN)
- API Layer: Node.js (ECS Fargate)
- Database: PostgreSQL (RDS Multi-AZ)
- Cache: Redis Cluster
- Queue: SQS + Lambda
- Search: Elasticsearch
Regions: us-east-1 (primary), eu-west-1 (DR)""",
    },
    {
        "category": "user_manual",
        "context_text": """User manuals including product guides, user documentation,
how-to guides, feature documentation, and end-user guides.""",
        "sample_content": """User Guide: Dashboard Module
Getting Started:
1. Log in to your account
2. Navigate to Dashboard tab
3. Select date range filter

Creating a Custom Dashboard:
1. Click "New Dashboard"
2. Drag widgets from sidebar
3. Configure each widget
4. Click "Save"

Exporting Data:
- CSV, Excel, PDF formats available""",
    },
    {
        "category": "security_policy",
        "context_text": """Security policies including IT security, access controls,
cybersecurity guidelines, data security, and security standards.""",
        "sample_content": """Information Security Policy v3.0
Classification: Internal
Password Requirements:
- Minimum 12 characters
- Complexity: upper, lower, number, symbol
- Rotation: Every 90 days
- No password reuse (last 12)
MFA: Required for all remote access
Data Encryption: AES-256 at rest, TLS 1.3 in transit""",
    },
    # ==================== RESEARCH & ACADEMIC (10) ====================
    {
        "category": "research_paper",
        "context_text": """Research papers including academic research, peer-reviewed studies,
scholarly articles, journal publications, and research findings.""",
        "sample_content": """RESEARCH PAPER
Title: Machine Learning in Healthcare Diagnostics
Authors: Smith, J., Johnson, A., Williams, K.
Institution: MIT
Abstract: This study presents a novel approach to
automated medical image classification using
transformer-based models, achieving 96.2% accuracy...
Keywords: Deep Learning, Medical Imaging, Transformers""",
    },
    {
        "category": "whitepaper",
        "context_text": """Whitepapers including industry papers, thought leadership,
technical whitepapers, solution papers, and position papers.""",
        "sample_content": """WHITEPAPER
Title: The Future of Sustainable Manufacturing
Executive Summary:
This paper explores emerging technologies that enable
manufacturers to reduce carbon footprint by 40% while
maintaining profitability. Key areas include:
- AI-powered energy optimization
- Circular economy practices
- Green supply chain management
Published: December 2024""",
    },
    {
        "category": "case_study",
        "context_text": """Case studies including detailed analyses, real-world examples,
business cases, success stories, and implementation studies.""",
        "sample_content": """CASE STUDY: Digital Transformation at RetailCo
Challenge: Legacy systems causing 3-hour checkout delays
Solution: Cloud-native POS system implementation
Results:
- Checkout time reduced to 30 seconds
- 99.99% system uptime
- $2.5M annual savings
- Customer satisfaction up 35%
Timeline: 8 months""",
    },
    # ==================== COMMUNICATIONS (10) ====================
    {
        "category": "official_letter",
        "context_text": """Official letters including formal correspondence, business letters,
official communications, administrative letters, and formal notices.""",
        "sample_content": """OFFICIAL CORRESPONDENCE
Reference No: ADM/2024/POL/0045
Date: December 10, 2024

From: Department of Administration
To: All Department Heads

Subject: Updated Remote Work Policy

Dear Colleagues,
Please be advised that effective January 1, 2025,
the remote work policy has been updated...

[Official Seal]
Director of Administration""",
    },
    {
        "category": "memo",
        "context_text": """Memos including internal memos, office memoranda,
interoffice communications, policy memos, and administrative notices.""",
        "sample_content": """MEMORANDUM
To: All Staff
From: HR Department
Date: December 12, 2024
Subject: Holiday Schedule 2025

Please note the following office closures:
- January 1: New Year's Day
- January 20: MLK Day
- February 17: Presidents' Day
...
Questions: Contact HR at ext. 5000""",
    },
    {
        "category": "press_release",
        "context_text": """Press releases including media announcements, news releases,
public statements, company announcements, and media communications.""",
        "sample_content": """PRESS RELEASE
FOR IMMEDIATE RELEASE
December 15, 2024

TechCorp Announces $50M Series C Funding

SAN FRANCISCO - TechCorp today announced the close
of a $50 million Series C funding round led by
Venture Capital Partners. The investment will
accelerate product development and global expansion.

Media Contact: press@techcorp.com""",
    },
    # ==================== INTELLIGENCE & SECURITY (12) ====================
    {
        "category": "threat_assessment",
        "context_text": """Threat assessments including risk evaluations, threat analysis,
security threats, vulnerability analysis, and threat intelligence.""",
        "sample_content": """THREAT ASSESSMENT
Classification: Confidential
Date: December 2024
Region: EMEA Operations

Threat Level: ELEVATED
Primary Concerns:
1. Ransomware campaigns targeting sector
2. Social engineering attacks increasing
3. Supply chain compromise risks

Recommended Actions:
- Enhanced monitoring
- Staff awareness training
- Backup verification""",
    },
    {
        "category": "incident_report",
        "context_text": """Incident reports including security incidents, accident reports,
event documentation, breach reports, and incident investigations.""",
        "sample_content": """INCIDENT REPORT
Incident ID: INC-2024-0892
Date: December 10, 2024
Time: 14:32 UTC
Type: Security - Unauthorized Access Attempt

Description: Multiple failed login attempts
detected from external IP range.

Impact: None - Blocked by firewall
Root Cause: Credential stuffing attack
Actions Taken: IP range blocked, passwords reset
Status: Resolved""",
    },
    {
        "category": "intelligence_summary",
        "context_text": """Intelligence summaries including intel briefs, situation summaries,
analysis reports, strategic intelligence, and assessment summaries.""",
        "sample_content": """INTELLIGENCE SUMMARY
Date: December 2024
Subject: Regional Market Intelligence

Key Findings:
1. Competitor X launching product Q1 2025
2. Market consolidation expected
3. Regulatory changes pending

Confidence Level: Medium-High
Sources: OSINT (70%), Industry contacts (30%)
Implications: Review product roadmap priorities""",
    },
    {
        "category": "situation_report",
        "context_text": """Situation reports including SITREP, status reports,
operational updates, field reports, and current situation assessments.""",
        "sample_content": """SITUATION REPORT (SITREP)
DTG: 101400ZDEC24
Location: Operations Center
Period: 24-hour update

Current Status: GREEN
Operations: Normal
Personnel: 95% available
Equipment: 98% operational

Notable Events:
- Scheduled maintenance completed
- New security protocols implemented

Next Report: 111400ZDEC24""",
    },
]


def seed_predefined_contexts() -> tuple[int, int]:
    """
    Seed the database with predefined category contexts.

    Safe to run multiple times - will update existing entries.

    NOTE: This seeds a representative subset of the 100 categories.
    Additional categories will be learned from high-confidence classifications.

    Returns:
        Tuple of (success_count, error_count).
    """
    print("=" * 60)
    print("SEEDING METADATA CONTEXT STORE (100 Categories)")
    print("=" * 60)
    print("NOTE: Seeding representative contexts. Additional categories")
    print("      will be learned from high-confidence classifications.")
    print("=" * 60)

    db_service = DatabaseService()

    success_count = 0
    error_count = 0

    for ctx_data in PREDEFINED_CONTEXTS:
        try:
            context_id = db_service.save_predefined_context(
                category=ctx_data["category"],
                context_text=ctx_data["context_text"],
                sample_content=ctx_data["sample_content"],
            )
            print(f"✓ Saved/Updated: {ctx_data['category'].upper()} (ID: {context_id})")
            success_count += 1
        except Exception as e:
            print(f"✗ Error saving {ctx_data['category']}: {e}")
            error_count += 1

    print("=" * 60)
    print(f"COMPLETE: {success_count} contexts saved, {error_count} errors")
    print("=" * 60)

    # Verify by listing all contexts
    print("\nVerifying saved contexts:")
    all_contexts = db_service.get_all_contexts()
    for ctx in all_contexts:
        print(f"  - {ctx['category']} ({ctx['context_type']}): {ctx['context_text'][:50]}...")

    return success_count, error_count


def clear_learned_contexts() -> None:
    """
    Clear all learned contexts (but keep predefined ones).

    Useful for resetting the learning.
    """
    print("Clearing learned contexts...")
    # This would require adding a delete method to DatabaseService
    # For now, just a placeholder
    print("Note: Implement clear_learned_contexts in DatabaseService if needed")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed metadata context store")
    parser.add_argument(
        "--clear-learned",
        action="store_true",
        help="Clear learned contexts before seeding",
    )
    args = parser.parse_args()

    if args.clear_learned:
        clear_learned_contexts()

    seed_predefined_contexts()
