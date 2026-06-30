"""
Runs YOLOv8 object detection on downloaded Telegram images.
Classifies images and saves results to CSV for dbt ingestion.
"""

import csv
import logging
from pathlib import Path
from datetime import datetime

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            f"logs/yolo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

IMAGES_PATH  = Path("data/raw/images")
RESULTS_PATH = Path("data/processed")
RESULTS_PATH.mkdir(parents=True, exist_ok=True)

PERSON_CLASSES  = {"person"}
PRODUCT_CLASSES = {"bottle", "bowl", "cup", "vase", "box", "book"}


def classify_image(detected_classes):
    has_person  = bool(detected_classes & PERSON_CLASSES)
    has_product = bool(detected_classes & PRODUCT_CLASSES)
    if has_person and has_product:
        return "promotional"
    elif has_product:
        return "product_display"
    elif has_person:
        return "lifestyle"
    else:
        return "other"


def run_detection():
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("Run: pip install ultralytics")
        return

    logger.info("Loading YOLOv8 nano model...")
    model = YOLO("yolov8n.pt")

    image_files = (
        list(IMAGES_PATH.rglob("*.jpg")) +
        list(IMAGES_PATH.rglob("*.jpeg"))
    )
    logger.info(f"Found {len(image_files)} images")

    if not image_files:
        logger.warning("No images found. Run scraper first.")
        return

    results_file = RESULTS_PATH / "yolo_detections.csv"

    with open(results_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            "message_id", "channel_name", "image_path",
            "detected_class", "confidence_score",
            "image_category", "detected_at"
        ])
        writer.writeheader()

        for img_path in image_files:
            try:
                logger.info(f"Processing: {img_path}")
                results = model(str(img_path), verbose=False)

                detected_classes = set()
                detections = []

                for result in results:
                    for box in result.boxes:
                        class_name = model.names[int(box.cls)]
                        confidence = float(box.conf)
                        detected_classes.add(class_name)
                        detections.append((class_name, confidence))

                image_category = classify_image(detected_classes)
                message_id     = img_path.stem
                channel_name   = img_path.parent.name

                if detections:
                    for class_name, confidence in detections:
                        writer.writerow({
                            "message_id":       message_id,
                            "channel_name":     channel_name,
                            "image_path":       str(img_path),
                            "detected_class":   class_name,
                            "confidence_score": round(confidence, 4),
                            "image_category":   image_category,
                            "detected_at":      datetime.now().isoformat(),
                        })
                else:
                    writer.writerow({
                        "message_id":       message_id,
                        "channel_name":     channel_name,
                        "image_path":       str(img_path),
                        "detected_class":   "none",
                        "confidence_score": 0.0,
                        "image_category":   "other",
                        "detected_at":      datetime.now().isoformat(),
                    })

            except Exception as e:
                logger.error(f"Error processing {img_path}: {e}")
                continue

    logger.info(f"Results saved to {results_file}")


if __name__ == "__main__":
    run_detection()