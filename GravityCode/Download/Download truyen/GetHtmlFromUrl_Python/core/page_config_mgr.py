import json
import logging
from typing import List, Dict, Optional
from models.page_config import PageConfig, OverMaxSizePageCountState

logger = logging.getLogger(__name__)

class PageConfigManager:
    """Quản lý các cấu hình trang từ ghfuConfig.json"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.page_configs: List[PageConfig] = []
        self.load_config()

    def _camel_to_snake(self, name: str) -> str:
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _snake_to_camel(self, name: str) -> str:
        components = name.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])

    def load_config(self) -> None:
        """Đọc file JSON và parse thành list of PageConfig"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.page_configs.clear()
            for item in data:
                pc = PageConfig()
                for key, value in item.items():
                    snake_key = self._camel_to_snake(key)
                    if snake_key == "over_max_size_page_count_state":
                        if hasattr(OverMaxSizePageCountState, value):
                            setattr(pc, snake_key, getattr(OverMaxSizePageCountState, value))
                        continue
                    
                    if hasattr(pc, snake_key):
                        setattr(pc, snake_key, value)
                self.page_configs.append(pc)
            logger.info(f"Đã nạp {len(self.page_configs)} cấu hình trang từ {self.config_path}")
        except Exception as e:
            logger.error(f"Lỗi đọc config: {e}")

    def get_config_by_url(self, url: str) -> Optional[PageConfig]:
        """Tìm cấu hình phù hợp với URL"""
        dummy = PageConfig(page_code=url)
        for pc in self.page_configs:
            if pc == dummy:
                return pc
        return None

    def get_all_configs(self) -> List[PageConfig]:
        return self.page_configs

    def save_config(self) -> bool:
        """Lưu danh sách hiện tại vào file JSON"""
        try:
            output_data = []
            for pc in self.page_configs:
                item_dict = {}
                # Bỏ qua các field nội bộ bắt đầu bằng _
                for k, v in pc.__dict__.items():
                    if k.startswith('_'):
                        continue
                        
                    camel_key = self._snake_to_camel(k)
                    
                    if camel_key == "overMaxSizePageCountState":
                        # Convert Enum to string
                        item_dict[camel_key] = getattr(v, "name", "CONTINUE")
                        continue
                        
                    item_dict[camel_key] = v
                output_data.append(item_dict)
                
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Đã ghi {len(self.page_configs)} cấu hình vào {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Lỗi ghi config: {e}")
            return False
