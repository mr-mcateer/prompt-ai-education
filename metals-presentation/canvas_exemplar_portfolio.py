#!/usr/bin/env python3
"""
Generate and deploy exemplar portfolio for "What Nobody Teaches You
About Owning a Car" -- 16-page student exemplar using a 2015 Toyota Prius.

Vehicle: 2015 Toyota Prius Two, white, 80K miles, $12,000 private party purchase (2025)
Location: Corvallis, OR

Modes:
  --dry-run    Generate all 16 pages to terminal (no Canvas calls)
  --review     Generate + run 3-pass Gemini QA per page
  --execute    Deploy to Canvas as Course Pages + Test Student submissions
  --audit      Verify exemplar pages exist on Canvas
  --page N     Generate only page N (works with any mode)

Usage:
  python3 canvas_exemplar_portfolio.py --dry-run
  python3 canvas_exemplar_portfolio.py --dry-run --page 3
  python3 canvas_exemplar_portfolio.py --review
  python3 canvas_exemplar_portfolio.py --execute
  python3 canvas_exemplar_portfolio.py --audit
"""

import argparse
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field

import requests

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from tools.env_loader import get_env

# ── Constants ─────────────────────────────────────────────────
ENGINES_FAB_COURSE_IDS = [23124, 23344]
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_RPM_DELAY = 2.0  # seconds between Gemini calls


# ══════════════════════════════════════════════════════════════
# VEHICLE PROFILE -- Single source of truth for ALL numbers
# ══════════════════════════════════════════════════════════════

@dataclass
class VehicleProfile:
    """Central data truth source. Every page pulls numbers from here."""

    # Identity
    year: int = 2015
    make: str = "Toyota"
    model: str = "Prius"
    trim: str = "Two"
    generation: str = "Gen 3 (2010-2015)"
    color: str = "White"
    body_style: str = "Hatchback"
    drivetrain: str = "FWD"
    engine: str = "1.8L 4-Cylinder Hybrid (2ZR-FXE)"
    transmission: str = "CVT (eCVT)"
    vin_example: str = "JTDKN3DU5F0123456"

    # Purchase
    purchase_price: float = 12000.00
    purchase_year: int = 2025
    purchase_type: str = "Private Party"
    mileage_at_purchase: int = 80000
    annual_miles: int = 12000

    # Location
    state: str = "Oregon"
    city: str = "Corvallis"
    zip_code: str = "97330"

    # Original MSRP (when new)
    original_msrp_base: float = 24200.00
    original_msrp_destination: float = 825.00

    # Financing
    down_payment_pct: float = 0.20
    apr: float = 0.055
    loan_terms: list = field(default_factory=lambda: [48, 60, 72])

    # Insurance (Oregon, young adult on parent's policy)
    liability_limits: str = "50/100/50"
    collision_deductible_low: int = 500
    collision_deductible_high: int = 1000
    comprehensive_deductible: int = 250
    pip_coverage: int = 15000
    um_uim_limits: str = "50/100"
    monthly_premium_500: float = 142.00
    monthly_premium_1000: float = 128.00

    # Fuel
    mpg_city: int = 51
    mpg_highway: int = 48
    mpg_combined: int = 50
    gas_price: float = 3.85

    # Tires
    tire_size: str = "P195/65R15"
    tire_brand: str = "Michelin"
    tire_model: str = "Defender T+H"
    tire_type: str = "All-Season"
    tire_price_each: float = 142.00
    tire_install_each: float = 22.00
    tire_warranty_miles: int = 80000
    tire_rotation_interval: int = 5000

    # Maintenance
    oil_type: str = "0W-20 Full Synthetic"
    oil_capacity_qt: float = 4.4
    oil_change_interval: int = 10000
    oil_change_cost: float = 65.00
    coolant_flush_interval: int = 100000
    coolant_flush_cost: float = 150.00
    brake_fluid_interval: int = 30000
    brake_fluid_cost: float = 100.00
    cabin_filter_interval: int = 15000
    cabin_filter_cost: float = 25.00
    engine_filter_interval: int = 30000
    engine_filter_cost: float = 40.00
    annual_maintenance_est: float = 450.00

    # Oregon fees
    registration_2yr: float = 306.00
    title_fee: float = 98.50

    # Depreciation -- lesson rates from Module 14 curriculum
    # Applied from purchase date (year of MY ownership, not vehicle age)
    depreciation_yr1_pct: float = 0.20
    depreciation_yr3_pct: float = 0.15
    depreciation_yr5_pct: float = 0.10
    depreciation_late_pct: float = 0.06  # midpoint of 5-7%

    # Comparison vehicles (Page 1)
    comp1_year: int = 2014
    comp1_make: str = "Honda"
    comp1_model: str = "Civic LX"
    comp1_miles: int = 85000
    comp1_price: float = 11500.00
    comp1_mpg: int = 33
    comp1_insurance_est: float = 155.00
    comp1_reliability: str = "4.2/5 (Consumer Reports)"

    comp2_year: int = 2013
    comp2_make: str = "Hyundai"
    comp2_model: str = "Elantra GLS"
    comp2_miles: int = 78000
    comp2_price: float = 10200.00
    comp2_mpg: int = 32
    comp2_insurance_est: float = 148.00
    comp2_reliability: str = "3.8/5 (Consumer Reports)"

    prius_reliability: str = "4.5/5 (Consumer Reports)"
    prius_insurance_est: float = 142.00

    # EV comparison (Page 15)
    ev_year: int = 2015
    ev_make: str = "Nissan"
    ev_model: str = "Leaf SV"
    ev_price: float = 9500.00
    ev_range_miles: int = 84
    ev_kwh_per_mile: float = 0.30
    ev_electricity_rate: float = 0.11
    ev_annual_maintenance: float = 300.00
    ev_insurance_monthly: float = 125.00
    ev_resale_5yr: float = 3500.00

    # Gas comparison (Page 15) -- Corolla as pure ICE baseline
    gas_comp_year: int = 2015
    gas_comp_make: str = "Toyota"
    gas_comp_model: str = "Corolla LE"
    gas_comp_price: float = 11000.00
    gas_comp_mpg: int = 32
    gas_comp_maintenance: float = 500.00
    gas_comp_insurance_monthly: float = 138.00
    gas_comp_resale_5yr: float = 5500.00

    # ── Computed Properties ───────────────────────────────
    @property
    def original_msrp_total(self) -> float:
        return self.original_msrp_base + self.original_msrp_destination

    @property
    def down_payment(self) -> float:
        return self.purchase_price * self.down_payment_pct

    @property
    def loan_amount(self) -> float:
        return self.purchase_price - self.down_payment

    def monthly_payment(self, months: int) -> float:
        r = self.apr / 12
        n = months
        p = self.loan_amount
        if r == 0:
            return p / n
        return p * (r * (1 + r) ** n) / ((1 + r) ** n - 1)

    def total_interest(self, months: int) -> float:
        return self.monthly_payment(months) * months - self.loan_amount

    def total_loan_cost(self, months: int) -> float:
        return self.monthly_payment(months) * months

    @property
    def annual_fuel_cost(self) -> float:
        return (self.annual_miles / self.mpg_combined) * self.gas_price

    @property
    def monthly_fuel_cost(self) -> float:
        return self.annual_fuel_cost / 12

    @property
    def annual_insurance(self) -> float:
        return self.monthly_premium_500 * 12

    @property
    def annual_registration(self) -> float:
        return self.registration_2yr / 2

    @property
    def annual_depreciation(self) -> float:
        # For TCO (Page 5): use realistic used-car depreciation (~8%/yr)
        # Page 14 uses lesson rates via depreciation_value_at_year()
        return self.purchase_price * 0.08

    @property
    def preferred_term(self) -> int:
        return 48

    @property
    def preferred_monthly_payment(self) -> float:
        return self.monthly_payment(self.preferred_term)

    @property
    def tco_monthly(self) -> float:
        return (
            self.preferred_monthly_payment
            + self.monthly_premium_500
            + self.monthly_fuel_cost
            + self.annual_maintenance_est / 12
            + self.annual_registration / 12
            + self.annual_depreciation / 12
        )

    @property
    def tco_annual(self) -> float:
        return self.tco_monthly * 12

    @property
    def tco_per_mile(self) -> float:
        return self.tco_annual / self.annual_miles

    @property
    def tire_set_price(self) -> float:
        return self.tire_price_each * 4

    @property
    def tire_installed_total(self) -> float:
        return (self.tire_price_each + self.tire_install_each) * 4

    @property
    def tire_cost_per_mile(self) -> float:
        return self.tire_installed_total / self.tire_warranty_miles

    @property
    def tire_rotations_per_year(self) -> float:
        return self.annual_miles / self.tire_rotation_interval

    @property
    def oil_changes_per_year(self) -> float:
        return self.annual_miles / self.oil_change_interval

    @property
    def annual_oil_cost(self) -> float:
        return self.oil_changes_per_year * self.oil_change_cost

    def depreciation_value_at_year(self, year: int) -> float:
        """Project vehicle value at a given ownership year."""
        value = self.purchase_price
        for y in range(1, year + 1):
            if y == 1:
                rate = self.depreciation_yr1_pct
            elif y <= 3:
                rate = self.depreciation_yr3_pct
            elif y <= 5:
                rate = self.depreciation_yr5_pct
            else:
                rate = self.depreciation_late_pct
            value *= (1 - rate)
        return round(value, 0)

    @property
    def deductible_savings_3yr(self) -> float:
        """Savings from $1000 vs $500 deductible over 3 claim-free years."""
        return (self.monthly_premium_500 - self.monthly_premium_1000) * 36

    # String helpers
    @property
    def full_name(self) -> str:
        return f"{self.year} {self.make} {self.model} {self.trim}"

    @property
    def short_name(self) -> str:
        return f"{self.year} {self.make} {self.model}"


# ══════════════════════════════════════════════════════════════
# HTML FORMATTING UTILITIES
# ══════════════════════════════════════════════════════════════

def html_page(title: str, body: str, page_num: int = 0) -> str:
    """Wrap body content in a styled HTML page."""
    return f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6;">
<h1 style="color: #1a5276; border-bottom: 3px solid #2980b9; padding-bottom: 10px;">
  Page {page_num}: {title}
</h1>
<p style="color: #666; font-size: 0.9em;">
  <strong>Portfolio Vehicle:</strong> 2015 Toyota Prius Two | White | 80,000 miles | $12,000 purchase
</p>
<hr style="border: 1px solid #eee;">
{body}
<hr style="border: 1px solid #eee; margin-top: 30px;">
<p style="color: #999; font-size: 0.8em; text-align: center;">
  Exemplar Portfolio -- Mr. McAteer's Engines &amp; Fabrication
</p>
</div>"""


def html_table(headers: list, rows: list, caption: str = "") -> str:
    """Generate a styled HTML table."""
    cap = f'<caption style="font-weight: bold; margin-bottom: 8px; text-align: left;">{caption}</caption>' if caption else ""
    hdr = "".join(f'<th style="background: #2980b9; color: white; padding: 8px 12px; text-align: left;">{h}</th>' for h in headers)
    body_rows = []
    for i, row in enumerate(rows):
        bg = "#f8f9fa" if i % 2 == 0 else "white"
        cells = "".join(f'<td style="padding: 8px 12px; border-bottom: 1px solid #eee; background: {bg};">{c}</td>' for c in row)
        body_rows.append(f"<tr>{cells}</tr>")
    return f"""<table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
{cap}<thead><tr>{hdr}</tr></thead>
<tbody>{"".join(body_rows)}</tbody></table>"""


def html_section(title: str, content: str) -> str:
    """Generate a section with heading."""
    return f"""<h2 style="color: #2c3e50; margin-top: 25px; border-left: 4px solid #2980b9; padding-left: 12px;">{title}</h2>
{content}"""


def html_checklist(items: list) -> str:
    """Generate a checklist with checkboxes."""
    lis = "".join(f'<li style="margin: 6px 0; list-style: none;"><input type="checkbox" disabled> {item}</li>' for item in items)
    return f'<ul style="padding-left: 5px;">{lis}</ul>'


def fmt(val: float, prefix: str = "$") -> str:
    """Format a number as currency or plain."""
    if prefix == "$":
        return f"${val:,.2f}"
    return f"{val:,.2f}"


def fmti(val: float, prefix: str = "$") -> str:
    """Format as integer currency."""
    return f"${val:,.0f}"


# ══════════════════════════════════════════════════════════════
# PAGE GENERATORS -- Each function returns (title, html_body)
# ══════════════════════════════════════════════════════════════

def page_01(v: VehicleProfile) -> tuple:
    """Page 1: Vehicle Selection & Comparison (20 pts)."""
    title = "Your First Car Is Probably a Bad Deal"

    comp_table = html_table(
        ["", v.full_name, f"{v.comp1_year} {v.comp1_make} {v.comp1_model}", f"{v.comp2_year} {v.comp2_make} {v.comp2_model}"],
        [
            ["Year/Make/Model/Trim", v.full_name, f"{v.comp1_year} {v.comp1_make} {v.comp1_model}", f"{v.comp2_year} {v.comp2_make} {v.comp2_model}"],
            ["Mileage", f"{v.mileage_at_purchase:,}", f"{v.comp1_miles:,}", f"{v.comp2_miles:,}"],
            ["Asking Price", fmti(v.purchase_price), fmti(v.comp1_price), fmti(v.comp2_price)],
            ["Combined MPG", str(v.mpg_combined), str(v.comp1_mpg), str(v.comp2_mpg)],
            ["Est. Monthly Insurance", fmt(v.prius_insurance_est), fmt(v.comp1_insurance_est), fmt(v.comp2_insurance_est)],
            ["Annual Fuel Cost (12K mi)", fmt(v.annual_fuel_cost), fmt((12000 / v.comp1_mpg) * v.gas_price), fmt((12000 / v.comp2_mpg) * v.gas_price)],
            ["Reliability Rating", v.prius_reliability, v.comp1_reliability, v.comp2_reliability],
        ],
        caption="Vehicle Comparison: Three Candidates",
    )

    civic_fuel = (12000 / v.comp1_mpg) * v.gas_price
    elantra_fuel = (12000 / v.comp2_mpg) * v.gas_price
    prius_fuel = v.annual_fuel_cost

    rationale = f"""<p>I picked the <strong>{v.full_name}</strong>. Yeah, it's the most expensive one at
{fmti(v.purchase_price)}, but the gas savings are huge. At {v.mpg_combined} MPG I'd only spend about
{fmt(prius_fuel)}/year on fuel. The Civic would cost me {fmt(civic_fuel)} and the Elantra {fmt(elantra_fuel)}.
That's {fmt(civic_fuel - prius_fuel)} to {fmt(elantra_fuel - prius_fuel)} saved every year just on gas.</p>

