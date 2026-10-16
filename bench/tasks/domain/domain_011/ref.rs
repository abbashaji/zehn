struct Rule {
    role: String,
    action: String,
    allow: bool,
}

fn first_applying<'a>(
    rules: &'a [Rule],
    roles: &[String],
    action: &str,
    allow: bool,
) -> Option<&'a Rule> {
    rules.iter().find(|r| {
        r.allow == allow && roles.contains(&r.role) && (r.action == action || r.action == "*")
    })
}

fn check_access(rules: Vec<Rule>, roles: Vec<String>, action: String) -> Result<String, String> {
    if action.is_empty() {
        return Err("action required".to_string());
    }
    if let Some(rule) = first_applying(&rules, &roles, &action, false) {
        return Err(format!("denied by role {}", rule.role));
    }
    if let Some(rule) = first_applying(&rules, &roles, &action, true) {
        return Ok(format!("allowed by role {}", rule.role));
    }
    Err(format!("no rule for {}", action))
}
