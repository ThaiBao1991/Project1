import os
import time
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.core.window import Window

from database import DBManager
from auth import AuthManager
from sync import SyncManager

class LoginScreen(Screen):
    def __init__(self, auth_manager, **kwargs):
        super().__init__(**kwargs)
        self.auth_manager = auth_manager
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Title
        title = Label(text='Ứng dụng Quản lý Quán Ăn', font_size=24, size_hint=(1, 0.2))
        layout.add_widget(title)
        
        # Username
        username_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        username_label = Label(text='Tên đăng nhập:', size_hint=(0.3, 1))
        self.username_input = TextInput(multiline=False, size_hint=(0.7, 1))
        username_layout.add_widget(username_label)
        username_layout.add_widget(self.username_input)
        layout.add_widget(username_layout)
        
        # Password
        password_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        password_label = Label(text='Mật khẩu:', size_hint=(0.3, 1))
        self.password_input = TextInput(multiline=False, password=True, size_hint=(0.7, 1))
        password_layout.add_widget(password_label)
        password_layout.add_widget(self.password_input)
        layout.add_widget(password_layout)
        
        # Login button
        login_button = Button(text='Đăng nhập', size_hint=(1, 0.15))
        login_button.bind(on_press=self.login)
        layout.add_widget(login_button)
        
        # Skip button
        skip_button = Button(text='Bỏ qua (Chế độ xem)', size_hint=(1, 0.15))
        skip_button.bind(on_press=self.skip_login)
        layout.add_widget(skip_button)
        
        self.add_widget(layout)
    
    def login(self, instance):
        username = self.username_input.text
        password = self.password_input.text
        
        if self.auth_manager.login(username, password):
            # Successful login as admin
            self.manager.transition.direction = 'left'
            self.manager.current = 'main'
        else:
            # Failed login
            popup = Popup(title='Lỗi đăng nhập',
                         content=Label(text='Tên đăng nhập hoặc mật khẩu không đúng'),
                         size_hint=(0.8, 0.3))
            popup.open()
    
    def skip_login(self, instance):
        # Enter as guest - no admin rights
        self.auth_manager.is_admin = False
        self.manager.transition.direction = 'left'
        self.manager.current = 'main'

