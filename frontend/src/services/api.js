// FinTrace API Service Client
// Configured to connect to backend if available, with robust fallback to synthetic demonstration data

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Canonical Synthetic Claims Store matching Stitch designs
export const SYNTHETIC_CLAIMS = [
  {
    id: 'claim_mgs_01',
    ticker: 'MGS',
    company: 'Meridian Grid Systems',
    statement: 'MGS will rise 30% in two months on strong grid backlog.',
    date: '18 Nov 2026',
    validationStatus: 'Needs Verification',
    direction: 'Bullish',
    evidenceCoverage: 64,
    sourceUrl: 'https://twitter.com/energy_analyst_pro/status/17258390',
    horizon: '2 months',
    targetPrice: '$192.50',
    currentPrice: '$148.20',
    breakdown: {
      statedTarget: '30% price appreciation',
      impliedHorizon: '60 days (January 2027)',
      primaryCatalyst: 'Contracted substation delivery pipeline',
      missingConditions: [
        'High-voltage transformer delivery lead times',
        'Raw copper cost index fluctuations',
        'Interconnection queue FERC approval timelines'
      ]
    },
    completeness: {
      score: 58,
      provenanceStatus: 'USER-PROVIDED + PARTIALLY VERIFIED',
      identifiedAssumptions: 4,
      testedAssumptions: 1
    },
    interpretations: [
      {
        fork: 'A: Optimistic Grid Expansion',
        stance: 'Bullish',
        rationale: 'Backlog conversion matches historical FY25 run-rate with gross margin expansion.',
        source: 'AI-GENERATED FORK'
      },
      {
        fork: 'B: Supply Chain Chokepoint',
        stance: 'Neutral / Cautious',
        rationale: 'Transformer vendor lead times now exceed 72 weeks; revenue recognition deferred.',
        source: 'AI-GENERATED FORK'
      },
      {
        fork: 'C: Regulatory Cap Risk',
        stance: 'Bearish Risk',
        rationale: 'State utility commission rate-case filings pending public hearing resistance.',
        source: 'AI-GENERATED FORK'
      }
    ],
    supportingEvidence: [
      {
        id: 'ev_01',
        title: 'MGS Q3 Form 10-Q Contracted Backlog Schedule',
        source: 'SEC EDGAR',
        date: '02 Nov 2026',
        provenance: 'REAL',
        excerpt: 'Reported firm backlog reached $2.4B, with 68% slated for delivery across fiscal 2027.',
        url: 'https://www.sec.gov/edgar/mgs/q3-2026'
      },
      {
        id: 'ev_02',
        title: 'Transformer Input Cost & Lead-Time Briefing',
        source: 'DOE Grid Deployment Office',
        date: '15 Oct 2026',
        provenance: 'REAL',
        excerpt: 'Large power transformer procurement lead times currently average 84-110 weeks across North America.',
        url: 'https://energy.gov/gdo/reports/2026-lpt'
      }
    ],
    contradictoryEvidence: [
      {
        id: 'ev_03',
        title: 'Component Freight Congestion Index',
        provenance: 'SYNTHETIC',
        excerpt: 'Inbound Pacific transit times increased 14% month-over-month for heavy industrial switchgear.'
      }
    ]
  },
  {
    id: 'claim_apxr_02',
    ticker: 'APXR',
    company: 'Apex Renewables',
    statement: 'Apex Renewables capacity will double post-tax credit announcement.',
    date: '18 Nov 2026',
    validationStatus: 'Needs Verification',
    direction: 'Bullish',
    evidenceCoverage: 71,
    sourceUrl: 'https://linkedin.com/posts/cleanpower-brief',
    horizon: '6 months',
    targetPrice: '$42.00',
    currentPrice: '$28.40',
    breakdown: {
      statedTarget: '100% capacity expansion',
      impliedHorizon: '180 days',
      primaryCatalyst: 'Section 45X advanced manufacturing production credit',
      missingConditions: ['Local permitting approval rate', 'Grid tie-in transmission capacity']
    },
    completeness: { score: 62, provenanceStatus: 'SYNTHETIC', identifiedAssumptions: 3, testedAssumptions: 1 },
    interpretations: [
      { fork: 'Tax Credit Flow-through', stance: 'Bullish', rationale: 'Direct monetization accelerates Phase 2 fab.', source: 'AI-GENERATED FORK' }
    ],
    supportingEvidence: [
      { id: 'ev_04', title: 'APXR Investor Day Presentation Deck', source: 'Corporate IR', date: '22 Oct 2026', provenance: 'REAL', excerpt: 'Capacity roadmap models 2.8GW additions subject to interconnection approval.' }
    ]
  },
  {
    id: 'claim_vrtx_03',
    ticker: 'VRTX',
    company: 'Vortex Semiconductors',
    statement: 'Next-gen packaging yields will crush competitor margins.',
    date: '17 Nov 2026',
    validationStatus: 'Completed',
    direction: 'Bullish',
    evidenceCoverage: 88,
    sourceUrl: 'https://semi-analysis.substack.com/p/vortex-yields',
    horizon: '1 year',
    targetPrice: '$115.00',
    currentPrice: '$94.10',
    breakdown: {
      statedTarget: 'Gross margin premium > 600 bps',
      impliedHorizon: '12 months',
      primaryCatalyst: 'Hybrid bonding yield improvement',
      missingConditions: ['Thermal dissipation validation', 'Client qualification cycles']
    },
    completeness: { score: 85, provenanceStatus: 'VERIFIED', identifiedAssumptions: 5, testedAssumptions: 4 },
    interpretations: [
      { fork: 'Yield Moat', stance: 'Bullish', rationale: 'Patent protection blocks second-source foundry adoption.', source: 'AI-GENERATED FORK' }
    ],
    supportingEvidence: [
      { id: 'ev_05', title: 'Patent US-118942-B2: Die-to-Wafer Fusion', source: 'USPTO', date: '14 Sep 2026', provenance: 'REAL', excerpt: 'Approved patent claims cover thermal expansion compensation layers.' }
    ]
  },
  {
    id: 'claim_qntm_04',
    ticker: 'QNTM',
    company: 'Quantum Logistics',
    statement: 'Quantum route optimization cuts fleet fuel burn by 25%.',
    date: '14 Nov 2026',
    validationStatus: 'Provider Unavailable',
    direction: 'Neutral',
    evidenceCoverage: 42,
    sourceUrl: 'https://news.ycombinator.com/item?id=381920',
    horizon: '3 months',
    targetPrice: '$18.00',
    currentPrice: '$17.20',
    breakdown: {
      statedTarget: '25% diesel expense reduction',
      impliedHorizon: '90 days',
      primaryCatalyst: 'Annealing coprocessor dispatching',
      missingConditions: ['Driver compliance', 'Sub-zero battery degradation']
    },
    completeness: { score: 40, provenanceStatus: 'SYNTHETIC', identifiedAssumptions: 4, testedAssumptions: 0 },
    interpretations: [
      { fork: 'Lab Simulation vs Highway Reality', stance: 'Cautious', rationale: 'Bench tests do not account for port dwell congestion.', source: 'AI-GENERATED FORK' }
    ],
    supportingEvidence: []
  }
];

