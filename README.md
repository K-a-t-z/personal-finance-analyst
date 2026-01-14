# Personal Finance Analyst

An explainable, full-stack AI system for analyzing personal financial data with **guaranteed numeric correctness**, **evidence-backed answers**, and a **chat-based interface**.

Built with FastAPI, Next.js, and a deterministic evaluation pipeline to prevent hallucinations in financial analysis.

## Motivation

Many AI-powered personal finance tools today rely heavily on large language models to answer questions about spending, budgets, and trends. While these systems often sound convincing, they frequently suffer from serious issues:

- hallucinated or incorrect numbers
- no clear link between answers and the underlying data
- lack of transparency into how results were computed
- no systematic way to evaluate correctness

For personal finance, these problems are especially critical. Users needs answers that are **numerically correct**, **auditable**, and **trustworthy** – not just fluent.

This project was built to explore a different approach: treating financial analysis as a **deterministic problem first**, and a **language problem second**. Instead of asking an LLM to "figure out" numbers, this system computes all financial results using deterministic code and uses structured logic to interpret user questions.

The goal is to demonstrate how AI systems can be designed to prioritize correctness, explainability, and evaluation – qualities that are essential for real-world, user-facing applications.

## High-Level System Overview

The Personal Finance Analyst is a full-stack system composed of three main layers: a frontend user interface, a backend analysis engine, and a local data store.

At a high level, the system works as follows:

1. The user uploads a CSV file containing personal financial transactions through a web interface.
2. The backend validates and ingests this data into a local SQLite database.
3. The user asks natural-language questions through a chat-based interface.
4. The backend interprets the question, computes the required financial metrics deterministically, and returns:
    - a human-readable answer,
    - the computed numeric results,
    - the supporting evidence rows, and
    - an execution trace explaining how the answer was produced.
5. The frontend renders the response along with expandable views for evidence and trace data.

The frontend is implemented using Next.js and focuses on usability and transparency. The backend is implemented using FastAPI and is responsible for all data validation, computation, and query handling. All financial calculations are performed using deterministic logic to ensure correctness, while natural language is treated as an input and output interface rather than a source of truth.

## Core Design Principles

This project is guided by a small set of core principles that shape every part of the system design.

### 1. Deterministic Logic for Financial Truth
All financial calculations are performed using deterministic code rather than probabilistic models. Expenses, totals, and breakdowns are computed directly from validated transaction data using well-defined metric functions. This guarantees numeric correctness and makes results reproducible and testable.

### 2. Natural Language as an Interface, Not an Authority
Natural language is treated as a way for users to express intent, not as a source of truth. User questions are interpreted to extract structured intent (such as time period, category, merchant, or source), but the language model or routing logic never invents or modifies numbers.

### 3. Evidence-Backed Answers
Every numeric answer returned by the system is accompanied by the underlying transaction rows that contributed to the result. This allows users to verify outputs directly against their data and prevents "black box" answers.

### 4. Transparent Execution Traces
Each response includes a structured execution trace that records the detected intent, applied filters, and metric functions that were executed. This makes the system debuggable, auditable, and easy to reason about during development and evaluation.

### 5. Evaluation as a First-Class Feature
Correctness is not assumed – it is measured. The system includes an evaluation harness that automatically tests intent routing, numeric accuracy, evidence compliance, and trace completeness across a suite of natural-language queries. This ensures reliability even as the system evolves.

## Backend Architecture (FastAPI)

The backend is implemented using FastAPI and is responsible for all data validation, computation, and query handling. It is designed to be deterministic, testable, and transparent.

### Data Ingestion
Users upload a CSV file containing financial transactions. During ingestion:

- The CSV schema is validated to ensure required columns are present.
- Dates, amounts, categories, and sources are parsed and normalized.
- Amounts are handled using precise decimal arithmetic.
- Transactions are stored in a local SQLite database.

To avoid accidental duplication, the ingestion endpoint supports a *replace mode*, where uploading a new CSV clears previously ingested data before inserting the new dataset.

