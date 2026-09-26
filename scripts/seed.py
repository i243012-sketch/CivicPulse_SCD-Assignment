#!/usr/bin/env python3
"""
Idempotent seed script for CivicPulse complaints.

Seeds at least 30 realistic complaints in Urdu-influenced English across all categories.
Idempotent: running multiple times will not create duplicates.

USAGE:
    From project root:
        cd backend
        source venv/bin/activate
        python ../scripts/seed.py
    
    Or directly:
        cd backend
        venv/bin/python ../scripts/seed.py

REQUIREMENTS:
    - Backend virtual environment with dependencies installed
    - Database running (docker compose up postgres)
    - .env file configured in backend/ directory
"""
import sys
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.complaint import Category, Complaint, Priority, Status


# Seed data: realistic complaints in Urdu-influenced English
SEED_COMPLAINTS = [
    # WATER complaints
    {
        "text": "Pani ki line toot gayi hai, full road flooded ho raha hai. Plz fix karo urgent",
        "location": "Street 14, G-6/2, Islamabad",
        "reporter_contact": "03001234567",
        "category": Category.WATER,
        "priority": Priority.HIGH,
        "ai_summary": "Water line burst causing road flooding",
    },
    {
        "text": "Bahut zyada pani leakage hai underground, road ke neeche se pani aa raha hai continuous",
        "location": "Main Boulevard, DHA Phase 5, Lahore",
        "reporter_contact": "03219876543",
        "category": Category.WATER,
        "priority": Priority.HIGH,
        "ai_summary": "Underground water leak under road",
    },
    {
        "text": "Water supply band hai last 3 days se. Koi tanker bhi nahi aaya. Please help",
        "location": "Block C, Gulshan-e-Iqbal, Karachi",
        "reporter_contact": "03331122334",
        "category": Category.WATER,
        "priority": Priority.NORMAL,
        "ai_summary": "No water supply for 3 days",
    },
    {
        "text": "Main pipe se pani waste ho raha hai continuously. Raat din behta rehta hai. Ye municipality ka paisa waste hai",
        "location": "F-10 Markaz, Islamabad",
        "reporter_contact": None,
        "category": Category.WATER,
        "priority": Priority.NORMAL,
        "ai_summary": "Main pipe wasting water continuously",
    },
    {
        "text": "Gutter ka pani drinking water line mein mix ho raha hai. Health hazard hai ye to",
        "location": "Tariq Road, PECHS, Karachi",
        "reporter_contact": "03457654321",
        "category": Category.WATER,
        "priority": Priority.HIGH,
        "ai_summary": "Sewage mixing with drinking water",
    },
    
    # ELECTRICITY complaints
    {
        "text": "Bijli ka wire loose hai aur road pe gir gaya. Very dangerous situation hai, someone can die",
        "location": "Jail Road, Lahore Cantt",
        "reporter_contact": "03008765432",
        "category": Category.ELECTRICITY,
        "priority": Priority.HIGH,
        "ai_summary": "Loose electrical wire on road, danger",
    },
    {
        "text": "Power outage daily 6 hours. Load shedding schedule bhi follow nahi hoti. Business band ho raha hai",
        "location": "Saddar Bazar, Rawalpindi",
        "reporter_contact": "03124567890",
        "category": Category.ELECTRICITY,
        "priority": Priority.NORMAL,
        "ai_summary": "Daily 6-hour power outages, business impact",
    },
    {
        "text": "Transformer smoke kar raha hai last 2 days se. Anytime blast ho sakta hai. Please replace karo",
        "location": "Model Town, Block D, Lahore",
        "reporter_contact": "03445566778",
        "category": Category.ELECTRICITY,
        "priority": Priority.HIGH,
        "ai_summary": "Transformer smoking, explosion risk",
    },
    {
        "text": "Low voltage ki wajah se sare appliances kharab ho rahe hain. Meter reading bhi galat aati hai",
        "location": "Nazimabad Block 3, Karachi",
        "reporter_contact": None,
        "category": Category.ELECTRICITY,
        "priority": Priority.NORMAL,
        "ai_summary": "Low voltage damaging appliances",
    },
    {
        "text": "Electric pole teda ho gaya hai storm mein. Kisi ghar pe gir sakta hai. Inspection needed",
        "location": "I-8/3, Islamabad",
        "reporter_contact": "03337778899",
        "category": Category.ELECTRICITY,
        "priority": Priority.HIGH,
        "ai_summary": "Tilted electric pole, falling risk",
    },
    {
        "text": "Street ka main junction box khula pada hai bachon ki reach mein. Covering broken hai",
        "location": "Satellite Town, Rawalpindi",
        "reporter_contact": "03112223344",
        "category": Category.ELECTRICITY,
        "priority": Priority.NORMAL,
        "ai_summary": "Open junction box accessible to children",
    },
    
    # SANITATION complaints
    {
        "text": "Sewerage overflow ho raha hai pure mohalle mein. Smell aur flies se rehna mushkil ho gaya",
        "location": "Liaquatabad, Karachi",
        "reporter_contact": "03218887766",
        "category": Category.SANITATION,
        "priority": Priority.HIGH,
        "ai_summary": "Sewage overflow in neighborhood",
    },
    {
        "text": "Garbage collection nahi ho rahi 2 hafte se. Kuda ka dhair ban gaya hai jo hospital ke samne hai",
        "location": "Near Civil Hospital, Faisalabad",
        "reporter_contact": "03009998877",
        "category": Category.SANITATION,
        "priority": Priority.HIGH,
        "ai_summary": "No garbage collection for 2 weeks near hospital",
    },
    {
        "text": "Manhole ka cover missing hai already 1 month se. Raat ko kisi ka accident ho sakta hai easily",
        "location": "Gulberg III, Main Boulevard, Lahore",
        "reporter_contact": "03334445566",
        "category": Category.SANITATION,
        "priority": Priority.HIGH,
        "ai_summary": "Missing manhole cover for 1 month",
    },
    {
        "text": "Public toilet bilkul ganda condition mein hai. Na pani hai na saaf safai. Disease spread ho raha hai",
        "location": "Saddar Metro Station, Karachi",
        "reporter_contact": None,
        "category": Category.SANITATION,
        "priority": Priority.NORMAL,
        "ai_summary": "Unsanitary public toilet, no water/cleaning",
    },
    {
        "text": "Garbage bin overflowing hai 24/7. Collection van sirf 2 baar aati hai week mein. Not enough",
        "location": "F-7 Markaz, Islamabad",
        "reporter_contact": "03227778888",
        "category": Category.SANITATION,
        "priority": Priority.NORMAL,
        "ai_summary": "Overflowing garbage bin, insufficient collection",
    },
    {
        "text": "Gutter ka paani stagnant hai park ke paas. Mosquitoes ka breeding ground ban gaya hai",
        "location": "Johar Town, Block H, Lahore",
        "reporter_contact": "03459998877",
        "category": Category.SANITATION,
        "priority": Priority.NORMAL,
        "ai_summary": "Stagnant sewage water, mosquito breeding",
    },
    
    # ROADS complaints
    {
        "text": "Road pe bada crater ban gaya hai barish ke baad. Cars ka tyre puncture ho raha hai daily",
        "location": "University Road, Peshawar",
        "reporter_contact": "03341112233",
        "category": Category.ROADS,
        "priority": Priority.HIGH,
        "ai_summary": "Large crater on road after rain, daily punctures",
    },
    {
        "text": "Main road ki carpeting utar gayi hai completely. Dust aur potholes se driving impossible hai",
        "location": "Shahrah-e-Faisal, Karachi",
        "reporter_contact": "03008889999",
        "category": Category.ROADS,
        "priority": Priority.HIGH,
        "ai_summary": "Road carpeting gone, dust and potholes",
    },
    {
        "text": "Construction ka kaam incomplete chor diya 6 months se. Half road banda hai traffic jam lagta rehta hai",
        "location": "Mall Road, Murree",
        "reporter_contact": "03126667788",
        "category": Category.ROADS,
        "priority": Priority.NORMAL,
        "ai_summary": "Incomplete construction blocking half road for 6 months",
    },
    {
        "text": "Speed breaker bilkul unmarked hai visibility zero. Already 3 accidents ho chuke hain iss mahine",
        "location": "Main GT Road, Gujranwala",
        "reporter_contact": "03445554433",
        "category": Category.ROADS,
        "priority": Priority.HIGH,
        "ai_summary": "Unmarked speed breaker, 3 accidents this month",
    },
    {
        "text": "Footpath toot gaya hai senior citizens walk nahi kar sakte. Repair urgently needed hai",
        "location": "Clifton Block 5, Karachi",
        "reporter_contact": None,
        "category": Category.ROADS,
        "priority": Priority.NORMAL,
        "ai_summary": "Broken footpath, seniors cannot walk",
    },
    {
        "text": "Road pe bohot chhote chhote potholes hain har jagah. Bike riders ko takleef hoti hai",
        "location": "Garden Town, Lahore",
        "reporter_contact": "03228889900",
        "category": Category.ROADS,
        "priority": Priority.LOW,
        "ai_summary": "Multiple small potholes, difficulty for bikers",
    },
    
    # STREETLIGHTS complaints
    {
        "text": "Saari streetlights band hain 2 hafte se. Raat ko purse snatching incidents badh gaye hain security issue hai",
        "location": "Bahria Town Phase 4, Rawalpindi",
        "reporter_contact": "03331234567",
        "category": Category.STREETLIGHTS,
        "priority": Priority.HIGH,
        "ai_summary": "All streetlights off for 2 weeks, security risk",
    },
    {
        "text": "Street light ka electric wire dangle kar raha hai neeche. Touch karne se shock lag sakta hai",
        "location": "Blue Area, Islamabad",
        "reporter_contact": "03118887654",
        "category": Category.STREETLIGHTS,
        "priority": Priority.HIGH,
        "ai_summary": "Streetlight wire dangling, shock hazard",
    },
    {
        "text": "Light bulbs jal gaye hain 6 poles ki. Din mein bhi dikhai nahi deta andhera rehta hai shade ki wajah se",
        "location": "Saddar, Multan",
        "reporter_contact": None,
        "category": Category.STREETLIGHTS,
        "priority": Priority.NORMAL,
        "ai_summary": "6 pole bulbs burned out, poor visibility",
    },
    {
        "text": "Solar lights install kiye the but wo 3 months se kharab hain. Maintenance ka koi system nahi hai",
        "location": "DHA Phase 2, Karachi",
        "reporter_contact": "03229876543",
        "category": Category.STREETLIGHTS,
        "priority": Priority.NORMAL,
        "ai_summary": "Solar lights broken for 3 months, no maintenance",
    },
    {
        "text": "Raat 10 baje tak on rehti hain lights phir automatic off ho jati hain. Timer setting galat hai",
        "location": "E-11, Islamabad",
        "reporter_contact": "03447778899",
        "category": Category.STREETLIGHTS,
        "priority": Priority.LOW,
        "ai_summary": "Streetlights turn off at 10pm, timer issue",
    },
    
    # OTHER complaints
    {
        "text": "Park ke swings toote hue hain aur rusty bhi. Bachon ke liye dangerous hai khelna",
        "location": "Jinnah Park, Rawalpindi",
        "reporter_contact": "03338889911",
        "category": Category.OTHER,
        "priority": Priority.NORMAL,
        "ai_summary": "Broken rusty swings in park, danger to children",
    },
    {
        "text": "Stray dogs ka pack ban gaya hai 15-20 dogs. School jane wale bachon ko dart te hain threatening behaviour",
        "location": "Model Colony, Karachi",
        "reporter_contact": "03125554433",
        "category": Category.OTHER,
        "priority": Priority.HIGH,
        "ai_summary": "Pack of stray dogs threatening school children",
    },
    {
        "text": "Bus stop ka shelter gir gaya hai storm mein. Dhoop aur barish mein logo ko wait karna mushkil hai",
        "location": "Zero Point, Islamabad",
        "reporter_contact": None,
        "category": Category.OTHER,
        "priority": Priority.NORMAL,
        "ai_summary": "Bus stop shelter collapsed in storm",
    },
    {
        "text": "Public WiFi jo lagaya tha wo kabhi kaam nahi karta. Students library mein online classes attend nahi kar sakte",
        "location": "Central Library, Lahore",
        "reporter_contact": "03457772211",
        "category": Category.OTHER,
        "priority": Priority.LOW,
        "ai_summary": "Public WiFi never works, students affected",
    },
    {
        "text": "Footpath pe encroachment ho gayi hai dukandaron ne. Pedestrians road pe chalne par majboor hain dangerous",
        "location": "Anarkali Bazaar, Lahore",
        "reporter_contact": "03008881122",
        "category": Category.OTHER,
        "priority": Priority.NORMAL,
        "ai_summary": "Shop encroachment on footpath, pedestrians forced to road",
    },
    {
        "text": "Community center ki building cracks aa gayi hain walls mein. Safety inspection karwao please",
        "location": "I-10, Islamabad",
        "reporter_contact": "03229991122",
        "category": Category.OTHER,
        "priority": Priority.NORMAL,
        "ai_summary": "Wall cracks in community center, safety concern",
    },
]


