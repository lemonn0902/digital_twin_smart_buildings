from sqlalchemy import create_engine
from core.utils.config import get_settings
from core.models.database import Base

from core.models.database import Building, Zone, ZoneConnection


def init_database():
    """Initialize database tables."""
    settings = get_settings()
    engine = create_engine(settings.db_url, echo=True)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    print("Database tables created successfully!")


def create_demo_data():
    """Create demo building data."""
    from sqlalchemy.orm import sessionmaker
    
    settings = get_settings()
    engine = create_engine(settings.db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create demo building
        building = Building(
            id="demo-building",
            name="Demo Smart Building",
            address="123 Innovation Drive",
            total_area_m2=500.0,
            num_floors=2
        )
        session.add(building)
        
        # Create zones
        zones = [
            Zone(id="z1", building_id="demo-building", name="Open Office", floor=1, area_m2=120.0, zone_type="office"),
            Zone(id="z2", building_id="demo-building", name="Meeting Room", floor=1, area_m2=30.0, zone_type="meeting"),
            Zone(id="z3", building_id="demo-building", name="Corridor", floor=1, area_m2=40.0, zone_type="circulation"),
        ]
        
        for zone in zones:
            session.add(zone)
        
        # Create connections
        connections = [
            ZoneConnection(zone_a_id="z1", zone_b_id="z2", connection_type="door"),
            ZoneConnection(zone_a_id="z1", zone_b_id="z3", connection_type="door"),
        ]
        
        for conn in connections:
            session.add(conn)
        
        session.commit()
        print("Demo data created successfully!")
    
    except Exception as e:
        session.rollback()
        print(f"Error creating demo data: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    init_database()
    create_demo_data()
