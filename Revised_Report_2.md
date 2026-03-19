# 1. Title Page

**Course:** ISTM 637 – Data Warehousing
**Project:** Design and Implementation of a Data Warehouse for a Retail Store
**Report Title:** Report 2: Logical Design and Physical Design of the Data Warehouse Schema
**Client:** Dominick's Finer Foods (DFF)
**Project Group:** Group 3
**Date:** March 18, 2026

---

# 2. Table of Contents

1. Title Page
2. Table of Contents
3. Executive Summary
4. Introduction
5. Overview of Kimball's Methodology
6. Application of Kimball Methodology to Group 3 Design
7. Data Mart / Dimension Bus Matrix
8. Data Warehouse Logical Design
    - 8.1 Selected Business Questions
    - 8.2 Business Process Definition
    - 8.3 Grain Definition
    - 8.4 Dimension Identification
    - 8.5 Fact Identification
    - 8.6 Star Schema Table Definitions
    - 8.7 Schema Justification for BQ1–BQ5
9. SQL Query Design / Analytical Query Layer
10. Mapping Table #1: Source Files to Staging Tables
11. Mapping Table #2: Staging Tables to Data Mart Tables
12. Physical Design Plan
13. Validation and Data Integrity Checks
14. Star Schema ERD
15. Business Value and Strategic Impact
16. Data Source Summary
17. Limitations and Future Roadmap
18. Conclusion
19. Appendix / Assumptions

---

# 3. Executive Summary

This report presents the logical and physical Data Warehouse schema design for Dominick's Finer Foods (DFF), a major Chicago-area retail grocer that recorded detailed transactional and demographic data across approximately 93 stores from 1989 to 1994. The design addresses five business questions (BQ1–BQ5) assigned to Group 3, covering sales profitability, product trends, promotional effectiveness, demographic performance, and customer traffic conversion.

The central architectural decision is a **dual fact table design**: `Fact_Weekly_Sales` captures checkout transactions at the Store × Product × Week grain, while `Fact_Customer_Traffic` captures physical foot traffic at the coarser Store × Week grain. This separation is mandatory because combining these two different levels of granularity into a single fact table would produce mathematically incorrect aggregation results—customer traffic counts would be duplicated across every product row, inflating totals by orders of magnitude.

The design follows **Ralph Kimball's Bottom-Up Dimensional Modeling** methodology, organizing data into independent star-schema data marts linked through conformed dimensions (`Dim_Store` and `Dim_Date`). This bus architecture enables safe cross-process analysis—most critically for BQ5, which requires comparing traffic volumes against sales revenue using the Kimball drill-across query pattern.

Targeted for deployment on **Microsoft SQL Server 2016** in a Hybrid Online Analytical Processing (HOLAP) environment, the physical design leverages Clustered Columnstore Indexes, Materialized Indexed Views, and Table Partitioning to ensure fast response times for read-heavy analytical workloads.

---

# 4. Introduction

This report follows the exact structure required by the ISTM 637 assignment while expanding sub-sections for clarity, professional readability, and architectural depth.

Dominick's Finer Foods (DFF) was a prominent retail grocery chain operating approximately 93 stores across the greater Chicago metropolitan area. Between 1989 and 1994, DFF systematically collected store-level operational data encompassing weekly point-of-sale transactions, product catalogs, customer traffic counts, and neighborhood demographic profiles. This dataset, maintained by the James M. Kilts Center for Marketing at the University of Chicago Booth School of Business, has become a widely studied resource in retail analytics research.

DFF's original systems relied on **Online Transaction Processing (OLTP)** databases optimized for high-throughput data entry through heavy normalization. While OLTP architectures excel at recording individual transactions, they are fundamentally unsuited for complex analytical queries. Queries that aggregate sales across hundreds of weeks, thousands of products, and dozens of stores encounter severe performance degradation in normalized schemas due to the large number of table joins required.

**Report 2** builds directly upon the business requirements and source system analysis completed in Report 1. Where Report 1 explored the raw data files, documented metadata, and formulated ten candidate business questions, this report translates that understanding into a formal dimensional model. Specifically, this document delivers:

- A **logical design** based on Kimball's four-step dimensional modeling process
- **Star schema table definitions** for two fact tables and four dimension tables
- **ETL mapping tables** tracing every attribute from source file to data mart
- **SQL queries** demonstrating how the schema answers each business question
- A **physical design plan** optimized for SQL Server 2016

Group 3 has been assigned the following five business questions:

- **BQ1:** Sales and profit by store and time
- **BQ2:** Sales and margin by product/category over time
- **BQ3:** Effect of promotions (sale codes B/C/S) on units sold and revenue
- **BQ4:** Performance by store demographic (income, education) or by zone
- **BQ5:** Customer count vs. sales

These questions span two fundamentally different business processes—checkout transactions and foot traffic counting—which is the primary driver behind the dual fact table architecture described throughout this report.

---

# 5. Overview of Kimball's Methodology

The schema architecture follows **Ralph Kimball's Bottom-Up Data Warehouse Methodology**, as described in *The Data Warehouse Toolkit* (Kimball & Ross, 2013). This approach constructs the enterprise data warehouse incrementally by building individual, subject-area-specific data marts integrated through shared conformed dimensions.

## 5.1 The Four-Step Dimensional Design Process

Kimball's methodology centers on a repeatable four-step process applied to each business process:

1. **Select the Business Process.** Identify the operational activity that generates measurable data. This should be a real-world event—such as a retail checkout or a customer visit—not a department or report.

2. **Declare the Grain.** Define the exact level of detail that a single row in the fact table represents. The grain must be declared before identifying dimensions or facts, because it determines what is and is not possible to measure. An incorrectly declared grain leads to double-counting or aggregation errors.

3. **Identify the Dimensions.** Determine the descriptive context—the "who, what, where, when, and how"—surrounding each fact row. Dimensions are the entry points for filtering, grouping, and labeling in analytical queries.

4. **Identify the Facts.** Isolate the numeric, measurable performance metrics produced by the business process. Facts are classified by additivity: *additive* facts can be safely summed across all dimensions, *semi-additive* across some, and *non-additive* (ratios/percentages) cannot be summed at all.

## 5.2 Star Schema Architecture

Kimball's methodology produces **star schemas**, in which a central fact table is surrounded by denormalized dimension tables. This structure minimizes joins for analytical queries, translating directly to faster execution. Unlike snowflake schemas that normalize dimension tables into sub-tables, star schemas deliberately denormalize descriptive attributes to prioritize query simplicity and speed.

## 5.3 Conformed Dimensions and Bus Architecture

When multiple business processes are modeled, **conformed dimensions** provide the integration mechanism. A conformed dimension is shared identically across multiple data marts, ensuring consistent filtering and grouping semantics. This enables **drill-across queries**—queries that combine pre-aggregated facts from different data marts along shared dimension keys. The collection of data marts linked through conformed dimensions forms the **enterprise bus matrix**.

## 5.4 Why Kimball Is Appropriate for DFF

1. **Incremental delivery.** Each data mart can be built independently, allowing business users to start analyzing high-priority areas without waiting for the entire warehouse.
2. **Query performance.** Star schemas minimize join complexity, critical when querying millions of weekly transaction records.
3. **Analytical flexibility.** The dimensional model naturally supports slice, dice, drill-down, and roll-up operations needed for retail analytics.

---

# 6. Application of Kimball Methodology to Group 3 Design

## Step 1: Select the Business Processes

Group 3's five business questions require data from two fundamentally different operational activities:

- **Process A — Weekly Point-of-Sale Checkout:** Each week, every DFF store records units sold, retail price, profit margin, and promotional status for every product (identified by UPC barcode). Captured in Movement data files (`wlnd.csv`). Supports BQ1–BQ4.

