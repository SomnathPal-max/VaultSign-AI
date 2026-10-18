"""
VaultSign AI - Benchmark Evaluation Dataset
Contains 25 labeled contracts (synthetic, public templates, and variations)
with hand-labeled ground truth across all 8 Freelancer Clause Families.
Used to measure Precision, Recall, and False-Fabrication Rate per Section 8.
"""

from typing import List, Dict, Any
from pydantic import BaseModel

class BenchmarkContract(BaseModel):
    id: str
    title: str
    contract_type: str
    text: str
    ground_truth: Dict[str, bool]  # Maps each of the 8 clause families to True/False

BENCHMARK_SUITE: List[BenchmarkContract] = [
    BenchmarkContract(
        id="bench_01",
        title="Agency Master Services Agreement (High Risk)",
        contract_type="Creative / Marketing",
        text="""
        MASTER SERVICES AGREEMENT
        1. Fees & Payment: Payment terms are Net-90 days following approval of invoice by end client.
        2. Intellectual Property: Contractor irrevocably assigns all right, title, and interest in and to all works, inventions, and proprietary rights throughout the universe perpetually, irrespective of receipt of funds.
        3. Liability: Contractor shall defend, indemnify and hold harmless Client against any and all claims, damages, liabilities, and costs without limitation.
        4. Restrictive Covenant: Contractor shall not directly or indirectly provide services to any competing business worldwide for a period of 24 months.
        5. Revisions: Contractor shall modify deliverables until satisfied to the Client's sole satisfaction without additional fee.
        6. Termination: Client may terminate at will for convenience immediately without further payment for work completed.
        7. Late Fees: No late fee or interest shall accrue on any overdue invoice.
        8. Exclusivity: Contractor agrees to provide services on a sole and exclusive basis and shall not provide services to any other client.
        """,
        ground_truth={
            "ip_transfer": True,
            "extended_payment": True,
            "broad_non_compete": True,
            "asymmetric_liability": True,
            "unlimited_revisions": True,
            "termination_kill_fee": True,
            "late_payment_consequences": True,
            "exclusivity": True
        }
    ),
    BenchmarkContract(
        id="bench_02",
        title="Fair Freelancer Standard Contract (Clean Baseline)",
        contract_type="Engineering / Design",
        text="""
        STANDARD FREELANCER AGREEMENT
        1. Invoicing: Client shall pay undisputed invoices within fifteen (15) days of invoice date (Net-15). Late payments accrue interest at 1.5% monthly.
        2. IP Assignment: Custom deliverables transfer to Client strictly upon receipt of full payment. Contractor retains all ownership in pre-existing developer tools and libraries.
        3. Mutual Liability: Each party agrees to mutual indemnification capped at total fees paid under this Agreement.
        4. Independent Contractor: Contractor is an independent operator and is free to offer services to any non-conflicting clients. No non-compete applies.
        5. Revisions: Includes up to two rounds of revisions. Additional changes require an hourly Change Order.
        6. Termination: 14 days written notice. Client pays pro-rata for work done plus a 25% kill fee.
        """,
        ground_truth={
            "ip_transfer": False,
            "extended_payment": False,
            "broad_non_compete": False,
            "asymmetric_liability": False,
            "unlimited_revisions": False,
            "termination_kill_fee": False,
            "late_payment_consequences": False,
            "exclusivity": False
        }
    ),
    BenchmarkContract(
        id="bench_03",
        title="Web Development Consulting Contract",
        contract_type="Web Dev",
        text="""
        CONSULTING AGREEMENT
        1. Payment: Invoices are payable within sixty (60) days of receipt (Net-60). Client may withhold payments in the event of any dispute without interest.
        2. Deliverables: Revisions shall be made until client is satisfied to sole satisfaction.
        3. Intellectual Property: Contractor assigns all inventions made during the term on a perpetual, worldwide basis as work made for hire.
        4. Confidentiality: Both parties shall preserve proprietary trade secrets.
        """,
        ground_truth={
            "ip_transfer": True,
            "extended_payment": True,
            "broad_non_compete": False,
            "asymmetric_liability": False,
            "unlimited_revisions": True,
            "termination_kill_fee": False,
            "late_payment_consequences": True,
            "exclusivity": False
        }
    ),
    BenchmarkContract(
        id="bench_04",
        title="Graphic Design Retainer",
        contract_type="Design",
        text="""
        GRAPHIC DESIGN RETAINER
        1. Retainer: Billed at $4,000 monthly, payable within 14 days.
        2. Scope: 40 hours per month. Unused hours do not roll over.
        3. Exclusivity: Contractor shall not perform services for any other design client during the contract term.
        4. Non-compete: For 12 months after expiration, contractor agrees not to engage in competing business.
        """,
        ground_truth={
            "ip_transfer": False,
            "extended_payment": False,
            "broad_non_compete": True,
            "asymmetric_liability": False,
            "unlimited_revisions": False,
            "termination_kill_fee": False,
            "late_payment_consequences": False,
            "exclusivity": True
        }
    ),
    BenchmarkContract(
        id="bench_05",
        title="Enterprise IT Vendor Agreement",
        contract_type="DevOps",
        text="""
        IT SERVICES VENDOR AGREEMENT
        1. Compensation: Client shall pay Net-90 days, subject to client receiving payment from end customers (pay-when-paid).
        2. Indemnification: Consultant shall defend, indemnify and hold harmless Client against any and all claims, without limitation on liability.
        3. Cancellation: Client may terminate at will without notice and without payment for uncompleted work.
        """,
        ground_truth={
            "ip_transfer": False,
            "extended_payment": True,
            "broad_non_compete": False,
            "asymmetric_liability": True,
            "unlimited_revisions": False,
            "termination_kill_fee": True,
            "late_payment_consequences": False,
            "exclusivity": False
        }
    )
]

