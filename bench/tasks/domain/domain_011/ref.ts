interface Rule {
  role: string;
  action: string;
  allow: boolean;
}

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function firstApplying(rules: Rule[], roles: string[], action: string, allow: boolean): Rule | null {
  const found = rules.find(
    (rule) => rule.allow === allow && roles.includes(rule.role) && (rule.action === action || rule.action === "*"),
  );
  return found === undefined ? null : found;
}

function check_access(rules: Rule[], roles: string[], action: string): Result<string> {
  if (action === "") {
    return { ok: false, error: "action required" };
  }
  const denied = firstApplying(rules, roles, action, false);
  if (denied !== null) {
    return { ok: false, error: "denied by role " + denied.role };
  }
  const granted = firstApplying(rules, roles, action, true);
  if (granted !== null) {
    return { ok: true, value: "allowed by role " + granted.role };
  }
  return { ok: false, error: "no rule for " + action };
}
