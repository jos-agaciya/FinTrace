import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './hooks/useTheme';
import Layout from './components/Layout';
import Login from './pages/Login';
import Registration from './pages/Registration';
import InvestorDashboard from './pages/InvestorDashboard';
import AnalyseClaim from './pages/AnalyseClaim';
import ClaimAnalysisReport from './pages/ClaimAnalysisReport';
import AnalysisReports from './pages/AnalysisReports';
import EvidenceCentre from './pages/EvidenceCentre';
import VirtualDecisionLab from './pages/VirtualDecisionLab';
import DecisionIntelligence from './pages/DecisionIntelligence';
import SettingsProfile from './pages/SettingsProfile';

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Auth Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Registration />} />

          {/* Authenticated Application Workspace Routes */}
          <Route
            path="/"
            element={<Navigate to="/investor-dashboard" replace />}
          />
          <Route
            path="/investor-dashboard"
            element={
              <Layout>
                <InvestorDashboard />
              </Layout>
            }
          />
          <Route
            path="/analyse-claim"
            element={
              <Layout>
                <AnalyseClaim />
              </Layout>
            }
          />
          <Route
            path="/claim-analysis-report"
            element={
              <Layout>
                <ClaimAnalysisReport />
              </Layout>
            }
          />
          <Route
            path="/analysis-reports"
            element={
              <Layout>
                <AnalysisReports />
              </Layout>
            }
          />
          <Route
            path="/evidence-centre"
            element={
              <Layout>
                <EvidenceCentre />
              </Layout>
            }
          />
          <Route
            path="/virtual-decision-lab"
            element={
              <Layout>
                <VirtualDecisionLab />
              </Layout>
            }
          />
          <Route
            path="/decision-intelligence"
            element={
              <Layout>
                <DecisionIntelligence />
              </Layout>
            }
          />
          <Route
            path="/settings"
            element={
              <Layout>
                <SettingsProfile />
              </Layout>
            }
          />

          {/* Catch-all redirect */}
          <Route
            path="*"
            element={<Navigate to="/investor-dashboard" replace />}
          />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}
