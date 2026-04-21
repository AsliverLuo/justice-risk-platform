import { Navigate } from "react-router-dom";
import LoginPage from "../pages/Login";
import DashboardPage from "../pages/Dashboard";
import CaseDetailPage from "../pages/Dashboard/CaseDetailPage";
import DefendantCasesPage from "../pages/Dashboard/DefendantCasesPage";
import NlpDemoPage from "../pages/Analysis/NlpDemoPage";
import CommunityRiskPage from "../pages/CommunityRisk";
import StreetCasesPage from "../pages/CommunityRisk/StreetCasesPage";
import StreetProfilePage from "../pages/CommunityRisk/StreetProfilePage";
import SupportProsecutionPage from "../pages/SupportProsecution";
import FormPage from "../pages/SupportProsecution/FormPage";
import DetailPage from "../pages/SupportProsecution/DetailPage";
import DocumentPage from "../pages/SupportProsecution/DocumentPage";
import WorkflowPage from "../pages/SupportProsecution/WorkflowPage";
import ProgressCasesPage from "../pages/SupportProsecution/ProgressCasesPage";
import TaskCreatePage from "../pages/Workflow/TaskCreatePage";
import TaskListPage from "../pages/Workflow/TaskListPage";

const routes = [
  {
    path: "/",
    element: <Navigate to="/login" replace />,
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/dashboard",
    element: <DashboardPage />,
  },
  {
    path: "/dashboard/cases/:caseId",
    element: <CaseDetailPage />,
  },
  {
    path: "/dashboard/defendants",
    element: <DefendantCasesPage />,
  },
  {
    path: "/analysis/nlp",
    element: <NlpDemoPage />,
  },
  {
    path: "/community-risk",
    element: <CommunityRiskPage />,
  },
  {
    path: "/community-risk/:street/cases",
    element: <StreetCasesPage />,
  },
  {
    path: "/community-risk/:street/profile",
    element: <StreetProfilePage />,
  },
  {
    path: "/support-prosecution",
    element: <SupportProsecutionPage />,
  },
  {
    path: "/support-prosecution/form",
    element: <FormPage />,
  },
  {
    path: "/support-prosecution/detail",
    element: <DetailPage />,
  },
  {
    path: "/support-prosecution/document",
    element: <DocumentPage />,
  },
  {
    path: "/support-prosecution/workflow",
    element: <WorkflowPage />,
  },
  {
    path: "/support-prosecution/progress-cases",
    element: <ProgressCasesPage />,
  },
  {
    path: "/workflow/tasks/create",
    element: <TaskCreatePage />,
  },
  {
    path: "/workflow/tasks",
    element: <TaskListPage />,
  },
];

export default routes;
