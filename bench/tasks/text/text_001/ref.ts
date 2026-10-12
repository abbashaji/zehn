function csv_field_count(line: string): number {
  if (line === "") {
    return 0;
  }
  return line.split(",").length;
}
