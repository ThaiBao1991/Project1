from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Boolean, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class City(Base):
    __tablename__ = 'cities'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    wards = relationship("Ward", back_populates="city")

class Ward(Base):
    __tablename__ = 'wards'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    city_id = Column(Integer, ForeignKey('cities.id'))
    city = relationship("City", back_populates="wards")
    streets = relationship("Street", back_populates="ward")

class Street(Base):
    __tablename__ = 'streets'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    ward_id = Column(Integer, ForeignKey('wards.id'))
    ward = relationship("Ward", back_populates="streets")
    restaurants = relationship("Restaurant", back_populates="street")

class Food(Base):
    __tablename__ = 'foods'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    restaurant_foods = relationship("RestaurantFood", back_populates="food")

class Restaurant(Base):
    __tablename__ = 'restaurants'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    street_id = Column(Integer, ForeignKey('streets.id'))
    street = relationship("Street", back_populates="restaurants")
    opening_time = Column(String)
    closing_time = Column(String)
    rating = Column(Float, default=0.0)
    foods = relationship("RestaurantFood", back_populates="restaurant")
    is_deleted = Column(Boolean, default=False)
    last_modified = Column(Integer)  # Unix timestamp

class RestaurantFood(Base):
    __tablename__ = 'restaurant_foods'
    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'))
    food_id = Column(Integer, ForeignKey('foods.id'))
    price = Column(Float)
    restaurant = relationship("Restaurant", back_populates="foods")
    food = relationship("Food", back_populates="restaurant_foods")

class DBManager:
    def __init__(self, db_path='data/local_db.sqlite'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        return self.Session()