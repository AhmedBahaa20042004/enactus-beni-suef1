from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from core.database import engine, Base
from core.config import settings
from core.security import hash_password

# Import all models so SQLAlchemy registers them before create_all
from models import user, product, order, contact  # noqa

from routers import auth, products, orders, contact as contact_router, admin

# ── Create all tables ────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Seed first admin if not exists ──────────────────────────
def seed_admin():
    from core.database import SessionLocal
    from models.user import User
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == settings.FIRST_ADMIN_EMAIL).first():
            admin_user = User(
                name=settings.FIRST_ADMIN_NAME,
                email=settings.FIRST_ADMIN_EMAIL,
                password=hash_password(settings.FIRST_ADMIN_PASSWORD),
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()
            print(f"✅ Admin created: {settings.FIRST_ADMIN_EMAIL}")
        else:
            print("ℹ️  Admin already exists")

        # Seed default products if none exist
        from models.product import Product, ProductVariant
        if db.query(Product).count() == 0:
            _seed_products(db)
    finally:
        db.close()

def _seed_products(db):
    from models.product import Product, ProductVariant
    default_products = [
        {
            "name": "Chitosan Powder",
            "slug": "chitosan-powder",
            "description": "High-purity chitosan with DD ≥85%. Suitable for agriculture, water treatment, cosmetics, and research.",
            "category": "powder",
            "variants": [
                {"label": "100g", "price_egp": 120, "stock": 50},
                {"label": "500g", "price_egp": 500, "stock": 30},
                {"label": "1 kg",  "price_egp": 900, "stock": 20},
            ],
        },
        {
            "name": "Chitosan Capsules",
            "slug": "chitosan-capsules",
            "description": "500mg food-grade chitosan in vegetarian capsules for dietary supplement use.",
            "category": "capsule",
            "variants": [
                {"label": "30 capsules",  "price_egp": 150, "stock": 100},
                {"label": "60 capsules",  "price_egp": 270, "stock": 80},
                {"label": "120 capsules", "price_egp": 490, "stock": 60},
            ],
        },
        {
            "name": "Natural Coating Solution",
            "slug": "natural-coating-solution",
            "description": "Chitosan-based antimicrobial coating for fruits and vegetables. Extends shelf life naturally.",
            "category": "coating",
            "variants": [
                {"label": "250 ml", "price_egp": 85,   "stock": 200},
                {"label": "1 litre","price_egp": 290,  "stock": 100},
                {"label": "5 litres","price_egp": 1200, "stock": 40},
            ],
        },
    ]
    for p_data in default_products:
        variants = p_data.pop("variants")
        product = Product(**p_data)
        db.add(product)
        db.flush()
        for v in variants:
            db.add(ProductVariant(product_id=product.id, **v))
    db.commit()
    print("✅ Default products seeded")

seed_admin()

# ── App setup ────────────────────────────────────────────────
app = FastAPI(
    title="Enactus New Beni Suef — ChitoShell API",
    description="Backend API for the ChitoShell project. Manages products, orders, users, and contact messages.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Restrict to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(contact_router.router)
app.include_router(admin.router)

# ── Serve the frontend HTML ──────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.get("/", include_in_schema=False)
def serve_frontend():
    index = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"message": "Enactus New Beni Suef API is running. Visit /api/docs for documentation."}

@app.get("/health")
def health():
    return {"status": "ok", "project": "Enactus New Beni Suef — ChitoShell"}

@app.get("/admin", include_in_schema=False)
def serve_admin():
    admin_path = os.path.join(FRONTEND_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return {"message": "Admin dashboard not found."}
