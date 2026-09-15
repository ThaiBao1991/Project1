import re
import urllib.request
import urllib.parse
import json
import logging

logger = logging.getLogger(__name__)

# Bảng tra âm Hán-Việt cho các chữ Hán thường gặp trong tên truyện tiên hiệp, huyền huyễn, đô thị
HAN_VIET_COMMON = {
    '苟': 'Cẩu', '在': 'Tại', '初': 'Sơ', '圣': 'Thánh', '魔': 'Ma', '门': 'Môn', '当': 'Đương',
    '人': 'Nhân', '材': 'Tài', '宗': 'Tông', '大': 'Đại', '小': 'Tiểu', '仙': 'Tiên', '神': 'Thần',
    '帝': 'Đế', '尊': 'Tôn', '王': 'Vương', '皇': 'Hoàng', '剑': 'Kiếm', '刀': 'Đao', '天': 'Thiên',
    '地': 'Địa', '玄': 'Huyền', '黄': 'Hoàng', '道': 'Đạo', '修': 'Tu', '真': 'Chân', '界': 'Giới',
    '武': 'Vũ', '极': 'Cực', '凡': 'Phàm', '生': 'Sinh', '死': 'Tử', '无': 'Vô', '敌': 'Địch',
    '重': 'Trọng', '开': 'Khai', '百': 'Bách', '世': 'Thế', '书': 'Thư', '劫': 'Kiếp', '气': 'Khí',
    '运': 'Vận', '长': 'Trường', '空': 'Không', '逆': 'Nghịch', '天': 'Thiên', '命': 'Mệnh', '太': 'Thái',
    '古': 'Cổ', '荒': 'Hoang', '万': 'Vạn', '星': 'Tinh', '辰': 'Thần', '龙': 'Long', '凤': 'Phượng',
    '妖': 'Yêu', '鬼': 'Quỷ', '灵': 'Linh', '丹': 'Đan', '符': 'Phù', '阵': 'Trận', '器': 'Khí',
    '傲': 'Ngạo', '世': 'Thế', '霸': 'Bá', '绝': 'Tuyệt', '顶': 'Đỉnh', '狂': 'Cuồng', '邪': 'Tà',
    '九': 'Cửu', '霄': 'Tiêu', '云': 'Vân', '雷': 'Lôi', '风': 'Phong', '火': 'Hỏa', '水': 'Thủy',
    '一': 'Nhất', '二': 'Nhị', '三': 'Tam', '四': 'Tứ', '五': 'Ngũ', '六': 'Lục', '七': 'Thất',
    '八': 'Bát', '十': 'Thập', '之': 'Chi', '从': 'Tòng', '开': 'Khai', '始': 'Thủy', '了': 'Liễu',
    '成': 'Thành', '我': 'Ngã', '你': 'Nhĩ', '他': 'Tha', '她': 'Tha', '是': 'Thị', '有': 'Hữu',
    '无': 'Vô', '不': 'Bất', '得': 'Đắc', '以': 'Dĩ', '为': 'Vi', '子': 'Tử', '主': 'Chủ',
    '阁': 'Các', '府': 'Phủ', '院': 'Viện', '山': 'Sơn', '海': 'Hải', '江': 'Giang', '河': 'Hà',
    '湖': 'Hồ', '林': 'Lâm', '森': 'Sâm', '城': 'Thành', '国': 'Quốc', '朝': 'Triều', '代': 'Đại',
    '传': 'Truyện', '记': 'Ký', '录': 'Lục', '志': 'Chí', '经': 'Kinh', '法': 'Pháp', '功': 'Công',
    '术': 'Thuật', '决': 'Quyết', '诀': 'Quyết', '篇': 'Phần', '章': 'Chương', '卷': 'Quyển',
    '师': 'Sư', '徒': 'Đồ', '兄': 'Huynh', '弟': 'Đệ', '姐': 'Tỷ', '妹': 'Muội', '君': 'Quân',
    '侯': 'Hầu', '将': 'Tướng', '相': 'Tướng', '兵': 'Binh', '战': 'Chiến', '斗': 'Đấu',
    '破': 'Phá', '立': 'Lập', '封': 'Phong', '锁': 'Tỏa', '镇': 'Trấn', '压': 'Áp', '戮': 'Lục',
    '诛': 'Chu', '灭': 'Diệt', '斩': 'Trảm', '杀': 'Sát', '戮': 'Lục', '噬': 'Phệ', '吞': 'Thôn',
    '炼': 'Luyện', '化': 'Hóa', '变': 'Biến', '转': 'Chuyển', '轮': 'Luân', '回': 'Hồi',
    '阴': 'Âm', '阳': 'Dương', '乾': 'Càn', '坤': 'Khôn', '日': 'Nhật', '月': 'Nguyệt',
    '深': 'Thâm', '渊': 'Uyên', '秘': 'Bí', '境': 'Cảnh', '宝': 'Bảo', '藏': 'Tàng', '殿': 'Điện',
    '堂': 'Đường', '洞': 'Động', '窟': 'Quật', '谷': 'Cốc', '崖': 'Nhai', '岭': 'Lĩnh', '峰': 'Phong',
    '巅峰': 'Đỉnh Phong', '无上': 'Vô Thượng', '至尊': 'Chí Tôn', '主宰': 'Chủ Tể', '逍遥': 'Tiêu Dao',
}

def han_viet_transliterate(text: str) -> str:
    """Chuyển đổi từng ký tự chữ Hán sang âm Hán-Việt."""
    result = []
    for ch in text:
        if ch in HAN_VIET_COMMON:
            result.append(HAN_VIET_COMMON[ch])
        elif '\u4e00' <= ch <= '\u9fff':
            # Chữ Hán chưa có trong từ điển rút gọn
            result.append(ch)
        else:
            result.append(ch)
    return " ".join(result)

def translate_online(text: str) -> str:
    """Dịch nhanh qua Google Translate API client=dict-chrome-ex."""
    try:
        q = urllib.parse.quote(text)
        url = f"https://translate.googleapis.com/translate_a/single?client=dict-chrome-ex&sl=zh-CN&tl=vi&dt=t&q={q}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data and data[0]:
                trans = "".join([part[0] for part in data[0] if part and part[0]])
                return trans.strip()
    except Exception as e:
        logger.debug(f"Online translate error: {e}")
    return ""

def translate_chinese_novel_title(title: str) -> str:
    """
    Dịch tên truyện tiếng Trung sang tên tiếng Việt:
    Ưu tiên dịch âm Hán-Việt (chuẩn truyện tiên hiệp/huyền huyễn),
    Nếu còn ký tự chữ Hán thì kết hợp với bản dịch online.
    """
    title = title.strip()
    if not title:
        return ""

    # 1. Thử âm Hán-Việt trước
    hv = han_viet_transliterate(title)
    has_untranslated_hanzi = any('\u4e00' <= ch <= '\u9fff' for ch in hv)
    
    if not has_untranslated_hanzi:
        # Tất cả chữ Hán đều được dịch âm Hán-Việt hoàn hảo
        words = [w.capitalize() for w in hv.split() if w]
        return " ".join(words)

    # 2. Nếu còn sót chữ Hán, thử gọi Google Translate
    online = translate_online(title)
    if online:
        # Viết hoa chữ cái đầu mỗi từ
        words = [w.capitalize() for w in online.split() if w]
        return " ".join(words)

    # 3. Fallback: dùng âm Hán-Việt tốt nhất có thể
    words = [w.capitalize() for w in hv.split() if w]
    return " ".join(words)
