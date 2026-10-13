"""Seed a default CompanyConfig row if none exists."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings
from app.models.company import CompanyConfig


async def seed():
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        result = await session.execute(select(CompanyConfig).limit(1))
        existing = result.scalar_one_or_none()

        if existing:
            print("Company config already exists — skipping seed.")
            return

        company = CompanyConfig(
            name="TapReview",
            mission="Help small businesses collect more Google reviews with a single NFC tap.",
            vision="Every restaurant, cafe, and convenience store in India has a tap-to-review system at the counter.",
            description="NFC tags pre-programmed to open customised Google review flows, with a management dashboard for business owners.",
            target_market="Small businesses in India — restaurants, cafes, convenience stores.",
            value_prop="Get 5x more Google reviews by making it effortless — customers tap, review, done in under 10 seconds.",
            pricing_model={"plans": [{"name": "Starter", "price_inr": 999, "nfc_cards": 2}, {"name": "Business", "price_inr": 2499, "nfc_cards": 10}]},
            goals={"2026": ["Validate product-market fit with 10 paying beta customers", "Launch in Mumbai and Pune", "Build waitlist of 500 businesses"]},
            kpis={"mrr_inr": 0, "active_customers": 0, "nfc_cards_shipped": 0, "avg_reviews_per_card_per_month": 0},
            website_url="https://tapreview.in",
            github_repo="placeholder/tapreview",
            product_type="Hardware + SaaS",
            industry="Local Business Tech",
            timezone="Asia/Kolkata",
            daily_cycle_hour=10,
        )
        session.add(company)
        await session.commit()
        print(f"Seeded company: {company.name}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
