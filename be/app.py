from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os
from typing import List, Dict, Any
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uas-ml")

from csv_loader import parse_csv_text
from twitter_fetcher import fetch_recent_tweets
from tweepy.errors import TooManyRequests
from db import (
    insert_analysis_history,
    fetch_analysis_history,
    delete_analysis_history,
    clear_analysis_history,
)

# --- Inisialisasi App ---
app = FastAPI(
    title="API Analisis Sentimen Bencana Sumatra",
    description="API untuk klasifikasi tweet bencana menggunakan IndoBERT (Fine-tuned).",
    version="1.0.0"
)

# --- Konfigurasi CORS ---
# Penting: Diizinkan "*" agar Frontend dari Vercel/Localhost bisa akses tanpa blokir.
from fastapi.middleware.cors import CORSMiddleware
cors_origins = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Variables untuk Model ---
MODEL_PATH = "./results/checkpoint-5" # Pastikan folder ini ada dan lengkap
model = None
tokenizer = None
id2label = {}
fetch_status = {
    "last_run": None,
    "last_error": None,
    "last_count": 0,
    "last_inserted": 0,
}

scheduler = BackgroundScheduler()

# --- Event Startup (Load Model Sekali Saja) ---
@app.on_event("startup")
async def startup() -> None:
    global model, tokenizer, id2label

    logger.info("Sedang memuat model IndoBERT... (Mungkin butuh waktu 30-60 detik)")
    try:
        # Load Tokenizer & Model
        tokenizer = AutoTokenizer.from_pretrained("indobenchmark/indobert-base-p2")
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

        # Simpan mapping ID ke Label (misal: 0 -> "Kritik Pemerintah")
        id2label = model.config.id2label

        # Pindah ke CPU (Hugging Face Spaces Free Tier biasanya CPU only, tapi support GPU jika ada)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        logger.info("Model berhasil dimuat di device: %s", device)
    except Exception as e:
        logger.exception("FATAL ERROR: Gagal memuat model.")
        # Jangan raise error di sini agar app tetap jalan (untuk debugging log),
        # tapi endpoint predict akan gagal.

    interval_hours = int(os.getenv("FETCH_INTERVAL_HOURS", "2"))
    query = os.getenv("TWITTER_QUERY", "banjir sumatera -is:retweet lang:id")

    def scheduled_fetch() -> None:
        global fetch_status
        try:
            result = fetch_recent_tweets(query=query)
            fetch_status = {
                "last_run": result.get("fetched_at"),
                "last_error": None,
                "last_count": result.get("total", 0),
                "last_inserted": result.get("inserted", 0),
            }
            logger.info(
                "Scheduled fetch sukses. total=%s inserted=%s query=%s",
                result.get("total", 0),
                result.get("inserted", 0),
                query,
            )
        except TooManyRequests:
            fetch_status = {
                "last_run": None,
                "last_error": "Rate limit Twitter tercapai. Coba lagi nanti.",
                "last_count": 0,
                "last_inserted": 0,
            }
            logger.warning("Scheduled fetch dibatasi rate limit Twitter.")
        except Exception as exc:
            fetch_status = {
                "last_run": None,
                "last_error": str(exc),
                "last_count": 0,
                "last_inserted": 0,
            }
            logger.exception("Scheduled fetch gagal.")

    scheduler.add_job(scheduled_fetch, "interval", hours=interval_hours, id="twitter_fetch", replace_existing=True)
    scheduler.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    scheduler.shutdown()

# --- Schema Data (Pydantic) ---
class TweetRequest(BaseModel):
    text: str

class PredictionResult(BaseModel):
    label: str
    score: float

class APIResponse(BaseModel):
    text: str
    sentiment: PredictionResult | None # Positif/Netral/Negatif
    categories: List[PredictionResult] # Kritik, Logistik, dll
    all_predictions: Dict[str, float]  # Raw data untuk debug
    history_id: int | None = None
    created_at: datetime | None = None
    source: str | None = None


class CsvAnalysisResponse(BaseModel):
    sentiment_percentages: Dict[str, float]
    category_percentages: Dict[str, float]


