import os
import json
import time
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

class SyncManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.drive = None
        self.file_id = None
        self.last_sync = 0
    
    def authenticate_drive(self):
        try:
            gauth = GoogleAuth()
            # Try to load saved client credentials
            gauth.LoadCredentialsFile("credentials.json")
            
            if gauth.credentials is None:
                # Authenticate if they're not there
                gauth.LocalWebserverAuth()
            elif gauth.access_token_expired:
                # Refresh them if expired
                gauth.Refresh()
            else:
                # Initialize the saved creds
                gauth.Authorize()
                
            # Save the current credentials to a file
            gauth.SaveCredentialsFile("credentials.json")
            self.drive = GoogleDrive(gauth)
            return True
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def find_or_create_data_file(self):
        if not self.drive:
            return False
            
        file_list = self.drive.ListFile({'q': "title='food_app_data.json'"}).GetList()
        
        if file_list:
            self.file_id = file_list[0]['id']
        else:
            # Create new file
            file = self.drive.CreateFile({'title': 'food_app_data.json'})
            file.SetContentString(json.dumps({
                'timestamp': int(time.time()),
                'data': {
                    'cities': [],
                    'wards': [],
                    'streets': [],
                    'foods': [],
                    'restaurants': [],
                    'restaurant_foods': []
                }
            }))
            file.Upload()
            self.file_id = file['id']
        
        return True
    
    def export_data(self):
        """Export database to JSON for sync"""
        session = self.db_manager.get_session()
        data = {
            'timestamp': int(time.time()),
            'data': {
                'cities': [],
                'wards': [],
                'streets': [],
                'foods': [],
                'restaurants': [],
                'restaurant_foods': []
            }
        }
        
        # Export cities
        from database import City, Ward, Street, Food, Restaurant, RestaurantFood
        
        cities = session.query(City).all()
        for city in cities:
            data['data']['cities'].append({
                'id': city.id,
                'name': city.name
            })
        
        # Export wards
        wards = session.query(Ward).all()
        for ward in wards:
            data['data']['wards'].append({
                'id': ward.id,
                'name': ward.name,
                'city_id': ward.city_id
            })
        
        # Export streets
        streets = session.query(Street).all()
        for street in streets:
            data['data']['streets'].append({
                'id': street.id,
                'name': street.name,
                'ward_id': street.ward_id
            })
        
        # Export foods
        foods = session.query(Food).all()
        for food in foods:
            data['data']['foods'].append({
                'id': food.id,
                'name': food.name
            })
        
        # Export restaurants
        restaurants = session.query(Restaurant).all()
        for restaurant in restaurants:
            data['data']['restaurants'].append({
                'id': restaurant.id,
                'name': restaurant.name,
                'street_id': restaurant.street_id,
                'opening_time': restaurant.opening_time,
                'closing_time': restaurant.closing_time,
                'rating': restaurant.rating,
                'is_deleted': restaurant.is_deleted,
                'last_modified': restaurant.last_modified
            })
        
        # Export restaurant foods
        restaurant_foods = session.query(RestaurantFood).all()
        for rf in restaurant_foods:
            data['data']['restaurant_foods'].append({
                'id': rf.id,
                'restaurant_id': rf.restaurant_id,
                'food_id': rf.food_id,
                'price': rf.price
            })
        
        session.close()
        return data
    
    def import_data(self, data):
        """Import JSON data to database"""
        session = self.db_manager.get_session()
        
        from database import City, Ward, Street, Food, Restaurant, RestaurantFood
        
        # Import cities
        for city_data in data['data']['cities']:
            city = session.query(City).filter_by(id=city_data['id']).first()
            if not city:
                city = City(id=city_data['id'], name=city_data['name'])
                session.add(city)
            else:
                city.name = city_data['name']
        
        # Import wards
        for ward_data in data['data']['wards']:
            ward = session.query(Ward).filter_by(id=ward_data['id']).first()
            if not ward:
                ward = Ward(id=ward_data['id'], name=ward_data['name'], city_id=ward_data['city_id'])
                session.add(ward)
            else:
                ward.name = ward_data['name']
                ward.city_id = ward_data['city_id']
        
        # Import streets
        for street_data in data['data']['streets']:
            street = session.query(Street).filter_by(id=street_data['id']).first()
            if not street:
                street = Street(id=street_data['id'], name=street_data['name'], ward_id=street_data['ward_id'])
                session.add(street)
            else:
                street.name = street_data['name']
                street.ward_id = street_data['ward_id']
        
        # Import foods
        for food_data in data['data']['foods']:
            food = session.query(Food).filter_by(id=food_data['id']).first()
            if not food:
                food = Food(id=food_data['id'], name=food_data['name'])
                session.add(food)
            else:
                food.name = food_data['name']
        
        # Import restaurants
        for restaurant_data in data['data']['restaurants']:
            restaurant = session.query(Restaurant).filter_by(id=restaurant_data['id']).first()
            if not restaurant:
                restaurant = Restaurant(
                    id=restaurant_data['id'], 
                    name=restaurant_data['name'],
                    street_id=restaurant_data['street_id'],
                    opening_time=restaurant_data['opening_time'],
                    closing_time=restaurant_data['closing_time'],
                    rating=restaurant_data['rating'],
                    is_deleted=restaurant_data['is_deleted'],
                    last_modified=restaurant_data['last_modified']
                )
                session.add(restaurant)
            else:
                if restaurant.last_modified < restaurant_data['last_modified']:
                    restaurant.name = restaurant_data['name']
                    restaurant.street_id = restaurant_data['street_id']
                    restaurant.opening_time = restaurant_data['opening_time']
                    restaurant.closing_time = restaurant_data['closing_time']
                    restaurant.rating = restaurant_data['rating']
                    restaurant.is_deleted = restaurant_data['is_deleted']
                    restaurant.last_modified = restaurant_data['last_modified']
        
        # Import restaurant foods
        for rf_data in data['data']['restaurant_foods']:
            rf = session.query(RestaurantFood).filter_by(id=rf_data['id']).first()
            if not rf:
                rf = RestaurantFood(
                    id=rf_data['id'],
                    restaurant_id=rf_data['restaurant_id'],
                    food_id=rf_data['food_id'],
                    price=rf_data['price']
                )
                session.add(rf)
            else:
                rf.restaurant_id = rf_data['restaurant_id']
                rf.food_id = rf_data['food_id']
                rf.price = rf_data['price']
        
        session.commit()
        session.close()
    
    def upload_to_drive(self):
        if not self.drive or not self.file_id:
            return False
        
        try:
            data = self.export_data()
            file = self.drive.CreateFile({'id': self.file_id})
            file.SetContentString(json.dumps(data))
            file.Upload()
            self.last_sync = data['timestamp']
            return True
        except Exception as e:
            print(f"Upload error: {e}")
            return False
    
    def download_from_drive(self):
        if not self.drive or not self.file_id:
            return False
        
        try:
            file = self.drive.CreateFile({'id': self.file_id})
            file.GetContentFile('temp_data.json')
            
            with open('temp_data.json', 'r') as f:
                data = json.loads(f.read())
            
            if data['timestamp'] > self.last_sync:
                self.import_data(data)
                self.last_sync = data['timestamp']
                os.remove('temp_data.json')
                return True
            
            os.remove('temp_data.json')
            return False
        except Exception as e:
            print(f"Download error: {e}")
            return False
    
    def check_for_updates(self):
        """Check if there are new updates on Drive"""
        if not self.drive or not self.file_id:
            return False
        
        try:
            file = self.drive.CreateFile({'id': self.file_id})
            metadata = file.GetMetadata()
            drive_modified = int(metadata['modifiedDate'].timestamp())
            
            return drive_modified > self.last_sync
        except Exception as e:
            print(f"Check updates error: {e}")
            return False
    
    def merge_changes(self, local_changes):
        """Merge local changes with cloud data"""
        # This is a simplified version - real implementation would need conflict resolution
        if not self.drive or not self.file_id:
            return False
            
        try:
            # Get cloud data
            file = self.drive.CreateFile({'id': self.file_id})
            file.GetContentFile('temp_data.json')
            
            with open('temp_data.json', 'r') as f:
                cloud_data = json.loads(f.read())
            
            # Import cloud data first
            self.import_data(cloud_data)
            
            # Then apply local changes
            session = self.db_manager.get_session()
            
            # Apply local_changes to database
            # This is simplified - would need proper merge logic
            
            session.commit()
            session.close()
            
            # Upload merged data back to drive
            self.upload_to_drive()
            
            os.remove('temp_data.json')
            return True
        except Exception as e:
            print(f"Merge error: {e}")
            return False