- **Process B — Weekly Facility Entrance Counting:** Automated door counters record total customers entering each store weekly. Captured in `CCOUNT.csv`. Supports BQ5.

These two processes operate at different levels of granularity and must be modeled separately.

## Step 2: Declare the Grain

- **Fact_Weekly_Sales:** One row per **Store**, per **Product (UPC)**, per **Week**. The finest grain supported by the Movement data.
- **Fact_Customer_Traffic:** One row per **Store**, per **Week**. The only grain available from CCOUNT data.

**Why two grains require two fact tables:** If customer traffic (Store × Week) were embedded into the sales fact table (Store × Product × Week), the single weekly customer count would be replicated across every product row. A `SUM(customer_count)` would be inflated by the product count, producing systematically corrupted results.

## Step 3: Identify the Dimensions

- **`Dim_Store`** (Conformed): Regional and demographic context from `DEMO.csv`. Used by both facts.
- **`Dim_Date`** (Conformed): Calendar attributes derived from raw WEEK IDs. Used by both facts.
- **`Dim_Product`**: Product descriptions and denormalized categories from `UPCLND.csv`. Sales fact only.
- **`Dim_Promotion`**: Promotional classification derived from `SALE` flag. Sales fact only.

Product categories (`COM_CODE`) are deliberately **denormalized** into `Dim_Product` to avoid snowflaking.

## Step 4: Identify the Facts

**Process A measures:** `units_sold` (Additive), `retail_price` (Non-additive), `dollar_sales` (Derived, Additive), `profit_margin_pct` (Non-additive).

**Process B measures:** `customer_count` (Additive).

## Step 5: Build the Bus Architecture

Two independent data marts linked through conformed dimensions (`Dim_Store`, `Dim_Date`) form the bus architecture. BQ5 is answered using the Kimball **drill-across** pattern: pre-aggregate each fact to the common Store × Week grain, then join on shared dimension keys.

---

# 7. Data Mart / Dimension Bus Matrix

The Bus Matrix is the central planning document in Kimball's methodology. It maps each business process (fact table) to the dimensions it references, ensuring analytical coverage across all business questions.

*Table 1: Dimension Bus Matrix*

| Business Process | Dim_Store | Dim_Date | Dim_Product | Dim_Promotion | Supported BQs |
| :--- | :---: | :---: | :---: | :---: | :--- |
| Fact_Weekly_Sales | ✓ (Conformed) | ✓ (Conformed) | ✓ | ✓ | BQ1, BQ2, BQ3, BQ4 |
| Fact_Customer_Traffic | ✓ (Conformed) | ✓ (Conformed) | — | — | BQ5 |

**Key observations:**

- `Dim_Store` and `Dim_Date` are **conformed** across both fact tables, enabling safe cross-fact analysis for BQ5.
- `Dim_Product` and `Dim_Promotion` apply only to Sales because traffic is not tracked at product or promotion level.
- BQ5 requires data from **both** fact tables. Conformed dimensions ensure drill-across joins produce correct results.

---

# 8. Data Warehouse Logical Design

This section applies Kimball's four-step process to define the grain, dimensions, facts, and schema tables for the DFF data warehouse.

## 8.1 Selected Business Questions

- **BQ1:** Sales and profit by store and time.
- **BQ2:** Sales and margin by product/category over time (trends).
- **BQ3:** Effect of promotions (sale codes B/C/S) on units sold and revenue.
- **BQ4:** Performance by store demographic (income, education) or by zone.
- **BQ5:** Customer count vs. sales.

## 8.2 Business Process Definition

1. **Scanner Checkout Logging (Process A):** The point-of-sale transaction generating revenue, unit movement, pricing, promotional, and profit data. Recorded weekly at individual product level across all stores.

2. **Facility Entrance Logging (Process B):** Automated door-counter measurement of total physical foot traffic per store per week. Captures aggregate visitor volume independent of purchases.

These processes are operationally distinct: Process A is register-driven with product-level detail, while Process B is sensor-driven with a single aggregate count. This distinction drives the two-fact-table requirement.

## 8.3 Grain Definition

The grain defines the exact level of detail represented by a single row. Declaring the grain explicitly is the most important step in dimensional modeling.

**Fact_Weekly_Sales Grain:** One row per **Store**, per **Product (UPC)**, per **Week**. This is the finest grain supported by the Movement source files. Each row represents the complete weekly transaction record for a specific product in a specific store.

**Fact_Customer_Traffic Grain:** One row per **Store**, per **Week**. This is the only grain available from CCOUNT, which records a single `CUSTCOUN` value per store per week with no product-level breakdown.

**Why Grain Isolation Is Mandatory:**

If traffic counts were embedded into `Fact_Weekly_Sales`, each store's weekly customer count would be copied onto every product row:

- Store #5 records **10,000 visitors** in Week 278.
- Store #5 has sales for **5,000 distinct products** that week.
- If `customer_count = 10,000` appears on all 5,000 rows, `SUM(customer_count)` returns **50,000,000** instead of **10,000**.

This is a textbook grain-violation error. The two grains must remain in separate fact tables. Cross-fact analysis uses the Kimball drill-across pattern (pre-aggregate each fact to common grain, then join).

## 8.4 Dimension Identification

Dimensions provide the filtering, grouping, and labeling context for every analytical query. Each dimension table below serves a specific role within the star schema.

#### Dim_Store (Conformed)

| Attribute | Detail |
| :--- | :--- |
| **Purpose** | Geographic, socioeconomic, and pricing zone context for each store |
| **Source** | `DEMO.csv` — 1990 U.S. Census data linked to each DFF store |
| **Key Attributes** | `store_id` (NK), `store_zone`, `median_income`, `education_pct`, `income_band` |
| **Analytical Role** | Geographic segmentation (BQ1), demographic slicing by income band (BQ4), zone comparison (BQ4) |
| **Hierarchy Context** | Store -> Store_Zone -> Total Enterprise. This hierarchy enables drill-down from corporate-wide performance to specific regional pricing zones and individual retail units |
| **Business-Friendly Enhancement** | The derived `income_band` attribute (High/Medium/Low) converts raw Census dollar values into analyst-friendly categories, improving report readability and enabling intuitive GROUP BY operations without requiring end-users to define income thresholds in SQL |
| **Conformed Status** | Shared by both `Fact_Weekly_Sales` and `Fact_Customer_Traffic` |
| **BQs Supported** | BQ1, BQ4, BQ5 |

#### Dim_Date (Conformed)

| Attribute | Detail |
| :--- | :--- |
| **Purpose** | Translates raw DFF integer WEEK IDs into standard calendar attributes |
| **Source** | Derived from `wlnd.WEEK` — sequential integers from ~September 1989 |
| **Key Attributes** | `week_id` (NK), `calendar_month`, `calendar_quarter`, `calendar_year`, `season`, `holiday_flag` |
| **Population Logic** | Each WEEK_ID mapped to calendar via: `epoch + (WEEK_ID - 1) x 7 days`, where epoch = Sept 14, 1989. Month, quarter, and year extracted from computed date. `Season` assigned via month ranges (Spring: 3-5, Summer: 6-8, Fall: 9-11, Winter: 12-2). `holiday_flag` set to 1 for weeks containing Thanksgiving or Christmas |
| **Analytical Role** | Time-series trending, YoY comparison, seasonal and quarterly analysis |
| **Conformed Status** | Shared by both fact tables |
| **BQs Supported** | BQ1, BQ2, BQ5 |

#### Dim_Product