class MainScreen(Screen):
    def __init__(self, db_manager, auth_manager, sync_manager, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.sync_manager = sync_manager
        
        # Main layout
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        # Top bar with sync status and admin actions
        top_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        
        self.sync_status = Label(text='Offline', size_hint=(0.3, 1))
        top_bar.add_widget(self.sync_status)
        
        # Sync button 
        self.sync_button = Button(text='Đồng bộ', size_hint=(0.3, 1))
        self.sync_button.bind(on_press=self.sync_data)
        top_bar.add_widget(self.sync_button)
        
        # Admin button (only visible for admin)
        self.admin_button = Button(text='Quản lý', size_hint=(0.4, 1))
        self.admin_button.bind(on_press=self.open_admin)
        top_bar.add_widget(self.admin_button)
        
        self.layout.add_widget(top_bar)
        
        # Search filters
        filter_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        
        self.city_spinner = Spinner(text='Chọn thành phố', size_hint=(0.33, 1))
        self.ward_spinner = Spinner(text='Chọn phường', size_hint=(0.33, 1))
        self.street_spinner = Spinner(text='Chọn đường', size_hint=(0.33, 1))
        
        filter_bar.add_widget(self.city_spinner)
        filter_bar.add_widget(self.ward_spinner)
        filter_bar.add_widget(self.street_spinner)
        
        self.layout.add_widget(filter_bar)
        
        # Search bar
        search_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        
        self.search_input = TextInput(hint_text='Tìm kiếm quán ăn hoặc món ăn', 
                                     multiline=False, size_hint=(0.7, 1))
        search_button = Button(text='Tìm', size_hint=(0.3, 1))
        search_button.bind(on_press=self.search_restaurants)
        
        search_bar.add_widget(self.search_input)
        search_bar.add_widget(search_button)
        
        self.layout.add_widget(search_bar)
        
        # Restaurant list (placeholder - will be populated)
        self.restaurant_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.7))
        self.layout.add_widget(self.restaurant_layout)
        
        self.add_widget(self.layout)
        
        # Check sync on init and load data
        Clock.schedule_once(self.check_initial_sync, 1)
        Clock.schedule_interval(self.update_admin_visibility, 0.5)
    
    def check_initial_sync(self, dt):
        """Check for internet and sync status on startup"""
        # Try to authenticate with Google Drive
        if self.sync_manager.authenticate_drive():
            self.sync_status.text = 'Online'
            self.sync_manager.find_or_create_data_file()
            
            # Check for updates
            if self.sync_manager.check_for_updates():
                popup = Popup(title='Cập nhật từ Drive',
                             content=Label(text='Có dữ liệu mới trên Drive. Bạn có muốn tải xuống?'),
                             size_hint=(0.8, 0.3))
                
                # Buttons
                btn_layout = BoxLayout(orientation='horizontal')
                yes_btn = Button(text='Có')
                no_btn = Button(text='Không')
                
                yes_btn.bind(on_press=lambda x: self.download_updates(popup))
                no_btn.bind(on_press=popup.dismiss)
                
                btn_layout.add_widget(yes_btn)
                btn_layout.add_widget(no_btn)
                
                popup.content = btn_layout
                popup.open()
        else:
            self.sync_status.text = 'Offline'
        
        # Load restaurant data
        self.load_restaurants()
        self.load_filter_data()
    
    def download_updates(self, popup):
        """Download updates from Drive"""
        popup.dismiss()
        self.sync_manager.download_from_drive()
        self.load_restaurants()  # Reload with new data
    
    def update_admin_visibility(self, dt):
        """Update UI elements based on admin status"""
        is_admin = self.auth_manager.check_admin()
        self.admin_button.disabled = not is_admin
        self.admin_button.opacity = 1 if is_admin else 0
    
    def sync_data(self, instance):
        """Sync data with Google Drive"""
        if self.sync_manager.authenticate_drive():
            self.sync_status.text = 'Đang đồng bộ...'
            
            if self.sync_manager.find_or_create_data_file():
                if self.auth_manager.check_admin():
                    # Admin can upload changes
                    self.sync_manager.upload_to_drive()
                    self.sync_status.text = 'Đã đồng bộ'
                else:
                    # Non-admin can only download
                    self.sync_manager.download_from_drive()
                    self.load_restaurants()  # Reload with new data
                    self.sync_status.text = 'Đã đồng bộ'
            else:
                self.sync_status.text = 'Lỗi đồng bộ'
        else:
            self.sync_status.text = 'Offline'
    
    def load_filter_data(self):
        """Load data for filter spinners"""
        session = self.db_manager.get_session()
        
        from database import City, Ward, Street
        
        # Load cities
        cities = session.query(City).all()
        city_names = [city.name for city in cities]
        self.city_spinner.values = city_names
        
        # Update ward spinner when city is selected
        def on_city_select(spinner, text):
            if text not in city_names:
                return
                
            selected_city = session.query(City).filter_by(name=text).first()
            
            if selected_city:
                wards = session.query(Ward).filter_by(city_id=selected_city.id).all()
                ward_names = [ward.name for ward in wards]
                self.ward_spinner.values = ward_names
                self.ward_spinner.text = 'Chọn phường'
        
        self.city_spinner.bind(text=on_city_select)
        
        # Update street spinner when ward is selected
        def on_ward_select(spinner, text):
            if self.city_spinner.text == 'Chọn thành phố':
                return
                
            selected_city = session.query(City).filter_by(name=self.city_spinner.text).first()
            
            if not selected_city:
                return
                
            selected_ward = session.query(Ward).filter_by(name=text, city_id=selected_city.id).first()
            
            if selected_ward:
                streets = session.query(Street).filter_by(ward_id=selected_ward.id).all()
                street_names = [street.name for street in streets]
                self.street_spinner.values = street_names
                self.street_spinner.text = 'Chọn đường'
        
        self.ward_spinner.bind(text=on_ward_select)
        
        session.close()
    
    def load_restaurants(self):
        """Load restaurant data based on filters"""
        # Clear current list
        self.restaurant_layout.clear_widgets()
        
        session = self.db_manager.get_session()
        
        from database import Restaurant, Street, Ward, City
        
        # Base query
        query = session.query(Restaurant).filter_by(is_deleted=False)
        
        # Apply filters
        if self.street_spinner.text != 'Chọn đường':
            street = session.query(Street).filter_by(name=self.street_spinner.text).first()
            if street:
                query = query.filter_by(street_id=street.id)
        elif self.ward_spinner.text != 'Chọn phường':
            ward = session.query(Ward).filter_by(name=self.ward_spinner.text).first()
            if ward:
                streets = session.query(Street).filter_by(ward_id=ward.id).all()
                street_ids = [street.id for street in streets]
                query = query.filter(Restaurant.street_id.in_(street_ids))
        elif self.city_spinner.text != 'Chọn thành phố':
            city = session.query(City).filter_by(name=self.city_spinner.text).first()
            if city:
                wards = session.query(Ward).filter_by(city_id=city.id).all()
                ward_ids = [ward.id for ward in wards]
                streets = session.query(Street).filter(Street.ward_id.in_(ward_ids)).all()
                street_ids = [street.id for street in streets]
                query = query.filter(Restaurant.street_id.in_(street_ids))
        
        # Get restaurants
        restaurants = query.all()
        
        # Add to list
        if not restaurants:
            self.restaurant_layout.add_widget(Label(text='Không tìm thấy quán ăn nào'))
        else:
            for restaurant in restaurants:
                # Create restaurant entry
                entry = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40)
                
                # Restaurant name
                name_label = Label(text=restaurant.name, size_hint=(0.6, 1))
                entry.add_widget(name_label)
                
                # Rating
                rating_label = Label(text=f"{restaurant.rating}/5.0", size_hint=(0.2, 1))
                entry.add_widget(rating_label)
                
                # View button
                view_btn = Button(text='Xem', size_hint=(0.2, 1))
                view_btn.restaurant_id = restaurant.id  # Store restaurant ID in button
                view_btn.bind(on_press=self.view_restaurant)
                entry.add_widget(view_btn)
                
                self.restaurant_layout.add_widget(entry)
        
        session.close()
    
    def search_restaurants(self, instance):
        """Search restaurants by name or food item"""
        search_text = self.search_input.text.strip().lower()
        
        if not search_text:
            self.load_restaurants()
            return
            
        # Clear current list
        self.restaurant_layout.clear_widgets()
        
        session = self.db_manager.get_session()
        
        from database import Restaurant, RestaurantFood, Food
        from sqlalchemy import or_
        
        # Search by restaurant name or food name
        food_ids = session.query(Food.id).filter(Food.name.like(f"%{search_text}%")).all()
        food_ids = [fid[0] for fid in food_ids]
        
        restaurant_ids_by_food = []
        if food_ids:
            restaurant_ids_by_food = session.query(RestaurantFood.restaurant_id).filter(
                RestaurantFood.food_id.in_(food_ids)).distinct().all()
            restaurant_ids_by_food = [rid[0] for rid in restaurant_ids_by_food]
        
        # Combined query
        restaurants = session.query(Restaurant).filter(
            or_(
                Restaurant.name.like(f"%{search_text}%"),
                Restaurant.id.in_(restaurant_ids_by_food)
            ),
            Restaurant.is_deleted == False
        ).all()
        
        # Add to list
        if not restaurants:
            self.restaurant_layout.add_widget(Label(text='Không tìm thấy quán ăn nào'))
        else:
            for restaurant in restaurants:
                # Create restaurant entry
                entry = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40)
                
                # Restaurant name
                name_label = Label(text=restaurant.name, size_hint=(0.6, 1))
                entry.add_widget(name_label)
                
                # Rating
                rating_label = Label(text=f"{restaurant.rating}/5.0", size_hint=(0.2, 1))
                entry.add_widget(rating_label)
                
                # View button
                view_btn = Button(text='Xem', size_hint=(0.2, 1))
                view_btn.restaurant_id = restaurant.id  # Store restaurant ID in button
                view_btn.bind(on_press=self.view_restaurant)
                entry.add_widget(view_btn)
                
                self.restaurant_layout.add_widget(entry)
        
        session.close()
    
    def view_restaurant(self, instance):
        """View restaurant details"""
        restaurant_id = instance.restaurant_id
        
        # Pass id to restaurant screen and switch to it
        restaurant_screen = self.manager.get_screen('restaurant')
        restaurant_screen.load_restaurant(restaurant_id)
        
        self.manager.transition.direction = 'left'
        self.manager.current = 'restaurant'
    
    def open_admin(self, instance):
        """Open admin panel (only for admin)"""
        if self.auth_manager.check_admin():
            self.manager.transition.direction = 'left'
            self.manager.current = 'admin'

