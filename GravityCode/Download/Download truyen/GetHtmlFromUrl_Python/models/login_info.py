from dataclasses import dataclass

@dataclass
class LoginInfo:
    page_code: str = ""
    cookies: str = ""

    def __eq__(self, other):
        if not isinstance(other, LoginInfo):
            return False
        
        # Mô phỏng logic so sánh host pattern của Java
        p1 = self.page_code
        p2 = other.page_code
        
        if not p1 or not p2:
            return p1 == p2
            
        if "*" in p1 or "*" in p2:
            if "*" in p1 and p1.replace("*", "") not in p2:
                return False
            if "*" in p2 and p2.replace("*", "") not in p1:
                return False
            return True
            
        from utils.url_handler import normalize_host
        return normalize_host(p1) == normalize_host(p2)

    def __hash__(self):
        return hash(self.page_code)