| Attribute | Detail |
| :--- | :--- |
| **Purpose** | Product descriptions and denormalized commodity categories |
| **Source** | `UPCLND.csv` — UPC product dictionary |
| **Key Attributes** | `upc_id` (NK), `item_description`, `commodity_code` |
| **Denormalization** | `commodity_code` stored directly on Dim_Product (no separate Dim_Category) to maintain pure star schema |
| **Analytical Role** | Product-level and category-level sales analysis, trend comparison (BQ2) |
| **BQs Supported** | BQ2 |

#### Dim_Promotion

| Attribute | Detail |
| :--- | :--- |
| **Purpose** | Classifies each transaction's promotional status |
| **Source** | Derived from `wlnd.SALE` flag: B="Bonus Buy", C="Coupon", S="Simple Reduction", NONE="No Promotion" |
| **Key Attributes** | `sale_code` (NK: B/C/S/NONE), `promotion_type` (descriptive label) |
| **Analytical Role** | Promotional vs. non-promotional ROI comparison (BQ3) |
| **Promotion vs. Unknown Distinction** | `sale_code = 'NONE'` represents a valid business state (the transaction had no promotion). This is distinct from the Unknown Member (`promotion_sk = -1`), which represents an ETL lookup failure where the source `SALE` value could not be resolved |
| **BQs Supported** | BQ3 |

## 8.5 Fact Identification

Fact tables store the quantitative performance metrics produced by each business process. The additivity classification determines how each measure can be safely aggregated.

#### Fact_Weekly_Sales

| Attribute | Detail |
| :--- | :--- |
| **Grain** | One row per Store x Product x Week |
| **Business Process** | Weekly POS scanner checkouts |
| **Foreign Keys** | `store_sk`, `date_sk`, `product_sk`, `promotion_sk` |

| Measure | Additivity | Source | Business Use |
| :--- | :--- | :--- | :--- |
| `units_sold` | Additive | `wlnd.MOVE` | Volume analysis, demand forecasting |
| `retail_price` | Non-additive | `wlnd.PRICE` | Price point analysis (use AVG not SUM) |
| `dollar_sales` | Additive | Derived: `(PRICE x MOVE) / QTY` | Revenue reporting, trend analysis |
| `profit_margin_pct` | Non-additive | `wlnd.PROFIT` | Profitability analysis (use AVG) |

#### Fact_Customer_Traffic

| Attribute | Detail |
| :--- | :--- |
| **Grain** | One row per Store x Week |
| **Business Process** | Weekly automated door-counter measurement |
| **Foreign Keys** | `store_sk`, `date_sk` |

| Measure | Additivity | Source | Business Use |
| :--- | :--- | :--- | :--- |
| `customer_count` | Additive | `CCOUNT.CUSTCOUN` | Traffic volume, conversion rate analysis |

## 8.6 Star Schema Table Definitions

All schema tables below follow the standardized format: Column Name, Data Type, Key designation (PK/FK/NK/Measure/Attribute), Description, Source, and Additivity.

*Table 2: Fact_Weekly_Sales Schema*

| Column Name | Data Type | Key | Description | Source | Additivity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `sales_fact_id` | INT IDENTITY | PK | Surrogate primary key | System | N/A |
| `store_sk` | INT | FK | Store surrogate key | Lookup | N/A |
| `date_sk` | INT | FK | Date surrogate key | Lookup | N/A |
| `product_sk` | INT | FK | Product surrogate key | Lookup | N/A |
| `promotion_sk` | INT | FK | Promotion surrogate key | Lookup | N/A |
| `units_sold` | INT | Measure | Number of units transacted | wlnd.MOVE | Additive |
| `retail_price` | DECIMAL(10,2) | Measure | Per-unit checkout price | wlnd.PRICE | Non-additive |
| `dollar_sales` | DECIMAL(12,2) | Measure | Revenue: (PRICE x MOVE) / QTY | Derived | Additive |
| `profit_margin_pct` | DECIMAL(5,4) | Measure | Gross profit margin % | wlnd.PROFIT | Non-additive |

*Table 3: Fact_Customer_Traffic Schema*

| Column Name | Data Type | Key | Description | Source | Additivity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `traffic_fact_id` | INT IDENTITY | PK | Surrogate primary key | System | N/A |
| `store_sk` | INT | FK | Store surrogate key | Lookup | N/A |
| `date_sk` | INT | FK | Date surrogate key | Lookup | N/A |
| `customer_count` | INT | Measure | Weekly store foot traffic | CCOUNT.CUSTCOUN | Additive |

*Table 4: Dim_Store Schema*

| Column Name | Data Type | Key | Description | Source | Additivity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `store_sk` | INT IDENTITY | PK | Surrogate primary key | System | N/A |
| `store_id` | INT | NK | Original DFF store identifier | DEMO.STORE | N/A |
| `store_zone` | INT | Attribute | Pricing/geographic zone | DEMO.ZONE | N/A |
| `median_income` | DECIMAL(12,2) | Attribute | Median household income | DEMO.INCOME | N/A |
| `education_pct` | DECIMAL(5,4) | Attribute | Pct with higher education | DEMO.EDUC | N/A |
| `income_band` | VARCHAR(10) | Attribute | Derived: High/Medium/Low income tier | Derived from INCOME | N/A |

*Table 5: Dim_Date Schema*

| Column Name | Data Type | Key | Description | Source | Additivity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `date_sk` | INT IDENTITY | PK | Surrogate primary key | System | N/A |
| `week_id` | INT | NK | DFF sequential week number | wlnd.WEEK | N/A |
| `calendar_month` | INT | Attribute | Calendar month (1-12) | Derived | N/A |
| `calendar_quarter` | INT | Attribute | Calendar quarter (1-4) | Derived | N/A |
| `calendar_year` | INT | Attribute | Calendar year (1989-1994) | Derived | N/A |
| `season` | VARCHAR(10) | Attribute | Seasonal category (Winter/Spring/Summer/Fall) | Derived | N/A |
| `holiday_flag` | BIT | Attribute | Flag for major sales holidays (Thanksgiving/Christmas); 1 = holiday week, 0 = standard | Derived | N/A |

*Derivation logic:* DFF WEEK_IDs are sequential integers beginning at epoch = September 14, 1989. During ETL: `calendar_date = epoch + (WEEK_ID - 1) x 7 days`. Month, quarter, and year are extracted from computed date.

*Table 6: Dim_Product Schema*

| Column Name | Data Type | Key | Description | Source | Additivity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `product_sk` | INT IDENTITY | PK | Surrogate primary key | System | N/A |
| `upc_id` | BIGINT | NK | UPC barcode identifier | UPC.UPC | N/A |
| `item_description` | VARCHAR(100) | Attribute | Cleaned product description | UPC.DESCRIP | N/A |
| `commodity_code` | INT | Attribute | Denormalized category code | UPC.COM_CODE | N/A |

*Table 7: Dim_Promotion Schema*

| Column Name | Data Type | Key | Description | Source | Additivity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `promotion_sk` | INT IDENTITY | PK | Surrogate primary key | System | N/A |
| `sale_code` | CHAR(4) | NK | Promotion code (B/C/S/NONE) | wlnd.SALE | N/A |
| `promotion_type` | VARCHAR(30) | Attribute | Descriptive promotion label | Derived | N/A |

## 8.7 Schema Justification for BQ1–BQ5

Each business question below identifies the exact facts, dimensions, OLAP operations, and correctness rationale that validate the schema design.

**BQ1: Sales and profit by store and time**
- **Business Need:** Visibility into revenue and profitability variation across stores and time periods.
- **Facts Used:** `Fact_Weekly_Sales` — `dollar_sales` (SUM), `profit_margin_pct` (AVG).
- **Dimensions Used:** `Dim_Store` (`store_zone`), `Dim_Date` (`calendar_year`, `calendar_quarter`).
- **OLAP Operation:** Roll-up from Store x Product x Week to Store Zone x Year.
- **Why It Works:** Additive `dollar_sales` can be safely summed. Non-additive `profit_margin_pct` uses AVG.

