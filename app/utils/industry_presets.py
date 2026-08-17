# Production-grade Industry Department Presets for Multi-Tenant EMS

INDUSTRY_DEPARTMENT_PRESETS = {
    "IT & Software": [
        "Software Development",
        "Quality Assurance & Testing",
        "DevOps & Cloud Infrastructure",
        "Product Management & UI/UX",
        "IT Support & Security",
        "Human Resources",
        "Finance & Accounting"
    ],
    "Healthcare & Medical": [
        "Outpatient Department (OPD)",
        "Intensive Care Unit (ICU)",
        "Nursing & Patient Care",
        "Pharmacy & Medical Supplies",
        "Emergency & Trauma",
        "Human Resources",
        "Finance & Billing"
    ],
    "Finance & Banking": [
        "Accounts & Audit",
        "Taxation & Compliance",
        "Risk Management & Security",
        "Investment & Portfolio",
        "Financial Operations",
        "Human Resources",
        "Legal & Advisory"
    ],
    "Manufacturing & Engineering": [
        "Production & Assembly Line",
        "Quality Assurance (QA/QC)",
        "Supply Chain & Logistics",
        "Plant Maintenance",
        "EHS & Safety Management",
        "Human Resources",
        "Finance & Accounts"
    ],
    "Retail & E-Commerce": [
        "Store Operations",
        "E-Commerce & Digital Sales",
        "Inventory & Warehouse",
        "Merchandising & Sourcing",
        "Customer Care",
        "Human Resources",
        "Finance & Accounts"
    ],
    "Education & Academia": [
        "Academic Faculty",
        "Admissions & Student Welfare",
        "Examination & Registrar",
        "Library & Information",
        "Campus Administration",
        "Human Resources",
        "Accounts & Finance"
    ],
    "Real Estate & Construction": [
        "Architecture & Design",
        "Project Site Engineering",
        "Safety & Compliance",
        "Procurement & Materials",
        "Sales & Marketing",
        "Human Resources",
        "Finance & Accounts"
    ],
    "Hospitality & Tourism": [
        "Front Desk & Reservations",
        "Housekeeping & Facilities",
        "Food & Beverage (F&B)",
        "Event & Banquet Operations",
        "Sales & Marketing",
        "Human Resources",
        "Accounts & Finance"
    ],
    "Logistics & Supply Chain": [
        "Fleet Management",
        "Warehouse & Fulfillment",
        "Dispatch & Routing",
        "Import/Export Customs",
        "Customer Support",
        "Human Resources",
        "Accounts & Finance"
    ],
    "Agriculture & Agrotech": [
        "Agronomy & Crop Science",
        "Farm Operations",
        "Supply Chain & Distribution",
        "R&D & Biotechnology",
        "Sales & Trade",
        "Human Resources",
        "Finance & Accounts"
    ],
    "Media & Entertainment": [
        "Content Creation & Editorial",
        "Video Production & Editing",
        "Public Relations & Marketing",
        "Digital Media & SEO",
        "Talent Management",
        "Human Resources",
        "Finance & Accounts"
    ],
    "Legal & Professional Services": [
        "Litigation & Dispute Resolution",
        "Corporate Law & Compliance",
        "Intellectual Property (IP)",
        "Client Advisory",
        "Legal Operations",
        "Human Resources",
        "Finance & Accounts"
    ]
}

def get_preset_departments(industry_name: str) -> list[str]:
    """Returns department names for a given industry. Falls back to IT & Software if not found."""
    return INDUSTRY_DEPARTMENT_PRESETS.get(
        industry_name,
        INDUSTRY_DEPARTMENT_PRESETS["IT & Software"]
    )
