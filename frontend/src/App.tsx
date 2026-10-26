import { useState } from "react";
import { Login } from "./pages/Login";
import { Home } from "./pages/Home";
import { StudentWorkspace } from "./pages/StudentWorkspace";
import { InstructorDashboard } from "./pages/InstructorDashboard";
import type { User, Task } from "./types";

type Screen = { name: "home" } | { name: "workspace"; task: Task };

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [screen, setScreen] = useState<Screen>({ name: "home" });

  if (!user) return <Login onLogin={setUser} />;

  if (user.role === "instructor") return <InstructorDashboard user={user} />;

  if (screen.name === "home") {
    return <Home user={user} onSelectTask={(task) => setScreen({ name: "workspace", task })} />;
  }

  return (
    <StudentWorkspace
      user={user}
      initialTask={screen.task}
      onBackToOverview={() => setScreen({ name: "home" })}
    />
  );
}