<p>The other big thing is reliability -- it's rated {v.prius_reliability} and these Prius hybrids regularly go
past 200K miles if you keep up on maintenance. Insurance is actually the cheapest of the three at
{fmt(v.prius_insurance_est)}/month, which I didn't expect. I think it's because they're not really
"fun" cars to speed in, so insurance companies see them as low risk. After five years the gas and insurance
savings would more than make up for the higher sticker price.</p>"""

    evidence = """<h3>Evidence / Sources</h3>
<ul>
<li><strong>KBB:</strong> <a href="https://www.kbb.com/toyota/prius/">kbb.com/toyota/prius/</a> -- Used for private party value estimates</li>
<li><strong>Edmunds:</strong> <a href="https://www.edmunds.com/toyota/prius/2015/">edmunds.com/toyota/prius/2015/</a> -- True Market Value cross-check</li>
<li><strong>Consumer Reports:</strong> Reliability ratings for all three vehicles (subscription required)</li>
<li><strong>Fueleconomy.gov:</strong> EPA fuel economy data for all three vehicles</li>
</ul>"""

    body = (
        html_section("Vehicle Candidates", comp_table)
        + html_section("Selection Rationale", rationale)
        + html_section("Evidence", evidence)
    )
    return title, html_page(title, body, 1)


def page_02(v: VehicleProfile) -> tuple:
    """Page 2: Window Sticker & VIN Decode (20 pts)."""
    title = "Everything on the Sticker They Hope You Won't Read"

    sticker = html_table(
        ["Line Item", "Amount"],
        [
            ["Base Price (Prius Two)", fmt(v.original_msrp_base)],
            ["Factory Options", "$0.00 (Two trim is base -- no factory options added)"],
            ["Destination Charge", fmt(v.original_msrp_destination)],
            ["<strong>Total MSRP (when new in 2015)</strong>", f"<strong>{fmt(v.original_msrp_total)}</strong>"],
            ["Dealer-Installed Options", "$0.00 (private party purchase -- no dealer add-ons)"],
            ["<strong>My Purchase Price (2025, 80K mi)</strong>", f"<strong>{fmt(v.purchase_price)}</strong>"],
            ["Depreciation from MSRP", fmt(v.original_msrp_total - v.purchase_price)],
        ],
        caption="Original Window Sticker Breakdown",
    )

    vin_table = html_table(
        ["Position", "Character", "Meaning"],
        [
            ["1", "J", "Country of Origin: Japan"],
            ["2", "T", "Manufacturer: Toyota Motor Corporation"],
            ["3", "D", "Vehicle Type: Passenger Vehicle (sedan/hatchback)"],
            ["4", "K", "Model Line: Prius"],
            ["5", "N", "Engine/Drivetrain: 1.8L 4-cyl Hybrid (2ZR-FXE)"],
            ["6", "3", "Body Type: 4-door Hatchback"],
            ["7", "D", "Restraint System: Driver &amp; Passenger Airbags, Active Belts, Side Curtain"],
            ["8", "U", "Trim/Grade: Two (base trim)"],
            ["9", "5", "Check Digit: Computed value for VIN validation (prevents fraud)"],
            ["10", "F", "Model Year: 2015 (F = 2015 in VIN year encoding)"],
            ["11", "0", "Assembly Plant: Toyota City, Aichi, Japan (Plant Code 0)"],
            ["12", "1", "Production Sequence: 1st digit of serial number"],
            ["13", "2", "Production Sequence: 2nd digit"],
            ["14", "3", "Production Sequence: 3rd digit"],
            ["15", "4", "Production Sequence: 4th digit"],
            ["16", "5", "Production Sequence: 5th digit"],
            ["17", "6", "Production Sequence: 6th digit (unit built #123,456 at this plant)"],
        ],
        caption=f"VIN Decode -- All 17 Characters: {v.vin_example}",
    )

    options_analysis = """<p><strong>What comes with the base Prius Two:</strong></p>
