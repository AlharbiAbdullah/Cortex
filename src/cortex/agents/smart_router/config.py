"""
Smart Router Configuration - Constants and Category Definitions.

This module contains all configuration constants, pipeline categories,
and category aliases used by the Smart Router Agent.
"""

# =============================================================================
# Confidence Thresholds
# =============================================================================

HIGH_CONFIDENCE_THRESHOLD = 0.85  # Auto-learn from these
LOW_CONFIDENCE_THRESHOLD = 0.70  # Below 70% = unclassified, requires human review

# =============================================================================
# Ensemble Classification Configuration
# =============================================================================

# Full ensemble: ["qwen2.5:14b", "qwen3:8b", "mistral:7b", "gemma2:9b"]
ENSEMBLE_MODELS = ["qwen3:8b", "gemma2:9b"]  # 2 LLMs for faster routing
ENSEMBLE_TOP_CANDIDATES = 10  # Use embeddings to pre-filter to top N categories
ENSEMBLE_ADDITIONAL_THRESHOLD = 0.70  # Categories with avg confidence > 70%

# =============================================================================
# Pipeline Categories (100 Total)
# =============================================================================

PIPELINE_CATEGORIES: dict[str, str] = {
    # ==================== BUSINESS & OPERATIONS (15) ====================
    "operations_report": (
        "Operational reports: daily/weekly/monthly operations summaries, "
        "status updates, operational metrics"
    ),
    "kpi_dashboard": (
        "KPI dashboards: key performance indicators, metrics visualization, "
        "performance scorecards"
    ),
    "performance_review": (
        "Performance reviews: business unit performance, department evaluations, "
        "quarterly reviews"
    ),
    "inventory_management": (
        "Inventory documents: stock levels, inventory counts, warehouse reports, "
        "material tracking"
    ),
    "supply_chain": (
        "Supply chain documents: logistics, shipping, procurement, vendor management, "
        "distribution"
    ),
    "production_schedule": (
        "Production schedules: manufacturing timelines, production plans, "
        "capacity planning"
    ),
    "quality_control": (
        "Quality control: QA reports, inspection records, defect tracking, "
        "quality metrics"
    ),
    "project_management": (
        "Project management: project plans, timelines, milestones, resource allocation, "
        "Gantt charts"
    ),
    "business_strategy": (
        "Business strategy: strategic plans, vision documents, competitive positioning, "
        "growth plans"
    ),
    "meeting_minutes": (
        "Meeting minutes: board meetings, team meetings, stakeholder meetings, "
        "action items"
    ),
    "organizational_chart": (
        "Organizational charts: org structures, hierarchy diagrams, reporting lines, "
        "team structures"
    ),
    "process_documentation": (
        "Process documentation: workflows, procedures, process maps, operational guides"
    ),
    "standard_operating_procedure": (
        "SOPs: standard operating procedures, work instructions, operational protocols"
    ),
    "compliance_report": (
        "Compliance reports: regulatory compliance, policy adherence, audit findings, "
        "corrective actions"
    ),
    "vendor_management": (
        "Vendor management: supplier contracts, vendor evaluations, procurement documents"
    ),
    # ==================== FINANCIAL (15) ====================
    "invoice": "Invoices: billing documents, payment requests, itemized charges, service invoices",
    "receipt": "Receipts: payment confirmations, transaction receipts, proof of purchase",
    "purchase_order": "Purchase orders: POs, order requests, requisitions, buying orders",
    "budget": "Budgets: financial plans, budget allocations, spending plans, cost estimates",
    "expense_report": "Expense reports: reimbursement requests, travel expenses, cost claims",
    "profit_loss": "P&L statements: profit and loss, income statements, earnings reports",
    "balance_sheet": (
        "Balance sheets: assets and liabilities, financial position, equity statements"
    ),
    "cash_flow": "Cash flow: cash flow statements, liquidity reports, fund movements",
    "tax_document": (
        "Tax documents: tax returns, tax filings, tax assessments, withholding records"
    ),
    "audit_report": (
        "Audit reports: financial audits, internal audits, external audits, audit findings"
    ),
    "financial_forecast": (
        "Financial forecasts: projections, financial models, revenue predictions"
    ),
    "investment_report": (
        "Investment reports: portfolio analysis, investment performance, asset allocation"
    ),
    "bank_statement": (
        "Bank statements: account statements, transaction history, bank records"
    ),
    "payroll": (
        "Payroll: salary records, wage statements, compensation documents, pay stubs"
    ),
    "financial_contract": (
        "Financial contracts: loan agreements, credit terms, financing documents"
    ),
    # ==================== LEGAL & REGULATORY (12) ====================
    "legal_contract": (
        "Legal contracts: binding agreements, service contracts, partnership agreements"
    ),
    "nda": "NDAs: non-disclosure agreements, confidentiality agreements, secrecy contracts",
    "terms_conditions": "Terms & conditions: T&C documents, user agreements, service terms",
    "privacy_policy": (
        "Privacy policies: data protection policies, GDPR documents, privacy notices"
    ),
    "regulatory_filing": (
        "Regulatory filings: government submissions, regulatory reports, compliance filings"
    ),
    "court_document": (
        "Court documents: legal filings, court orders, judgments, legal proceedings"
    ),
    "patent": "Patents: patent applications, patent grants, intellectual property filings",
    "trademark": "Trademarks: trademark registrations, brand protection, IP documentation",
    "license_agreement": (
        "License agreements: software licenses, usage rights, licensing terms"
    ),
    "legal_brief": "Legal briefs: legal arguments, case summaries, legal memoranda",
    "power_of_attorney": (
        "Power of attorney: authorization documents, legal representation, proxy documents"
    ),
    "corporate_governance": (
        "Corporate governance: bylaws, board resolutions, shareholder documents"
    ),
    # ==================== HUMAN RESOURCES (12) ====================
    "employee_record": "Employee records: personnel files, employee data, HR records",
    "resume_cv": "Resumes/CVs: job applications, career histories, professional profiles",
    "job_description": "Job descriptions: role definitions, position requirements, job postings",
    "performance_evaluation": (
        "Performance evaluations: employee reviews, appraisals, feedback forms"
    ),
    "training_material": (
        "Training materials: learning content, course materials, skill development"
    ),
    "onboarding_document": (
        "Onboarding documents: new hire paperwork, orientation materials, welcome packets"
    ),
    "benefits_summary": (
        "Benefits summaries: insurance plans, retirement plans, employee benefits"
    ),
    "disciplinary_record": (
        "Disciplinary records: warnings, corrective actions, HR incidents"
    ),
    "termination_letter": (
        "Termination letters: dismissal notices, resignation acceptance, exit documents"
    ),
    "salary_structure": "Salary structures: compensation plans, pay grades, salary bands",
    "leave_request": "Leave requests: vacation requests, time-off applications, absence records",
    "employee_handbook": (
        "Employee handbooks: company policies, workplace rules, HR guidelines"
    ),
    # ==================== MARKETING & SALES (12) ====================
    "marketing_campaign": (
        "Marketing campaigns: campaign plans, promotional strategies, marketing initiatives"
    ),
    "brand_guidelines": "Brand guidelines: brand standards, visual identity, brand books",
    "market_research": "Market research: market analysis, consumer studies, market surveys",
    "competitive_analysis": (
        "Competitive analysis: competitor reports, market positioning, benchmarking"
    ),
    "sales_report": "Sales reports: sales performance, revenue tracking, sales metrics",
    "customer_feedback": (
        "Customer feedback: reviews, surveys, satisfaction scores, testimonials"
    ),
    "lead_generation": "Lead generation: prospect lists, lead tracking, sales pipeline",
    "advertising_content": "Advertising content: ads, promotional materials, creative briefs",
    "social_media_analytics": (
        "Social media analytics: engagement metrics, social performance, platform stats"
    ),
    "product_catalog": "Product catalogs: product listings, specifications, pricing sheets",
    "customer_segmentation": (
        "Customer segmentation: audience analysis, demographic data, customer profiles"
    ),
    "crm_data": "CRM data: customer relationship data, contact records, interaction history",
    # ==================== TECHNICAL & IT (12) ====================
    "technical_specification": (
        "Technical specifications: system specs, requirements documents, design specs"
    ),
    "api_documentation": (
        "API documentation: API references, integration guides, endpoint documentation"
    ),
    "system_architecture": (
        "System architecture: architecture diagrams, system designs, infrastructure plans"
    ),
    "user_manual": "User manuals: product guides, user documentation, how-to guides",
    "installation_guide": (
        "Installation guides: setup instructions, deployment guides, configuration docs"
    ),
    "troubleshooting_guide": (
        "Troubleshooting guides: problem resolution, FAQ, support documentation"
    ),
    "software_requirements": (
        "Software requirements: SRS documents, functional specifications, feature lists"
    ),
    "network_diagram": (
        "Network diagrams: topology maps, network architecture, infrastructure diagrams"
    ),
    "security_policy": (
        "Security policies: IT security, access controls, cybersecurity guidelines"
    ),
    "data_dictionary": (
        "Data dictionaries: database schemas, data definitions, field descriptions"
    ),
    "release_notes": "Release notes: version updates, changelog, software releases",
    "technical_report": (
        "Technical reports: engineering reports, technical analysis, feasibility studies"
    ),
    # ==================== RESEARCH & ACADEMIC (10) ====================
    "research_paper": (
        "Research papers: academic research, peer-reviewed studies, scholarly articles"
    ),
    "thesis": "Theses: dissertations, academic theses, graduate research",
    "literature_review": (
        "Literature reviews: academic reviews, research summaries, state-of-the-art"
    ),
    "case_study": "Case studies: detailed analyses, real-world examples, business cases",
    "scientific_report": (
        "Scientific reports: lab reports, experimental findings, scientific documentation"
    ),
    "experimental_data": (
        "Experimental data: raw research data, test results, measurement records"
    ),
    "survey_results": (
        "Survey results: questionnaire responses, polling data, research surveys"
    ),
    "statistical_analysis": (
        "Statistical analysis: data analysis, quantitative studies, statistical reports"
    ),
    "whitepaper": "Whitepapers: industry papers, thought leadership, technical whitepapers",
    "conference_proceedings": (
        "Conference proceedings: academic conferences, symposium papers, presentations"
    ),
    # ==================== COMMUNICATIONS & CORRESPONDENCE (10) ====================
    "official_letter": (
        "Official letters: formal correspondence, business letters, official communications"
    ),
    "memo": "Memos: internal memos, office memoranda, interoffice communications",
    "email_correspondence": (
        "Email correspondence: business emails, email threads, electronic communications"
    ),
    "press_release": "Press releases: media announcements, news releases, public statements",
    "newsletter": (
        "Newsletters: company newsletters, internal communications, periodic updates"
    ),
    "announcement": "Announcements: company announcements, notices, organizational updates",
    "circular": "Circulars: administrative circulars, policy circulars, information bulletins",
    "notification": "Notifications: official notices, alerts, formal notifications",
    "invitation": "Invitations: event invitations, meeting invitations, formal invites",
    "thank_you_letter": (
        "Thank you letters: appreciation letters, acknowledgment letters, gratitude notes"
    ),
    # ==================== INTELLIGENCE & SECURITY (12) ====================
    "threat_assessment": (
        "Threat assessments: risk evaluations, threat analysis, security threats"
    ),
    "security_report": (
        "Security reports: security incidents, breach reports, security audits"
    ),
    "surveillance_report": (
        "Surveillance reports: monitoring reports, observation records, watch lists"
    ),
    "risk_analysis": "Risk analysis: risk assessments, vulnerability analysis, risk matrices",
    "geopolitical_brief": (
        "Geopolitical briefs: political analysis, regional assessments, international relations"
    ),
    "incident_report": (
        "Incident reports: security incidents, accident reports, event documentation"
    ),
    "background_check": (
        "Background checks: due diligence, personnel verification, screening reports"
    ),
    "intelligence_summary": (
        "Intelligence summaries: intel briefs, situation summaries, analysis reports"
    ),
    "situation_report": "Situation reports: SITREP, status reports, operational updates",
    "vulnerability_assessment": (
        "Vulnerability assessments: security vulnerabilities, penetration test reports"
    ),
    "osint_report": (
        "OSINT reports: open source intelligence, publicly available information analysis"
    ),
    "classified_document": (
        "Classified documents: sensitive information, restricted access materials"
    ),
}