class RestaurantScreen(Screen):
    def __init__(self, db_manager, auth_manager, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.restaurant_id = None
        
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        # Header with restaurant name and back button
        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        
        back_btn = Button(text='Quay lại', size_hint=(0.3, 1))
        back_btn.bind(on_press=self.go_back)
        header.add_widget(back_btn)
        
        self.restaurant_name = Label(text='Chi tiết quán ăn', size_hint=(0.7, 1))
        header.add_widget(self.restaurant_name)
        
        self.layout.add_widget(header)
        
        # Restaurant details
        self.details_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.3))
        self.layout.add_widget(self.details_layout)
        
        # Food menu
        menu_header = Label(text='Thực đơn', size_hint=(1, 0.1))
        self.layout.add_widget(menu_header)
        
        self.menu_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.5))
        self.layout.add_widget(self.menu_layout)
        
        self.add_widget(self.layout)
    
    def load_restaurant(self, restaurant_id):
        """Load restaurant data"""
        self.restaurant_id = restaurant_id
        session = self.db_manager.get_session()
        
        from database import Restaurant, Street, Ward, City, RestaurantFood, Food
        
        # Get restaurant
        restaurant = session.query(Restaurant).get(restaurant_id)
        
        if restaurant:
            # Set restaurant name
            self.restaurant_name.text = restaurant.name
            
            # Clear previous details
            self.details_layout.clear_widgets()
            
            # Get location info
            street = session.query(Street).get(restaurant.street_id)
            ward = None
            city = None
            
            if street:
                ward = session.query(Ward).get(street.ward_id)
                if ward:
                    city = session.query(City).get(ward.city_id)
            
            # Build address string
            address = ""
            if street:
                address += street.name
            if ward:
                address += f", {ward.name}"
            if city:
                address += f", {city.name}"
            
            # Add details
            self.details_layout.add_widget(Label(text=f"Địa chỉ: {address}"))
            self.details_layout.add_widget(Label(text=f"Giờ mở cửa: {restaurant.opening_time or 'N/A'} - {restaurant.closing_time or 'N/A'}"))
            self.details_layout.add_widget(Label(text=f"Đánh giá: {restaurant.rating}/5.0"))
            
            # Clear menu
            self.menu_layout.clear_widgets()
            
            # Get menu items
            menu_items = session.query(RestaurantFood).filter_by(restaurant_id=restaurant_id).all()
            
            if not menu_items:
                self.menu_layout.add_widget(Label(text='Không có thông tin về thực đơn'))
            else:
                # Create headers
                header = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40)
                header.add_widget(Label(text='Món ăn', size_hint=(0.7, 1)))
                header.add_widget(Label(text='Giá (VND)', size_hint=(0.3, 1)))
                self.menu_layout.add_widget(header)
                
                # Add menu items
                for item in menu_items:
                    food = session.query(Food).get(item.food_id)
                    if food:
                        entry = BoxLayout(orientation='horizontal', size_hint=(1, None), height=30)
                        entry.add_widget(Label(text=food.name, size_hint=(0.7, 1)))
                        entry.add_widget(Label(text=f"{item.price:,.0f}" if item.price else 'N/A', size_hint=(0.3, 1)))
                        self.menu_layout.add_widget(entry)
        else:
            # Restaurant not found
            self.restaurant_name.text = 'Không tìm thấy quán ăn'
        
        session.close()
    
    def go_back(self, instance):
        """Go back to main screen"""
        self.manager.transition.direction = 'right'
        self.manager.current = 'main'