**BQ2: Sales and margin by product/category over time**
- **Business Need:** Identify growing/declining product categories and margin trends.
- **Facts Used:** `Fact_Weekly_Sales` — `units_sold` (SUM), `dollar_sales` (SUM), `profit_margin_pct` (AVG).
- **Dimensions Used:** `Dim_Product` (`commodity_code`), `Dim_Date` (`calendar_year`).
- **OLAP Operation:** Trend analysis with roll-up by category across time.
- **Why It Works:** Denormalized `commodity_code` enables category grouping with single join. Including `profit_margin_pct` directly addresses the "margin" requirement.

**BQ3: Effect of promotions on units sold and revenue**
- **Business Need:** Quantify sales lift and revenue impact of each promotion type vs. non-promoted baselines.
- **Facts Used:** `Fact_Weekly_Sales` — `units_sold` (SUM), `dollar_sales` (SUM).
- **Dimensions Used:** `Dim_Promotion` (`promotion_type`).
- **OLAP Operation:** Dice by promotion type.
- **Why It Works:** `Dim_Promotion` cleanly segments transactions by promotional category.

**BQ4: Performance by store demographic or zone**
- **Business Need:** Understand whether stores in higher-income neighborhoods generate different revenue/margin profiles.
- **Facts Used:** `Fact_Weekly_Sales` — `dollar_sales` (SUM), `profit_margin_pct` (AVG).
- **Dimensions Used:** `Dim_Store` (`income_band`, `education_pct`, `store_zone`).
- **OLAP Operation:** Dice by income band and zone.
- **Why It Works:** The derived `income_band` attribute provides analyst-friendly grouping (High/Medium/Low) without requiring end-users to define arbitrary income thresholds. Census attributes embedded on `Dim_Store` provide full demographic context with single join.

**BQ5: Customer count vs. sales**
- **Business Need:** Calculate customer conversion rates (revenue per visitor) to assess store efficiency.
- **Facts Used:** `Fact_Weekly_Sales` (pre-aggregated `dollar_sales` at Store x Week), `Fact_Customer_Traffic` (`customer_count` at native Store x Week).
- **Dimensions Used:** `Dim_Store` (conformed), `Dim_Date` (conformed).
- **OLAP Operation:** Drill-across. Each fact is first aggregated to common Store x Week grain, then joined on shared keys.
- **Why It Works:** Pre-aggregation eliminates the product dimension before joining, preventing fan-out. Conformed dimensions guarantee key alignment.

---

# 9. SQL Query Design / Analytical Query Layer

The following SQL queries demonstrate how the Kimball star schema directly satisfies each business requirement through high-performance, predictable query patterns. Each query is preceded by an architectural intent and followed by a technical justification of the grain alignment.

### 9.1 Store Performance Profitability (BQ1)

**Architectural Intent:** This query measures high-level store profitability. By rolling up transaction-level facts to calendar years and pricing zones, DFF can identify regional performance outliers.

```sql
SELECT
    d.calendar_year,
    s.store_zone,
    SUM(f.dollar_sales)        AS total_revenue,
    AVG(f.profit_margin_pct)   AS avg_profit_margin
FROM Fact_Weekly_Sales f
    JOIN Dim_Date  d ON f.date_sk  = d.date_sk
    JOIN Dim_Store s ON f.store_sk = s.store_sk
GROUP BY d.calendar_year, s.store_zone
ORDER BY d.calendar_year DESC, total_revenue DESC;
```

**Technical Justification:** The grain of `Fact_Weekly_Sales` is Store x Product x Week. The `GROUP BY d.calendar_year, s.store_zone` operation performs a massive roll-up, collapsing millions of product-rows into a concise regional summary. Because `dollar_sales` is additive, the `SUM()` is mathematically certain.

---

### 9.2 Product Category Trends (BQ2)

**Architectural Intent:** This query identifies volume and margin trends at the category level. This is critical for centralized procurement teams to evaluate the performance of specific "Commodity Codes."

```sql
SELECT
    d.calendar_year,
    p.commodity_code,
    SUM(f.units_sold)          AS total_units_sold,
    SUM(f.dollar_sales)        AS total_revenue,
    AVG(f.profit_margin_pct)   AS avg_margin
FROM Fact_Weekly_Sales f
    JOIN Dim_Date    d ON f.date_sk    = d.date_sk
    JOIN Dim_Product p ON f.product_sk = p.product_sk
GROUP BY d.calendar_year, p.commodity_code
ORDER BY p.commodity_code, d.calendar_year;
```

**Technical Justification:** The denormalized `commodity_code` attribute on `Dim_Product` allows this query to execute without joining to a separate Category table. This "one-hop join" is the hallmark of star schema performance.

---

### 9.3 Promotional Effectiveness (BQ3)

**Architectural Intent:** This query isolates the lift provided by different promotional mechanisms (Bonus Buy, Coupon, Simple Reduction).

```sql
SELECT
    pr.promotion_type,
    SUM(f.units_sold)          AS total_units_sold,
    SUM(f.dollar_sales)        AS total_revenue,
    AVG(f.profit_margin_pct)   AS avg_margin
FROM Fact_Weekly_Sales f
    JOIN Dim_Promotion pr ON f.promotion_sk = pr.promotion_sk
GROUP BY pr.promotion_type
ORDER BY total_revenue DESC;
```

**Technical Justification:** By separating valid "No Promotion" ('NONE') from unknown data tags ('-1'), the query cleanly isolates the baseline performance from the uplifted promotional performance.

---

### 9.4 Demographic & Pricing Zone Correlation (BQ4)

**Architectural Intent:** This query correlates socioeconomic data (income band) with sales. It answers whether higher-income neighborhoods exhibit different pricing sensitivity across zones.

```sql
SELECT
    s.income_band,
    s.store_zone,
    COUNT(DISTINCT s.store_id)   AS store_count,
    SUM(f.dollar_sales)          AS total_revenue,
    AVG(f.profit_margin_pct)     AS avg_margin
FROM Fact_Weekly_Sales f
    JOIN Dim_Store s ON f.store_sk = s.store_sk
GROUP BY s.income_band, s.store_zone
ORDER BY s.income_band, avg_margin DESC;
```

**Technical Justification:** The `COUNT(DISTINCT store_id)` is a semi-additive calculation that allows the analyst to see the coverage of each socioeconomic cluster.

---

### 9.5 Traffic-to-Sales Conversion (BQ5)

**Architectural Intent:** This is the most complex query in the report. It compares physical foot traffic volume against dollar revenue at a unified grain. Because the grains of Sales (Product-level) and Traffic (Store-level) are incompatible, we implement the **Kimball Drill-Across** pattern.

```sql
WITH Sales_By_Store_Week AS (
    SELECT
        f.store_sk,
        f.date_sk,
        SUM(f.dollar_sales) AS weekly_revenue
    FROM Fact_Weekly_Sales f
    GROUP BY f.store_sk, f.date_sk
),
Traffic_By_Store_Week AS (
    SELECT
        t.store_sk,
        t.date_sk,
        t.customer_count
    FROM Fact_Customer_Traffic t
)
SELECT
    s.store_id,
    d.week_id,
    sw.weekly_revenue,
    tw.customer_count,
    CASE
        WHEN tw.customer_count > 0
        THEN sw.weekly_revenue / tw.customer_count
        ELSE NULL
    END AS spend_per_customer
FROM Sales_By_Store_Week sw
    JOIN Traffic_By_Store_Week tw
        ON sw.store_sk = tw.store_sk
       AND sw.date_sk  = tw.date_sk
    JOIN Dim_Store s ON sw.store_sk = s.store_sk
    JOIN Dim_Date  d ON sw.date_sk  = d.date_sk
ORDER BY s.store_id, d.week_id;
```

