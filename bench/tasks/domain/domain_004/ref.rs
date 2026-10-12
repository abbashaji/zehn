struct Student {
    name: String,
    score: i64,
}

struct Graded {
    name: String,
    grade: String,
}

fn letter(score: i64) -> &'static str {
    if score >= 90 {
        "A"
    } else if score >= 80 {
        "B"
    } else if score >= 70 {
        "C"
    } else if score >= 60 {
        "D"
    } else {
        "F"
    }
}

fn assign_grades(students: Vec<Student>, curve: i64) -> Result<Vec<Graded>, String> {
    if curve < 0 {
        return Err("curve must not be negative".to_string());
    }
    let mut graded = Vec::new();
    for s in students {
        if s.score < 0 || s.score > 100 {
            return Err(format!("invalid score for {}", s.name));
        }
        let grade = letter(std::cmp::min(100, s.score + curve)).to_string();
        graded.push(Graded {
            name: s.name,
            grade,
        });
    }
    Ok(graded)
}