<ul>
<li>Hybrid Synergy Drive (that's the whole point of the car)</li>
<li>Automatic climate control (you need this in Oregon)</li>
<li>Power windows, locks, mirrors</li>
<li>Bluetooth for hands-free calls (required by Oregon law if you're under 18)</li>
<li>Toyota Star Safety System -- VSC, TRAC, ABS, EBD, BA, Smart Stop Technology</li>
</ul>
<p><strong>Options I wouldn't pay extra for:</strong></p>
<ul>
<li>Nav package ($1,500+ new) -- Google Maps on my phone is free and way more updated</li>
<li>Advanced Tech Package ($2,500 new) -- head-up display and dynamic cruise are cool but not worth it</li>
<li>Solar roof ($1,000 new) -- it only runs a tiny fan, not worth a grand</li>
</ul>
<p>Since I bought it used at {fmti(v.purchase_price)}, I didn't have to pay for the depreciation on any
of those extras. The built-in nav is basically useless now anyway since everyone just uses their phone.
The base Two trim has everything I actually need.</p>"""

    evidence_html = """<h3>Evidence</h3>
<ul>
<li><strong>Window Sticker Source:</strong> <a href="https://www.toyota.com/configurator/build/step-01/prius/2015">Toyota.com 2015 Prius Build & Price (archived)</a></li>
<li><strong>VIN Decoder:</strong> <a href="https://www.nhtsa.gov/vin-decoder">NHTSA VIN Decoder</a></li>
<li><strong>Monroney Sticker Reference:</strong> <a href="https://www.edmunds.com/toyota/prius/2015/features-specs/">Edmunds 2015 Prius Features & Specs</a></li>
</ul>"""

    body = (
        html_section("Price Breakdown (Original MSRP vs. My Purchase Price)", sticker)
        + html_section("VIN Decode", vin_table)
        + html_section("Options Analysis: Essential vs. Unnecessary", options_analysis)
        + html_section("Evidence", evidence_html)
    )
    return title, html_page(title, body, 2)


def page_03(v: VehicleProfile) -> tuple:
    """Page 3: Financing Comparison (20 pts)."""
    title = "The Most Expensive Room in the Dealership"

    down_section = f"""<p><strong>Purchase Price:</strong> {fmt(v.purchase_price)}<br>
<strong>Down Payment (20%):</strong> {fmt(v.purchase_price)} x 0.20 = <strong>{fmt(v.down_payment)}</strong><br>
<strong>Loan Amount:</strong> {fmt(v.purchase_price)} - {fmt(v.down_payment)} = <strong>{fmt(v.loan_amount)}</strong><br>
<strong>APR:</strong> 5.5% (pre-approved through Oregon State Credit Union)</p>"""

    scenario_rows = []
    for t in v.loan_terms:
        mp = v.monthly_payment(t)
        ti = v.total_interest(t)
        tc = v.total_loan_cost(t)
        total_with_down = tc + v.down_payment
        scenario_rows.append([
            f"{t} months",
            fmt(mp),
            fmt(ti),
            fmt(tc),
            fmt(total_with_down),
        ])

    loan_table = html_table(
        ["Term", "Monthly Payment", "Total Interest", "Total Loan Cost", "Total Paid (incl. down)"],
        scenario_rows,
        caption=f"Loan Scenarios: {fmt(v.loan_amount)} at {v.apr*100}% APR",
    )

    # Show the math
    r = v.apr / 12
    p = v.loan_amount
    math_section = f"""<h3>How I Calculated (Amortization Formula)</h3>
<p style="font-family: monospace; background: #f5f5f5; padding: 12px; border-radius: 4px;">
M = P x [r(1+r)^n] / [(1+r)^n - 1]<br><br>
Where:<br>
&nbsp;&nbsp;P = {fmt(p)} (principal / loan amount)<br>
&nbsp;&nbsp;r = {v.apr*100}% / 12 = {r:.6f} (monthly interest rate)<br>
&nbsp;&nbsp;n = number of months<br><br>
Example (48-month):<br>
&nbsp;&nbsp;M = {fmt(p)} x [{r:.6f} x (1 + {r:.6f})^48] / [(1 + {r:.6f})^48 - 1]<br>
&nbsp;&nbsp;M = {fmt(p)} x [{r:.6f} x {(1+r)**48:.6f}] / [{(1+r)**48:.6f} - 1]<br>
&nbsp;&nbsp;M = {fmt(p)} x {r * (1+r)**48:.6f} / {(1+r)**48 - 1:.6f}<br>
&nbsp;&nbsp;M = <strong>{fmt(v.monthly_payment(48))}/month</strong>
</p>
<p><em>Calculator used: <a href="https://www.bankrate.com/calculators/auto/auto-loan-calculator.aspx">Bankrate.com Auto Loan Calculator</a></em></p>"""

    pref = v.preferred_term
    short_t = v.loan_terms[0]
    long_t = v.loan_terms[2]
    analysis = f"""<p>I'm going with the <strong>{pref}-month term</strong>. The monthly payment is higher at
{fmt(v.monthly_payment(pref))} compared to {fmt(v.monthly_payment(60))} for 60 months or
{fmt(v.monthly_payment(long_t))} for 72 months, but look at the interest: I'd only pay
{fmt(v.total_interest(pref))} total interest instead of {fmt(v.total_interest(60))} or
{fmt(v.total_interest(long_t))}.</p>

<p>That's {fmt(v.total_interest(long_t) - v.total_interest(pref))} less in interest just by picking
48 months over 72. On a {fmti(v.purchase_price)} car that's a lot. {fmt(v.monthly_payment(pref))}/month
is doable with a part-time job, and I'll have it paid off in four years instead of six. Plus with the
shorter loan I won't end up "upside down" where I owe more than the car's worth -- that can definitely
happen with 72-month loans on used cars.</p>"""

    body = (
        html_section("Down Payment & Loan Amount", down_section)
        + html_section("Loan Scenarios", loan_table)
        + math_section
        + html_section("Term Analysis: Why I Chose 48 Months", analysis)
    )
    return title, html_page(title, body, 3)


def page_04(v: VehicleProfile) -> tuple:
    """Page 4: Insurance Decoded (20 pts)."""
    title = "Insurance: You're Required to Buy It, You Should Understand It"

    quote_table = html_table(
        ["Coverage Type", "My Coverage", "Oregon Minimum"],
        [
            ["Bodily Injury Liability", f"${v.liability_limits} (per person/per accident/property)", "$25/50/20"],
            ["Collision Deductible", fmt(v.collision_deductible_low), "Not required (but recommended)"],
            ["Comprehensive Deductible", fmt(v.comprehensive_deductible), "Not required"],
            ["Personal Injury Protection (PIP)", fmti(v.pip_coverage), "$15,000"],
            ["Uninsured/Underinsured Motorist (UM/UIM)", f"${v.um_uim_limits}", "$25/50"],
        ],
        caption="Insurance Coverage for 2015 Toyota Prius Two",
    )

    cost_section = f"""<p><strong>Monthly Premium (with $500 deductible):</strong> {fmt(v.monthly_premium_500)}<br>
<strong>Annual Cost:</strong> {fmt(v.monthly_premium_500)} x 12 = <strong>{fmt(v.annual_insurance)}</strong></p>
<p><em>Quote based on: 17-year-old on parent's policy, good student discount (3.0+ GPA),
Corvallis OR 97330, 12,000 miles/year, no accidents or violations. Added to existing
family policy with State Farm.</em></p>"""

    savings = v.deductible_savings_3yr
    ded_table = html_table(
        ["", "$500 Deductible", "$1,000 Deductible", "Difference"],
        [
            ["Monthly Premium", fmt(v.monthly_premium_500), fmt(v.monthly_premium_1000),
             fmt(v.monthly_premium_500 - v.monthly_premium_1000)],
            ["Annual Premium", fmt(v.annual_insurance), fmt(v.monthly_premium_1000 * 12),
             fmt((v.monthly_premium_500 - v.monthly_premium_1000) * 12)],
            ["3-Year Total (no claims)", fmt(v.monthly_premium_500 * 36), fmt(v.monthly_premium_1000 * 36),
             f"<strong>{fmt(savings)}</strong>"],
        ],
        caption="Deductible Comparison: $500 vs $1,000 over 3 Claim-Free Years",
    )

    ded_analysis = f"""<p>If I don't crash for three years, the $1,000 deductible saves me
<strong>{fmt(savings)}</strong> in premiums. But if I do get in an accident, I'd have to pay $500 more
out of pocket. Since the savings ({fmt(savings)}) are pretty close to that extra $500 risk, I'm going
with the $500 deductible for now. I'm a new driver so I'd rather pay a little more each month
and not get hit with a huge bill if something happens. Once I've got a few clean years under my belt
I'll switch to the $1,000 deductible.</p>"""

    evidence_html = """<h3>Evidence</h3>
<ul>
<li><strong>Quote Tool:</strong> State Farm online quote tool at <a href="https://www.statefarm.com/insurance/auto">statefarm.com</a></li>
<li><strong>Oregon Insurance Requirements:</strong> <a href="https://dfr.oregon.gov/insure/auto/required">Oregon Division of Financial Regulation</a></li>
<li><strong>Oregon minimum: 25/50/20 liability + $15,000 PIP required by law</strong></li>
</ul>"""

    body = (
        html_section("Quote Data: Coverage Levels", quote_table)
        + html_section("Cost Calculation", cost_section)
        + html_section("Deductible Comparison", ded_table + ded_analysis)
        + html_section("Evidence", evidence_html)
    )
    return title, html_page(title, body, 4)


def page_05(v: VehicleProfile) -> tuple:
    """Page 5: Total Cost of Ownership (25 pts)."""
    title = "The Car Payment Is the Smallest Part"

    payment_mo = v.preferred_monthly_payment
    ins_mo = v.monthly_premium_500
    fuel_mo = v.monthly_fuel_cost
    maint_mo = v.annual_maintenance_est / 12
    reg_mo = v.annual_registration / 12
    dep_mo = v.annual_depreciation / 12
    parking_mo = 0.0
    total_mo = payment_mo + ins_mo + fuel_mo + maint_mo + reg_mo + dep_mo + parking_mo

    tco_table = html_table(
        ["Cost Category", "Monthly", "Annual", "Notes"],
        [
            ["Loan Payment", fmt(payment_mo), fmt(payment_mo * 12), f"{v.preferred_term}-month term at {v.apr*100}% APR"],
            ["Insurance", fmt(ins_mo), fmt(v.annual_insurance), f"${v.liability_limits} liability, $500 deductible"],
            ["Fuel", fmt(fuel_mo), fmt(v.annual_fuel_cost), f"{v.annual_miles:,} mi / {v.mpg_combined} MPG x {fmt(v.gas_price)}/gal"],
            ["Maintenance", fmt(maint_mo), fmt(v.annual_maintenance_est), "Oil, filters, rotation, brake fluid"],
            ["Registration & Fees", fmt(reg_mo), fmt(v.annual_registration), f"Oregon 2-year: {fmt(v.registration_2yr)}"],
            ["Depreciation", fmt(dep_mo), fmt(v.annual_depreciation), "~8%/year (realistic for used vehicle)"],
            ["Parking / Tolls", "$0.00", "$0.00", "Free school parking, no tolls in Corvallis"],
            ["<strong>TOTAL</strong>", f"<strong>{fmt(total_mo)}</strong>", f"<strong>{fmt(total_mo * 12)}</strong>", ""],
        ],
        caption="Total Cost of Ownership: 2015 Toyota Prius Two",
    )

    per_mile = (total_mo * 12) / v.annual_miles
    summary = f"""<p><strong>Monthly TCO:</strong> {fmt(total_mo)}<br>
<strong>Annual TCO:</strong> {fmt(total_mo * 12)}<br>
<strong>Cost Per Mile:</strong> {fmt(total_mo * 12)} / {v.annual_miles:,} miles = <strong>{fmt(per_mile)}/mile</strong></p>"""

    # New vs Used comparison
    new_price = 32000  # 2025 Prius base
    new_payment = new_price * 0.80  # 80% financed
    r_new = 0.065 / 12  # higher rate for new
    new_mo_pay = new_payment * (r_new * (1 + r_new)**60) / ((1 + r_new)**60 - 1)
    new_ins = 185.00  # higher for new
    new_fuel_mo = fuel_mo * 0.90  # slightly better MPG
    new_maint = 30.00  # under warranty
    new_dep = (new_price * 0.20) / 12  # 20% year 1
    new_reg = reg_mo
    new_total = new_mo_pay + new_ins + new_fuel_mo + new_maint + new_dep + new_reg

    comparison = html_table(
        ["", "My 2015 Prius (Used)", "2025 Prius (New)"],
        [
            ["Purchase Price", fmti(v.purchase_price), fmti(new_price)],
            ["Monthly Payment", fmt(payment_mo), fmt(new_mo_pay)],
            ["Insurance", fmt(ins_mo), fmt(new_ins)],
            ["Fuel", fmt(fuel_mo), fmt(new_fuel_mo)],
            ["Maintenance", fmt(maint_mo), fmt(new_maint)],
            ["Depreciation", fmt(dep_mo), fmt(new_dep)],
            ["Registration", fmt(reg_mo), fmt(new_reg)],
            ["<strong>Monthly Total</strong>", f"<strong>{fmt(total_mo)}</strong>", f"<strong>{fmt(new_total)}</strong>"],
            ["<strong>Annual Total</strong>", f"<strong>{fmt(total_mo * 12)}</strong>", f"<strong>{fmt(new_total * 12)}</strong>"],
            ["<strong>5-Year Total</strong>", f"<strong>{fmti(total_mo * 60)}</strong>", f"<strong>{fmti(new_total * 60)}</strong>"],
        ],
        caption="5-Year New vs. Used Comparison",
    )

    savings_5yr = (new_total - total_mo) * 60
    reflection = f"""<p>The two things eating most of my money are the <strong>loan payment</strong>
({fmt(payment_mo)}/month) and <strong>insurance</strong> ({fmt(ins_mo)}/month). Together that's like
{((payment_mo + ins_mo) / total_mo * 100):.0f}% of everything. Gas is actually pretty cheap at
{fmt(fuel_mo)}/month because the Prius gets 50 MPG -- that's about half what I'd spend with the Civic
or Elantra.</p>

<p>The easiest way I could lower my costs is <strong>bumping my insurance deductible from $500 to $1,000</strong>
after a year of no accidents. That'd save me {fmt(v.monthly_premium_500 - v.monthly_premium_1000)}/month
({fmt((v.monthly_premium_500 - v.monthly_premium_1000) * 12)}/year). The new vs. used comparison is
pretty eye-opening too -- buying used saved me about <strong>{fmti(savings_5yr)}</strong> over 5 years.
That's a crazy amount of money just for not needing the newest model.</p>"""

    body = (
        html_section("Seven Cost Categories", tco_table + summary)
        + html_section("New vs. Used: 5-Year Comparison", comparison)
        + html_section("Reflection", reflection)
    )
    return title, html_page(title, body, 5)


def page_06(v: VehicleProfile) -> tuple:
    """Page 6: Tires & Safety (15 pts)."""
    title = "Four Patches of Rubber Between You and the Road"

    size_section = f"""<p><strong>Tire Size:</strong> {v.tire_size}<br>
<strong>Source:</strong> Door jamb placard (driver's side) and 2015 Toyota Prius Owner's Manual, page 397<br>
<strong>Load Index / Speed Rating:</strong> 89H (1,279 lbs per tire / 130 mph max)</p>
<p style="font-family: monospace; background: #f5f5f5; padding: 10px; border-radius: 4px;">
Decoding {v.tire_size} 89H:<br>
&nbsp;&nbsp;P = Passenger vehicle<br>
&nbsp;&nbsp;195 = Tire width in millimeters<br>
&nbsp;&nbsp;65 = Aspect ratio (sidewall height = 65% of width)<br>
&nbsp;&nbsp;R = Radial construction<br>
&nbsp;&nbsp;15 = Wheel diameter in inches<br>
&nbsp;&nbsp;89 = Load index (1,279 lbs per tire)<br>
&nbsp;&nbsp;H = Speed rating (up to 130 mph)
</p>"""

    tire_table = html_table(
        ["Detail", "Value"],
        [
            ["Brand", v.tire_brand],
            ["Model", v.tire_model],
            ["Type", v.tire_type],
            ["Price Per Tire", fmt(v.tire_price_each)],
            ["Set of 4", fmt(v.tire_set_price)],
            ["Treadwear Warranty", f"{v.tire_warranty_miles:,} miles"],
            ["Cost Per Mile", fmt(v.tire_cost_per_mile, "")],
        ],
        caption="Selected Tire: Michelin Defender T+H",
    )

    install = f"""<p><strong>Installation Estimate:</strong> {fmt(v.tire_install_each)} per tire at Les Schwab Tire Center, Corvallis<br>
<strong>Includes:</strong> Mounting, balancing, valve stems, and tire disposal<br>
<strong>Total Installed Cost:</strong> ({fmt(v.tire_price_each)} + {fmt(v.tire_install_each)}) x 4 = <strong>{fmt(v.tire_installed_total)}</strong></p>
<p><em>Source: Les Schwab Corvallis, 541-753-7251, quoted February 2026</em></p>"""

    rotation = f"""<p><strong>Manufacturer Recommendation:</strong> Every {v.tire_rotation_interval:,} miles
(2015 Prius Owner's Manual, Maintenance Schedule)<br>
<strong>My Annual Mileage:</strong> {v.annual_miles:,} miles<br>
<strong>Rotations Per Year:</strong> {v.annual_miles:,} / {v.tire_rotation_interval:,} = <strong>{v.tire_rotations_per_year:.1f} rotations/year</strong><br>
<strong>Cost:</strong> $0.00 per rotation (Les Schwab provides free lifetime rotation with tire purchase)</p>

<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
<tr style="background: #f5f5f5;"><th style="padding: 8px; text-align: left;">Month</th><th style="padding: 8px;">Approx. Mileage</th><th style="padding: 8px;">Action</th></tr>
<tr><td style="padding: 8px;">January</td><td style="padding: 8px; text-align: center;">85,000</td><td style="padding: 8px;">Rotation #1</td></tr>
<tr style="background: #f5f5f5;"><td style="padding: 8px;">June</td><td style="padding: 8px; text-align: center;">90,000</td><td style="padding: 8px;">Rotation #2</td></tr>
<tr><td style="padding: 8px;">November</td><td style="padding: 8px; text-align: center;">95,000</td><td style="padding: 8px;">Rotation #3 (check tread depth)</td></tr>
</table>"""

    body = (
        html_section("Tire Size Lookup", size_section)
        + html_section("Tire Selection", tire_table)
        + html_section("Installation Cost", install)
        + html_section("Rotation Schedule", rotation)
    )
    return title, html_page(title, body, 6)


def page_07(v: VehicleProfile) -> tuple:
    """Page 7: Routine Maintenance Schedule (15 pts)."""
    title = "The 3,000-Mile Myth"

    manual_src = """<p><strong>Owner's Manual:</strong> 2015 Toyota Prius Owner's Manual<br>
<strong>Source:</strong> <a href="https://www.toyota.com/owners/resources/warranty-owners-manuals/prius/2015">Toyota Owners: 2015 Prius Manual (PDF)</a><br>
<strong>Maintenance Schedule Section:</strong> Pages 399-412</p>"""

    svc_table = html_table(
        ["Service", "Type/Spec", "Interval", "Local Cost", "Times/Year", "Annual Cost"],
        [
            ["Oil Change", v.oil_type, f"Every {v.oil_change_interval:,} mi or 12 mo", fmt(v.oil_change_cost), f"{v.oil_changes_per_year:.1f}", fmt(v.annual_oil_cost)],
            ["Tire Rotation", "Front-to-rear pattern", f"Every {v.tire_rotation_interval:,} mi", "$0 (Les Schwab)", f"{v.tire_rotations_per_year:.1f}", "$0.00"],
            ["Coolant Flush", "Toyota Super Long-Life Coolant", f"Every {v.coolant_flush_interval:,} mi (first)", fmt(v.coolant_flush_cost), "Due at 100K", "$15.00*"],
            ["Transmission Fluid", "Toyota WS ATF (inspect)", "Inspect at 60,000 mi", "$0 (inspect only)", "Already past", "$0.00"],
            ["Brake Fluid", "DOT 3 or DOT 4", f"Every {v.brake_fluid_interval:,} mi or 3 yr", fmt(v.brake_fluid_cost), "0.4", fmt(v.brake_fluid_cost * 0.4)],
            ["Cabin Air Filter", "Standard particulate", f"Every {v.cabin_filter_interval:,} mi", fmt(v.cabin_filter_cost), "0.8", fmt(v.cabin_filter_cost * 0.8)],
            ["Engine Air Filter", "Standard panel filter", f"Every {v.engine_filter_interval:,} mi", fmt(v.engine_filter_cost), "0.4", fmt(v.engine_filter_cost * 0.4)],
            ["12V Battery Check", "Auxiliary battery", "Every 12 months", "$0 (free test)", "1.0", "$0.00"],
        ],
        caption="Manufacturer-Recommended Maintenance Schedule",
    )

    total_annual = v.annual_oil_cost + 0 + 15 + 0 + (v.brake_fluid_cost * 0.4) + (v.cabin_filter_cost * 0.8) + (v.engine_filter_cost * 0.4)
    cost_summary = f"""<p><em>*Coolant: {fmt(v.coolant_flush_cost)} service amortized over remaining 20K miles = ~$15/year equivalent</em></p>
<p><strong>Estimated Annual Maintenance Cost:</strong> <strong>{fmt(total_annual)}</strong></p>
<p>One cool thing about the Prius -- the hybrid system uses regenerative braking, so the brake pads last
way longer than a normal car (sometimes 100K+ miles). That saves a lot of money over time. The hybrid
battery itself doesn't need any maintenance, and in Oregon it's covered under an extended warranty
(10 years / 150,000 miles) because Oregon uses California emission standards.</p>"""

    body = (
        html_section("Owner's Manual Source", manual_src)
        + html_section("Service Intervals & Costs", svc_table + cost_summary)
    )
    return title, html_page(title, body, 7)


def page_08(v: VehicleProfile) -> tuple:
    """Page 8: Finding a Mechanic You Can Trust (15 pts)."""
    title = "Trust, But Verify"

    shop_table = html_table(
        ["", "Heartland Automotive", "Toyota of Corvallis", "Les Schwab Tire Center"],
        [
            ["Type", "Independent", "Dealership", "Chain (Tires & Basic Service)"],
            ["Address", "2275 NW 9th St, Corvallis", "400 NW 2nd St, Corvallis", "633 NW 9th St, Corvallis"],
            ["ASE Certified", "Yes (all technicians)", "Yes (Toyota Master Technicians)", "Yes (tire & alignment)"],
            ["Google Rating", "4.8 stars (200+ reviews)", "4.3 stars (350+ reviews)", "4.7 stars (180+ reviews)"],
            ["Negative Review Response", "Owner responds personally within 24 hrs", "Service manager responds, offers resolution", "Corporate template, offers callback"],
            ["Written Estimates", "Yes, always before work begins", "Yes, required by policy", "Yes, printed estimate"],
            ["Labor Rate", "~$95/hour", "~$135/hour", "Flat rate (tire services)"],
        ],
        caption="Three Repair Shops Evaluated",
    )

    rationale = """<p>I'm going to use <strong>Heartland Automotive</strong> as my main shop. They're independent,
all their mechanics are ASE certified, and they only charge $95/hour -- that's $40 less than the dealership.
They've got a 4.8 star rating on Google with over 200 reviews, which is the best of the three I looked at.
I also noticed the owner replies to every bad review personally, which tells me they actually care.
They give you a written estimate before they do anything too.</p>

<p>For anything related to the hybrid system (the battery, inverter, electric motor stuff) I'd go to
<strong>Toyota of Corvallis</strong> because they have the Toyota-specific scan tool called Techstream
that regular shops probably don't have. And for tires I'll go to <strong>Les Schwab</strong> -- when you
buy tires there you get free rotations, mounting, balancing, and flat repair for the life of the tires.
Can't beat that.</p>"""

    evidence_html = """<h3>Evidence</h3>
<ul>
<li><strong>Heartland Automotive:</strong> <a href="https://www.google.com/maps/place/Heartland+Automotive">Google Reviews</a></li>
<li><strong>Toyota of Corvallis:</strong> <a href="https://www.google.com/maps/place/Toyota+of+Corvallis">Google Reviews</a></li>
<li><strong>Les Schwab Corvallis:</strong> <a href="https://www.google.com/maps/place/Les+Schwab+Tire+Center">Google Reviews</a></li>
</ul>"""

    body = (
        html_section("Shop Research: Three Corvallis-Area Shops", shop_table)
        + html_section("Evaluation & Selection Rationale", rationale)
        + html_section("Evidence", evidence_html)
    )
    return title, html_page(title, body, 8)


def page_09(v: VehicleProfile) -> tuple:
    """Page 9: Pre-Purchase Inspection Checklist (20 pts)."""
    title = "What the Seller Won't Tell You"

    visual_items = [
        "Body panels: Check for uneven gaps, misaligned panels (sign of collision repair)",
        "Paint: Look for color mismatch between panels, orange peel texture, overspray on trim",
        "Rust: Check wheel wells, rocker panels, door bottoms, and underbody for bubbling or scale",
        "Tires: Measure tread depth with a penny (Lincoln's head visible = replace). Check for uneven wear",
        "Glass: Inspect windshield and all windows for chips, cracks, or delamination",
        "Lights: Test all headlights (low/high), taillights, turn signals, brake lights, reverse lights",
        "Fluid spots: Look under the car for oil, coolant (green/orange), or transmission fluid drips",
        "Interior seats: Check for excessive wear, tears, stains, or mismatched upholstery",
        "Dashboard warning lights: Turn key to ON (don't start). ALL lights should illuminate then turn off",
        "Odors: Sniff for mold/mildew (water leak), burning oil, sweet smell (coolant leak), or cigarette smoke",
        "Trunk/hatch: Check spare tire is present and inflated. Look for water stains or dampness",
        "Hybrid battery cooling vent: Check rear seat vent for debris/blockage (critical for Prius battery life)",
    ]

    test_items = [
        "Cold start: Arrive early, start engine when cold. Listen for unusual noises, check for exhaust smoke",
        "Idle: Engine should idle smooth. Hybrid system should cycle between gas and electric quietly",
        "Acceleration: Steady pull with no hesitation, jerking, or unusual vibration from 0-60 mph",
        "Braking: Firm pedal, no pulling to either side, no grinding or squealing, no ABS trigger on dry pavement",
        "Steering: Should track straight on a flat road with hands briefly removed. No play or wandering",
        "Highway speed: No vibration at 55-70 mph. Wind noise should be reasonable for the vehicle class",
        "A/C and heat: Both should blow cold/hot within 2 minutes. Check all fan speeds",
        "Radio and controls: Test all buttons, touchscreen, Bluetooth pairing, backup camera if equipped",
        "Transmission: CVT should be smooth with no lurching, whining, or delayed response",
        "Hybrid system transition: Gas-to-electric switch should be seamless. EV mode indicator should work",
    ]

    seller_questions = [
        "Why are you selling? (Watch for vague answers like 'just upgrading' -- ask follow-up questions)",
        "How many owners has this vehicle had? (Cross-check with Carfax. More owners = more unknowns)",
        "Do you have maintenance records? (Oil changes, major services. No records is a red flag)",
        "Has this vehicle ever been in an accident? (Ask directly. Even if they say no, verify with history report)",
        "Has the hybrid battery ever been replaced or serviced? (Original 2015 battery at 80K is fine, but ask)",
        "Are there any current warning lights, noises, or known issues? (Honest sellers disclose. Evasion = walk away)",
    ]

    history_section = """<p><strong>Vehicle History Verification Tools:</strong></p>
<ul>
<li><strong>NHTSA Recalls:</strong> <a href="https://www.nhtsa.gov/recalls">nhtsa.gov/recalls</a> -- Free VIN-specific recall search. Check for open (unfixed) recalls</li>
<li><strong>Carfax / AutoCheck:</strong> $25-$50 one-time report. Shows accident history, ownership count, service records, title status (clean/salvage/flood)</li>
<li><strong>NICB VINCheck:</strong> <a href="https://www.nicb.org/vincheck">nicb.org/vincheck</a> -- Free. Checks if vehicle was reported stolen or has a salvage/junk title</li>
<li><strong>OBD-II Scan:</strong> Ask your mechanic or use a $20 Bluetooth scanner. Check for stored and pending trouble codes. On a Prius, pay special attention to P0A80 (hybrid battery degradation) and any P3000-series codes</li>
</ul>
<p><strong>Key items to verify in reports:</strong></p>
<ul>
<li>Title status: Must be "Clean." Salvage, rebuilt, or flood titles = walk away</li>
<li>Odometer readings: Should show consistent mileage increases at each service visit</li>
<li>Accident history: Minor fender bender is OK if properly repaired. Structural/frame damage = walk away</li>
<li>Service history: Regular oil changes and maintenance indicate a cared-for vehicle</li>
</ul>"""

    format_note = """<p style="background: #fff3cd; padding: 12px; border-radius: 4px; border-left: 4px solid #ffc107;">
<strong>Printable Format:</strong> This checklist is designed to be printed and brought to a car viewing.
Each item has a checkbox for on-site use. Bring a pen, a flashlight, a tire depth gauge, and this checklist.
</p>"""

    body = (
        format_note
        + html_section("Visual Inspection (12 items)", html_checklist(visual_items))
        + html_section("Test Drive Checklist (10 items)", html_checklist(test_items))
        + html_section("Questions for the Seller (6 questions)", html_checklist(seller_questions))
        + html_section("Vehicle History Verification", history_section)
    )
    return title, html_page(title, body, 9)


def page_10(v: VehicleProfile) -> tuple:
    """Page 10: Roadside Emergencies (20 pts)."""
    title = "Stranded Is a Plan You Didn't Make"

    kit_items = [
        ("Reflective Warning Triangles (set of 3)", "Visibility", "Amazon", 12.99, "Legally required in some states. Makes your stopped vehicle visible from 500+ feet in darkness or rain"),
        ("LED Flashlight (500+ lumens)", "Visibility", "Amazon", 14.99, "Hands-free headlamp style preferred. Essential for nighttime tire changes or engine bay inspection"),
        ("Reflective Safety Vest", "Visibility", "Amazon", 8.99, "Makes you visible to passing traffic while working outside the car at night"),
        ("First Aid Kit (100-piece)", "First Aid", "Amazon", 17.99, "Bandages, gauze, antiseptic, gloves, emergency blanket. Covers minor injuries from broken glass or road rash"),
        ("Jumper Cables (12 ft, 6 gauge)", "Recovery", "AutoZone", 24.99, "Heavy-gauge cables reach between vehicles. 12V battery in Prius can be jumped like any car"),
        ("Tire Pressure Gauge (digital)", "Recovery", "AutoZone", 7.99, "Check pressure before long trips. Correct pressure (35 PSI front, 33 PSI rear on Prius) improves MPG and safety"),
        ("12V Phone Charger (USB-C + USB-A)", "Recovery", "Amazon", 11.99, "Dead phone = no GPS, no calls for help. Keep one permanently in the car"),
        ("Rain Poncho (2-pack)", "Recovery", "Amazon", 4.99, "Oregon weather. Changing a tire in the rain without a poncho is miserable"),
        ("Water Bottles (2-pack, 32 oz)", "First Aid", "Grocery Store", 2.99, "Hydration during long waits for roadside assistance. Also useful for cleaning wounds"),
        ("Emergency Mylar Blanket", "First Aid", "Amazon", 6.99, "Retains 90% of body heat. Compact enough to fit in a glovebox. Critical for winter breakdowns"),
        ("Work Gloves (leather palm)", "Recovery", "AutoZone", 7.99, "Protect hands from hot components, sharp edges, and road grime during tire changes"),
        ("Pen + Notepad", "Recovery", "Dollar Store", 2.00, "Document accident details, exchange information, write down tow truck ETA"),
    ]

    kit_rows = []
    total = 0
    for name, cat, source, price, reason in kit_items:
        kit_rows.append([name, cat, source, fmt(price), reason])
        total += price

    kit_table = html_table(
        ["Item", "Category", "Source", "Price", "Why Included"],
        kit_rows,
        caption="Emergency Kit Contents (12 items)",
    )

    budget = f"""<p><strong>Total Kit Cost: {fmt(total)}</strong></p>
<p>All items fit in a small duffel bag or plastic bin in the Prius hatch area.
The Prius has a compact spare tire under the rear cargo floor -- this kit sits on top of it,
always accessible without moving other cargo.</p>"""

    scenario1 = """<h3>Scenario 1: Flat Tire on a Two-Lane Road</h3>
<ol>
<li><strong>Signal and pull over</strong> as far right as safely possible. Turn on hazard lights immediately</li>
<li><strong>Put on reflective vest</strong> (Kit item #3) before exiting the vehicle</li>
<li><strong>Set up warning triangles</strong> (Kit item #1) -- one 10 feet behind, one 100 feet behind, one 200 feet behind your car</li>
<li><strong>Get the spare tire and jack</strong> from under the rear cargo floor. The Prius jack point is behind the front wheel or in front of the rear wheel on the pinch weld</li>
<li><strong>Loosen lug nuts</strong> (one turn each) BEFORE jacking up the car. Use the lug wrench from the vehicle toolkit</li>
<li><strong>Jack the car, swap tires</strong>. Hand-tighten lug nuts in a star pattern, then lower and torque to 76 ft-lbs</li>
<li><strong>Drive to the nearest tire shop</strong> -- spare is rated for max 50 mph / 50 miles. Head to Les Schwab for repair or replacement</li>
</ol>
<p><em>When to call for help: If you are on a highway with no shoulder, if traffic is too fast to safely exit, or if you do not have a usable spare. Call Oregon Highway Assistance at *677.</em></p>"""

    scenario2 = """<h3>Scenario 2: Dead Battery in a Parking Lot</h3>
<ol>
<li><strong>Identify the 12V battery location</strong> -- in the Prius, it is in the right rear of the cargo area (NOT under the hood). The hybrid HV battery is separate and cannot be jumped</li>
<li><strong>Get jumper cables</strong> (Kit item #5) and find a helper vehicle. Position them close enough for cables to reach</li>
<li><strong>Connect cables in order:</strong> Red to dead (+), Red to helper (+), Black to helper (-), Black to unpainted metal bolt on dead car (NOT the battery terminal)</li>
<li><strong>Start the helper vehicle</strong>, wait 2-3 minutes, then press the Prius POWER button. The hybrid system should initialize</li>
<li><strong>Remove cables in reverse order</strong>. Drive for at least 20 minutes to let the 12V battery recharge. Have the battery tested at AutoZone (free) within 48 hours</li>
</ol>
<p><em>When to call for help: If jumping does not work after 2 attempts, the 12V battery may be completely dead and need replacement (~$200-$250 for the Prius-specific AGM battery).</em></p>"""

    scenario3 = """<h3>Scenario 3: Minor Fender-Bender at an Intersection</h3>
<ol>
<li><strong>Check yourself and passengers for injuries</strong>. If anyone is hurt, call 911 immediately. Use the first aid kit (Kit item #4) for minor injuries only</li>
<li><strong>Move vehicles out of traffic</strong> if safe to do so. Turn on hazard lights. Put on reflective vest (Kit item #3)</li>
<li><strong>Call police</strong> if there are injuries, the other driver leaves, or damage exceeds $2,500 (Oregon reporting threshold)</li>
<li><strong>Document everything</strong> with your phone: damage to both cars (all angles), license plates, driver's licenses, insurance cards. Use pen and notepad (Kit item #12) as backup</li>
<li><strong>Exchange information:</strong> Name, phone, insurance company, policy number, driver's license number. Do NOT admit fault or apologize -- just exchange facts</li>
<li><strong>File a claim</strong> with your insurance within 24 hours. Provide photos and the police report number if applicable</li>
</ol>
<p><em>Oregon is a "fault" state -- the at-fault driver's insurance pays. Your collision coverage ($500 deductible) covers your repairs if the other driver is uninsured.</em></p>"""

    body = (
        html_section("Emergency Kit List", kit_table + budget)
        + html_section("Response Procedures", scenario1 + scenario2 + scenario3)
    )
    return title, html_page(title, body, 10)


def page_11(v: VehicleProfile) -> tuple:
    """Page 11: Warranties & Recalls (15 pts)."""
    title = "Free Repairs You Didn't Know You Had"

    warranty_table = html_table(
        ["Warranty Type", "Coverage Period", "Status (2026, ~92K mi)", "What It Covers"],
        [
            ["Bumper-to-Bumper", "3 years / 36,000 miles", "<span style='color: red;'>EXPIRED</span>", "Everything except wear items (brakes, tires, wiper blades)"],
            ["Powertrain", "5 years / 60,000 miles", "<span style='color: red;'>EXPIRED</span>", "Engine, transmission, drivetrain components"],
            ["Corrosion (body panels)", "5 years / unlimited miles", "<span style='color: red;'>EXPIRED</span>", "Body panel rust-through from the inside out"],
            ["Federal Emissions", "8 years / 80,000 miles", "<span style='color: #e67e22;'>AT THRESHOLD</span>", "Catalytic converter, ECU, onboard diagnostics. Check exact VIN manufacture date"],
            ["Hybrid Battery (CA/OR)", "10 years / 150,000 miles", "<span style='color: #e67e22;'>AT THRESHOLD</span>", "HV battery pack, hybrid control module, inverter. Oregon adopts CA emission standards. 10 yr from original in-service date (~2015) = ~2025. Expired by date, still under mileage (92K &lt; 150K). Check exact VIN date -- may have just expired"],
        ],
        caption="Warranty Status: 2015 Toyota Prius (purchased 2025 at 80,000 miles)",
    )

    warranty_note = """<p style="background: #fff3cd; padding: 12px; border-radius: 4px; border-left: 4px solid #e67e22;">
<strong>Big deal here:</strong> Oregon uses California emission standards, so the hybrid battery warranty
is <strong>10 years / 150,000 miles</strong> instead of the regular federal 8yr/80K. But here's the catch --
the 10 years started when the car was first sold new (around 2015), not when I bought it. So the time
part of the warranty probably already ran out around 2025, even though I'm only at ~92K miles which is way
under the 150K limit. It expires based on whichever comes first -- date or miles.
<br><br><strong>What I need to do:</strong> Call Toyota at 1-800-331-4331 and give them my VIN to find out
the exact date the car was first sold. If it was sold late in 2015, I might still have a few months left
in early 2026. This is really important to check because the hybrid battery costs $2,500-$4,000 to replace
and that's the most expensive thing on the whole car.
</p>"""

    recall_section = """<p><strong>NHTSA Recall Search Results for VIN: JTDKN3DU5F0123456</strong></p>
<p><em>Searched at: <a href="https://www.nhtsa.gov/recalls">nhtsa.gov/recalls</a></em></p>
<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
<tr style="background: #2980b9; color: white;">
<th style="padding: 8px;">Campaign #</th><th style="padding: 8px;">Description</th><th style="padding: 8px;">Status</th></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;">16V-651</td>
<td style="padding: 8px; border-bottom: 1px solid #eee;">Curtain shield airbag inflator may produce excessive internal pressure</td>
<td style="padding: 8px; border-bottom: 1px solid #eee;">Verify with dealer (Takata airbag recall)</td></tr>
<tr style="background: #f8f9fa;"><td style="padding: 8px; border-bottom: 1px solid #eee;">14V-700</td>
<td style="padding: 8px; border-bottom: 1px solid #eee;">Hybrid system software may cause vehicle to stall</td>
<td style="padding: 8px; border-bottom: 1px solid #eee;">Likely completed (software update -- verify at dealer)</td></tr>
</table>
<p><strong>Action:</strong> Contact Toyota of Corvallis with VIN to verify completion status of both recalls.
Recall repairs are always free regardless of warranty status or mileage.</p>"""

    tsb_section = """<p><strong>Technical Service Bulletin (TSB) Search:</strong></p>
<ul>
<li><strong>TSB-0100-15:</strong> Inverter coolant pump noise -- Toyota may replace under goodwill if reported early</li>
<li><strong>TSB-0087-14:</strong> EGR valve carbon buildup causing rough idle -- cleaning covered under emissions warranty at qualifying mileage</li>
<li><strong>TSB-0152-15:</strong> 12V battery drain in cold weather -- software update available at dealer</li>
</ul>
<p><em>TSBs aren't the same as recalls -- they're not mandatory. But if you ask the dealer about them, sometimes they'll fix it for free or cheap as a "goodwill" thing, especially if you're close to a warranty limit. It never hurts to ask.</em></p>"""

    glovebox = """<div style="background: #f5f5f5; padding: 15px; border: 2px solid #333; border-radius: 4px; font-family: monospace; font-size: 0.9em;">
<p style="text-align: center; font-weight: bold; font-size: 1.1em; border-bottom: 2px solid #333; padding-bottom: 8px;">
GLOVEBOX WARRANTY SUMMARY -- 2015 TOYOTA PRIUS TWO</p>
<p><strong>VIN:</strong> JTDKN3DU5F0123456<br>
<strong>Owner:</strong> [Student Name] | <strong>Purchase Date:</strong> 2025 | <strong>Purchase Mileage:</strong> 80,000</p>
<table style="width: 100%; font-size: 0.85em;">
<tr><td>Bumper-to-Bumper:</td><td style="color: red;">EXPIRED (3yr/36K)</td></tr>
<tr><td>Powertrain:</td><td style="color: red;">EXPIRED (5yr/60K)</td></tr>
<tr><td>Emissions (Federal):</td><td style="color: orange;">CHECK -- 8yr/80K threshold</td></tr>
<tr><td>Hybrid Battery (OR/CA):</td><td style="color: orange;"><strong>CHECK -- 10yr/150K (date ~expired, mileage OK)</strong></td></tr>
</table>
<p style="margin-top: 10px;"><strong>Open Recalls:</strong> Verify 16V-651 (airbag) and 14V-700 (hybrid software) with dealer<br>
<strong>Dealer Contact:</strong> Toyota of Corvallis, 541-757-1616</p>
</div>"""

    body = (
        html_section("Recall Check (NHTSA VIN Lookup)", recall_section)
        + html_section("Warranty Coverage", warranty_table + warranty_note)
        + html_section("TSB Research", tsb_section)
        + html_section("One-Page Glovebox Summary", glovebox)
    )
    return title, html_page(title, body, 11)


def page_12(v: VehicleProfile) -> tuple:
    """Page 12: Negotiation Strategy (20 pts)."""
    title = "The Word 'No' Is Worth Thousands"

    research = f"""<p><strong>Edmunds True Market Value:</strong> $11,800 (private party, good condition, 80K miles, Corvallis OR)<br>
<strong>KBB Private Party Value:</strong> $11,200 - $13,400 range (fair to good condition)<br>
<strong>Cross-Check Result:</strong> Both sources agree on approximately $11,500 - $12,200 for this vehicle in good condition</p>
<p><em>Sources:</em></p>
<ul>
<li><a href="https://www.edmunds.com/toyota/prius/2015/appraisal/">Edmunds 2015 Prius Appraisal</a></li>
<li><a href="https://www.kbb.com/toyota/prius/2015/">KBB 2015 Prius Values</a></li>
</ul>"""

    targets = f"""<p><strong>Opening Offer:</strong> $10,500</p>
<ul>
<li>About 10% below Edmunds TMV. Gives room to negotiate up while staying under fair market value</li>
<li>Justified by: approaching 80K miles (federal emissions warranty threshold), tires will need replacement within 15K miles (~$650 cost), and 12V auxiliary battery is original (9+ years old, replacement ~$200)</li>
</ul>
<p><strong>Walk-Away Price:</strong> $12,500</p>
<ul>
<li>Above KBB midpoint but still within the fair range. I would not pay more than this because at $12,500+ I could find a similar Prius with fewer miles or a newer model year</li>
<li>The asking price of {fmti(v.purchase_price)} is at the high end of fair. The goal is to negotiate down to $11,000-$11,500</li>
</ul>"""

    scripts = """<p><strong>Three things I'd actually say to the seller:</strong></p>
<ol>
<li style="margin-bottom: 12px;"><em>"I looked this car up on Edmunds and KBB and both say a 2015 Prius Two with 80K miles should be
around $11,200 to $12,200. I can do $10,500 today and I've got a cashier's check ready."</em>
<br><small>Why: Shows I did my homework, starts low so there's room to negotiate, and the cashier's check shows I'm serious.</small></li>
<li style="margin-bottom: 12px;"><em>"It's at 80,000 miles so the emissions warranty is basically used up, and the tires are gonna need
replacing pretty soon -- that's about $650 I'll have to spend. I'm factoring that into what I can pay."</em>
<br><small>Why: These are real upcoming costs I can prove, and it gives me a reason to offer less.</small></li>
<li style="margin-bottom: 12px;"><em>"It looks like you've taken good care of it, I can see that from the records. I've got financing
set up through Oregon State Credit Union for up to $10,000. Is there a price that works within that?"</em>
<br><small>Why: Saying something nice about the car keeps things friendly, and mentioning my loan limit sets a ceiling without being rude about it.</small></li>
</ol>"""

    walkaway = """<p><strong>Walk-Away Plan:</strong></p>
<p>If they won't go below $12,500, here's what I'd say:</p>
<blockquote style="background: #f5f5f5; padding: 12px; border-left: 4px solid #2980b9; margin: 10px 0;">
"Thanks for showing me the car, it's really nice. It's just more than I can do right now at that
price. I'm looking at a couple other cars this weekend too. If you'd take $11,500, here's my number."
</blockquote>
<p><strong>What I would do next:</strong></p>
<ul>
<li>Leave my phone number so they know I'm legit but not desperate</li>
<li>Go actually look at the Civic and Elantra from Page 1</li>
<li>Wait a couple days. A lot of private sellers will call back if nobody else shows up</li>
<li>If they don't call, I'd come back and offer $12,000 as my absolute max -- meet in the middle</li>
</ul>"""

    body = (
        html_section("Market Research", research)
        + html_section("Price Targets", targets)
        + html_section("Negotiation Phrases", scripts)
        + html_section("Walk-Away Plan", walkaway)
    )
    return title, html_page(title, body, 12)


def page_13(v: VehicleProfile) -> tuple:
    """Page 13: Your Driving Record (15 pts)."""
    title = "Every Mile Is on Your Record"

    ins_mo = v.monthly_premium_500
    violations = [
        ("Speeding (11-20 mph over)", "$225", "20-30%", fmt(ins_mo * 0.25), "3 years"),
        ("Running a Red Light", "$265", "18-25%", fmt(ins_mo * 0.215), "3 years"),
        ("Distracted Driving (phone)", "$265 first / $440 second", "20-30%", fmt(ins_mo * 0.25), "3 years"),
        ("Reckless Driving", "Up to $5,000 + 1 year jail", "40-60%", fmt(ins_mo * 0.50), "5+ years"),
        ("DUI (first offense)", "$1,000 min fine + license suspension", "75-100%+", fmt(ins_mo * 0.90), "5+ years (lifetime OR record)"),
    ]

    vio_table = html_table(
        ["Violation", "Oregon Base Fine", "Insurance Increase", "My Monthly Increase", "Surcharge Duration"],
        violations,
        caption="Five Oregon Traffic Violations and Their True Cost",
    )

    # 3-year speeding cost calculation
    fine = 225
    pct_increase = 0.25
    monthly_increase = ins_mo * pct_increase
    insurance_36mo = monthly_increase * 36
    total_3yr = fine + insurance_36mo
    multiplier = total_3yr / fine

    calc_section = f"""<h3>3-Year Cost of a Speeding Ticket (11-20 mph over)</h3>
<table style="width: 100%; border-collapse: collapse; margin: 10px 0;">
<tr style="background: #f5f5f5;"><td style="padding: 8px;"><strong>Court Fine:</strong></td><td style="padding: 8px;">{fmt(fine)}</td></tr>
<tr><td style="padding: 8px;"><strong>Insurance Increase:</strong></td><td style="padding: 8px;">{fmt(ins_mo)} x 25% = {fmt(monthly_increase)}/month increase</td></tr>
<tr style="background: #f5f5f5;"><td style="padding: 8px;"><strong>36-Month Insurance Surcharge:</strong></td><td style="padding: 8px;">{fmt(monthly_increase)} x 36 months = <strong>{fmt(insurance_36mo)}</strong></td></tr>
<tr><td style="padding: 8px;"><strong>Defensive Driving Course (optional):</strong></td><td style="padding: 8px;">$40 (Oregon-approved, can dismiss ticket once per 5 years)</td></tr>
<tr style="background: #e8f5e9;"><td style="padding: 8px;"><strong>TOTAL 3-YEAR COST:</strong></td><td style="padding: 8px;"><strong>{fmt(total_3yr)}</strong> ({multiplier:.1f}x the base fine)</td></tr>
</table>
<p>A $225 speeding ticket actually costs <strong>{fmt(total_3yr)}</strong> over three years -- that is
a <strong>{multiplier:.1f}x multiplier</strong>. The insurance surcharge alone ({fmt(insurance_36mo)})
is {insurance_36mo/fine:.1f} times the original fine.</p>"""

    commitment = f"""<p>Here's what I'm going to do to keep my record clean (and my wallet intact):</p>
<ol>
<li><strong>Use cruise control on the highway.</strong> It's easy to accidentally go 15 over without
realizing it, and that one ticket would cost me {fmt(total_3yr)} over three years. That's almost two
months of car expenses gone.</li>
<li><strong>Phone goes in the glovebox before I start driving.</strong> Oregon's distracted driving fine
is $265, plus my insurance would go up about 25%. Over three years that's more than $1,500. And if
you're under 18, ANY phone use while driving is illegal in Oregon -- even hands-free.</li>
<li><strong>Keep a 4-second following distance.</strong> Even if someone else hits you, filing a claim
on your own collision insurance can still make your rates go up. Not worth it.</li>
<li><strong>Never drive after drinking. Period.</strong> A DUI in Oregon costs $10,000-$20,000+ when
you add up the fines, lawyer, getting your license back, SR-22 insurance, and the ignition interlock
thing. That's more than my whole car is worth.</li>
<li><strong>Take a defensive driving course this year.</strong> It's only $30-$50 and in Oregon you can
use it to get one ticket dismissed every 5 years. Some insurance companies also give you a discount for
finishing the course.</li>
</ol>"""

    body = (
        html_section("Oregon Violation Research", vio_table)
        + html_section("3-Year Cost Calculation", calc_section)
        + html_section("Safe Driving Commitment", commitment)
    )
    return title, html_page(title, body, 13)


def page_14(v: VehicleProfile) -> tuple:
    """Page 14: Depreciation & Selling (20 pts)."""
    title = "The Breakeven Point"

    current_value = v.depreciation_value_at_year(1)
    current_miles = v.mileage_at_purchase + v.annual_miles

    value_section = f"""<p><strong>KBB Private Party Value (today, ~{current_miles:,} miles):</strong>
<strong>{fmti(current_value)}</strong></p>
<p><em>Source: <a href="https://www.kbb.com/toyota/prius/2015/">KBB 2015 Toyota Prius Two, Good condition, {current_miles:,} miles, Corvallis OR</a></em></p>
<p>It's been about a year since I bought it for {fmti(v.purchase_price)}, and it's already lost around
{fmti(v.purchase_price - current_value)} in value ({v.depreciation_yr1_pct*100:.0f}%). I'm using the
depreciation rates from the lesson (20% year 1, 15% years 2-3, 10% years 4-5, 5-7% after). These are
honestly a little harsh for a used car since used cars don't drop as fast as new ones, but that's what
the lesson says to use so I'm going with it.</p>"""

    dep_rows = []
    for yr in [1, 3, 5, 7, 10]:
        val = v.depreciation_value_at_year(yr)
        miles = v.mileage_at_purchase + (v.annual_miles * yr)
        dep_rows.append([
            f"Year {yr}",
            f"{miles:,}",
            fmti(val),
            fmti(v.purchase_price - val) if yr <= 1 else fmti(v.depreciation_value_at_year(yr - 1) - val),
        ])

    dep_table = html_table(
        ["Ownership Year", "Est. Mileage", "Projected Value", "Year-Over-Year Loss"],
        dep_rows,
        caption="Depreciation Projection Using Lesson Rates (20%/15%/10%/6% from $12,000 purchase)",
    )

    # Find when $2000 repair > 50% of value
    threshold_year = 10  # fallback
    threshold_value = v.depreciation_value_at_year(10)
    for yr in range(1, 15):
        val = v.depreciation_value_at_year(yr)
        if 2000 > val * 0.50:
            threshold_year = yr
            threshold_value = val
            break

    repair_section = f"""<p><strong>The 50% Rule:</strong> If a single repair costs more than half of what
your car is worth, it's time to think about getting a different car.</p>
<p><strong>So when does that happen for me?</strong></p>
<p>A $2,000 repair hits 50% when the car is worth $4,000 or less. Looking at my depreciation table,
that happens around <strong>Year {threshold_year}</strong> when the car would be worth about
<strong>{fmti(threshold_value)}</strong> with roughly
<strong>{v.mileage_at_purchase + (v.annual_miles * threshold_year):,} miles</strong> on it. So basically,
once I'm past that point a major repair might not be worth it.</p>"""

    plan_miles = v.mileage_at_purchase + (v.annual_miles * 6)
    plan_value = v.depreciation_value_at_year(6)
    plan = f"""<p>My plan is to keep this Prius for <strong>5-6 years</strong> and sell it around
<strong>{plan_miles:,} miles</strong>. At that point it should still be worth about {fmti(plan_value)}
and I'd be selling well before any major repairs start costing more than the car is worth.</p>

<p><strong>The sweet spot:</strong> Years 1 through 6. After that, big stuff starts to come up --
the hybrid battery (if the warranty is done), the catalytic converter, suspension parts -- and those
repairs could easily cost more than 50% of what the car is worth at that point.</p>

<p><strong>When I'd sell:</strong> Around year 5-6, or sooner if I start spending more on repairs in a
year than I'd spend on monthly payments for a different car.</p>

<p><strong>How I would sell:</strong> Private party sale through Craigslist, Facebook Marketplace, or
Toyota Prius owner forums. Private party value is typically 15-25% higher than trade-in. I would sell
in spring/summer when demand for fuel-efficient cars peaks (gas prices typically rise). I would
prepare by detailing the car, gathering all maintenance records, and pricing it at KBB private party
value for my zip code.</p>"""

    body = (
        html_section("Current Value", value_section)
        + html_section("Depreciation Projection", dep_table)
        + html_section("Repair Threshold Calculation", repair_section)
        + html_section("Long-Term Ownership Plan", plan)
    )
    return title, html_page(title, body, 14)


def page_15(v: VehicleProfile) -> tuple:
    """Page 15: EV vs Gas Comparison (25 pts)."""
    title = "The Drivetrain Is Changing"

    baseline = f"""<p><strong>My Portfolio Vehicle (Hybrid Baseline):</strong> {v.full_name}</p>
<ul>
<li>Purchase Price: {fmti(v.purchase_price)}</li>
<li>Fuel Economy: {v.mpg_combined} MPG combined (hybrid)</li>
<li>Annual Fuel Cost: {v.annual_miles:,} mi / {v.mpg_combined} MPG x {fmt(v.gas_price)}/gal = <strong>{fmt(v.annual_fuel_cost)}</strong></li>
<li>Annual Maintenance: {fmt(v.annual_maintenance_est)}</li>
</ul>
<p><em>Note: Since my Prius is already a hybrid, I'm comparing it against both a regular gas car (Corolla)
and a full electric (Leaf) so you can see the difference across all three types.</em></p>"""

    ev_info = f"""<p><strong>EV Equivalent:</strong> {v.ev_year} {v.ev_make} {v.ev_model}</p>
<ul>
<li>Purchase Price: {fmti(v.ev_price)} (used, comparable age/condition)</li>
<li>Range: {v.ev_range_miles} miles per charge (EPA rated -- real-world ~70 miles in Oregon winter)</li>
<li>Efficiency: {v.ev_kwh_per_mile} kWh/mile</li>
<li>Annual Electricity Cost: {v.annual_miles:,} mi x {v.ev_kwh_per_mile} kWh/mi x {fmt(v.ev_electricity_rate)}/kWh = <strong>{fmt(v.annual_miles * v.ev_kwh_per_mile * v.ev_electricity_rate)}</strong></li>
<li>Annual Maintenance: {fmt(v.ev_annual_maintenance)}</li>
<li><em>Source: <a href="https://www.edmunds.com/nissan/leaf/2015/">Edmunds 2015 Nissan Leaf SV</a></em></li>
</ul>"""

    # 5-year TCO calculation
    prius_fuel_5yr = v.annual_fuel_cost * 5
    prius_maint_5yr = v.annual_maintenance_est * 5
    prius_ins_5yr = v.annual_insurance * 5
    prius_resale = v.depreciation_value_at_year(5)
    prius_tco = v.purchase_price + prius_fuel_5yr + prius_maint_5yr + prius_ins_5yr - prius_resale

    ev_fuel_5yr = v.annual_miles * v.ev_kwh_per_mile * v.ev_electricity_rate * 5
    ev_maint_5yr = v.ev_annual_maintenance * 5
    ev_ins_5yr = v.ev_insurance_monthly * 12 * 5
    ev_resale = v.ev_resale_5yr
    ev_tco = v.ev_price + ev_fuel_5yr + ev_maint_5yr + ev_ins_5yr - ev_resale

    gas_fuel_5yr = (v.annual_miles / v.gas_comp_mpg) * v.gas_price * 5
    gas_maint_5yr = v.gas_comp_maintenance * 5
    gas_ins_5yr = v.gas_comp_insurance_monthly * 12 * 5
    gas_resale = v.gas_comp_resale_5yr
    gas_tco = v.gas_comp_price + gas_fuel_5yr + gas_maint_5yr + gas_ins_5yr - gas_resale

    tco_table = html_table(
        ["Category", f"{v.gas_comp_year} {v.gas_comp_make} {v.gas_comp_model} (Gas)", f"{v.short_name} (Hybrid)", f"{v.ev_year} {v.ev_make} {v.ev_model} (EV)"],
        [
            ["Purchase Price", fmti(v.gas_comp_price), fmti(v.purchase_price), fmti(v.ev_price)],
            ["5-Year Fuel/Electricity", fmt(gas_fuel_5yr), fmt(prius_fuel_5yr), fmt(ev_fuel_5yr)],
            ["5-Year Maintenance", fmt(gas_maint_5yr), fmt(prius_maint_5yr), fmt(ev_maint_5yr)],
            ["5-Year Insurance", fmt(gas_ins_5yr), fmt(prius_ins_5yr), fmt(ev_ins_5yr)],
            ["Estimated Resale (Year 5)", f"-{fmti(gas_resale)}", f"-{fmti(prius_resale)}", f"-{fmti(ev_resale)}"],
            ["<strong>5-Year TCO</strong>", f"<strong>{fmti(gas_tco)}</strong>", f"<strong>{fmti(prius_tco)}</strong>", f"<strong>{fmti(ev_tco)}</strong>"],
        ],
        caption="5-Year Total Cost of Ownership: Gas vs. Hybrid vs. EV",
    )

    ev_annual_fuel = v.annual_miles * v.ev_kwh_per_mile * v.ev_electricity_rate
    analysis = f"""<p><strong>Which one's cheapest over 5 years?</strong></p>
<p>The {v.ev_year} Nissan Leaf actually wins at {fmti(ev_tco)}, then my Prius at {fmti(prius_tco)},
and the Corolla at {fmti(gas_tco)}. The Leaf is cheap mostly because used ones have dropped a ton in
price (people are scared of the short range) and electricity is way cheaper than gas --
{fmt(ev_annual_fuel)}/year versus {fmt(v.annual_fuel_cost)}/year for my Prius and
{fmt((v.annual_miles / v.gas_comp_mpg) * v.gas_price)}/year for the Corolla.</p>

<p><strong>Would I actually want a Leaf though?</strong></p>
<p>Honestly, no. The 2015 Leaf only gets 84 miles on a charge, and in cold Oregon winters that drops
to like 65-70. Corvallis to the coast is 45 miles round trip, and Portland is 85 miles one way -- I
wouldn't even make it there without stopping to charge, and there aren't many fast chargers on Highway
20 or 34. My Prius gets 50 MPG and I can fill up in 5 minutes at any gas station. No range anxiety.</p>

<p><strong>What would make an EV work for me?</strong></p>
<p>It'd need at least 200 miles of real range (not just what the sticker says) so I could get to Portland
and back in the winter. That means a newer EV like a 2022+ Leaf or Bolt, which would be $15,000-$20,000
used. There'd also need to be more fast chargers between here and the coast. And I'd need somewhere to
plug in at night -- if I'm renting an apartment with no garage, that's a problem. For now the Prius
makes the most sense for me.</p>"""

    body = (
        html_section("Gas Vehicle Baseline", baseline)
        + html_section("EV Equivalent", ev_info)
        + html_section("5-Year TCO Comparison", tco_table)
        + html_section("Written Analysis", analysis)
    )
    return title, html_page(title, body, 15)


def page_16(v: VehicleProfile) -> tuple:
    """Page 16: Portfolio Capstone Assembly (50 pts)."""
    title = "Your Owner's Manual for Owning a Car"

    # Cross-page consistency verification
    consistency = html_table(
        ["Data Point", "Source Page", "Value", "Matches?"],
        [
            ["Purchase Price", "Pages 1, 2, 3, 5, 12, 14", fmti(v.purchase_price), "Yes"],
            ["Monthly Insurance", "Pages 4, 5", fmt(v.monthly_premium_500), "Yes"],
            ["Monthly Loan Payment", "Pages 3, 5", fmt(v.preferred_monthly_payment), "Yes"],
            ["Annual Fuel Cost", "Pages 5, 15", fmt(v.annual_fuel_cost), "Yes"],
            ["Tire Size", "Pages 6, 9", v.tire_size, "Yes"],
            ["Oil Type", "Pages 7, 9", v.oil_type, "Yes"],
            ["Annual Mileage", "Pages 5, 6, 7, 13, 14, 15", f"{v.annual_miles:,}", "Yes"],
            ["MPG Combined", "Pages 1, 5, 15", str(v.mpg_combined), "Yes"],
            ["Annual Maintenance", "Pages 5, 7", fmt(v.annual_maintenance_est), "Yes"],
        ],
        caption="Cross-Page Numerical Consistency Check",
    )

    peer_review = """<h3>Peer Review Checklist</h3>
<p><em>Exchange portfolios with a classmate. Complete this checklist and provide written feedback.</em></p>
<ol>
<li><input type="checkbox" disabled> All 15 portfolio pages are present and in order</li>
<li><input type="checkbox" disabled> Title page includes student name, vehicle, and date</li>
<li><input type="checkbox" disabled> Numbers are consistent across pages (insurance matches TCO, financing matches purchase price)</li>
<li><input type="checkbox" disabled> Evidence is included on pages that require it (links, screenshots, or citations)</li>
<li><input type="checkbox" disabled> Calculations show work (not just final answers)</li>
<li><input type="checkbox" disabled> Written sections are specific to the student's vehicle (not generic copy-paste)</li>
<li><input type="checkbox" disabled> Formatting is consistent (same font, headings, table style throughout)</li>
</ol>
<p><strong>Written Feedback to Classmate:</strong></p>
<div style="background: #f5f5f5; padding: 12px; border: 1px solid #ddd; border-radius: 4px; min-height: 80px;">
<p><em>"Your portfolio for the 2017 Honda Accord is thorough -- I liked how you broke down the F&I
products in Page 3 and explained exactly why you would decline each one. One thing I noticed:
your insurance premium on Page 4 ($165/month) does not match the insurance line in your TCO table
on Page 5 ($155/month). You might want to double-check which number is correct and update both
pages. Your emergency kit on Page 10 was creative -- I had not thought to include a battery-powered
tire inflator. Overall, this is solid work."</em></p>
</div>"""

    reflection = f"""<h3>Final Reflection</h3>

<p><strong>The Surprise:</strong></p>
<p>I had no idea insurance was going to be that expensive. {fmt(v.monthly_premium_500)}/month is my
second biggest cost after the car payment itself, and unlike the loan it never goes away. Before doing
all this I honestly thought the monthly payment was basically the whole cost of having a car. Turns out
the payment is only like {(v.preferred_monthly_payment / v.tco_monthly * 100):.0f}% of what I actually
spend each month. The rest -- insurance, gas, maintenance, depreciation, registration -- you don't
really see it until you sit down and add it all up like I did for Page 5.</p>

<p><strong>The Change:</strong></p>
<p>I used to think a "good deal" on a car just meant getting a low sticker price. Now I know my
{fmti(v.purchase_price)} Prius is actually going to cost me about {fmti(v.tco_annual * 5)} over five
years when you count everything. That's a lot more than I expected. I also figured out that going with
the Prius instead of something that gets 32 MPG saves me roughly
{fmti(((12000/32)*v.gas_price - v.annual_fuel_cost) * 5)} just in gas over five years. I'm definitely
sticking with the 20/4/10 rule going forward -- 20% down, 48 months max on the loan, total car costs
under 10% of what I make.</p>

<p><strong>The Keeper:</strong></p>
<p>The negotiation stuff from Page 12 is what I'll use the most. Before this I would've just shown up
and either paid what they asked or tried to lowball without any real reason. Now I know how to look up
what the car is actually worth, decide ahead of time what I'll walk away at, and say specific things
backed by real numbers. "I need to think about it" might be the most powerful thing you can say when
buying a car. I'm also going to print out that glovebox warranty card from Page 11 and actually keep
it in my glovebox -- if something goes wrong with the hybrid battery, knowing the warranty status could
save me thousands.</p>"""

    toc = """<h3>Portfolio Table of Contents</h3>
<table style="width: 100%; border-collapse: collapse;">
<tr style="background: #2980b9; color: white;"><th style="padding: 6px;">Page</th><th style="padding: 6px;">Title</th><th style="padding: 6px;">Points</th></tr>"""
    page_titles = [
        ("Title Page", "--"),
        ("01: Vehicle Selection & Comparison", "20"),
        ("02: Window Sticker & VIN Decode", "20"),
        ("03: Financing Comparison", "20"),
        ("04: Insurance Coverage & Deductible Strategy", "20"),
        ("05: Total Cost of Ownership", "25"),
        ("06: Tire Specifications & Replacement", "15"),
        ("07: Maintenance Schedule", "15"),
        ("08: Mechanic Selection", "15"),
        ("09: Pre-Purchase Inspection Checklist", "20"),
        ("10: Emergency Kit & Procedures", "20"),
        ("11: Warranties & Recalls", "15"),
        ("12: Negotiation Strategy", "20"),
        ("13: Driving Record & Commitments", "15"),
        ("14: Depreciation & Long-Term Plan", "20"),
        ("15: EV/Hybrid vs Gas Comparison", "25"),
        ("16: Capstone (this page)", "50"),
    ]
    for pt, pts in page_titles:
        toc += f'<tr><td style="padding: 4px 6px; border-bottom: 1px solid #eee;">{pt}</td><td style="padding: 4px 6px; border-bottom: 1px solid #eee;">{pts}</td></tr>'
    toc += "</table>"

    body = (
        html_section("Portfolio Table of Contents", toc)
        + html_section("Cross-Page Consistency Verification", consistency)
        + html_section("Peer Review", peer_review)
        + html_section("Final Reflection", reflection)
    )
    return title, html_page(title, body, 16)


# ══════════════════════════════════════════════════════════════
# PAGE REGISTRY & ASSIGNMENT MAPPING
# ══════════════════════════════════════════════════════════════

# Maps page number -> (generator_fn, Canvas assignment name)
# Assignment names must match EXACTLY what's in canvas_autos_rubrics.py
PAGE_REGISTRY = {
    1:  (page_01, "01 \u2014 Your First Car Is Probably a Bad Deal"),
    2:  (page_02, "02 \u2014 Everything on the Sticker They Hope You Won\u2019t Read"),
    3:  (page_03, "03 \u2014 The Most Expensive Room in the Dealership"),
    4:  (page_04, "04 \u2014 Insurance: You\u2019re Required to Buy It, You Should Understand It"),
    5:  (page_05, "05 \u2014 The Car Payment Is the Smallest Part"),
    6:  (page_06, "06 \u2014 Four Patches of Rubber Between You and the Road"),
    7:  (page_07, "07 \u2014 The 3,000-Mile Myth"),
    8:  (page_08, "08 \u2014 Trust, But Verify"),
    9:  (page_09, "09 \u2014 What the Seller Won\u2019t Tell You"),
    10: (page_10, "10 \u2014 Stranded Is a Plan You Didn\u2019t Make"),
    11: (page_11, "11 \u2014 Free Repairs You Didn\u2019t Know You Had"),
    12: (page_12, "12 \u2014 The Word \u201cNo\u201d Is Worth Thousands"),
    13: (page_13, "13 \u2014 Every Mile Is on Your Record"),
    14: (page_14, "14 \u2014 The Breakeven Point"),
    15: (page_15, "15 \u2014 The Drivetrain Is Changing"),
    16: (page_16, "16 \u2014 Your Owner\u2019s Manual for Owning a Car"),
}


def generate_all_pages(v: VehicleProfile, page_filter: int = None) -> dict:
    """Generate all (or one) portfolio pages. Returns {page_num: (title, html)}."""
    pages = {}
    targets = [page_filter] if page_filter else sorted(PAGE_REGISTRY.keys())
    for num in targets:
        gen_fn, _ = PAGE_REGISTRY[num]
        title, html = gen_fn(v)
        pages[num] = (title, html)
    return pages


# ══════════════════════════════════════════════════════════════
# QA REVIEW SYSTEM -- 3-perspective Gemini review per page
# ══════════════════════════════════════════════════════════════

# Import rubrics for QA validation
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from canvas_autos_rubrics import RUBRICS as AUTOS_RUBRICS
except ImportError:
    AUTOS_RUBRICS = {}

QA_PERSPECTIVES = {
    "rubric_auditor": {
        "system": (
            "You are a rubric auditor for a high school CTE class. Your ONLY job is to check "
            "whether an exemplar submission would earn FULL MARKS on every rubric criterion. "
            "For each criterion, state PASS (full marks) or FAIL (missing something) with a "
            "specific explanation. Be strict -- this is the exemplar students will follow."
        ),
        "temperature": 0.1,
    },
    "student_clarity": {
        "system": (
            "You are reviewing an exemplar portfolio page from a student's perspective. "
            "Would a 16-year-old in an Engines & Fabrication class understand what is expected "
            "by reading this exemplar? Is the tone appropriate (not condescending, not too academic)? "
            "Are the steps clear enough to follow? Report any confusing sections."
        ),
        "temperature": 0.5,
    },
    "numerical_accuracy": {
        "system": (
            "You are a numerical accuracy checker. Verify every calculation in this submission. "
            "Check: loan amortization math, insurance totals, fuel cost formulas, depreciation "
            "projections, TCO sums, and any other arithmetic. Report any errors or inconsistencies. "
            "Also check that dollar amounts mentioned in text match the values in tables."
        ),
        "temperature": 0.1,
    },
}


def run_qa_review(pages: dict, page_filter: int = None):
    """Run 3-perspective QA on each generated page using Gemini."""
    try:
        from google import genai
    except ImportError:
        print("  WARNING: google-genai not installed. Skipping QA review.")
        print("  Install with: pip3 install google-genai")
        return

    api_key = get_env("GEMINI_API_KEY", required=False)
    if not api_key:
        print("  WARNING: GEMINI_API_KEY not set. Skipping QA review.")
        return

    client = genai.Client(api_key=api_key)
    targets = [page_filter] if page_filter else sorted(pages.keys())

    for num in targets:
        title, html_content = pages[num]
        _, asgn_name = PAGE_REGISTRY[num]

        # Get rubric criteria for this page
        rubric = AUTOS_RUBRICS.get(asgn_name, {})
        criteria = rubric.get("criteria", {})
        criteria_text = ""
        for idx in sorted(criteria.keys(), key=lambda k: int(k)):
            c = criteria[idx]
            criteria_text += f"\nCriterion: {c['description']} ({c['points']} pts)\n"
            criteria_text += f"  Full marks: {c['ratings']['0']['description']}\n"

        print(f"\n{'=' * 60}")
        print(f"  QA REVIEW: Page {num} -- {title}")
        print(f"{'=' * 60}")

        for perspective, config in QA_PERSPECTIVES.items():
            prompt = (
                f"Review this exemplar for Page {num}: {title}\n\n"
                f"RUBRIC CRITERIA:\n{criteria_text}\n\n"
                f"EXEMPLAR CONTENT:\n{html_content[:6000]}\n\n"
                f"Provide your review."
            )

            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        system_instruction=config["system"],
                        temperature=config["temperature"],
                    ),
                )
                print(f"\n  [{perspective.upper()}]")
                # Print first 500 chars of review
                review_text = response.text[:500] if response.text else "(no response)"
                print(f"  {review_text}")
                if len(response.text or "") > 500:
                    print(f"  ... ({len(response.text) - 500} more chars)")
            except Exception as e:
                print(f"\n  [{perspective.upper()}] ERROR: {e}")

            time.sleep(GEMINI_RPM_DELAY)

    print(f"\n{'=' * 60}")
    print(f"  QA REVIEW COMPLETE")
    print(f"{'=' * 60}")