class AdminScreen(Screen):
    def __init__(self, db_manager, auth_manager, sync_manager, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.sync_manager = sync_manager
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        
        back_btn = Button(text='Quay lại', size_hint=(0.3, 1))
        back_btn.bind(on_press=self.go_back)
        header.add_widget(back_btn)
        
        title = Label(text='Quản lý dữ liệu', size_hint=(0.7, 1))
        header.add_widget(title)
        
        layout.add_widget(header)
        
        # Action buttons
        actions = BoxLayout(orientation='vertical', spacing=10, size_hint=(1, 0.3))
        
        add_restaurant_btn = Button(text='Thêm quán ăn mới')
        add_restaurant_btn.bind(on_press=self.add_restaurant)
        actions.add_widget(add_restaurant_btn)
        
        manage_cities_btn = Button(text='Quản lý Thành phố/Phường/Đường')
        manage_cities_btn.bind(on_press=self.manage_locations)
        actions.add_widget(manage_cities_btn)
        
        manage_foods_btn = Button(text='Quản lý món ăn')
        manage_foods_btn.bind(on_press=self.manage_foods)
        actions.add_widget(manage_foods_btn)
        
        sync_btn = Button(text='Đồng bộ dữ liệu với Google Drive')
        sync_btn.bind(on_press=self.sync_data)
        actions.add_widget(sync_btn)
        
        layout.add_widget(actions)
        
        # Restaurant list for editing
        list_label = Label(text='Danh sách quán ăn', size_hint=(1, 0.1))
        layout.add_widget(list_label)
        
        self.restaurant_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.5))
        layout.add_widget(self.restaurant_layout)
        
        self.add_widget(layout)
    
    def on_enter(self):
        """Load restaurant list when screen is entered"""
        self.load_restaurants()
    
    def load_restaurants(self):
        """Load all restaurants for editing"""
        # Clear current list
        self.restaurant_layout.clear_widgets()
        
        session = self.db_manager.get_session()
        
        from database import Restaurant
        
        # Get all restaurants including deleted ones
        restaurants = session.query(Restaurant).all()
        
        # Add to list
        if not restaurants:
            self.restaurant_layout.add_widget(Label(text='Không có quán ăn nào'))
        else:
            # Add header row
            header = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40)
            header.add_widget(Label(text='Tên quán ăn', size_hint=(0.5, 1)))
            header.add_widget(Label(text='Trạng thái', size_hint=(0.2, 1)))
            header.add_widget(Label(text='Hành động', size_hint=(0.3, 1)))
            self.restaurant_layout.add_widget(header)
            
            for restaurant in restaurants:
                # Create restaurant entry
                entry = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40)
                
                # Restaurant name
                name_label = Label(text=restaurant.name, size_hint=(0.5, 1))
                entry.add_widget(name_label)
                
                # Status
                status = 'Đã xóa' if restaurant.is_deleted else 'Hiển thị'
                status_label = Label(text=status, size_hint=(0.2, 1))
                entry.add_widget(status_label)
                
                # Action buttons
                actions = BoxLayout(orientation='horizontal', size_hint=(0.3, 1))
                
                edit_btn = Button(text='Sửa')
                edit_btn.restaurant_id = restaurant.id
                edit_btn.bind(on_press=self.edit_restaurant)
                
                toggle_btn = Button(text='Xóa' if not restaurant.is_deleted else 'Khôi phục')
                toggle_btn.restaurant_id = restaurant.id
                toggle_btn.is_deleted = restaurant.is_deleted
                toggle_btn.bind(on_press=self.toggle_restaurant)
                
                actions.add_widget(edit_btn)
                actions.add_widget(toggle_btn)
                
                entry.add_widget(actions)
                
                self.restaurant_layout.add_widget(entry)
        
        session.close()
    
    def go_back(self, instance):
        """Go back to main screen"""
        self.manager.transition.direction = 'right'
        self.manager.current = 'main'
    
    def add_restaurant(self, instance):
        """Open add restaurant screen"""
        add_screen = self.manager.get_screen('add_restaurant')
        add_screen.reset_form()
        
        self.manager.transition.direction = 'left'
        self.manager.current = 'add_restaurant'
    
    def edit_restaurant(self, instance):
        """Edit existing restaurant"""
        restaurant_id = instance.restaurant_id
        
        add_screen = self.manager.get_screen('add_restaurant')
        add_screen.load_restaurant(restaurant_id)
        
        self.manager.transition.direction = 'left'
        self.manager.current = 'add_restaurant'
    
    def toggle_restaurant(self, instance):
        """Toggle restaurant deleted status"""
        restaurant_id = instance.restaurant_id
        is_deleted = instance.is_deleted
        
        session = self.db_manager.get_session()
        
        from database import Restaurant
        
        restaurant = session.query(Restaurant).get(restaurant_id)
        
        if restaurant:
            restaurant.is_deleted = not is_deleted
            restaurant.last_modified = int(time.time())
            session.commit()
        
        session.close()
        
        # Reload list
        self.load_restaurants()
    
    def manage_locations(self, instance):
        """Manage cities, wards and streets"""
        # Create popup for location management
        popup = Popup(title='Quản lý Địa điểm', 
                     size_hint=(0.9, 0.9))
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        # Tabs for City, Ward, Street
        tabs = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        
        city_btn = Button(text='Thành phố')
        ward_btn = Button(text='Phường')
        street_btn = Button(text='Đường')
        
        tabs.add_widget(city_btn)
        tabs.add_widget(ward_btn)
        tabs.add_widget(street_btn)
        
        layout.add_widget(tabs)
        
        # Content area
        content_area = BoxLayout(orientation='vertical', size_hint=(1, 0.9))
        layout.add_widget(content_area)
        
        # City management content
        city_content = BoxLayout(orientation='vertical')
        
        # Add city form
        add_city_form = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        city_input = TextInput(hint_text='Tên thành phố', size_hint=(0.7, 1))
        add_city_btn = Button(text='Thêm', size_hint=(0.3, 1))
        add_city_form.add_widget(city_input)
        add_city_form.add_widget(add_city_btn)
        
        city_content.add_widget(add_city_form)
        
        # City list
        city_list = BoxLayout(orientation='vertical', size_hint=(1, 0.9))
        refresh_city_list = lambda: self.load_cities(city_list)
        
        add_city_btn.bind(on_press=lambda x: self.add_city(city_input, refresh_city_list))
        
        city_content.add_widget(city_list)
        
        # Ward management content
        ward_content = BoxLayout(orientation='vertical')
        
        # Add ward form
        add_ward_form = BoxLayout(orientation='vertical', size_hint=(1, 0.2))
        
        city_selection = BoxLayout(orientation='horizontal')
        ward_city_spinner = Spinner(text='Chọn thành phố', size_hint=(0.7, 1))
        refresh_city_spinner = Button(text='Làm mới', size_hint=(0.3, 1))
        city_selection.add_widget(ward_city_spinner)
        city_selection.add_widget(refresh_city_spinner)
        
        ward_form = BoxLayout(orientation='horizontal')
        ward_input = TextInput(hint_text='Tên phường', size_hint=(0.7, 1))
        add_ward_btn = Button(text='Thêm', size_hint=(0.3, 1))
        ward_form.add_widget(ward_input)
        ward_form.add_widget(add_ward_btn)
        
        add_ward_form.add_widget(city_selection)
        add_ward_form.add_widget(ward_form)
        
        ward_content.add_widget(add_ward_form)
        
        # Ward list
        ward_list = BoxLayout(orientation='vertical', size_hint=(1, 0.8))
        refresh_ward_list = lambda: self.load_wards(ward_list, ward_city_spinner.text)
        
        refresh_city_spinner.bind(on_press=lambda x: self.update_city_spinner(ward_city_spinner))
        add_ward_btn.bind(on_press=lambda x: self.add_ward(ward_city_spinner.text, ward_input, refresh_ward_list))
        ward_city_spinner.bind(text=lambda x, y: refresh_ward_list())
        
        ward_content.add_widget(ward_list)
        
        # Street management content
        street_content = BoxLayout(orientation='vertical')
        
        # Add street form
        add_street_form = BoxLayout(orientation='vertical', size_hint=(1, 0.3))
        
        street_city_selection = BoxLayout(orientation='horizontal')
        street_city_spinner = Spinner(text='Chọn thành phố', size_hint=(0.7, 1))
        street_refresh_city = Button(text='Làm mới', size_hint=(0.3, 1))
        street_city_selection.add_widget(street_city_spinner)
        street_city_selection.add_widget(street_refresh_city)
        
        street_ward_selection = BoxLayout(orientation='horizontal')
        street_ward_spinner = Spinner(text='Chọn phường', size_hint=(0.7, 1))
        street_refresh_ward = Button(text='Làm mới', size_hint=(0.3, 1))
        street_ward_selection.add_widget(street_ward_spinner)
        street_ward_selection.add_widget(street_refresh_ward)
        
        street_form = BoxLayout(orientation='horizontal')
        street_input = TextInput(hint_text='Tên đường', size_hint=(0.7, 1))
        add_street_btn = Button(text='Thêm', size_hint=(0.3, 1))
        street_form.add_widget(street_input)
        street_form.add_widget(add_street_btn)
        
        add_street_form.add_widget(street_city_selection)
        add_street_form.add_widget(street_ward_selection)
        add_street_form.add_widget(street_form)
        
        street_content.add_widget(add_street_form)
        
        # Street list
        street_list = BoxLayout(orientation='vertical', size_hint=(1, 0.7))
        refresh_street_list = lambda: self.load_streets(street_list, street_ward_spinner.text)
        
        street_refresh_city.bind(on_press=lambda x: self.update_city_spinner(street_city_spinner))
        
        def update_ward_spinner(dt=None):
            self.update_ward_spinner(street_city_spinner.text, street_ward_spinner)
            refresh_street_list()
        
        street_refresh_ward.bind(on_press=lambda x: update_ward_spinner())
        street_city_spinner.bind(text=lambda x, y: update_ward_spinner())
        street_ward_spinner.bind(text=lambda x, y: refresh_street_list())
        
        add_street_btn.bind(on_press=lambda x: self.add_street(
            street_ward_spinner.text, street_input, refresh_street_list))
        
        street_content.add_widget(street_list)
        
        # Initially show city content
        content_area.add_widget(city_content)
        
        # Tab switching logic
        def show_city_tab(instance):
            content_area.clear_widgets()
            content_area.add_widget(city_content)
            refresh_city_list()
        
        def show_ward_tab(instance):
            content_area.clear_widgets()
            content_area.add_widget(ward_content)
            self.update_city_spinner(ward_city_spinner)
        
        def show_street_tab(instance):
            content_area.clear_widgets()
            content_area.add_widget(street_content)
            self.update_city_spinner(street_city_spinner)
        
        city_btn.bind(on_press=show_city_tab)
        ward_btn.bind(on_press=show_ward_tab)
        street_btn.bind(on_press=show_street_tab)
        
        # Initial data loading
        refresh_city_list()
        self.update_city_spinner(ward_city_spinner)
        self.update_city_spinner(street_city_spinner)
        
        popup.content = layout
        popup.open()
    
    def load_cities(self, container):
        """Load cities into container"""
        container.clear_widgets()
        
        session = self.db_manager.get_session()
        
        from database import City
        
        cities = session.query(City).all()
        
        if not cities:
            container.add_widget(Label(text='Không có thành phố nào'))
        else:
            for city in cities:
                entry = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40)
                
                name_label = Label(text=city.name, size_hint=(0.7, 1))
                entry.add_widget(name_label)
                
                delete_btn = Button(text='Xóa', size_hint=(0.3, 1))
                delete_btn.city_id = city.id
                delete_btn.bind(on_press=lambda x: self.delete_city(x.city_id, lambda: self.load_cities(container)))
                entry.add_widget(delete_btn)
                
                container.add_widget(entry)
        
        session.close()
    
    def add_city(self, input_widget, refresh_callback):
        """Add new city"""
        city_name = input_widget.text.strip()
        
        if not city_name:
            return
            
        session = self.db_manager.get_session()
        
        from database import City
        
        # Check if city already exists
        existing = session.query(City).filter_by(name=city_name).first()
        
        if not existing:
            city = City(name=city_name)
            session.add(city)
            session.commit()
            
            # Clear input
            input_widget.text = ''
            
            # Refresh list
            refresh_callback()
        
        session.close()
    
    def delete_city(self, city_id, refresh_callback):
        """Delete city"""
        session = self.db_manager.get_session()
        
        from database import City
        
        city = session.query(City).get(city_id)
        
        if city:
            session.delete(city)
            session.commit()
            
            # Refresh list
            refresh_callback()
        
        session.close()
    
    def update_city_spinner(self, spinner):
        """Update city spinner values"""
        session = self.db_manager.get_session()
        
        from database import City
        
        cities = session.query(City).all()
        city_names = [city.name for city in cities]
        
        spinner.values = city_names
        if city_names:
            spinner.text = city_names[0]
        else:
            spinner.text = 'Không có thành phố'
        
        session.close()
    
    def load_wards(self, container, city_name):
        """Load wards for a city into container"""
        container.clear_widgets()
        
        if city_name == 'Chọn thành phố' or city_name == 'Không có thành phố':
            container.add_widget(Label(text='Vui lòng chọn thành phố'))
            return
            
        session = self.db_manager.get_session()
        
        from database import City, Ward
        
        city = session.query(City).filter_by(name=city_name).first()
        
        if not city:
            container.add_widget(Label(text='Thành phố không tồn tại'))
            session.close()
            return
            
        wards = session.query(Ward).filter_by(city_id=city.id).all()
        
        if not wards:
            container.add_widget(Label(text='Không có phường nào'))
        else:
            for ward in wards:
                entry = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40)
                
                name_label = Label(text=ward.name, size_hint=(0.7, 1))
                entry.add_widget(name_label)
                
                delete_btn = Button(text='Xóa', size_hint=(0.3, 1))
                delete_btn.ward_id = ward.id
                delete_btn.bind(on_press=lambda x: self.delete_ward(
                    x.ward_id, lambda: self.load_wards(container, city_name)))
                entry.add_widget(delete_btn)
                
                container.add_widget(entry)
        
        session.close()
    
    def add_ward(self, city_name, input_widget, refresh_callback):
        """Add new ward to a city"""
        ward_name = input_widget.text.strip()
        
        if not ward_name or city_name == 'Chọn thành phố' or city_name == 'Không có thành phố':
            return
            
        session = self.db_manager.get_session()
        
        from database import City, Ward
        
        city = session.query(City).filter_by(name=city_name).first()
        
        if not city:
            session.close()
            return
            
        # Check if ward already exists in this city
        existing = session.query(Ward).filter_by(name=ward_name, city_id=city.id).first()
        
        if not existing:
            ward = Ward(name=ward_name, city_id=city.id)
            session.add(ward)
            session.commit()
            
            # Clear input
            input_widget.text = ''
            
            # Refresh list
            refresh_callback()
        
        session.close()
    
    def delete_ward(self, ward_id, refresh_callback):
        """Delete ward"""
        session = self.db_manager.get_session()
        
        from database import Ward
        
        ward = session.query(Ward).get(ward_id)
        
        if ward:
            session.delete(ward)
            session.commit()
            
            # Refresh list
            refresh_callback()
        
        session.close()
    
    def update_ward_spinner(self, city_name, spinner):
        """Update ward spinner based on selected city"""
        spinner.values = []
        
        if city_name == 'Chọn thành phố' or city_name == 'Không có thành phố':
            spinner.text = 'Chọn phường'
            return
            
        session = self.db_manager.get_session()
        
        from database import City, Ward
        
        city = session.query(City).filter_by(name=city_name).first()
        
        if not city:
            spinner.text = 'Chọn phường'
            session.close()
            return
            
        wards = session.query(Ward).filter_by(city_id=city.id).all()
        ward_names = [ward.name for ward in wards]
        
        spinner.values = ward_names
        if ward_names:
            spinner.text = ward_names[0]
        else:
            spinner.text = 'Không có phường'
        
        session.close()
    
    def load_streets(self, container, ward_name):
        """Load streets for a ward into container"""
        container.clear_widgets()
        
        if ward_name == 'Chọn phường' or ward_name == 'Không có phường':
            container.add_widget(Label(text='Vui lòng chọn phường'))
            return
            
        session = self.db_manager.get_session()
        
        from database import Ward, Street
        
        ward = session.query(Ward).filter_by(name=ward_name).first()
        
        if not ward:
            container.add_widget(Label(text='Phường không tồn tại'))
            session.close()
            return
            
        streets = session.query(Street).filter_by(ward_id=ward.id).all()
        
        if not streets:
            container.add_widget(Label(text='Không có đường nào'))
        else:
            for street in streets:
                entry = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40)
                
                name_label = Label(text=street.name, size_hint=(0.7, 1))
                entry.add_widget(name_label)
                
                delete_btn = Button(text='Xóa', size_hint=(0.3, 1))
                delete_btn.street_id = street.id
                delete_btn.bind(on_press=lambda x: self.delete_street(
                    x.street_id, lambda: self.load_streets(container, ward_name)))
                entry.add_widget(delete_btn)
                
                container.add_widget(entry)
        
        session.close()
    
    def add_street(self, ward_name, input_widget, refresh_callback):
        """Add new street to a ward"""
        street_name = input_widget.text.strip()
        
        if not street_name or ward_name == 'Chọn phường' or ward_name == 'Không có phường':
            return
            
        session = self.db_manager.get_session()
        
        from database import Ward, Street
        
        ward = session.query(Ward).filter_by(name=ward_name).first()
        
        if not ward:
            session.close()
            return
            
        # Check if street already exists in this ward
        existing = session.query(Street).filter_by(name=street_name, ward_id=ward.id).first()
        
        if not existing:
            street = Street(name=street_name, ward_id=ward.id)
            session.add(street)
            session.commit()
            
            # Clear input
            input_widget.text = ''
            
            # Refresh list
            refresh_callback()
        
        session.close()
    
    def delete_street(self, street_id, refresh_callback):
        """Delete street"""
        session = self.db_manager.get_session()
        
        from database import Street
        
        street = session.query(Street).get(street_id)
        
        if street:
            session.delete(street)
            session.commit()
            
            # Refresh list
            refresh_callback()
        
        session.close()
    
    def manage_foods(self, instance):
        """Manage food items"""
        popup = Popup(title='Quản lý Món ăn', 
                     size_hint=(0.8, 0.8))
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        
        # Add food form
        add_form = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        
        food_input = TextInput(hint_text='Tên món ăn', size_hint=(0.7, 1))
        add_btn = Button(text='Thêm', size_hint=(0.3, 1))
        
        add_form.add_widget(food_input)
        add_form.add_widget(add_btn)
        
        layout.add_widget(add_form)
        
        # Food list
        food_list = BoxLayout(orientation='vertical', size_hint=(1, 0.9))
        
        def refresh_food_list():
            self.load_foods(food_list)
        
        add_btn.bind(on_press=lambda x: self.add_food(food_input, refresh_food_list))
        
        layout.add_widget(food_list)
        
        # Initial data load
        refresh_food_list()
        
        popup.content = layout
        popup.open()
    
    def load_foods(self, container):
        """Load foods into container"""
        container.clear_widgets()
        
        session = self.db_manager.get_session()
        
        from database import Food
        
        foods = session.query(Food).all()
        
        if not foods:
            container.add_widget(Label(text='Không có món ăn nào'))
        else:
            for food in foods:
                entry = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40)
                
                name_label = Label(text=food.name, size_hint=(0.7, 1))
                entry.add_widget(name_label)
                
                delete_btn = Button(text='Xóa', size_hint=(0.3, 1))
                delete_btn.food_id = food.id
                delete_btn.bind(on_press=lambda x: self.delete_food(
                    x.food_id, lambda: self.load_foods(container)))
                entry.add_widget(delete_btn)
                
                container.add_widget(entry)
        
        session.close()
    
    def add_food(self, input_widget, refresh_callback):
        """Add new food"""
        food_name = input_widget.text.strip()
        
        if not food_name:
            return
            
        session = self.db_manager.get_session()
        
        from database import Food
        
        # Check if food already exists
        existing = session.query(Food).filter_by(name=food_name).first()
        
        if not existing:
            food = Food(name=food_name)
            session.add(food)
            session.commit()
            
            # Clear input
            input_widget.text = ''
            
            # Refresh list
            refresh_callback()
        
        session.close()
    
    def delete_food(self, food_id, refresh_callback):
        """Delete food"""
        session = self.db_manager.get_session()
        
        from database import Food
        
        food = session.query(Food).get(food_id)
        
        if food:
            session.delete(food)
            session.commit()
            
            # Refresh list
            refresh_callback()
        
        session.close()
    
    def sync_data(self, instance):
        """Sync data with Google Drive"""
        if self.sync_manager.authenticate_drive():
            if self.sync_manager.find_or_create_data_file():
                # Admin can upload changes
                if self.sync_manager.upload_to_drive():
                    popup = Popup(title='Đồng bộ thành công',
                                content=Label(text='Dữ liệu đã được đồng bộ lên Google Drive'),
                                size_hint=(0.8, 0.3))
                    popup.open()
                else:
                    popup = Popup(title='Lỗi đồng bộ',
                                content=Label(text='Không thể đồng bộ dữ liệu'),
                                size_hint=(0.8, 0.3))
                    popup.open()
            else:
                popup = Popup(title='Lỗi đồng bộ',
                             content=Label(text='Không thể tìm hoặc tạo file dữ liệu'),
                             size_hint=(0.8, 0.3))
                popup.open()
        else:
            popup = Popup(title='Lỗi kết nối',
                         content=Label(text='Không thể kết nối với Google Drive'),
                         size_hint=(0.8, 0.3))
            popup.open()

