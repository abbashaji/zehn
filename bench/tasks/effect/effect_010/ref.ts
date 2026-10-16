type Result<T> = { ok: true; value: T } | { ok: false; error: string };

function print_pages(items: string[], size: number): Result<number> {
  if (size < 1) {
    return { ok: false, error: "page size must be at least 1" };
  }
  if (items.length === 0) {
    console.log("(no items)");
    return { ok: true, value: 0 };
  }
  const pages = Math.floor((items.length + size - 1) / size);
  let page = 0;
  for (let start = 0; start < items.length; start += size) {
    page += 1;
    console.log(`-- page ${page} of ${pages} --`);
    for (const item of items.slice(start, start + size)) {
      console.log(item);
    }
  }
  return { ok: true, value: pages };
}