export const SYNTHETIC_EVIDENCE = [
  {
    id: 'ev-sec-mgs-10q',
    title: 'MGS Q3 Form 10-Q Contracted Backlog Schedule',
    source: 'SEC EDGAR · Meridian Grid Systems',
    ticker: 'MGS',
    date: '02 Nov 2026',
    category: 'SEC Filings',
    provenance: 'REAL',
    confidenceScore: 96,
    summary: 'Firm contracted backlog stands at $2.42B, of which $1.64B is slated for recognition across FY 2027.',
    fullText: 'Meridian Grid Systems Inc. filed Form 10-Q for the quarterly period ended September 30, 2026. Note 4: Performance Obligations. As of September 30, 2026, the aggregate amount of the transaction price allocated to remaining performance obligations was $2,420 million. The Company expects to recognize revenue on approximately 68% of these remaining performance obligations over the next 12 to 24 months, with the remaining balance recognized thereafter, subject to timely delivery of primary subcomponents by certified supplier networks.'
  },
  {
    id: 'ev-doe-trans-cost',
    title: 'Transformer Input Cost & Lead-Time Briefing',
    source: 'DOE Grid Deployment Office',
    ticker: 'SECTOR-WIDE',
    date: '15 Oct 2026',
    category: 'Industry Reports',
    provenance: 'REAL',
    confidenceScore: 92,
    summary: 'High-voltage transformer lead times remain extended at 84–110 weeks, creating potential project deployment lags.',
    fullText: 'The Department of Energy Grid Deployment Office published its Q3 2026 Heavy Electrical Equipment Assessment. Key Findings: Domestic demand for high-voltage step-up transformers (345kV+) exceeds domestic manufacturing output by 3.2x. Lead times from order placement to site commissioning average 98 weeks for standard units and up to 134 weeks for bespoke utility-grade configurations.'
  },
  {
    id: 'ev-nfgt-spot-log',
    title: 'Nordic Freight (NFGT) Spot Rate & Port Dwell Log',
    source: 'Port Authority Maritime Index',
    ticker: 'NFGT',
    date: '11 Nov 2026',
    category: 'Regulatory',
    provenance: 'REAL',
    confidenceScore: 88,
    summary: 'Intermodal dwell times for heavy electrical freight climbed 2.4 days across West Coast container terminals.',
    fullText: 'Monthly Intermodal Dwell Summary: Heavy containerized freight classified under HS Code 8504 (Electrical transformers, static converters and inductors) experienced an average terminal dwell of 6.8 days, up from 4.4 days in Q2 2026. Demurrage charges increased 18%.'
  },
  {
    id: 'ev-hlb-fasttrack',
    title: 'Helios Bio (HLB) Fast-Track Eligibility Checklist',
    source: 'FDA Centre for Drug Evaluation',
    ticker: 'HLB',
    date: '28 Oct 2026',
    category: 'Regulatory',
    provenance: 'SYNTHETIC',
    confidenceScore: 78,
    summary: 'Phase 2a preliminary cohort met primary safety endpoints, but secondary surrogate biomarkers require 6-month verification.',
    fullText: 'Regulatory Review Checklist (Demonstration Archive): IND 149202 Fast-Track designation application under review. Preliminary data submitted demonstrates safety profile in Cohort A (n=42). Statistical significance on secondary biomarker endpoints remains inconclusive until 24-week blinded readout.'
  }
];