class AddRestaurantScreen(Screen):
    def __init__(self, db_manager, **kwargs):
        super().__init__(**kwargs)
        self.db_manager = db_manager
        self.restaurant_id = None  # None for new, id for edit
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        
        back_btn = Button(text='Quay lại', size_hint=(0.3, 1))
        back_btn.bind(on_press=self.go_back)
        header.add_widget(back_btn)
        
        self.title_label = Label(text='Thêm quán ăn mới', size_hint=(0.7, 1))
        header.add_widget(self.title_label)
        
        layout.add_widget(header)
        
        # Form layout
        form = BoxLayout(orientation='vertical', spacing=10, size_hint=(1, 0.8))
        
        # Restaurant name
        name_layout = BoxLayout(orientation='horizontal')
        name_label = Label(text='Tên quán:', size_hint=(0.3, 1))
        self.name_input = TextInput(multiline=False, size_hint=(0.7, 1))
        name_layout.add_widget(name_label)
        name_layout.add_widget(self.name_input)
        form.add_widget(name_layout)
        
        # Location selectors
        # City
        city_layout = BoxLayout(orientation='horizontal')
        city_label = Label(text='Thành phố:', size_hint=(0.3, 1))
        self.city_spinner = Spinner(text='Chọn thành phố', size_hint=(0.7, 1))
        city_layout.add_widget(city_label)
        city_layout.add_widget(self.city_spinner)
        form.add_widget(city_layout)
        
        # Ward
        ward_layout = BoxLayout(orientation='horizontal')
        ward_label = Label(text='Phường:', size_hint=(0.3, 1))
        self.ward_spinner = Spinner(text='Chọn phường', size_hint=(0.7, 1))
        ward_layout.add_widget(ward_label)
        ward_layout.add_widget(self.ward_spinner)
        form.add_widget(ward_layout)
        
        # Street
        street_layout = BoxLayout(orientation='horizontal')
        street_label = Label(text='Đường:', size_hint=(0.3, 1))
        self.street_spinner = Spinner(text='Chọn đường', size_hint=(0.7, 1))
        street_layout.add_widget(street_label)
        street_layout.add_widget(self.street_spinner)
        form.add_widget(street_layout)
        
        # Opening hours
        hours_layout = BoxLayout(orientation='horizontal')
        hours_label = Label(text='Giờ mở cửa:', size_hint=(0.3, 1))
        
        hours_inputs = BoxLayout(orientation='horizontal', size_hint=(0.7, 1))
        self.opening_input = TextInput(hint_text='Mở cửa (HH:MM)', multiline=False, size_hint=(0.5, 1))
        self.closing_input = TextInput(hint_text='Đóng cửa (HH:MM)', multiline=False, size_hint=(0.5, 1))
        
        hours_inputs.add_widget(self.opening_input)
        hours_inputs.add_widget(self.closing_input)
        
        hours_layout.add_widget(hours_label)
        hours_layout.add_widget(hours_inputs)
        
        form.add_widget(hours_layout)
        
        # Rating
        rating_layout = BoxLayout(orientation='horizontal')
        rating_label = Label(text='Đánh giá:', size_hint=(0.3, 1))
        self.rating_input = TextInput(text='0.0', input_filter='float', multiline=False, size_hint=(0.7, 1))
        rating_layout.add_widget(rating_label)
        rating_layout.add_widget(self.rating_input)
        form.add_widget(rating_layout)
        
        # Food menu section
        menu_label = Label(text='Thực đơn:', halign='left', size_hint=(1, None), height=40)
        form.add_widget(menu_label)
        
        # Food selection and price
        food_row = BoxLayout(orientation='horizontal')
        self.food_spinner = Spinner(text='Chọn món ăn', size_hint=(0.6, 1))
        self.price_input = TextInput(hint_text='Giá (VND)', input_filter='float', multiline=False, size_hint=(0.2, 1))
        add_food_btn = Button(text='+', size_hint=(0.2, 1))
        add_food_btn.bind(on_press=self.add_food_to_menu)
        
        food_row.add_widget(self.food_spinner)
        food_row.add_widget(self.price_input)
        food_row.add_widget(add_food_btn)
        
        form.add_widget(food_row)
        
        # Menu list
        self.menu_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.4))
        form.add_widget(self.menu_layout)
        
        layout.add_widget(form)
        
        # Save button
        save_btn = Button(text='Lưu', size_hint=(1, 0.1))
        save_btn.bind(on_press=self.save_restaurant)
        layout.add_widget(save_btn)
        
        self.add_widget(layout)
        
        # Data binding
        self.city_spinner.bind(text=self.on_city_select)
        self.ward_spinner.bind(text=self.on_ward_select)
        
        # Menu items storage
        self.menu_items = []  # [(food_id, food_name, price), ...]
    
    def on_pre_enter(self):
        """Load data before showing the screen"""
        self.load_cities()
        self.load_foods()
    
    def load_cities(self):
        """Load cities for spinner"""
        session = self.db_manager.get_session()
        
        from database import City
        
        cities = session.query(City).all()
        city_names = [city.name for city in cities]
        
        self.city_spinner.values = city_names
        
        session.close()
    
    def on_city_select(self, spinner, text):
        """Update ward spinner when city is selected"""
        if text == 'Chọn thành phố':
            self.ward_spinner.values = []
            self.ward_spinner.text = 'Chọn phường'
            return
            
        session = self.db_manager.get_session()
        
        from database import City, Ward
        
        city = session.query(City).filter_by(name=text).first()
        
        if city:
            wards = session.query(Ward).filter_by(city_id=city.id).all()
            ward_names = [ward.name for ward in wards]
            self.ward_spinner.values = ward_names
            self.ward_spinner.text = 'Chọn phường'
        
        session.close()
    
    def on_ward_select(self, spinner, text):
        """Update street spinner when ward is selected"""
        if text == 'Chọn phường':
            self.street_spinner.values = []
            self.street_spinner.text = 'Chọn đường'
            return
            
        session = self.db_manager.get_session()
        
        from database import Ward, Street
        
        ward = session.query(Ward).filter_by(name=text).first()
        
        if ward:
            streets = session.query(Street).filter_by(ward_id=ward.id).all()
            street_names = [street.name for street in streets]
            self.street_spinner.values = street_names
            self.street_spinner.text = 'Chọn đường'
        
        session.close()
    
    def load_foods(self):
        """Load food items for spinner"""
        session = self.db_manager.get_session()
        
        from database import Food
        
        foods = session.query(Food).all()
        food_names = [food.name for food in foods]
        
        self.food_spinner.values = food_names
        
        session.close()
    
    def add_food_to_menu(self, instance):
        """Add food item to restaurant menu"""
        food_name = self.food_spinner.text
        price_text = self.price_input.text.strip()
        
        if food_name == 'Chọn món ăn' or not price_text:
            return
            
        try:
            price = float(price_text)
        except ValueError:
            return
            
        session = self.db_manager.get_session()
        
        from database import Food
        
        food = session.query(Food).filter_by(name=food_name).first()
        
        if food:
            # Add to menu items
            self.menu_items.append((food.id, food_name, price))
            
            # Clear inputs
            self.price_input.text = ''
            
            # Refresh menu list
            self.refresh_menu_list()
        
        session.close()
    
    def refresh_menu_list(self):
        """Refresh menu items list"""
        self.menu_layout.clear_widgets()
        
        # Add header
        header = BoxLayout(orientation='horizontal', size_hint=(1, None), height=30)
        header.add_widget(Label(text='Món ăn', size_hint=(0.6, 1)))
        header.add_widget(Label(text='Giá (VND)', size_hint=(0.2, 1)))
        header.add_widget(Label(text='', size_hint=(0.2, 1)))  # For remove button
        self.menu_layout.add_widget(header)
        
        # Add menu items
        for idx, (food_id, food_name, price) in enumerate(self.menu_items):
            item = BoxLayout(orientation='horizontal', size_hint=(1, None), height=30)
            
            item.add_widget(Label(text=food_name, size_hint=(0.6, 1)))
            item.add_widget(Label(text=f"{price:,.0f}", size_hint=(0.2, 1)))
            
            remove_btn = Button(text='X', size_hint=(0.2, 1))
            remove_btn.idx = idx
            remove_btn.bind(on_press=self.remove_food_from_menu)
            
            item.add_widget(remove_btn)
            
            self.menu_layout.add_widget(item)
    
    def remove_food_from_menu(self, instance):
        """Remove food item from menu"""
        idx = instance.idx
        
        if 0 <= idx < len(self.menu_items):
            del self.menu_items[idx]
            self.refresh_menu_list()
    
    def reset_form(self):
        """Reset form for new restaurant"""
        self.restaurant_id = None
        self.title_label.text = 'Thêm quán ăn mới'
        
        self.name_input.text = ''
        self.city_spinner.text = 'Chọn thành phố'
        self.ward_spinner.text = 'Chọn phường'
        self.street_spinner.text = 'Chọn đường'
        self.opening_input.text = ''
        self.closing_input.text = ''
        self.rating_input.text = '0.0'
        
        self.menu_items = []
        self.refresh_menu_list()
    
    def load_restaurant(self, restaurant_id):
        """Load restaurant data for editing"""
        self.restaurant_id = restaurant_id
        self.title_label.text = 'Chỉnh sửa quán ăn'
        
        session = self.db_manager.get_session()
        
        from database import Restaurant, Street, Ward, City, RestaurantFood, Food
        
        restaurant = session.query(Restaurant).get(restaurant_id)
        
        if restaurant:
            # Basic info
            self.name_input.text = restaurant.name
            self.opening_input.text = restaurant.opening_time or ''
            self.closing_input.text = restaurant.closing_time or ''
            self.rating_input.text = str(restaurant.rating)
            
            # Get location info
            street = session.query(Street).get(restaurant.street_id)
            
            if street:
                self.street_spinner.text = street.name
                
                ward = session.query(Ward).get(street.ward_id)
                if ward:
                    self.ward_spinner.text = ward.name
                    
                    city = session.query(City).get(ward.city_id)
                    if city:
                        self.city_spinner.text = city.name
                        
                        # Update spinner values
                        self.on_city_select(self.city_spinner, city.name)
                        self.on_ward_select(self.ward_spinner, ward.name)
            
            # Load menu items
            self.menu_items = []
            
            menu_items = session.query(RestaurantFood).filter_by(restaurant_id=restaurant_id).all()
            
            for item in menu_items:
                food = session.query(Food).get(item.food_id)
                if food:
                    self.menu_items.append((food.id, food.name, item.price))
            
            self.refresh_menu_list()
        
        session.close()
    
    def save_restaurant(self, instance):
        """Save restaurant data"""
        # Validate required fields
        if not self.name_input.text.strip():
            self.show_error('Vui lòng nhập tên quán ăn')
            return
            
        if self.street_spinner.text == 'Chọn đường':
            self.show_error('Vui lòng chọn đường')
            return
            
        # Get street_id
        session = self.db_manager.get_session()
        
        from database import Street, Restaurant, RestaurantFood
        import time
        
        street = session.query(Street).filter_by(name=self.street_spinner.text).first()
        
        if not street:
            session.close()
            self.show_error('Đường không tồn tại')
            return
            
        # Parse rating
        try:
            rating = float(self.rating_input.text)
            if rating < 0 or rating > 5:
                session.close()
                self.show_error('Đánh giá phải từ 0 đến 5')
                return
        except ValueError:
            session.close()
            self.show_error('Đánh giá không hợp lệ')
            return
            
        # Create or update restaurant
        if self.restaurant_id:  # Edit existing
            restaurant = session.query(Restaurant).get(self.restaurant_id)
            
            if restaurant:
                restaurant.name = self.name_input.text.strip()
                restaurant.street_id = street.id
                restaurant.opening_time = self.opening_input.text.strip()
                restaurant.closing_time = self.closing_input.text.strip()
                restaurant.rating = rating
                restaurant.last_modified = int(time.time())
                
                # Delete existing menu items
                session.query(RestaurantFood).filter_by(restaurant_id=self.restaurant_id).delete()
        else:  # Create new
            restaurant = Restaurant(
                name=self.name_input.text.strip(),
                street_id=street.id,
                opening_time=self.opening_input.text.strip(),
                closing_time=self.closing_input.text.strip(),
                rating=rating,
                is_deleted=False,
                last_modified=int(time.time())
            )
            session.add(restaurant)
            session.flush()  # Get ID
            
        # Add menu items
        for food_id, _, price in self.menu_items:
            menu_item = RestaurantFood(
                restaurant_id=restaurant.id,
                food_id=food_id,
                price=price
            )
            session.add(menu_item)
        
        session.commit()
        session.close()
        
        # Go back to admin screen
        self.go_back(instance)
    
    def show_error(self, message):
        """Show error popup"""
        popup = Popup(title='Lỗi',
                     content=Label(text=message),
                     size_hint=(0.8, 0.3))
        popup.open()
    
    def go_back(self, instance):
        """Go back to admin screen"""
        self.manager.transition.direction = 'right'
        self.manager.current = 'admin'

class FoodApp(App):
    def build(self):
        # Initialize managers
        self.db_manager = DBManager()
        self.auth_manager = AuthManager()
        self.sync_manager = SyncManager(self.db_manager)
        
        # Create screen manager
        sm = ScreenManager()
        
        # Add screens
        login_screen = LoginScreen(name='login', auth_manager=self.auth_manager)
        main_screen = MainScreen(name='main', db_manager=self.db_manager, 
                                auth_manager=self.auth_manager, 
                                sync_manager=self.sync_manager)
        admin_screen = AdminScreen(name='admin', db_manager=self.db_manager,
                                  auth_manager=self.auth_manager,
                                  sync_manager=self.sync_manager)
        restaurant_screen = RestaurantScreen(name='restaurant', 
                                           db_manager=self.db_manager,
                                           auth_manager=self.auth_manager)
        add_restaurant_screen = AddRestaurantScreen(name='add_restaurant',
                                                  db_manager=self.db_manager)
        
        sm.add_widget(login_screen)
        sm.add_widget(main_screen)
        sm.add_widget(admin_screen)
        sm.add_widget(restaurant_screen)
        sm.add_widget(add_restaurant_screen)
        
        return sm

if __name__ == '__main__':
    FoodApp().run()