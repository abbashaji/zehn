interface Student {
  name: string;
  score: number;
}

interface Graded {
  name: string;
  grade: string;
}

type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function letter(score: number): string {
  if (score >= 90) {
    return "A";
  }
  if (score >= 80) {
    return "B";
  }
  if (score >= 70) {
    return "C";
  }
  if (score >= 60) {
    return "D";
  }
  return "F";
}

function assign_grades(students: Student[], curve: number): Result<Graded[]> {
  if (curve < 0) {
    return { ok: false, error: "curve must not be negative" };
  }
  const graded: Graded[] = [];
  for (const s of students) {
    if (s.score < 0 || s.score > 100) {
      return { ok: false, error: "invalid score for " + s.name };
    }
    graded.push({ name: s.name, grade: letter(Math.min(100, s.score + curve)) });
  }
  return { ok: true, value: graded };
}
