# FinTrace — Frontend Application

> **React 18 Single-Page Application for Financial Claim Verification & Decision Intelligence**

The FinTrace frontend provides a clean user interface for retail and institutional investors to analyze financial claims, explore evidence disclosures, participate in the Virtual Decision Lab, and monitor critical thinking calibration.

---

## 1. Architecture & Key Pages

- **Investor Dashboard (`InvestorDashboard.jsx`):** High-level overview of claims submitted, analyses executed, decisions recorded, and learning evaluation progress.
- **Claim Analysis (`AnalyseClaim.jsx` & `ClaimAnalysisReport.jsx`):** End-to-end statement submission and structured report viewing, including falsifiability criteria, multi-model consensus, and supporting/contradictory evidence.
- **Virtual Decision Lab (`VirtualDecisionLab.jsx`):** Counterfactual decision workbench allowing investors to record initial decisions, inspect statutory disclosures, revise stances, and observe sensitivity shifts.
- **Decision Intelligence (`DecisionIntelligence.jsx`):** Progress tracking across the 5 evaluation rubric dimensions with stage comparisons.
- **Evidence Centre (`EvidenceCentre.jsx`):** Direct repository of statutory regulatory filings retrieved from NSE India and SEC EDGAR.
- **Authentication (`Login.jsx`, `Registration.jsx`, `SettingsProfile.jsx`):** Secure user management with JWT handling and persistent profile editing.

---

## 2. API Communication & Mock Elimination

All pages communicate exclusively with live FastAPI endpoints via `src/services/api.js`:
- Zero synthetic demonstration constants (`SYNTHETIC_CLAIMS`, `SYNTHETIC_EVIDENCE`, `SYNTHETIC_USER` eliminated).
- Authentic empty, loading, and error states rendered on all pages.
- Bearer token authentication attached automatically to all API requests.

---

## 3. Development & Production Build

```powershell
# Install dependencies
npm install

# Run local development server
npm run dev

# Run production build
npm run build
```
- Production build targets: `dist/index.html`, `dist/assets/*.css`, `dist/assets/*.js`.
