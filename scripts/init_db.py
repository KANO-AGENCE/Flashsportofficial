"""Initialize database tables."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import Base, engine
from app.models.models import Event, Photo, Detection, BibGroup  # noqa: F401
from app.models.auth import User  # noqa: F401
from app.models.participant import Participant  # noqa: F401
from app.models.frame import Frame  # noqa: F401
from app.models.web import WebEvent, WebPhoto, Customer, Order, OrderItem, Product, WebEventProduct  # noqa: F401
from app.models.mailing import Mailing  # noqa: F401
from app.models.training import GroundTruth, ReviewItem, Dataset, DatasetEntry, AIModel, TrainingSession  # noqa: F401

if __name__ == "__main__":
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done. All tables created.")