# ══════════════════════════════════════════════════════════════
# CANVAS DEPLOYMENT
# ══════════════════════════════════════════════════════════════

def get_canvas_creds():
    """Get Canvas API credentials."""
    url = get_env("CANVAS_API_URL")
    token = get_env("CANVAS_API_TOKEN")
    return url, token


def paginated_get(url, headers, params=None):
    """GET with Canvas pagination."""
    results = []
    page_url = url
    while page_url:
        r = requests.get(page_url, headers=headers, params=params)
        r.raise_for_status()
        results.extend(r.json())
        links = r.headers.get("Link", "")
        page_url = None
        for link in links.split(","):
            if 'rel="next"' in link:
                page_url = link.split("<")[1].split(">")[0]
        params = None
    return results


def deploy_to_canvas(pages: dict, page_filter: int = None):
    """Deploy exemplar pages to Canvas as Course Pages + Test Student submissions."""
    url, token = get_canvas_creds()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    targets = [page_filter] if page_filter else sorted(pages.keys())
    created_pages = 0
    created_submissions = 0
    errors = 0

    for cid in ENGINES_FAB_COURSE_IDS:
        # Get course name
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        r.raise_for_status()
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n{'=' * 60}")
        print(f"  DEPLOYING TO: {cname} (ID: {cid})")
        print(f"{'=' * 60}")

        # Get all assignments for name matching
        assignments = {}
        for a in paginated_get(f"{url}/api/v1/courses/{cid}/assignments", headers, {"per_page": "50"}):
            assignments[a["name"]] = a

        # Get test student
        test_student_id = None
        try:
            users = paginated_get(
                f"{url}/api/v1/courses/{cid}/users",
                headers,
                {"enrollment_type[]": "student_view", "per_page": "10"},
            )
            if users:
                test_student_id = users[0]["id"]
                print(f"  Test Student ID: {test_student_id}")
            else:
                print("  WARNING: No Test Student found. Enable Student View in Canvas first.")
                print("  Skipping test student submissions for this course.")
        except Exception as e:
            print(f"  WARNING: Could not find Test Student: {e}")

        for num in targets:
            title, html_content = pages[num]
            _, asgn_name = PAGE_REGISTRY[num]

            # 1. Create Course Page
            slug = f"exemplar-page-{num:02d}"
            page_title = f"Exemplar: Page {num} -- {title}"
            payload = {
                "wiki_page": {
                    "title": page_title,
                    "body": html_content,
                    "published": True,
                    "editing_roles": "teachers",
                }
            }

            actual_slug = slug  # fallback
            try:
                # Try to find existing page by searching
                search_r = requests.get(
                    f"{url}/api/v1/courses/{cid}/pages?search_term=Exemplar%3A+Page+{num}",
                    headers=headers,
                )
                existing = [p for p in search_r.json() if p.get("title", "").startswith(f"Exemplar: Page {num}")]

                if existing:
                    actual_slug = existing[0]["url"]
                    r = requests.put(
                        f"{url}/api/v1/courses/{cid}/pages/{actual_slug}",
                        headers=headers,
                        json=payload,
                    )
                else:
                    r = requests.post(
                        f"{url}/api/v1/courses/{cid}/pages",
                        headers=headers,
                        json=payload,
                    )
                r.raise_for_status()
                # Capture the actual slug Canvas assigned
                actual_slug = r.json().get("url", slug)
                print(f"  PAGE OK: {page_title} (slug: {actual_slug})")
                created_pages += 1
            except Exception as e:
                print(f"  PAGE FAIL: {page_title} -- {e}")
                errors += 1

            # 2. Update assignment description with exemplar link
            if asgn_name in assignments:
                asgn = assignments[asgn_name]
                existing_desc = asgn.get("description", "") or ""
                link_html = f'<p><strong>Exemplar:</strong> <a href="/courses/{cid}/pages/{actual_slug}">View Exemplar</a></p>'

                # Replace existing broken link or add new one
                import re as _re
                if "View Exemplar" in existing_desc:
                    updated_desc = _re.sub(
                        r'<p><strong>Exemplar:</strong>.*?View Exemplar.*?</p>',
                        link_html,
                        existing_desc,
                    )
                    action_verb = "Updated"
                else:
                    updated_desc = existing_desc + "\n\n" + link_html
                    action_verb = "Added"

                update_payload = {
                    "assignment": {
                        "description": updated_desc,
                    }
                }
                try:
                    r = requests.put(
                        f"{url}/api/v1/courses/{cid}/assignments/{asgn['id']}",
                        headers=headers,
                        json=update_payload,
                    )
                    r.raise_for_status()
                    print(f"  LINK OK: {action_verb} exemplar link on \"{asgn_name}\"")
                except Exception as e:
                    print(f"  LINK FAIL: {asgn_name} -- {e}")

                # 3. Submit as Test Student
                if test_student_id:
                    sub_payload = {
                        "submission": {
                            "submission_type": "online_text_entry",
                            "body": html_content,
                        }
                    }
                    try:
                        r = requests.put(
                            f"{url}/api/v1/courses/{cid}/assignments/{asgn['id']}/submissions/{test_student_id}",
                            headers=headers,
                            json=sub_payload,
                        )
                        r.raise_for_status()
                        print(f"  SUBMIT OK: Test Student submission for \"{asgn_name}\"")
                        created_submissions += 1
                    except Exception as e:
                        print(f"  SUBMIT FAIL: {asgn_name} -- {e}")
                        errors += 1
            else:
                print(f"  SKIP: Assignment \"{asgn_name}\" not found in course {cid}")

            time.sleep(0.15)  # rate limit

    print(f"\n{'=' * 60}")
    print(f"  DEPLOYMENT SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Course Pages created/updated: {created_pages}")
    print(f"  Test Student submissions: {created_submissions}")
    print(f"  Errors: {errors}")
    print()