### Deterministic Metric Engine
All financial computations are implemented as deterministic functions operating directly on the database. Examples include:

- total monthly expenses
- category-wise spending
- merchant-wise spending
- source-wise spending
- breakdowns and rankings

These functions are pure with respect to their inputs and always return reproducible results for the same data.

### Query Routing and Intent Handling
When a user submits a question, the backend:

1. Extracts the relevant time period (e.g., month).
2. Identifies the user's intent (such as monthly summary, category total, merchant total, or source total).
3. Extracts any relevant entities (category, merchant, or source).
4. Routes the request to the appropriate metric function.

Intent routing is rule-based and prioritized to ensure predictable behavior and easy evaluation.

### Evidence Retrieval
For every numeric result, the backend retrieves the exact set of transaction rows that contributed to the computation. Evidence is filtered using the same parameters as the metric function, ensuring consistency between reported numbers and supporting data.

### Execution Trace
Each response includes a structured execution trace that records:

- the detected intent,
- the resolved time period,
- applied filters,
- the metric functions invoked, and
- the number of evidence rows returned.

This trace enables debugging, auditing, and systematic evaluation of system behavior.

## Frontend Architecture (Next.js UI)

The frontend is implemented using Next.js and provides a simple, transparent interface for interacting with the system. Its primary goal is not visual complexity, but clarity and trust.

### CSV Upload Flow
Users begin by uploading a CSV file containing their financial transactions. The interface clearly indicates which dataset is currently active, ensuring users always know which data is being analyzed. Uploading a new CSV replaces the existing dataset in the backend, preventing accidental duplication.

### Chat-Based Query Interface
Once a dataset is loaded, users can ask natural-language questions through a chat-style interface. This interaction model mirrors modern AI tools while maintaining a clear separation between conversational input and deterministic computation.

### Result Presentation
Each response returned by the backend is rendered with multiple layers of transparency:

- A concise, human-readable answer summarizing the result.
- An expandable evidence table showing the individual transactions that contributed to the answer.
- A structured execution trace that explains how the system interpreted and processed the query.

This layered presentation allows users to quickly read answers while still having access to full details when needed.

### Navigation and Dataset Awareness
The interface includes clear navigation options to return to the home or upload view, allowing users to reset or replace their dataset at any time. This reinforces the idea that all answers are grounded in the currently selected data.

## End-to-End Query Flow

The following steps describe how a user query is processed from input to final response:

1. **User Input**
    The user submits a natural-language question through the chat interface, such as "How much did I spend on Food in June 2025?"

2. **Intent and Entity Extraction**
    The backend analyzes the question to extract structured information, including:
    - the time period (e.g., June 2025),
    - the query intent (e.g., category total), and
    - any relevant entities (e.g., the "Food" category).

3. **Deterministic Metric Execution**
    Based on the extracted intent, the backend routes the request to the appropriate deterministic metric function. This function computes the result directly from the database using validated transaction data.

4. **Evidence Selection**
    Using the same filters applied during computation, the backend retrieves the exact transaction rows that contributed to the numeric result. This guarantees consistency between the reported numbers and the supporting data.

5. **Trace Construction**
    A structured execution trace is generated, recording the detected intent, applied filters, metric functions executed, and evidence count. This trace provides a transparent explanation of how the answer was produced.

6. **Response Assembly**
    The backend returns a structured response containing:
    - a human-readable answer,
    - numeric values,
    - supporting evidence, and
    - the execution trace.

7. **Frontend Rendering**
    The frontend displays the answer in the chat interface, with expandable sections for evidence and trace data, allowing users to inspect results at their desired level of detail.

## Evaluation & Correctness Guarantees

Correctness is treated as a first-class concern in this project. Rather than assuming that the system behaves correctly, an explicit evaluation harness is used to continuously verify its behavior against real data.

### Evaluation Harness
The project includes a custom evaluation runner that executes a suite of natural-language questions against the backend and validates the system’s responses. Each evaluation case specifies the expected intent, filters, and numeric results.