def seed_complaints():
    """Seed the database with realistic complaints. Idempotent operation."""
    db = SessionLocal()
    try:
        print(f"Starting seed process with {len(SEED_COMPLAINTS)} complaints...")
        inserted = 0
        skipped = 0
        
        for complaint_data in SEED_COMPLAINTS:
            # Check if complaint already exists (same text + location)
            existing = db.execute(
                select(Complaint).where(
                    Complaint.text == complaint_data["text"],
                    Complaint.location == complaint_data["location"],
                )
            ).scalar_one_or_none()
            
            if existing:
                skipped += 1
                print(f"  ⏭️  Skipped (already exists): {complaint_data['location'][:30]}...")
                continue
            
            # Create new complaint
            complaint = Complaint(
                text=complaint_data["text"],
                location=complaint_data["location"],
                reporter_contact=complaint_data.get("reporter_contact"),
                category=complaint_data["category"],
                priority=complaint_data["priority"],
                status=Status.OPEN,
                ai_summary=complaint_data["ai_summary"],
                triaged_by="seed:manual",  # Indicate this was manually seeded
                triage_latency_ms=0,  # No actual triage was performed
            )
            
            db.add(complaint)
            inserted += 1
            print(f"  ✅ Inserted: {complaint_data['category'].value} - {complaint_data['location'][:40]}...")
        
        # Commit all insertions
        db.commit()
        
        print("\n" + "="*60)
        print(f"Seed complete!")
        print(f"  Inserted: {inserted} new complaints")
        print(f"  Skipped:  {skipped} existing complaints")
        print(f"  Total:    {len(SEED_COMPLAINTS)} complaints processed")
        print("="*60)
        
        # Show category distribution
        print("\nCategory distribution:")
        categories = {}
        for complaint_data in SEED_COMPLAINTS:
            cat = complaint_data["category"].value
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items()):
            print(f"  {cat:15} : {count} complaints")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("\n🌱 CivicPulse Database Seeding")
    print("="*60)
    seed_complaints()
    print("\n✨ Done!\n")
