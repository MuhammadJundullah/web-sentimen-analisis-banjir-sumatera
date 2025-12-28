import csv
import io


def parse_csv_text(content: str) -> tuple[list[str], int]:
    reader = csv.DictReader(io.StringIO(content))
    texts: list[str] = []
    skipped = 0

    for raw in reader:
        text = raw.get("Isi_Tweet") or raw.get("text") or raw.get("tweet") or raw.get("content")
        if not text:
            skipped += 1
            continue

        texts.append(text)

    return texts, skipped