The evaluation process checks multiple dimensions:

- **Intent correctness**: whether the system routes the question to the correct metric logic.
- **Numeric accuracy**: whether computed totals and breakdowns exactly match ground-truth values.
- **Evidence compliance**: whether every numeric result is supported by concrete transaction rows.
- **Trace completeness**: whether execution traces include all required fields.
- **Clarification behavior**: whether the system correctly asks follow-up questions when required information is missing.

### Real-Data Evaluation
The evaluation runner can operate directly on user-provided datasets, ensuring that results reflect real transaction data rather than synthetic examples. This avoids overfitting system behavior to artificial test cases and surfaces realistic edge cases.

### Results
After iterative refinement of intent routing and query handling, the system achieves a 100% pass rate across the evaluation suite. This guarantees that, for the supported query types, all answers are numerically correct, evidence-backed, and traceable.

By explicitly measuring correctness at the system level, this project demonstrates how AI-driven applications can be built with reliability and accountability in mind.

## Example Query & Response

**User question:**

> How much did I spend on Food in June 2025?

**System response:**

> You spent $59.87 on Food in 2025-06 across 6 transactions.


**Supporting evidence (excerpt):**

| Date       | Merchant                 | Description | Amount | Category | Source |
|------------|--------------------------|-------------|--------|----------|--------|
| 2025-06-30 | Strings Ramen            | Ramen       | 23.71  | Food     | Chase  |
| 2025-06-31 | Burger Federation        | Avocado toast | 12.29 | Food     | Chase  |
| 2025-06-28 | Thai Essence             | Noodles     | 10.00  | Food     | Chase  |
| ...        | ...                      | ...         | ...    | ...      | ...    |

**Execution trace (excerpt):**

```json
{
  "intent": "category_total",
  "resolved_month": "2025-06",
  "called_functions": ["get_category_total"],
  "filters_used": {
    "month": "2025-06",
    "kind": "expense",
    "category": "Food"
  },
  "evidence_count_returned": 6
}
```

This response demonstrates how every numeric answer is directly linked to the underlying data and accompanied by a transparent execution trace.

## Tech Stack

**Backend**
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- Pytest

**Frontend**
- Next.js (App Router)
- TypeScript
- TailwindCSS

**Evaluation & Tooling**
- Custom Python evaluation harness
- Deterministic metric testing
- Evidence and trace validation

## Running the Project Locally

The project consists of a FastAPI backend and a Next.js frontend. Both can be run locally with minimal setup.

### Backend Setup

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the backend server:

```bash
uvicorn app.main:app --reload
```

The backend will be available at:
```
http://127.0.0.1:8000
```

### Frontend Setup

In a separate terminal:

```bash
cd web
npm install
npm run dev
```

The frontend will be available at:
```
http://localhost:3000
```

### Using the Application

1. Open the frontend in your browser.
2. Upload a CSV file containing financial transactions.
3. Navigate to the chat interface.
4. Ask natural-language questions about your data.

Uploading a new CSV replaces the existing dataset in the backend.

## Data Privacy & Safety

This project is designed with data privacy in mind.

- No financial data is committed to the repository.
- All transaction data is provided by the user via CSV upload.
- Data is stored locally in a SQLite database during runtime.
- The database file is excluded from version control via `.gitignore`.

The system does not transmit financial data to external services. Users retain full control over their data at all times.

## Future Improvements

While the current system focuses on correctness, transparency, and evaluation, there are several natural extensions that could be explored:

- **LLM-based response narration**
    Introduce an optional language model layer to rewrite deterministic results into more conversational responses, while keep all numeric computation and evidence selection deterministic.

- **Richer query support**
    Extend intent handling to support comparisons across months, trend analysis, and custom time ranges.

- **Multiple dataset management**
    Allow users to switch between multiple uploaded datasets instead of replacing the active one.

- **Deployment and authentication**
    Add user authentication and deploy the system to a cloud environment, enabling persistent, per-user datasets.

These extensions would preserve the system's core guarantees while expanding its usability and scope.