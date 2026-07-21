import DashboardClient from "./DashboardClient";
import { requireChatGPTUser } from "./chatgpt-auth";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const user = await requireChatGPTUser("/");
  return <DashboardClient displayName={user.displayName} email={user.email} />;
}
