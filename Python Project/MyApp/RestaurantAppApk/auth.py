class AuthManager:
    def __init__(self):
        self.admin_username = "bao"
        self.admin_password = "bao1991"
        self.is_admin = False
    
    def login(self, username, password):
        if username == self.admin_username and password == self.admin_password:
            self.is_admin = True
            return True
        return False
    
    def logout(self):
        self.is_admin = False
    
    def check_admin(self):
        return self.is_admin