class FetchRequest(BaseModel):
    query: str | None = None


class TokenRequest(BaseModel):
    token: str


class AnalysisHistoryResponse(BaseModel):
    id: int
    text: str
    sentiment: PredictionResult | None
    categories: List[PredictionResult]
    all_predictions: Dict[str, Any] | None = None
    source: str
    created_at: datetime

# --- Logic Prediksi ---
@app.post("/predict", response_model=APIResponse)
async def predict(payload: TweetRequest):
    if not model or not tokenizer:
        raise HTTPException(status_code=503, detail="Model belum siap/gagal dimuat.")

    text = payload.text
    
    # 1. Tokenisasi
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    
    # 2. Inference
    with torch.no_grad():
        outputs = model(**inputs)
    
    # 3. Sigmoid & Thresholding
    logits = outputs.logits
    probs = torch.sigmoid(logits).squeeze().cpu()
    
    # 4. Parsing Hasil
    sentiment_result = None
    categories_result = []
    all_preds = {}

    # Daftar label sentimen (Hardcoded sesuai label training Anda)
    SENTIMENT_LABELS = ["Positif", "Netral", "Negatif"]
    sentiment_scores: Dict[str, float] = {}

    for i, prob in enumerate(probs):
        score = float(prob)
        label_name = id2label[i]
        all_preds[label_name] = score

        if label_name in SENTIMENT_LABELS:
            sentiment_scores[label_name] = score
        elif score > 0.5:
            categories_result.append(PredictionResult(label=label_name, score=score))

    # Ambil sentiment dengan score tertinggi (tanpa memaksa Netral)
    if sentiment_scores:
        best_label = max(sentiment_scores, key=sentiment_scores.get)
        sentiment_result = PredictionResult(label=best_label, score=sentiment_scores[best_label])

    history_payload = {
        "text": text,
        "sentiment_label": sentiment_result.label if sentiment_result else None,
        "sentiment_score": sentiment_result.score if sentiment_result else None,
        "categories": [{"label": category.label, "score": category.score} for category in categories_result],
        "all_predictions": all_preds,
        "source": "manual",
    }
    history_entry = None
    try:
        history_entry = insert_analysis_history(history_payload)
    except Exception as exc:
        logger.warning("Gagal menyimpan history analisis: %s", exc)

    return APIResponse(
        text=text,
        sentiment=sentiment_result,
        categories=categories_result,
        all_predictions=all_preds,
        history_id=history_entry["id"] if history_entry else None,
        created_at=history_entry["created_at"] if history_entry else None,
        source="manual",
    )