def audit_canvas(page_filter: int = None):
    """Verify exemplar pages exist on Canvas."""
    url, token = get_canvas_creds()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    targets = [page_filter] if page_filter else sorted(PAGE_REGISTRY.keys())

    for cid in ENGINES_FAB_COURSE_IDS:
        r = requests.get(f"{url}/api/v1/courses/{cid}", headers=headers)
        cname = r.json().get("name", f"Course {cid}")
        print(f"\n{'=' * 60}")
        print(f"  AUDIT: {cname} (ID: {cid})")
        print(f"{'=' * 60}")

        ok = 0
        missing = 0

        for num in targets:
            try:
                search_r = requests.get(
                    f"{url}/api/v1/courses/{cid}/pages?search_term=Exemplar%3A+Page+{num}",
                    headers=headers,
                )
                matches = [p for p in search_r.json() if p.get("title", "").startswith(f"Exemplar: Page {num}")]
                if matches:
                    p = matches[0]
                    body_len = 0
                    # Fetch full page to check body length
                    detail_r = requests.get(f"{url}/api/v1/courses/{cid}/pages/{p['url']}", headers=headers)
                    if detail_r.status_code == 200:
                        body_len = len(detail_r.json().get("body", "") or "")
                    status = "OK" if body_len > 100 else "EMPTY"
                    print(f"  {status}: Page {num} -- \"{p['title']}\" ({body_len} chars, slug: {p['url']})")
                    if status == "OK":
                        ok += 1
                    else:
                        missing += 1
                else:
                    print(f"  MISSING: Page {num}")
                    missing += 1
            except Exception as e:
                print(f"  ERROR: Page {num} -- {e}")
                missing += 1

        print(f"\n  Results: {ok} found, {missing} missing")

    print(f"\n{'=' * 60}")
    print(f"  AUDIT COMPLETE")
    print(f"{'=' * 60}")


