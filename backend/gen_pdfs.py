import fitz  # PyMuPDF


def make_pdf(path, title, pages_text):
    doc = fitz.open()

    for i, text in enumerate(pages_text, start=1):
        page = doc.new_page(width=595, height=842)

        rect = fitz.Rect(50, 50, 545, 792)

        full_text = (
            f"{title}\n"
            "(SYNTHETIC DEMO DATA — for hackathon demo purposes only)\n\n"
            f"Page {i}\n\n"
            f"{text}"
        )

        page.insert_textbox(
            rect,
            full_text,
            fontsize=11,
            fontname="helv"
        )

    doc.save(path)
    doc.close()

    print("wrote", path)


# --- RELIANCE: annual report ---
make_pdf(
    "data/documents/reliance/annual_report.pdf",
    "Reliance Industries Limited — Annual Report FY26 (Synthetic)",
    [
        (
            "Business Overview\n\n"
            "Reliance Industries Limited reported consolidated revenue growth of 14% "
            "year-on-year for fiscal year 2026, driven primarily by strong performance "
            "in the Retail and Digital Services segments. Reliance Retail delivered "
            "record growth, with same-store sales expanding across grocery, fashion, "
            "and electronics formats.\n\n"
            "Jio Platforms continued its expansion trajectory, adding over 12 million "
            "net subscribers during the year and improving average revenue per user "
            "following tariff rationalization implemented in Q3."
        ),
        (
            "Financial Highlights\n\n"
            "Consolidated EBITDA margin improved to 19.8%, up from 18.2% in the prior "
            "year, reflecting operating leverage in the retail business and continued "
            "cost discipline across the oil-to-chemicals segment. Net profit for the "
            "year increased 11% year-on-year to a new company record.\n\n"
            "The Board has approved continued capital expenditure toward new energy "
            "manufacturing capacity, with the first phase of the green hydrogen facility "
            "expected to be commissioned in the next fiscal year."
        ),
        (
            "Outlook and Risk Factors\n\n"
            "Management expects continued growth momentum in Retail and Digital Services "
            "into FY27, supported by festive season demand and continued 5G rollout. "
            "The company noted a minor implementation delay of approximately one quarter "
            "on one green energy manufacturing milestone due to equipment supply chain "
            "timing, which is not expected to materially affect the overall project timeline.\n\n"
            "Key risks disclosed include global crude oil price volatility, regulatory "
            "changes in the telecom sector, and currency fluctuation exposure on "
            "international operations."
        ),
    ],
)


# --- RELIANCE: Q4 results ---
make_pdf(
    "data/documents/reliance/q4_results.pdf",
    "Reliance Industries Limited — Q4 FY26 Results Presentation (Synthetic)",
    [
        (
            "Q4 FY26 Performance Summary\n\n"
            "Reliance Industries reported Q4 consolidated revenue growth of 12% "
            "year-on-year. Retail segment revenue grew 18% year-on-year, marking "
            "the segment's strongest quarterly performance on record, driven by "
            "store expansion and higher footfall during the quarter.\n\n"
            "Jio Platforms revenue grew 9% sequentially, aided by the full-quarter "
            "impact of the tariff increase implemented in the prior quarter."
        ),
        (
            "Segment Notes\n\n"
            "The Oil-to-Chemicals segment showed a modest decline in margins due to "
            "planned maintenance shutdowns at one refining unit during the quarter, "
            "which management characterized as a temporary and expected impact.\n\n"
            "New Energy segment capital expenditure continued as planned, with "
            "commissioning of the first manufacturing line still on track for early "
            "next fiscal year, subject to the previously disclosed minor equipment "
            "delivery delay."
        ),
    ],
)


# --- TCS: quarterly results ---
make_pdf(
    "data/documents/tcs/q4_results.pdf",
    "Tata Consultancy Services — Q4 FY26 Results Presentation (Synthetic)",
    [
        (
            "Q4 FY26 Highlights\n\n"
            "TCS reported steady revenue growth of 6% year-on-year in constant "
            "currency terms. The BFSI vertical showed resilient demand, while the "
            "Retail and Consumer Business Group vertical experienced softer "
            "discretionary technology spending during the quarter.\n\n"
            "The company announced a share buyback program, reflecting continued "
            "strong free cash flow generation and a disciplined approach to "
            "capital allocation."
        ),
        (
            "Deal Pipeline and Margins\n\n"
            "The order book remains healthy, though management noted that the pace "
            "of deal ramp-up has been gradual amid a cautious global demand environment. "
            "Operating margin was broadly stable quarter-on-quarter at 24.1%.\n\n"
            "Management reiterated a measured, watchful outlook for the coming fiscal "
            "year, citing macroeconomic uncertainty in key overseas markets as a "
            "factor tempering near-term growth acceleration."
        ),
    ],
)

print("done")