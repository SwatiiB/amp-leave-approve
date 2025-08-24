from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

# Prefer Atlas first, fallback to Local
MONGO_URI_ATLAS = os.getenv(
    "MONGO_URI_ATLAS",
    "mongodb+srv://swatibhadrapur:Sahana03@mcacluster24.9wd0u.mongodb.net/leaveapp?retryWrites=true&w=majority"
)
MONGO_URI_LOCAL = os.getenv("MONGO_URI_LOCAL", "mongodb://localhost:27017/leaveapp")

# Helper function to extract DB name from URI
def get_db_name(uri: str, default: str = "leaveapp") -> str:
    try:
        if "/" in uri:
            return uri.split("/")[-1].split("?")[0] or default
    except Exception:
        pass
    return default

# Try Atlas connection first
client = None
db = None
try:
    if "mongodb+srv://" in MONGO_URI_ATLAS or "ssl=true" in MONGO_URI_ATLAS.lower():
        client = MongoClient(
            MONGO_URI_ATLAS,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=20000,
            socketTimeoutMS=20000,
            retryWrites=True,
            w="majority",
        )
    else:
        client = MongoClient(MONGO_URI_ATLAS)

    # Test Atlas connection
    client.admin.command("ping")
    print("✅ Connected to MongoDB Atlas")
    db_name = get_db_name(MONGO_URI_ATLAS)
    db = client[db_name]

except Exception as e:
    print(f"⚠️ Atlas connection failed: {e}")
    print("🔄 Falling back to Local MongoDB...")

    try:
        client = MongoClient(MONGO_URI_LOCAL)
        client.admin.command("ping")
        print("✅ Connected to Local MongoDB")
        db_name = get_db_name(MONGO_URI_LOCAL)
        db = client[db_name]
    except Exception as e2:
        print(f"❌ Local MongoDB connection failed: {e2}")
        raise RuntimeError("No MongoDB connection available!")

# Collections
users_collection: Collection = db["users"]
leaves_collection: Collection = db["leave_requests"]