def analyze_texts(texts: list[str]) -> tuple[Dict[str, int], Dict[str, int]]:
    if not model or not tokenizer:
        raise HTTPException(status_code=503, detail="Model belum siap/gagal dimuat.")

    sentiment_counts: Dict[str, int] = {}
    category_counts: Dict[str, int] = {}
    device = next(model.parameters()).device
    batch_size = 16

    SENTIMENT_LABELS = {"Positif", "Netral", "Negatif"}
    all_labels = list(id2label.values())
    category_labels = [label for label in all_labels if label not in SENTIMENT_LABELS]
    sentiment_counts = {label: 0 for label in SENTIMENT_LABELS}
    category_counts = {label: 0 for label in category_labels}

    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        inputs = tokenizer(batch, return_tensors="pt", truncation=True, padding=True, max_length=128)
        inputs = {key: value.to(device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)

        probs = torch.sigmoid(outputs.logits).cpu()

        for row in probs:
            sentiment_scores: Dict[str, float] = {}
            for i, prob in enumerate(row):
                score = float(prob)
                label_name = id2label[i]
                if label_name in SENTIMENT_LABELS:
                    sentiment_scores[label_name] = score
                elif score > 0.5:
                    category_counts[label_name] = category_counts.get(label_name, 0) + 1

            if sentiment_scores:
                best_label = max(sentiment_scores, key=sentiment_scores.get)
                sentiment_counts[best_label] = sentiment_counts.get(best_label, 0) + 1

    return sentiment_counts, category_counts


def build_history_response(row: dict) -> dict:
    sentiment = None
    if row.get("sentiment_label"):
        sentiment = {
            "label": row.get("sentiment_label"),
            "score": row.get("sentiment_score"),
        }

    return {
        "id": row.get("id"),
        "text": row.get("text"),
        "sentiment": sentiment,
        "categories": row.get("categories") or [],
        "all_predictions": row.get("all_predictions") or {},
        "source": row.get("source") or "manual",
        "created_at": row.get("created_at"),
    }


@app.post("/upload-csv", response_model=CsvAnalysisResponse)
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File harus berformat CSV.")

    content = await file.read()
    texts, skipped = parse_csv_text(content.decode("utf-8-sig"))
    if not texts:
        raise HTTPException(status_code=400, detail="CSV tidak memiliki data teks yang valid.")

    sentiment_counts, category_counts = analyze_texts(texts)
    total = len(texts)
    sentiment_percentages = {label: (count / total) * 100 for label, count in sentiment_counts.items()}
    category_percentages = {label: (count / total) * 100 for label, count in category_counts.items()}

    history_payload = {
        "text": f"Upload CSV: {file.filename}",
        "sentiment_label": None,
        "sentiment_score": None,
        "categories": [],
        "all_predictions": {
            "sentiment_percentages": sentiment_percentages,
            "category_percentages": category_percentages,
            "total": total,
            "skipped": skipped,
        },
        "source": "csv",
    }
    try:
        insert_analysis_history(history_payload)
    except Exception as exc:
        logger.warning("Gagal menyimpan history upload CSV: %s", exc)

    return CsvAnalysisResponse(
        sentiment_percentages=sentiment_percentages,
        category_percentages=category_percentages,
    )


@app.get("/analysis-history", response_model=List[AnalysisHistoryResponse])
async def get_analysis_history(limit: int = 50, offset: int = 0):
    rows = fetch_analysis_history(limit=limit, offset=offset)
    return [build_history_response(row) for row in rows]


@app.delete("/analysis-history/{item_id}")
async def delete_analysis_history_endpoint(item_id: int):
    deleted = delete_analysis_history(item_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="History tidak ditemukan.")
    return {"deleted": item_id}


@app.delete("/analysis-history")
async def clear_analysis_history_endpoint():
    deleted = clear_analysis_history()
    return {"deleted": deleted}


@app.post("/fetch-tweets")
async def fetch_tweets(payload: FetchRequest | None = None):
    query = payload.query if payload and payload.query else os.getenv(
        "TWITTER_QUERY",
        "banjir sumatera -is:retweet lang:id",
    )

    try:
        logger.info("Fetch manual dimulai. query=%s", query)
        result = fetch_recent_tweets(query=query)
        fetch_status.update(
            {
                "last_run": result.get("fetched_at"),
                "last_error": None,
                "last_count": result.get("total", 0),
                "last_inserted": result.get("inserted", 0),
            }
        )
        logger.info(
            "Fetch manual sukses. total=%s inserted=%s",
            result.get("total", 0),
            result.get("inserted", 0),
        )
        return result
    except TooManyRequests:
        fetch_status.update(
            {
                "last_run": None,
                "last_error": "Rate limit Twitter tercapai. Coba lagi nanti.",
                "last_count": 0,
                "last_inserted": 0,
            }
        )
        logger.warning("Fetch manual dibatasi rate limit Twitter.")
        raise HTTPException(status_code=429, detail="Rate limit Twitter tercapai. Coba lagi nanti.")
    except Exception as exc:
        fetch_status.update(
            {
                "last_run": None,
                "last_error": str(exc),
                "last_count": 0,
                "last_inserted": 0,
            }
        )
        logger.exception("Fetch manual gagal.")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/fetch-status")
async def fetch_status_endpoint():
    return fetch_status


@app.post("/set-token")
async def set_token(payload: TokenRequest):
    token = payload.token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="Token tidak boleh kosong.")
    os.environ["TWITTER_BEARER_TOKEN"] = token
    return {"status": "ok"}

@app.get("/")
def read_root():
    return {"status": "active", "model": "IndoBERT Disaster Analysis"}