# Generate synthetic variations to complete 20+ contract test suite
VARIATIONS = [
    ("Content Writing Contract", "ip_transfer", "Contractor assigns all right, title and interest in all written articles perpetually without carve-out for prior writing samples."),
    ("UI/UX Mobile Design Agreement", "unlimited_revisions", "Designer agrees to unlimited revisions without additional fee until the app satisfies client's sole discretion."),
    ("SEO Services Terms", "extended_payment", "Payment terms shall be payable within one hundred twenty (120) days of invoice submission."),
    ("Copywriting Engagement", "termination_kill_fee", "Company may terminate this engagement immediately without cause and with no payment for uncompleted work or kill fee."),
    ("Video Production Contract", "asymmetric_liability", "Videographer shall indemnify and hold harmless Studio from any and all damages and claims, with uncapped liability."),
    ("Data Analysis Agreement", "exclusivity", "Analyst shall work on an exclusive basis and is strictly prohibited from providing services to any other company."),
    ("Mobile App Architecture Scope", "late_payment_consequences", "Under no circumstances shall any late fee or interest accrue on unpaid or overdue invoices."),
    ("Technical Writing Statement", "broad_non_compete", "Writer agrees not to compete or write for any competitive business worldwide for a period of 2 years."),
    ("Brand Strategy Engagement", "ip_transfer", "Strategist hereby assigns all intellectual property and inventions on an irrevocable, worldwide basis throughout the universe."),
    ("DevOps Cloud Architecture", "extended_payment", "Invoices shall be processed under Net-90 payment terms from invoice approval date."),
    ("Social Media Management", "unlimited_revisions", "Agency shall produce alternative creative variations until client is satisfied to sole satisfaction."),
    ("Quality Assurance Testing", "asymmetric_liability", "Tester agrees to defend, indemnify and hold harmless Client for any defects or claims without limitation."),
    ("Translation Services", "termination_kill_fee", "Client reserves right to terminate for convenience immediately without compensation for work in progress."),
    ("Podcast Audio Editing", "late_payment_consequences", "Client may withhold any and all payments in the event of dispute without interest or penalty."),
    ("Cybersecurity Assessment", "broad_non_compete", "Consultant shall not directly or indirectly provide services to any competing business in any geographic area."),
    ("Firmware Engineering", "ip_transfer", "Engineer agrees all firmware is work made for hire, assigning all rights irrespective of receipt of funds."),
    ("Animation Services Agreement", "exclusivity", "Animator shall devote full time and efforts solely and exclusively to Studio."),
    ("Clean Technical Document Review", "none", "Standard consulting at $120/hr, Net-30 payment, mutual indemnity with aggregate fee cap, non-exclusive."),
    ("Clean Security Architecture Review", "none", "Net-15 payment terms, mutual NDA, contractor retains background tools, 14-day notice with kill fee."),
    ("Clean Editorial Services", "none", "Two revisions included, Net-30 payment, copyright assignment upon full payment, non-compete waived.")
]

for idx, (title, target_trap, snippet) in enumerate(VARIATIONS, start=6):
    is_clean = target_trap == "none"
    gt = {k: False for k in [
        "ip_transfer", "extended_payment", "broad_non_compete", "asymmetric_liability",
        "unlimited_revisions", "termination_kill_fee", "late_payment_consequences", "exclusivity"
    ]}
    if not is_clean and target_trap in gt:
        gt[target_trap] = True

    text_body = f"""
    {title.upper()}
    Date: 2026-05-15
    Parties: Acme Corp and Independent Contractor.
    Terms:
    {snippet}
    General: This agreement represents the entire understanding between the parties.
    """
    BENCHMARK_SUITE.append(BenchmarkContract(
        id=f"bench_{idx:02d}",
        title=title,
        contract_type="Freelance Service Agreement",
        text=text_body,
        ground_truth=gt
    ))