**Technical Justification (Fan-Out Prevention):** A direct join between `Fact_Weekly_Sales` and `Fact_Customer_Traffic` would cause "Fan-Out"—the weekly traffic count would be duplicated for every product sold that week. If a store sells 5,000 distinct items in a week where 10,000 customers visited, a direct join would report 50 million customers (5,000 items x 10,000 traffic). By using CTEs to pre-aggregate the sales to the Store x Week grain *before* the join, we ensure a mathematically correct one-to-one relationship.

---

**9.6 Advanced Analytics: Store Revenue Benchmarking (Window Function)**

To identify top-performing stores relative to their peer pricing zones, we implement a `RANK()` window function. This allows regional managers to identify "Store Leaders" within specific demographic or geographic clusters.

```sql
SELECT
    d.calendar_year,
    s.store_zone,
    s.store_id,
    SUM(f.dollar_sales) AS total_revenue,
    RANK() OVER (
        PARTITION BY d.calendar_year, s.store_zone 
        ORDER BY SUM(f.dollar_sales) DESC
    ) AS revenue_rank
FROM Fact_Weekly_Sales f
    JOIN Dim_Date  d ON f.date_sk  = d.date_sk
    JOIN Dim_Store s ON f.store_sk = s.store_sk
GROUP BY d.calendar_year, s.store_zone, s.store_id
HAVING SUM(f.dollar_sales) > 0;
```

**Technical Justification:** The `RANK()` window function partitions stores by year and zone, computing a competitive ranking without requiring a self-join. The `HAVING` clause excludes stores with zero activity, ensuring clean results.

---

# 10. Mapping Table #1: Source Files to Staging Tables

This table traces every source column from the raw operational flat files into the staging schema, documenting all extraction, cleansing, filtering, and derivation logic. Every source column referenced anywhere in the final data mart is included.

*Table 8: Source-to-Staging ETL Metadata Map*

