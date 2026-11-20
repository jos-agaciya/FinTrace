/**
 * Fictional Educational Scenarios & Mock Data for FINTRACE Virtual Decision Lab.
 * All scenarios, companies, and data points are SYNTHETIC / DEMONSTRATION DATA.
 */

export const MOCK_SCENARIOS = [
  {
    id: 'scenario_mgs_01',
    ticker: 'MGS',
    company: 'Megawatt Grid Systems',
    sector: 'Clean Infrastructure & Grid Tech',
    badge: 'SYNTHETIC / DEMONSTRATION DATA',
    title: 'Utility Grid Boom vs. Heavy Equipment Bottlenecks',
    summary:
      'Megawatt Grid Systems recently announced a record $2.4B in contracted purchase orders from major electric utilities. Social media analysts predict an immediate stock surge.',
    firstImpressionQuestion:
      'Given the massive $2.4B order backlog, what do you think will happen to the stock price in the near term?',
    defaultInitialRationale:
      'I believe strong customer orders and grid spending will push the stock price higher quickly.',
    evidenceItems: [
      {
        id: 'ev_mgs_pos_1',
        type: 'positive',
        category: 'Customer Orders',
        title: 'Confirmed Orders ($2.4B)',
        detail:
          'The company has orders worth $2.4B from 8 major electricity providers. These orders cannot be cancelled.',
        source: 'Company Report (Demo)'
      },
      {
        id: 'ev_mgs_pos_2',
        type: 'positive',
        category: 'Pricing',
        title: 'Can Increase Prices',
        detail:
          'The company can charge customers more when material costs increase.',
        source: 'Company Presentation (Demo)'
      },
      {
        id: 'ev_mgs_neg_1',
        type: 'negative',
        category: 'Delivery Delays',
        title: 'Transformer Delays (84–110 Weeks)',
        detail:
          'Large transformers can take 84–110 weeks to make and deliver. This may delay projects.',
        source: 'Energy Department Report (Demo)'
      },
      {
        id: 'ev_mgs_neg_2',
        type: 'negative',
        category: 'Price Approval Delays',
        title: 'Delayed Price Approvals',
        detail:
          'Two state commissions have scheduled price meetings. This may delay income from new projects until 2028.',
        source: 'State Commission Notice (Demo)'
      }
    ],
    learningOutcomes: {
      changedMind:
        'By checking official reports, you discovered that heavy electrical equipment takes up to 84–110 weeks to deliver. Changing your view to reflect this delay protected you from relying on an unrealistic short-term timeline.',
      keptMindCautious:
        'You carefully weighed the impressive order backlog against realistic supply chain constraints and maintained a balanced, grounded perspective.',
      keptMindOverconfident:
        'You maintained high optimism despite verified 84-week delivery constraints. Remember that customer orders cannot turn into revenue until the equipment is actually delivered.'
    }
  },
  {
    id: 'scenario_vrtx_02',
    ticker: 'VRTX',
    company: 'Vortex Semiconductors',
    sector: 'Artificial Intelligence & Semiconductor Packaging',
    badge: 'SYNTHETIC / DEMONSTRATION DATA',
    title: 'Next-Gen AI Chip Packaging Claims vs. Real Factory Yields',
    summary:
      'Vortex Semiconductors announced a patent-protected chip stacking technology, claiming it will deliver 65% profit margins within six months.',
    firstImpressionQuestion:
      'With soaring global demand for AI chips, what is your initial view on Vortex stock?',
    defaultInitialRationale:
      'Demand for AI hardware is surging and this breakthrough packaging technology will boost short-term profits.',
    evidenceItems: [
      {
        id: 'ev_vrtx_pos_1',
        type: 'positive',
        category: 'Intellectual Property',
        title: 'Approved Patent for Die-to-Wafer Fusion',
        detail:
          'Patent Office approved proprietary thermal dissipation architecture, granting Vortex a 3-year exclusivity window.',
        source: 'USPTO Patent Record #118942 (Synthetic)'
      },
      {
        id: 'ev_vrtx_pos_2',
        type: 'positive',
        category: 'Customer Interest',
        title: 'Early Testing by Hyperscale Cloud Providers',
        detail:
          'Two leading cloud providers received early prototype samples and reported 30% faster processing on machine learning workloads.',
        source: 'Industry Benchmark Newsletter (Synthetic)'
      },
      {
        id: 'ev_vrtx_neg_1',
        type: 'negative',
        category: 'Manufacturing Yield',
        title: 'Current Production Yield Only 42%',
        detail:
          'Foundry inspection reveals only 42% of manufactured wafers pass quality inspection. Commercial viability typically requires over 78% yields.',
        source: 'Semiconductor Fabrication Audit (Synthetic)'
      },
      {
        id: 'ev_vrtx_neg_2',
        type: 'negative',
        category: 'Lengthy Qualification Cycles',
        title: 'Enterprise Server Validation Takes 9–12 Months',
        detail:
          'Data center operators require extensive thermal and durability stress tests before placing volume commercial purchase orders.',
        source: 'Hardware Engineering Standards Body (Synthetic)'
      }
    ],
    learningOutcomes: {
      changedMind:
        'You noticed that low 42% manufacturing yields and lengthy 9–12 month test cycles could eat up short-term profits. Updating your view prevented falling for headline hype.',
      keptMindCautious:
        'You correctly recognized that revolutionary semiconductor technology requires reliable volume production before yielding steady profits.',
      keptMindOverconfident:
        'You stayed optimistic despite low production yields. When factories scrap more than half their chips, profit margins rarely meet optimistic targets.'
    }
  },
  {
    id: 'scenario_clnv_03',
    ticker: 'CLNV',
    company: 'CleanVolt Energy Storage',
    sector: 'Battery & Renewable Storage',
    badge: 'SYNTHETIC / DEMONSTRATION DATA',
    title: 'Solid-State Battery Pilot vs. Mass Factory Commercialization',
    summary:
      'CleanVolt announced that its solid-state battery achieved 1,000 cycles without degradation, claiming immediate readiness for national energy grids.',
    firstImpressionQuestion:
      'What is your first reaction to CleanVolt’s announcement of battery test results?',
    defaultInitialRationale:
      'The battery technology sounds revolutionary and clean energy adoption will create huge immediate demand.',
    evidenceItems: [
      {
        id: 'ev_clnv_pos_1',
        type: 'positive',
        category: 'Lab Durability',
        title: 'Zero Thermal Runaway in 1,000 Laboratory Cycles',
        detail:
          'Third-party national laboratory confirmed battery samples showed no fire hazards and retained 94% capacity after 1,000 cycles.',
        source: 'National Renewable Energy Lab Report (Synthetic)'
      },
      {
        id: 'ev_clnv_pos_2',
        type: 'positive',
        category: 'Government Funding',
        title: '$75M Advanced Energy Manufacturing Grant',
        detail:
          'Awarded federal clean energy infrastructure grant to construct a pilot assembly facility.',
        source: 'Department of Energy Grant Registry (Synthetic)'
      },
      {
        id: 'ev_clnv_neg_1',
        type: 'negative',
        category: 'Production Scale Limit',
        title: 'Pilot Facility Only Produces 20 Megawatt-Hours',
        detail:
          'Current pilot line capacity is 20 MWh per year. Utility grid deployment requires Gigawatt-hour scale (50x larger).',
        source: 'CleanVolt Facility Environmental Assessment (Synthetic)'
      },
      {
        id: 'ev_clnv_neg_2',
        type: 'negative',
        category: 'Raw Material Dependency',
        title: 'High Exposure to Rare Earth Precursor Costs',
        detail:
          'The solid-state electrolyte depends on specialized lithium-lanthanum precursors whose spot prices have doubled in 6 months.',
        source: 'Chemical & Minerals Market Bulletin (Synthetic)'
      }
    ],
    learningOutcomes: {
      changedMind:
        'Recognizing that small pilot capacity (20 MWh) cannot fulfill grid-scale orders right away helped you avoid an overconfident short-term bet.',
      keptMindCautious:
        'You balanced scientific lab success with the reality of building multi-billion dollar gigafactories.',
      keptMindOverconfident:
        'Laboratory breakthroughs are exciting, but scaling battery chemistry to gigafactories often takes 3–5 years.'
    }
  }
];