export const SYNTHETIC_USER = {
  name: 'Nakul Verma',
  initials: 'NV',
  email: 'nakul@fintrace.app',
  role: 'Retail Investor & Decision Analyst',
  joinedDate: 'October 2026',
  stats: {
    claimsAnalysed: 24,
    reportsGenerated: 19,
    independentScore: 78,
    learningSessions: 14
  }
};

// API Client Helper
async function apiFetch(endpoint, options = {}) {
  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    // Graceful fallback to synthetic data when backend server is offline
    return null;
  }
}

export const api = {
  // Auth
  async login(email, password) {
    const live = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    if (live) return live;
    // Synthetic local auth
    return {
      success: true,
      token: 'syn_tok_' + Math.random().toString(36).substring(2),
      user: { ...SYNTHETIC_USER, email }
    };
  },

  async register(data) {
    const live = await apiFetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    if (live) return live;
    return {
      success: true,
      token: 'syn_tok_' + Math.random().toString(36).substring(2),
      user: { ...SYNTHETIC_USER, name: data.name || 'Nakul Verma', email: data.email }
    };
  },

  // Claims
  async getClaims() {
    const live = await apiFetch('/claims');
    if (live) return live;
    return SYNTHETIC_CLAIMS;
  },

  async getClaim(id) {
    const live = await apiFetch(`/claims/${id}`);
    if (live) return live;
    return SYNTHETIC_CLAIMS.find(c => c.id === id) || SYNTHETIC_CLAIMS[0];
  },

  async analyzeClaim(claimData) {
    const live = await apiFetch('/claims/analyze', {
      method: 'POST',
      body: JSON.stringify(claimData)
    });
    if (live) return live;
    // Generate compiled claim report
    const newClaim = {
      id: 'claim_' + Date.now(),
      ticker: (claimData.ticker || 'SYN').toUpperCase(),
      company: claimData.company || 'Analyzed Entity',
      statement: claimData.statement,
      date: 'Today',
      validationStatus: 'Needs Verification',
      direction: 'Bullish',
      evidenceCoverage: 67,
      sourceUrl: claimData.sourceUrl || '',
      horizon: claimData.horizon || '3 months',
      breakdown: {
        statedTarget: 'Identified target price / milestone',
        impliedHorizon: claimData.horizon || '90 days',
        primaryCatalyst: 'Extracted catalyst mechanism',
        missingConditions: [
          'Supplier delivery lead times',
          'Sector regulatory approvals',
          'Macro interest rate sensitivity'
        ]
      },
      completeness: { score: 65, provenanceStatus: 'AI-GENERATED', identifiedAssumptions: 3, testedAssumptions: 1 },
      interpretations: [
        { fork: 'A: Base Scenario', stance: 'Bullish', rationale: 'Market demand supports forecast assuming on-time rollout.', source: 'AI-GENERATED FORK' },
        { fork: 'B: Downside Drag', stance: 'Bearish', rationale: 'Input cost spikes compress target operating margin.', source: 'AI-GENERATED FORK' }
      ],
      supportingEvidence: SYNTHETIC_EVIDENCE.slice(0, 2),
      contradictoryEvidence: []
    };
    return newClaim;
  },

  // Evidence
  async getEvidence(query = '') {
    const live = await apiFetch(`/evidence?q=${encodeURIComponent(query)}`);
    if (live) return live;
    if (!query) return SYNTHETIC_EVIDENCE;
    return SYNTHETIC_EVIDENCE.filter(e =>
      e.title.toLowerCase().includes(query.toLowerCase()) ||
      e.ticker.toLowerCase().includes(query.toLowerCase()) ||
      e.source.toLowerCase().includes(query.toLowerCase())
    );
  },

  // Decision Lab
  async submitDecisionCalibration(data) {
    const live = await apiFetch('/decision-lab/calibrate', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    if (live) return live;
    return {
      success: true,
      calibrationScore: 82,
      delta: +26,
      insights: 'Identified missing invalidation conditions before reviewing AI interpretations.'
    };
  }
};