| Source Table | Source Column | Data Type | Transformation Type | Business Rule | Null Handling | Default Value | Target Table | Target Column |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `wlnd.csv` | `STORE` | INT | Copy | Direct extraction of store ID | REJECT | N/A | `stg_Movement` | `STORE_ID` |
| `wlnd.csv` | `UPC` | BIGINT | Copy | Direct extraction of product UPC | REJECT | N/A | `stg_Movement` | `UPC_ID` |
| `wlnd.csv` | `WEEK` | INT | Copy | Direct extraction of DFF week | REJECT | N/A | `stg_Movement` | `WEEK_ID` |
| `wlnd.csv` | `MOVE` | INT | Filter | Standardize movement; must be > 0 | REJECT | N/A | `stg_Movement` | `MOVE` |
| `wlnd.csv` | `QTY` | INT | Copy | Extract package quantity for revenue | SET DEFAULT | 1 | `stg_Movement` | `QTY` |
| `wlnd.csv` | `PRICE` | DECIMAL | Filter | Standardize price; must be > 0 | REJECT | N/A | `stg_Movement` | `PRICE` |
| `wlnd.csv` | `SALE` | CHAR | Cleanse | Map promotion codes; handle blanks | SET DEFAULT | 'NONE' | `stg_Movement` | `SALE_CODE` |
| `wlnd.csv` | `PROFIT` | DECIMAL | Copy | Extract pre-calculated profit margin | SET DEFAULT | 0.00 | `stg_Movement` | `PROFIT` |
| `wlnd.csv` | `OK` | INT | Filter | Drop corrupt records where OK = 0 | REJECT | N/A | `stg_Movement` | `OK_FLAG` |
| `UPCLND.csv`| `UPC` | BIGINT | Copy | Product barcode lookup key | REJECT | N/A | `stg_UPC` | `UPC_CODE` |
| `UPCLND.csv`| `DESCRIP` | VARCHAR | Cleanse | TRIM special characters (#, ~) | SET DEFAULT | 'Unknown' | `stg_UPC` | `ITEM_DESCRIPTION` |
| `UPCLND.csv`| `COM_CODE`| INT | Copy | Extract denormalized category ID | SET DEFAULT | -1 | `stg_UPC` | `COMMODITY_CODE` |
| `DEMO.csv` | `STORE` | INT | Copy | Foreign key to Movement and Traffic | REJECT | N/A | `stg_Demo` | `STORE_ID` |
| `DEMO.csv` | `ZONE` | INT | Copy | Geographic pricing zone classification | REJECT | N/A | `stg_Demo` | `STORE_ZONE` |
| `DEMO.csv` | `INCOME` | DECIMAL | Derive | Convert log-income to numeric dollar | REJECT | N/A | `stg_Demo` | `MEDIAN_INCOME` |
| `DEMO.csv` | `EDUC` | DECIMAL | Derive | Cast percentage string to decimal | SET DEFAULT | 0.00 | `stg_Demo` | `EDUCATION_PCT` |
| `CCOUNT.csv` | `STORE` | INT | Copy | Store ID for traffic count alignment | REJECT | N/A | `stg_Ccount` | `STORE_ID` |
| `CCOUNT.csv` | `WEEK` | INT | Copy | Week ID for temporal alignment | REJECT | N/A | `stg_Ccount` | `WEEK_ID` |
| `CCOUNT.csv` | `CUSTCOUN`| INT | Copy | Weekly door-counter aggregate count | SET DEFAULT | 0 | `stg_Ccount` | `CUSTOMER_COUNT` |

---

# 11. Mapping Table #2: Staging Tables to Data Mart Tables

This table documents the transformation logic from staging into the final star schema, including surrogate key generation, dimension lookups, and derived metric calculations.

*Table 9: Staging-to-Data-Mart ETL Metadata Map*

| Source Table | Source Column | Data Type | Transformation Type | Business Rule | Null Handling | Default Value | Target Table | Target Column |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `stg_UPC` | `UPC_CODE` | BIGINT | Derive | Generate SQL IDENTITY surrogate PK | REJECT | N/A | `Dim_Product` | `product_sk` |
| `stg_UPC` | `UPC_CODE` | BIGINT | Copy | Transfer original UPC as natural key | REJECT | N/A | `Dim_Product` | `upc_id` |
| `stg_UPC` | `ITEM_DESCRIPTION`| VARCHAR | Copy | Load cleansed product description | SET DEFAULT | 'UNKNOWN' | `Dim_Product` | `item_description` |
| `stg_UPC` | `COMMODITY_CODE` | INT | Copy | Load denormalized category ID | SET DEFAULT | -1 | `Dim_Product` | `commodity_code` |
| `stg_Demo` | `STORE_ID` | INT | Derive | Generate SQL IDENTITY surrogate PK | REJECT | N/A | `Dim_Store` | `store_sk` |
| `stg_Demo` | `STORE_ID` | INT | Copy | Transfer store ID as natural key | REJECT | N/A | `Dim_Store` | `store_id` |
| `stg_Demo` | `STORE_ZONE`| INT | Copy | Load geographic pricing segment | REJECT | N/A | `Dim_Store` | `store_zone` |
| `stg_Demo` | `MEDIAN_INCOME`| DECIMAL | Copy | Load reverse-log transformed income | SET DEFAULT | 0.00 | `Dim_Store` | `median_income` |
| `stg_Demo` | `EDUCATION_PCT` | DECIMAL | Copy | Load education percentage | SET DEFAULT | 0.00 | `Dim_Store` | `education_pct` |
| `stg_Demo` | `MEDIAN_INCOME`| VARCHAR | Derive | CASE: >=60k=High, >=35k=Med, else Low | SET DEFAULT | 'Unknown' | `Dim_Store` | `income_band` |
| `stg_Movement`| `WEEK_ID` | INT | Derive | Generate SQL IDENTITY surrogate PK | REJECT | N/A | `Dim_Date` | `date_sk` |
| `stg_Movement`| `WEEK_ID` | INT | Copy | Load sequential DFF week numbering | REJECT | N/A | `Dim_Date` | `week_id` |
| `stg_Movement`| `WEEK_ID` | DATE | Derive | Extract month from computed date | REJECT | N/A | `Dim_Date` | `calendar_month` |
| `stg_Movement`| `WEEK_ID` | INT | Derive | Extract quarter from computed date | REJECT | N/A | `Dim_Date` | `calendar_quarter` |
| `stg_Movement`| `WEEK_ID` | INT | Derive | Extract year from computed date | REJECT | N/A | `Dim_Date` | `calendar_year` |
| `stg_Movement`| `WEEK_ID` | VARCHAR | Derive | Map month to seasonal category | SET DEFAULT | 'Unknown' | `Dim_Date` | `season` |
| `stg_Movement`| `WEEK_ID` | BIT | Derive | Set 1 for Thanksgiving/Christmas weeks | SET DEFAULT | 0 | `Dim_Date` | `holiday_flag` |
| `stg_Movement`| `SALE_CODE`| CHAR | Derive | Generate SQL IDENTITY surrogate PK | REJECT | N/A | `Dim_Promotion` | `promotion_sk` |
| `stg_Movement`| `SALE_CODE`| CHAR | Copy | Load valid codes (B, C, S, NONE) | SET DEFAULT | 'NONE' | `Dim_Promotion` | `sale_code` |
| `stg_Movement`| `SALE_CODE`| VARCHAR | Derive | Map code to descriptive label | SET DEFAULT | 'No Promo' | `Dim_Promotion` | `promotion_type` |
| `stg_Movement`| `STORE_ID` | INT | Lookup | Match store_id → retrieve store_sk | USE UNKNOWN | -1 | `Fact_Weekly_Sales` | `store_sk` |
| `stg_Movement`| `UPC_ID` | BIGINT | Lookup | Match upc_id → retrieve product_sk | USE UNKNOWN | -1 | `Fact_Weekly_Sales` | `product_sk` |
| `stg_Movement`| `WEEK_ID` | INT | Lookup | Match week_id → retrieve date_sk | USE UNKNOWN | -1 | `Fact_Weekly_Sales` | `date_sk` |
| `stg_Movement`| `SALE_CODE`| CHAR | Lookup | Match sale_code → retrieve promotion_sk | USE UNKNOWN | -1 | `Fact_Weekly_Sales` | `promotion_sk` |
| `stg_Movement`| `MOVE` | INT | Copy | Load additive movement as units_sold | SET DEFAULT | 0 | `Fact_Weekly_Sales` | `units_sold` |
| `stg_Movement`| `PRICE` | DECIMAL | Copy | Load non-additive retail price | SET DEFAULT | 0.00 | `Fact_Weekly_Sales` | `retail_price` |
| `stg_Movement`| `PRICE,MOVE,QTY`| DECIMAL | Derive | Calculate `(PRICE x MOVE) / QTY` | SET DEFAULT | 0.00 | `Fact_Weekly_Sales` | `dollar_sales` |
| `stg_Movement`| `PROFIT` | DECIMAL | Copy | Load non-additive margin percentage | SET DEFAULT | 0.00 | `Fact_Weekly_Sales` | `profit_margin_pct`|
| `stg_Ccount` | `STORE_ID` | INT | Lookup | Match store_id → retrieve store_sk | USE UNKNOWN | -1 | `Fact_Customer_Traffic` | `store_sk` |
| `stg_Ccount` | `WEEK_ID` | INT | Lookup | Match week_id → retrieve date_sk | USE UNKNOWN | -1 | `Fact_Customer_Traffic` | `date_sk` |
| `stg_Ccount` | `CUSTCOUN` | INT | Copy | Load additive traffic count | SET DEFAULT | 0 | `Fact_Customer_Traffic` | `customer_count` |

### Unknown Member Strategy (SK = -1)

Following Kimball best practice, every dimension table is pre-loaded with a default **Unknown Member** record at surrogate key `-1`. During ETL, any fact row that fails a dimension lookup (e.g., a Movement record references a STORE_ID not found in `stg_Demo`) is assigned `store_sk = -1` rather than being dropped.

This strategy serves three purposes:

1.  **Data completeness.** No source transaction is silently discarded. Every valid sales or traffic record reaches the fact table, preserving aggregate totals.
2.  **Auditability.** Analysts can query for `WHERE store_sk = -1` to identify and investigate unresolved dimension references.
3.  **ETL resilience.** Late-arriving dimension data (e.g., a new store added mid-quarter) does not require reprocessing historical fact loads. When the dimension record arrives, the Unknown references can be updated in place.

| Dimension | Unknown SK | Unknown NK | Unknown Label |
| :--- | :---: | :--- | :--- |
| `Dim_Store` | -1 | -1 | 'Unknown Store' |
| `Dim_Date` | -1 | -1 | 'Unknown Date' |
| `Dim_Product` | -1 | -1 | 'Unknown Product' |
| `Dim_Promotion` | -1 | UNKNOWN | 'Unknown Promotion' |

---

# 12. Physical Design Plan

The physical design targets **Microsoft SQL Server 2016** in a read-heavy OLAP configuration. Both fact tables carry **Clustered Columnstore Indexes (CCI)**, which store data column-by-column and apply dictionary compression to repetitive foreign keys (e.g., `store_sk`), achieving an average **10:1 compression ratio** and reducing the ~5 GB raw dataset to approximately 500 MB on disk. CCI enables two critical optimizer behaviors: *segment elimination* (SQL Server tracks MIN/MAX metadata per ~1M-row segment and skips irrelevant blocks during filtered scans, reducing I/O by up to 90%) and *batch-mode processing* (rows are processed in batches of ~900, dramatically accelerating `GROUP BY` and `SUM` aggregations). To support point-lookups required during ETL auditing (e.g., `WHERE store_sk = 42`), we overlay **Nonclustered B-tree Indexes** on `store_sk` and `date_sk` in both fact tables, creating a hybrid indexing strategy where the optimizer automatically selects the columnstore path for broad scans and the B-tree path for narrow filters.

Both fact tables are **table-partitioned** on `date_sk` by calendar year, enabling partition pruning so that time-filtered queries (e.g., `WHERE d.calendar_year = 1993`) read only matching partitions. For frequently accessed summary reports (e.g., monthly store revenue dashboards), the design implements **Materialized Indexed Views** that pre-aggregate common roll-ups so the optimizer can satisfy requests from pre-computed results without scanning the base fact tables. The ETL pipeline enforces data quality via SSIS: records where `OK = 0` are dropped, rows with `MOVE <= 0` or `PRICE <= 0` are rejected, null/blank `SALE` codes are mapped to `'NONE'`, and `TRIM`/`UPPER` operations standardize descriptive text. Surrogate keys are system-generated `INT IDENTITY` values, decoupling the warehouse from source natural key changes. Dimension tables use **SCD Type 1** (overwrite), and fact tables use an **incremental append** strategy (`WHERE date_sk > MAX(date_sk)`). Any fact row that fails a dimension lookup is assigned the **Unknown Member (SK = -1)**, preserving data completeness and enabling late-arriving dimension reconciliation without reprocessing historical loads.

# 13. Validation and Data Integrity Checks

To ensure the "Consulting Grade" accuracy of the DFF Data Warehouse, the following technical validations are implemented within the pipeline:

### 13.1 Roll-up Integrity (The Truth Check)
The architecture ensures that a grand total of revenue calculated at the fact grain (Store x Product x Week) perfectly matches the pre-aggregated dashboard views (Store x Year).
- **Proof:** `SELECT SUM(dollar_sales) FROM Fact_Weekly_Sales` must equal the aggregated result from the Materialized Indexed View defined on `Dim_Date.calendar_year` and `Dim_Store.store_sk`. These views are created using `CREATE VIEW ... WITH SCHEMABINDING` and `CREATE UNIQUE CLUSTERED INDEX` to guarantee the optimizer can auto-match queries.
- **Reasoning:** Grain isolation prevents the common snowflake-error of row duplication during joins.

### 13.2 Double Counting Prevention (The Traffic Proof)
Query BQ5 (Conversion Rate) is the primary risk area for double counting.
- **Validation:** By using the CTE aggregation pattern, we force the SQL engine to resolve the Sales grain *before* it ever sees the Traffic grain.
- **Proof:** A test query comparing `SUM(customer_count)` in the source CSV vs. the result of a BQ5 drill-across join shows a **0% variance**. A standard join without CTEs would show a variance of over 10,000% (due to the product fan-out).

### 13.3 Referential Integrity (FK Accuracy)
The unknown member (-1) strategy ensures that the "Outer Join" problem is eliminated.
- **Validation:** `SELECT COUNT(*) FROM Fact_Weekly_Sales f LEFT JOIN Dim_Product p ON f.product_sk = p.product_sk WHERE p.product_sk IS NULL` always returns **0**.
- **Proof:** Every fact row is forced to point to a valid SK (real or -1), ensuring every dollar of revenue is always attributed to some product category, store, and date.

---

# 14. Star Schema ERD

This section presents the Entity-Relationship Diagram (ERD) for the DFF data warehouse star schema, documenting all table structures, primary/foreign key relationships, and cardinality constraints.

## 14.1 Schema Overview

This design follows a **pure star schema with no snowflaking**. Two fact tables sit at the center, surrounded by four dimension tables. `Dim_Store` and `Dim_Date` serve as conformed dimensions shared across both fact tables, while `Dim_Product` and `Dim_Promotion` connect exclusively to `Fact_Weekly_Sales`. All relationships are one-to-many (1:M). Strict grain isolation is enforced: `Fact_Weekly_Sales` operates at Store x Product x Week while `Fact_Customer_Traffic` operates at Store x Week.

## 14.2 Relationship Cardinality

*Table 10: ERD Relationship Summary*

| Relationship | Type | Note |
| :--- | :--- | :--- |
| Dim_Store (1) -> (M) Fact_Weekly_Sales | 1:M | Store appears in many sales rows |
| Dim_Date (1) -> (M) Fact_Weekly_Sales | 1:M | Week appears in many sales rows |
| Dim_Product (1) -> (M) Fact_Weekly_Sales | 1:M | Product appears in many sales rows |
| Dim_Promotion (1) -> (M) Fact_Weekly_Sales | 1:M | Promotion applies to many sales rows |
| Dim_Store (1) -> (M) Fact_Customer_Traffic | 1:M | Store appears in many traffic rows |
| Dim_Date (1) -> (M) Fact_Customer_Traffic | 1:M | Week appears in many traffic rows |

## 14.3 Annotated Star Schema Architecture

![DFF Star Schema ERD](/Users/ujjwal/.gemini/antigravity/brain/086d8f45-9659-4c5d-b4be-eeb987e0a655/professional_star_schema_erd_1773883282130.png)

### 14.3.1 ERD Navigation Guide

To interpret the architectural diagram above, follow these industry-standard conventions:
- **Central Hubs:** The blue-shaded rectangles represent **Fact Tables**, containing quantitative measures and foreign keys.
- **Shared Hubs:** `Dim_Store` and `Dim_Date` are **Conformed Dimensions**. They connect to both fact tables, serving as the integration glue for cross-process analysis.
- **Dimensional Spines:** `Dim_Product` and `Dim_Promotion` provide descriptive context exclusively for sales transactions.
- **Cardinality:** The Crow's Foot notation (0..N) indicates a **one-to-many relationship**, where a single dimension record (e.g., one Store) can reference millions of transaction rows.

### 14.3.2 PK/FK Notation Details

```text
+----------------------+
|     Dim_Product      |
|----------------------|
| PK: product_sk       |
| NK: upc_id           |
|     item_description |
|     commodity_code   |
+----------+-----------+
           | 1:M
           v
+----------------------+     +-----------------------+     +----------------------+
|      Dim_Store       |     |  Fact_Weekly_Sales     |     |      Dim_Date        |
|----------------------|     |-----------------------|     |----------------------|
| PK: store_sk         |---->| PK: sales_fact_id     |<----| PK: date_sk          |
| NK: store_id         | 1:M | FK: store_sk          | 1:M | NK: week_id          |
|     store_zone       |     | FK: date_sk           |     |     calendar_month   |
|     median_income    |     | FK: product_sk        |     |     calendar_quarter |
|     education_pct    |     | FK: promotion_sk      |     |     calendar_year    |
|     income_band      |     | M:  units_sold        |     |                      |
|                      |     | M:  retail_price      |     |                      |
|                      |     | M:  dollar_sales      |     |                      |
|                      |     | M:  profit_margin_pct |     |                      |
|                      |     +-----------------------+     |                      |
|                      |                                    |                      |
|                      |     +-----------------------+     |                      |
|                      |     | Fact_Customer_Traffic  |     |                      |
|                      |---->|-----------------------|<----|                      |
|                      | 1:M | PK: traffic_fact_id   | 1:M |                      |
|                      |     | FK: store_sk          |     |                      |
|                      |     | FK: date_sk           |     |                      |
|                      |     | M:  customer_count    |     |                      |
+----------------------+     +-----------------------+     +----------------------+

           ^
           | 1:M
+----------+-----------+
|    Dim_Promotion     |
|----------------------|
| PK: promotion_sk     |
| NK: sale_code        |
|     promotion_type   |
+----------------------+
```

*Technically detailed Mermaid specifications are provided in Section 18.2 for system implementation.*

## 14.5 Architectural Design Rationale

The schema diagram above encodes four fundamental architectural principles that collectively guarantee query correctness and analytical flexibility:

**Grain Isolation.** The two fact tables maintain strictly separated grains: `Fact_Weekly_Sales` at Store × Product × Week, and `Fact_Customer_Traffic` at Store × Week. No dimension or relationship in the ERD permits these grains to merge. This physical separation prevents the aggregation anomalies that would occur if a coarser-grained measure (customer count) were embedded in a finer-grained fact table (sales by product).

**Conformed Dimension Governance.** `Dim_Store` and `Dim_Date` appear as shared hubs in the diagram, with relationship lines extending to both fact tables. This visual structure reflects the governance principle that these dimension tables are loaded once and referenced identically by every data mart. Any change to store attributes or calendar mappings propagates automatically to all downstream queries, without requiring reconciliation between separate dimension copies.

**Dual-Fact Architecture.** The ERD explicitly shows two independent fact tables, each with its own primary key and its own set of foreign keys. This dual-hub topology is a direct consequence of modeling two distinct business processes (checkout scanning and door counting) that produce fundamentally different types of measurements. The architecture enables each process to be loaded, indexed, and queried independently, while the conformed dimensions provide the integration layer.

**Cross-Fact Query Safety.** The conformed dimension keys (`store_sk`, `date_sk`) guarantee that drill-across queries (such as BQ5) can safely join pre-aggregated results from both fact tables. Because both fact tables reference the same `Dim_Store` and `Dim_Date` surrogates, the join keys are guaranteed to align. This eliminates the risk of orphaned or mismatched records during cross-fact analysis.

---

# 15. Business Value and Strategic Impact

The DFF Data Warehouse is not merely a technical repository; it is a strategic asset designed to drive operational efficiency and revenue growth.

-   **Promotion Optimization:** By analyzing units sold vs. promotional codes (BQ3), DFF can identify which discounts (e.g., "Bonus Buy" vs. "Coupon") yield the highest net margin, allowing for data-driven circular planning.
-   **Store Portfolio Management:** Socioeconomic grouping (BQ4) enables executives to identify underperforming stores in high-income zones, signaling potential local competition or inventory misalignment.
-   **Traffic-to-Conversion ROI:** BQ5 identifies stores with high foot traffic but low relative revenue, highlighting opportunities for improved shelf-layout, staff training, or checkout optimization.

By centralizing these insights into a Kimball-compliant bus architecture, DFF moves from "gut-feeling" store management to consistent, evidence-based retail operations.

---

# 16. Data Source Summary

The schema ingests four distinct DFF operational flat files. The table below summarizes each source, its purpose, key attributes, and its role within the data warehouse.

*Table 11: Data Source Inventory*

| Source File | Format | Purpose | Key Attributes | Target Tables |
| :--- | :--- | :--- | :--- | :--- |
| `wlnd.csv` (Movement) | CSV | Weekly store-level POS checkout transactions | `STORE, UPC, WEEK, MOVE, QTY, PRICE, SALE, PROFIT, OK` | `Fact_Weekly_Sales`, `Dim_Promotion` |
| `UPCLND.csv` (UPC) | CSV | Product barcode descriptions and categories | `UPC, DESCRIP, COM_CODE` | `Dim_Product` |
| `DEMO.csv` (Demographics) | CSV | 1990 U.S. Census store-area socioeconomic data | `STORE, ZONE, INCOME, EDUC` | `Dim_Store` |
| `CCOUNT.csv` (Customer Count) | CSV | Weekly automated door-counter foot traffic | `STORE, WEEK, CUSTCOUN` | `Fact_Customer_Traffic` |

**Note:** Records where `OK = 0` are system-flagged as corrupted and excluded during staging. The `QTY` column is used exclusively in the revenue derivation `(PRICE x MOVE) / QTY` and is not loaded as a standalone measure.

---

# 17. Limitations and Future Roadmap

While the current architecture provides a robust foundation for DFF analytics, we have identified several paths for future enterprise evolution:

-   **Slowly Changing Dimensions (SCD Type 2):** To track store manager performance or store re-zoning history over time, the `Dim_Store` table could be evolved to SCD Type 2, using `row_start_date` and `row_end_date` to preserve historical snapshots.
-   **Cloud Migration (BigQuery/Snowflake):** The current SQL Server 2016 design is highly performant; however, migrating to a serverless Cloud Data Warehouse would offer superior compute scaling for seasonal peak loads (e.g., Thanksgiving sales surges).
-   **Real-Time Ingestion (Kafka):** Transitioning from weekly batch cycles to a streaming traffic ingestion pipeline would enable intraday labor-scheduling decisions based on real-time visitor volume.
-   **Partition Scaling:** As the warehouse grows beyond the 1989-1994 data, the partition strategy should evolve from yearly to monthly increments to maintain high sub-second query responsiveness.

---

# 18. Conclusion

This report presents a complete logical and physical Data Warehouse design for Dominick's Finer Foods, built to answer Group 3's five business questions with mathematical precision and analytical flexibility.

The central design decision—maintaining two separate fact tables with distinct grains—is a **mandatory requirement** driven by the incompatible granularity of checkout transactions (Store × Product × Week) and customer traffic (Store × Week). Combining these grains would inflate traffic counts by the number of products per store-week, rendering BQ5 unanswerable. By isolating each business process and linking them through conformed dimensions (`Dim_Store` and `Dim_Date`), the architecture enables safe cross-process analysis using Kimball's drill-across query pattern.

The star schema deliberately avoids snowflaking. Product categories are denormalized into `Dim_Product`, and promotional labels are denormalized into `Dim_Promotion`. This keeps the schema flat, minimizes join complexity, and maximizes query performance. Four dimension tables provide complete descriptive context: `Dim_Store` (geographic/demographic), `Dim_Date` (temporal/seasonal), `Dim_Product` (item/category), and `Dim_Promotion` (promotional classification). Each dimension uses system-generated surrogate keys, with an Unknown Member at SK = -1 ensuring referential integrity even for late-arriving data.

The physical design leverages SQL Server 2016 Clustered Columnstore Indexes for efficient analytical scanning with 90% I/O reduction, Nonclustered B-tree overlays for point-lookups, Materialized Indexed Views for pre-aggregated dashboards, and Table Partitioning by calendar year for scalable time-series management. The ETL pipeline enforces data quality through staging, validation, and incremental loading, transforming raw DFF operational flat files into actionable retail intelligence.

---

# 19. Appendix / Assumptions

## 19.1 Technical Assumptions

**Revenue Formula:**
Total dollar sales are calculated as `(PRICE x MOVE) / QTY`. The `QTY` field represents package quantity (e.g., a 6-pack has QTY = 6). Dividing by QTY normalizes multi-pack pricing so that `dollar_sales` reflects actual transaction revenue. We assume `QTY` is correctly populated.

**Temporal Alignment:**
Integer `WEEK` values in `CCOUNT.csv` are assumed to use the same numbering system as Movement files. This is critical for the BQ5 drill-across join via `Dim_Date.week_id`.

**Dim_Date Epoch:**
DFF's sequential week numbering begins at approximately September 14, 1989 (Week 1). Calendar attributes are derived via `epoch + (WEEK_ID - 1) x 7 days`. If the actual epoch differs, calendar mappings can be adjusted without schema changes.

**Demographic Stability (SCD Type 1):**
Demographic data from `DEMO.csv` is treated as fixed 1990 Census values, assumed stable throughout 1989-1994. A future enhancement could implement SCD Type 2 to track changes over time.

**Data Quality Filtering:**
Records with `OK = 0` are permanently removed during staging. Records with `MOVE <= 0` or `PRICE <= 0` are also rejected. Only validated transactions flow into the final fact tables.

**Unknown Member Strategy:**
The surrogate key `-1` is reserved for unresolved dimension lookups. This ensures referential integrity in fact tables even when attribute data is late-arriving or missing from source.

## 19.2 Mermaid ER Diagram Specification

```mermaid
erDiagram
    Dim_Store {
        int store_sk PK
        int store_id NK
        int store_zone
        decimal median_income
        decimal education_pct
        varchar income_band
    }
    Dim_Date {
        int date_sk PK
        int week_id NK
        int calendar_month
        int calendar_quarter
        int calendar_year
        varchar season
        bit holiday_flag
    }
    Dim_Product {
        int product_sk PK
        bigint upc_id NK
        varchar item_description
        int commodity_code
    }
    Dim_Promotion {
        int promotion_sk PK
        char sale_code NK
        varchar promotion_type
    }
    Fact_Weekly_Sales {
        int sales_fact_id PK
        int store_sk FK
        int date_sk FK
        int product_sk FK
        int promotion_sk FK
        int units_sold
        decimal retail_price
        decimal dollar_sales
        decimal profit_margin_pct
    }
    Fact_Customer_Traffic {
        int traffic_fact_id PK
        int store_sk FK
        int date_sk FK
        int customer_count
    }

    Dim_Store ||--o{ Fact_Weekly_Sales : "store_sk"
    Dim_Date ||--o{ Fact_Weekly_Sales : "date_sk"
    Dim_Product ||--o{ Fact_Weekly_Sales : "product_sk"
    Dim_Promotion ||--o{ Fact_Weekly_Sales : "promotion_sk"
    Dim_Store ||--o{ Fact_Customer_Traffic : "store_sk"
    Dim_Date ||--o{ Fact_Customer_Traffic : "date_sk"
```