# =============================================================================
# Category Aliases (Maps common variations to canonical names)
# =============================================================================

CATEGORY_ALIASES: dict[str, str] = {
    # ==================== BUSINESS & OPERATIONS ====================
    "operations": "operations_report",
    "operational": "operations_report",
    "ops": "operations_report",
    "operation": "operations_report",
    "ops_report": "operations_report",
    "kpi": "kpi_dashboard",
    "kpis": "kpi_dashboard",
    "dashboard": "kpi_dashboard",
    "metrics": "kpi_dashboard",
    "performance": "performance_review",
    "review": "performance_review",
    "inventory": "inventory_management",
    "stock": "inventory_management",
    "warehouse": "inventory_management",
    "supply": "supply_chain",
    "logistics": "supply_chain",
    "shipping": "supply_chain",
    "procurement": "supply_chain",
    "production": "production_schedule",
    "manufacturing": "production_schedule",
    "schedule": "production_schedule",
    "quality": "quality_control",
    "qa": "quality_control",
    "qc": "quality_control",
    "inspection": "quality_control",
    "project": "project_management",
    "project_plan": "project_management",
    "timeline": "project_management",
    "milestone": "project_management",
    "strategy": "business_strategy",
    "strategic": "business_strategy",
    "vision": "business_strategy",
    "meeting": "meeting_minutes",
    "minutes": "meeting_minutes",
    "board_meeting": "meeting_minutes",
    "org_chart": "organizational_chart",
    "hierarchy": "organizational_chart",
    "structure": "organizational_chart",
    "process": "process_documentation",
    "workflow": "process_documentation",
    "procedure": "standard_operating_procedure",
    "sop": "standard_operating_procedure",
    "work_instruction": "standard_operating_procedure",
    "compliance": "compliance_report",
    "regulatory": "compliance_report",
    "vendor": "vendor_management",
    "supplier": "vendor_management",
    # ==================== FINANCIAL ====================
    "invoices": "invoice",
    "billing": "invoice",
    "bill": "invoice",
    "receipts": "receipt",
    "payment_confirmation": "receipt",
    "po": "purchase_order",
    "purchase": "purchase_order",
    "requisition": "purchase_order",
    "budgets": "budget",
    "budget_plan": "budget",
    "spending": "budget",
    "expense": "expense_report",
    "expenses": "expense_report",
    "reimbursement": "expense_report",
    "pnl": "profit_loss",
    "profit_and_loss": "profit_loss",
    "income_statement": "profit_loss",
    "earnings": "profit_loss",
    "balance": "balance_sheet",
    "assets_liabilities": "balance_sheet",
    "cashflow": "cash_flow",
    "liquidity": "cash_flow",
    "tax": "tax_document",
    "taxes": "tax_document",
    "tax_return": "tax_document",
    "audit": "audit_report",
    "auditing": "audit_report",
    "forecast": "financial_forecast",
    "projection": "financial_forecast",
    "investment": "investment_report",
    "portfolio": "investment_report",
    "bank": "bank_statement",
    "account_statement": "bank_statement",
    "salary": "payroll",
    "wages": "payroll",
    "compensation": "payroll",
    "pay": "payroll",
    "loan": "financial_contract",
    "credit": "financial_contract",
    "finance": "financial_contract",
    "financial": "financial_contract",
    # ==================== LEGAL & REGULATORY ====================
    "contract": "legal_contract",
    "contracts": "legal_contract",
    "agreement": "legal_contract",
    "legal": "legal_contract",
    "confidentiality": "nda",
    "non_disclosure": "nda",
    "secrecy": "nda",
    "terms": "terms_conditions",
    "conditions": "terms_conditions",
    "tos": "terms_conditions",
    "privacy": "privacy_policy",
    "gdpr": "privacy_policy",
    "data_protection": "privacy_policy",
    "filing": "regulatory_filing",
    "government_filing": "regulatory_filing",
    "court": "court_document",
    "lawsuit": "court_document",
    "judgment": "court_document",
    "legal_filing": "court_document",
    "patents": "patent",
    "ip": "patent",
    "intellectual_property": "patent",
    "trademarks": "trademark",
    "brand_protection": "trademark",
    "license": "license_agreement",
    "licensing": "license_agreement",
    "brief": "legal_brief",
    "memorandum": "legal_brief",
    "poa": "power_of_attorney",
    "proxy": "power_of_attorney",
    "authorization": "power_of_attorney",
    "governance": "corporate_governance",
    "bylaws": "corporate_governance",
    "resolution": "corporate_governance",
    # ==================== HUMAN RESOURCES ====================
    "employee": "employee_record",
    "personnel": "employee_record",
    "hr_record": "employee_record",
    "resume": "resume_cv",
    "cv": "resume_cv",
    "curriculum_vitae": "resume_cv",
    "job_application": "resume_cv",
    "job": "job_description",
    "position": "job_description",
    "role": "job_description",
    "posting": "job_description",
    "appraisal": "performance_evaluation",
    "evaluation": "performance_evaluation",
    "feedback": "performance_evaluation",
    "training": "training_material",
    "learning": "training_material",
    "course": "training_material",
    "onboarding": "onboarding_document",
    "new_hire": "onboarding_document",
    "orientation": "onboarding_document",
    "benefits": "benefits_summary",
    "insurance": "benefits_summary",
    "retirement": "benefits_summary",
    "disciplinary": "disciplinary_record",
    "warning": "disciplinary_record",
    "corrective_action": "disciplinary_record",
    "termination": "termination_letter",
    "dismissal": "termination_letter",
    "resignation": "termination_letter",
    "salary_band": "salary_structure",
    "pay_grade": "salary_structure",
    "leave": "leave_request",
    "vacation": "leave_request",
    "time_off": "leave_request",
    "handbook": "employee_handbook",
    "policy": "employee_handbook",
    "workplace_rules": "employee_handbook",
    # ==================== MARKETING & SALES ====================
    "campaign": "marketing_campaign",
    "marketing": "marketing_campaign",
    "promotion": "marketing_campaign",
    "brand": "brand_guidelines",
    "branding": "brand_guidelines",
    "visual_identity": "brand_guidelines",
    "market": "market_research",
    "consumer": "market_research",
    "competitor": "competitive_analysis",
    "benchmarking": "competitive_analysis",
    "sales": "sales_report",
    "revenue": "sales_report",
    "customer": "customer_feedback",
    "reviews": "customer_feedback",
    "testimonials": "customer_feedback",
    "leads": "lead_generation",
    "prospects": "lead_generation",
    "pipeline": "lead_generation",
    "ads": "advertising_content",
    "advertisement": "advertising_content",
    "creative": "advertising_content",
    "social_media": "social_media_analytics",
    "social": "social_media_analytics",
    "engagement": "social_media_analytics",
    "catalog": "product_catalog",
    "products": "product_catalog",
    "pricing": "product_catalog",
    "segmentation": "customer_segmentation",
    "demographics": "customer_segmentation",
    "audience": "customer_segmentation",
    "crm": "crm_data",
    "contacts": "crm_data",
    "relationship": "crm_data",
    # ==================== TECHNICAL & IT ====================
    "specs": "technical_specification",
    "specification": "technical_specification",
    "requirements": "technical_specification",
    "api": "api_documentation",
    "integration": "api_documentation",
    "endpoints": "api_documentation",
    "architecture": "system_architecture",
    "design": "system_architecture",
    "infrastructure": "system_architecture",
    "manual": "user_manual",
    "guide": "user_manual",
    "documentation": "user_manual",
    "installation": "installation_guide",
    "setup": "installation_guide",
    "deployment": "installation_guide",
    "troubleshooting": "troubleshooting_guide",
    "faq": "troubleshooting_guide",
    "support": "troubleshooting_guide",
    "srs": "software_requirements",
    "functional_spec": "software_requirements",
    "features": "software_requirements",
    "network": "network_diagram",
    "topology": "network_diagram",
    "it_security": "security_policy",
    "cybersecurity": "security_policy",
    "access_control": "security_policy",
    "schema": "data_dictionary",
    "database": "data_dictionary",
    "data_model": "data_dictionary",
    "release": "release_notes",
    "changelog": "release_notes",
    "version": "release_notes",
    "technical": "technical_report",
    "engineering": "technical_report",
    "feasibility": "technical_report",
    # ==================== RESEARCH & ACADEMIC ====================
    "research": "research_paper",
    "paper": "research_paper",
    "academic": "research_paper",
    "scholarly": "research_paper",
    "dissertation": "thesis",
    "graduate": "thesis",
    "phd": "thesis",
    "literature": "literature_review",
    "case": "case_study",
    "analysis": "case_study",
    "example": "case_study",
    "lab_report": "scientific_report",
    "lab": "scientific_report",
    "experiment": "experimental_data",
    "test_results": "experimental_data",
    "data": "experimental_data",
    "survey": "survey_results",
    "questionnaire": "survey_results",
    "poll": "survey_results",
    "statistics": "statistical_analysis",
    "quantitative": "statistical_analysis",
    "numbers": "statistical_analysis",
    "white_paper": "whitepaper",
    "thought_leadership": "whitepaper",
    "conference": "conference_proceedings",
    "symposium": "conference_proceedings",
    "presentation": "conference_proceedings",
    # ==================== COMMUNICATIONS & CORRESPONDENCE ====================
    "letter": "official_letter",
    "letters": "official_letter",
    "correspondence": "official_letter",
    "formal_letter": "official_letter",
    "official": "official_letter",
    "official_letters": "official_letter",
    "memos": "memo",
    "memoranda": "memo",
    "interoffice": "memo",
    "email": "email_correspondence",
    "emails": "email_correspondence",
    "electronic": "email_correspondence",
    "press": "press_release",
    "media_release": "press_release",
    "news": "press_release",
    "newsletters": "newsletter",
    "update": "newsletter",
    "announcements": "announcement",
    "notice": "announcement",
    "circulars": "circular",
    "bulletin": "circular",
    "notifications": "notification",
    "alert": "notification",
    "invitations": "invitation",
    "invite": "invitation",
    "event": "invitation",
    "thank_you": "thank_you_letter",
    "appreciation": "thank_you_letter",
    "acknowledgment": "thank_you_letter",
    # ==================== INTELLIGENCE & SECURITY ====================
    "threat": "threat_assessment",
    "threats": "threat_assessment",
    "security": "security_report",
    "breach": "security_report",
    "surveillance": "surveillance_report",
    "monitoring": "surveillance_report",
    "observation": "surveillance_report",
    "risk": "risk_analysis",
    "vulnerability": "vulnerability_assessment",
    "geopolitical": "geopolitical_brief",
    "political": "geopolitical_brief",
    "international": "geopolitical_brief",
    "incident": "incident_report",
    "accident": "incident_report",
    "background": "background_check",
    "due_diligence": "background_check",
    "screening": "background_check",
    "intel": "intelligence_summary",
    "intelligence": "intelligence_summary",
    "sitrep": "situation_report",
    "status": "situation_report",
    "pentest": "vulnerability_assessment",
    "penetration": "vulnerability_assessment",
    "osint": "osint_report",
    "open_source": "osint_report",
    "classified": "classified_document",
    "secret": "classified_document",
    "restricted": "classified_document",
}

