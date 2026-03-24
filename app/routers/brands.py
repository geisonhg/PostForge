"""
PostForge — Brands API Router
Manage brand configurations.
"""
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.brand import Brand
from app.schemas.brand import BrandCreate, BrandRead, BrandUpdate

settings = get_settings()
router = APIRouter(prefix="/brands", tags=["Brands"])


@router.get("/", response_model=list[BrandRead])
def list_brands(db: Session = Depends(get_db)):
    """List all registered brands."""
    return db.query(Brand).filter(Brand.active == True).all()


@router.get("/{brand_id}", response_model=BrandRead)
def get_brand(brand_id: str, db: Session = Depends(get_db)):
    """Get a brand by ID."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand '{brand_id}' not found.")
    return brand


@router.post("/", response_model=BrandRead, status_code=201)
def create_brand(payload: BrandCreate, db: Session = Depends(get_db)):
    """Create a new brand."""
    existing = db.query(Brand).filter(Brand.id == payload.id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Brand '{payload.id}' already exists.")

    brand = Brand(**payload.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)

    # Optionally write to config/brands/{id}.json
    _write_brand_config(brand)

    return brand


@router.patch("/{brand_id}", response_model=BrandRead)
def update_brand(brand_id: str, payload: BrandUpdate, db: Session = Depends(get_db)):
    """Update brand fields."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand '{brand_id}' not found.")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(brand, field, value)

    db.commit()
    db.refresh(brand)
    return brand


@router.delete("/{brand_id}", status_code=204)
def deactivate_brand(brand_id: str, db: Session = Depends(get_db)):
    """Soft-delete (deactivate) a brand."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail=f"Brand '{brand_id}' not found.")
    brand.active = False
    db.commit()


@router.post("/seed", response_model=list[BrandRead], tags=["Admin"])
def seed_brands_from_configs(db: Session = Depends(get_db)):
    """
    Seed the database with brands from config/brands/*.json files.
    Safe to call multiple times (upsert behavior).
    """
    brands_dir = settings.abs_path(settings.config_brands_dir)
    seeded = []

    for config_file in brands_dir.glob("*.json"):
        try:
            config = json.loads(config_file.read_text(encoding="utf-8"))
            brand_id = config.get("id") or config_file.stem
            existing = db.query(Brand).filter(Brand.id == brand_id).first()

            vis = config.get("visual_identity", {})
            voice = config.get("voice", {})
            content = config.get("content", {})
            assets = config.get("brand_assets", {})

            values = dict(
                id=brand_id,
                name=config.get("name", brand_id),
                description=config.get("description"),
                primary_color=vis.get("primary_color", "#0066FF"),
                secondary_color=vis.get("secondary_color", "#00D4FF"),
                accent_color=vis.get("accent_color", "#00FF88"),
                dark_color=vis.get("dark_color", "#0A0E1A"),
                light_color=vis.get("light_color", "#FFFFFF"),
                tone=voice.get("tone"),
                voice_keywords=voice.get("keywords", []),
                base_hashtags=content.get("base_hashtags", []),
                cta_options=content.get("cta_options", []),
                instagram_handle=assets.get("instagram_handle"),
                website=assets.get("website"),
                logo_path=assets.get("logo_path"),
                config_snapshot=config,
            )

            if existing:
                for k, v in values.items():
                    setattr(existing, k, v)
                brand = existing
            else:
                brand = Brand(**values)
                db.add(brand)

            db.commit()
            db.refresh(brand)
            seeded.append(brand)

        except Exception as e:
            import traceback
            raise HTTPException(
                status_code=500,
                detail=f"Failed to seed brand from {config_file.name}: {e}",
            )

    return seeded


def _write_brand_config(brand: Brand) -> None:
    """Persist brand config to the config/brands directory."""
    try:
        brands_dir = settings.abs_path(settings.config_brands_dir)
        brands_dir.mkdir(parents=True, exist_ok=True)
        config = {
            "id": brand.id,
            "name": brand.name,
            "description": brand.description,
            "visual_identity": {
                "primary_color": brand.primary_color,
                "secondary_color": brand.secondary_color,
                "accent_color": brand.accent_color,
                "dark_color": brand.dark_color,
                "light_color": brand.light_color,
            },
            "voice": {"tone": brand.tone, "keywords": brand.voice_keywords},
            "content": {
                "base_hashtags": brand.base_hashtags,
                "cta_options": brand.cta_options,
            },
            "brand_assets": {
                "instagram_handle": brand.instagram_handle,
                "website": brand.website,
                "logo_path": brand.logo_path,
            },
        }
        config_path = brands_dir / f"{brand.id}.json"
        config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))
    except Exception as e:
        import logging
        logging.getLogger("postforge").warning(f"Could not write brand config file: {e}")