export const INITIAL_SEED_HISTORY = [
  {
    id: 'session_seed_01',
    scenarioId: 'scenario_mgs_01',
    scenarioTitle: 'Utility Grid Boom vs. Heavy Equipment Bottlenecks',
    ticker: 'MGS',
    company: 'Megawatt Grid Systems',
    completedAt: '2026-11-20T14:30:00.000Z',
    displayDate: 'Nov 20, 2026',
    initialStance: 'Expect the price to rise',
    initialConfidence: 85,
    initialRationale:
      'Strong utility grid backlog and infrastructure spending will drive rapid stock rerating.',
    reviewedEvidenceCount: 3,
    totalEvidenceCount: 4,
    reviewedEvidenceTitles: [
      'Confirmed Orders ($2.4B)',
      'Transformer Delays (84–110 Weeks)',
      'Delayed Price Approvals'
    ],
    updatedStance: 'Not sure yet',
    updatedConfidence: 58,
    updatedRationale:
      'My confidence changed after learning that transformer delivery could take 84 weeks.',
    confidenceDelta: -27,
    stanceChanged: true,
    decisionStrength: 'Strong',
    learningSummary:
      'By checking official reports, you discovered that heavy electrical equipment takes up to 84–110 weeks to deliver. Changing your view to reflect this delay protected you from relying on an unrealistic 2-month timeline.',
    feedbackHeadline: 'You changed your view after reviewing new information.'
  }
];

const PRIMARY_STORAGE_KEY = 'fintrace_virtual_decision_lab_history';
const SECONDARY_STORAGE_KEY = 'fintrace_decision_lab_sessions';

export function getSavedDecisionSessions() {
  try {
    const raw = localStorage.getItem(PRIMARY_STORAGE_KEY) || localStorage.getItem(SECONDARY_STORAGE_KEY);
    if (!raw) {
      // Seed with sample session so user immediately sees how history works
      localStorage.setItem(PRIMARY_STORAGE_KEY, JSON.stringify(INITIAL_SEED_HISTORY));
      localStorage.setItem(SECONDARY_STORAGE_KEY, JSON.stringify(INITIAL_SEED_HISTORY));
      return INITIAL_SEED_HISTORY;
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    console.error('Error reading saved decision sessions:', err);
    return INITIAL_SEED_HISTORY;
  }
}

export function saveDecisionSession(sessionData) {
  try {
    const existing = getSavedDecisionSessions();
    // Prevent duplicate entries with the same session id
    const filtered = existing.filter((s) => s.id !== sessionData.id);
    const updated = [sessionData, ...filtered];
    localStorage.setItem(PRIMARY_STORAGE_KEY, JSON.stringify(updated));
    localStorage.setItem(SECONDARY_STORAGE_KEY, JSON.stringify(updated));
    return updated;
  } catch (err) {
    console.error('Error saving decision session:', err);
    return [];
  }
}

export function clearSavedDecisionSessions() {
  try {
    localStorage.removeItem(PRIMARY_STORAGE_KEY);
    localStorage.removeItem(SECONDARY_STORAGE_KEY);
    return [];
  } catch (err) {
    console.error('Error clearing sessions:', err);
    return [];
  }
}