# =============================================================================
# Category Domain Groupings (for routing decisions)
# =============================================================================

CATEGORY_DOMAINS: dict[str, list[str]] = {
    "business_operations": [
        "operations_report",
        "kpi_dashboard",
        "performance_review",
        "inventory_management",
        "supply_chain",
        "production_schedule",
        "quality_control",
        "project_management",
        "business_strategy",
        "meeting_minutes",
        "organizational_chart",
        "process_documentation",
        "standard_operating_procedure",
        "compliance_report",
        "vendor_management",
    ],
    "financial": [
        "invoice",
        "receipt",
        "purchase_order",
        "budget",
        "expense_report",
        "profit_loss",
        "balance_sheet",
        "cash_flow",
        "tax_document",
        "audit_report",
        "financial_forecast",
        "investment_report",
        "bank_statement",
        "payroll",
        "financial_contract",
    ],
    "legal": [
        "legal_contract",
        "nda",
        "terms_conditions",
        "privacy_policy",
        "regulatory_filing",
        "court_document",
        "patent",
        "trademark",
        "license_agreement",
        "legal_brief",
        "power_of_attorney",
        "corporate_governance",
    ],
    "hr": [
        "employee_record",
        "resume_cv",
        "job_description",
        "performance_evaluation",
        "training_material",
        "onboarding_document",
        "benefits_summary",
        "disciplinary_record",
        "termination_letter",
        "salary_structure",
        "leave_request",
        "employee_handbook",
    ],
    "marketing_sales": [
        "marketing_campaign",
        "brand_guidelines",
        "market_research",
        "competitive_analysis",
        "sales_report",
        "customer_feedback",
        "lead_generation",
        "advertising_content",
        "social_media_analytics",
        "product_catalog",
        "customer_segmentation",
        "crm_data",
    ],
    "technical": [
        "technical_specification",
        "api_documentation",
        "system_architecture",
        "user_manual",
        "installation_guide",
        "troubleshooting_guide",
        "software_requirements",
        "network_diagram",
        "security_policy",
        "data_dictionary",
        "release_notes",
        "technical_report",
    ],
    "research": [
        "research_paper",
        "thesis",
        "literature_review",
        "case_study",
        "scientific_report",
        "experimental_data",
        "survey_results",
        "statistical_analysis",
        "whitepaper",
        "conference_proceedings",
    ],
    "communications": [
        "official_letter",
        "memo",
        "email_correspondence",
        "press_release",
        "newsletter",
        "announcement",
        "circular",
        "notification",
        "invitation",
        "thank_you_letter",
    ],
    "intelligence_security": [
        "threat_assessment",
        "security_report",
        "surveillance_report",
        "risk_analysis",
        "geopolitical_brief",
        "incident_report",
        "background_check",
        "intelligence_summary",
        "situation_report",
        "vulnerability_assessment",
        "osint_report",
        "classified_document",
    ],
}


def get_domain_for_category(category: str) -> str | None:
    """
    Get the domain a category belongs to.

    Args:
        category: The category name.

    Returns:
        The domain name or None if not found.
    """
    for domain, categories in CATEGORY_DOMAINS.items():
        if category in categories:
            return domain
    return None