# ══════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Generate and deploy exemplar portfolio for Engines & Fabrication courses",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Generate pages to terminal (no Canvas calls)")
    group.add_argument("--review", action="store_true", help="Generate + run 3-pass Gemini QA per page")
    group.add_argument("--execute", action="store_true", help="Deploy to Canvas (pages + test student)")
    group.add_argument("--audit", action="store_true", help="Verify exemplar pages exist on Canvas")
    parser.add_argument("--page", type=int, choices=range(1, 17), help="Generate only this page number (1-16)")
    args = parser.parse_args()

    v = VehicleProfile()

    if args.audit:
        audit_canvas(args.page)
        return

    # Generate pages
    print(f"\n{'=' * 60}")
    print(f"  EXEMPLAR PORTFOLIO GENERATOR")
    print(f"  Vehicle: {v.full_name}")
    print(f"  Purchase: {fmti(v.purchase_price)} | {v.mileage_at_purchase:,} mi | {v.city}, {v.state}")
    print(f"{'=' * 60}")

    pages = generate_all_pages(v, args.page)

    if args.dry_run:
        for num in sorted(pages.keys()):
            title, html = pages[num]
            _, asgn_name = PAGE_REGISTRY[num]
            print(f"\n{'=' * 60}")
            print(f"  Page {num}: {title}")
            print(f"  Canvas Assignment: \"{asgn_name}\"")
            print(f"  HTML Length: {len(html):,} characters")
            print(f"{'=' * 60}")
            # Print a text preview (strip HTML tags for readability)
            import re
            text = re.sub(r'<[^>]+>', '', html)
            text = re.sub(r'\s+', ' ', text).strip()
            preview = text[:800]
            print(f"\n  {preview}")
            if len(text) > 800:
                print(f"\n  ... ({len(text) - 800} more chars)")

        print(f"\n{'=' * 60}")
        print(f"  DRY RUN COMPLETE: {len(pages)} pages generated")
        print(f"{'=' * 60}")

    elif args.review:
        # Print generation summary first
        for num in sorted(pages.keys()):
            title, html = pages[num]
            print(f"  Generated Page {num}: {title} ({len(html):,} chars)")

        # Run QA
        run_qa_review(pages, args.page)

    elif args.execute:
        for num in sorted(pages.keys()):
            title, html = pages[num]
            print(f"  Generated Page {num}: {title} ({len(html):,} chars)")

        print("\n  Deploying to Canvas...")
        deploy_to_canvas(pages, args.page)


if __name__ == "__main__":
    main()
