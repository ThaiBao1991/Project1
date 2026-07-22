import os

def generate_fitness_roadmap():
    filepath = r"c:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\AskCpl\roadmap_fitness_365days.md"
    
    cycle_names = [
        "Thân dưới (Low-impact, Bảo vệ gối)",
        "Thân trên (Chai nước/Dây kháng lực)",
        "Phục hồi (Yoga/Giãn cơ thảm)",
        "Toàn thân (Phối hợp tay chân)",
        "Cardio tại nhà (Shadow boxing/Bước ngang)",
        "Core & Bụng (Bảo vệ cột sống)",
        "Nghỉ ngơi hoàn toàn"
    ]
    
    meals = [
        "Sáng: 2 quả trứng luộc (140g) + 1 lát bánh mì đen (30g). Trưa: 1 lưng chén cơm trắng/gạo lứt (100g) + 150g Ức gà áp chảo (dùng xịt dầu) + 200g Canh rau luộc. Tối: 150g Cá hấp + 200g Rau luộc.",
        "Sáng: 40g Yến mạch nấu 150ml sữa không đường + 1 quả chuối (100g). Trưa: 1 lưng chén cơm (100g) + 150g Thịt bò xào (dùng ít dầu) + 200g Rau củ. Tối: 150g Đậu hũ sốt cà + 200g Rau xào nhạt.",
        "Sáng: Bún/phở gạo lứt (50g bánh phở khô) + 100g thịt bò nạc + nhiều rau. Trưa: 1 lưng chén cơm (100g) + 150g Tôm kho nhạt + 200g Rau luộc. Tối: Salad rau xà lách (200g) + 100g ức gà xé + 1 quả trứng luộc.",
        "Sáng: 2 quả trứng ốp la (ít dầu) + 1 lát bánh mì đen (30g) + dưa leo. Trưa: 1 lưng chén cơm (100g) + 150g Thịt heo nạc luộc + 200g Canh rau. Tối: Cháo yến mạch (40g) + 100g Thịt bằm nạc + Rau thơm.",
        "Sáng: 1 hộp sữa chua không đường (100g) + 30g granola ít đường. Trưa: 1 lưng chén cơm (100g) + 150g Cá lóc kho nhạt + 200g Rau luộc. Tối: 150g Ức gà áp chảo + 200g Rau củ hấp.",
        "Sáng: Bánh mì ốp la 1 trứng (ít dầu) + dưa leo/cà chua. Trưa: Bún/miến gạo lứt (50g khô) + 150g thịt nạc heo + Rau giá nhiều. Tối: Canh rau củ (200g) + 150g Đậu hũ trắng luộc.",
        "Ngày Chủ Nhật: Linh hoạt. Ưu tiên ăn ~150g - 200g đạm nạc mỗi bữa chính và 200g rau. Chỉ ăn 1 lưng chén cơm. Hạn chế tuyệt đối nước ngọt, bia rượu, đồ chiên ngập dầu."
    ]
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# 🏠 Lộ Trình Giảm Cân & Tăng Cơ Tại Nhà 1 Năm (365 Ngày) - Phiên bản Chi tiết\n\n")
        f.write("> **Mục tiêu**: Giảm mỡ an toàn, bảo vệ khớp (đặc biệt cho người 108kg). Lộ trình ghi chú rõ form tập và định lượng thức ăn theo Gram/Chén. Sau 6 tháng đầu sẽ chuyển sang xây cơ.\n\n")
        
        for d in range(1, 366):
            phase = (d - 1) // 90 + 1
            if phase == 1:
                duration = "15 - 20 phút"
                phase_name = "Phase 1: Giảm mỡ Low-impact & Tạo thói quen (Tháng 1-3)"
                reps = "3 hiệp x 10 lần"
                rest = "Nghỉ 60 giây"
            elif phase == 2:
                duration = "20 - 25 phút"
                phase_name = "Phase 2: Tăng sức bền & Săn chắc (Tháng 4-6)"
                reps = "3 hiệp x 15 lần"
                rest = "Nghỉ 45 giây"
            elif phase == 3:
                duration = "25 - 30 phút"
                phase_name = "Phase 3: Xây dựng cơ bắp tại nhà (Tháng 7-9)"
                reps = "4 hiệp x 12 lần"
                rest = "Nghỉ 40 giây"
            else:
                duration = "30 phút"
                phase_name = "Phase 4: Đốt mỡ tối đa & Định hình body (Tháng 10-12)"
                reps = "4 hiệp x 15 lần"
                rest = "Nghỉ 30 giây"
                
            cycle_idx = (d - 1) % 7
            day_type = cycle_names[cycle_idx]
            meal_plan = meals[cycle_idx]
            
            # Exercises
            if cycle_idx == 0:
                exercises = f"- Wall Squat (Tựa sát lưng vào tường, hạ mông sao cho đùi song song mặt đất, đầu gối không vượt quá mũi chân): {reps} ({rest})\n- Glute Bridge (Nằm ngửa gập gối, siết mông đẩy hông lên cao giữ 1 giây): {reps} ({rest})\n- Sit-to-stand (Ngồi trên ghế, gồng bụng đứng thẳng dậy rồi từ từ ngồi xuống nhẹ nhàng): {reps} ({rest})"
            elif cycle_idx == 1:
                exercises = f"- Incline Push-up (Hít đất tựa tay lên thành bàn/giường cứng, thân người thẳng tắp): {reps} ({rest})\n- Lateral Raise (Cầm 2 chai nước 1.5L, hơi gập khuỷu tay và nâng ngang vai): {reps} ({rest})\n- Seated Row (Ngồi duỗi chân, móc dây kháng lực vào bàn chân, kéo dây ép chặt bả vai ra sau): {reps} ({rest})"
            elif cycle_idx == 2:
                exercises = f"- Child's Pose (Quỳ gối, mông chạm gót chân, vươn dài tay về trước trán chạm thảm): Giữ 45s x 3 lần\n- Cat-Cow (Chống 4 chi, võng lưng hít sâu - cuộn cong lưng thở ra): 15 lần x 3 hiệp\n- Giãn đùi trước (Nằm nghiêng kéo gót chân chạm mông): Giữ 45s mỗi bên"
            elif cycle_idx == 3:
                exercises = f"- Side step (Bước ngang sải chân rộng, khuỵu gối nhẹ, đánh tay nhịp nhàng): {reps} ({rest})\n- Slow High Knees (Đứng thẳng, nâng từng gối lên vuông góc thật chậm rãi, gồng bụng): {reps} ({rest})\n- Wall Squat + Overhead Press (Tựa tường squat, tay cầm chai nước đẩy thẳng lên trời): {reps} ({rest})"
            elif cycle_idx == 4:
                exercises = f"- Shadow Boxing (Ngồi hoặc đứng thẳng, đấm thẳng 2 tay liên tục về phía trước): 3 hiệp x 3 phút ({rest})\n- V-step (Bước 2 chân tiến lên chéo hình chữ V, rồi lùi lại): 3 hiệp x 25 bước ({rest})\n- Calf Raise (Đứng bám tay vào ghế, kiễng gót chân lên cao rồi hạ chậm): {reps} ({rest})"
            elif cycle_idx == 5:
                exercises = f"- Plank gối chạm sàn (Chống khuỷu tay, đầu gối chạm đất, lưng và mông tạo đường thẳng): Giữ 30s-45s x 3 hiệp ({rest})\n- Deadbug (Nằm ngửa, tay chân giơ lên trời. Duỗi thẳng tay phải & chân trái không chạm đất, đổi bên): {reps} ({rest})\n- Gập bụng Crunch (Nằm ngửa co gối, chỉ nâng phần vai lên khỏi thảm, không kéo cổ): {reps} ({rest})"
            elif cycle_idx == 6:
                exercises = "- Nghỉ ngơi hoàn toàn cho cơ bắp phục hồi.\n- Hoạt động nhẹ nhàng: Đi dạo loanh quanh trong nhà 10-15 phút để thư giãn gân cốt.\n- Đi chợ, chuẩn bị chia hộp thực phẩm cho tuần mới."
                
            prompt = f"Đóng vai trò là PT cá nhân và Chuyên gia Dinh dưỡng. Hôm nay là Day {d} thuộc {phase_name}.\nLịch tập hôm nay ({duration}):\n{exercises}\n\nThực đơn hôm nay:\n{meal_plan}\n\nYêu cầu:\n1. Trình bày lại lịch tập và thực đơn trên một cách đẹp mắt, rõ ràng để tôi theo dõi tập luyện trong ngày.\n2. Với lịch tập trên, hãy phân tích nguy cơ sai tư thế của từng động tác cụ thể và đưa ra mẹo bảo vệ khớp gối/cột sống cho người 108kg.\n3. Phân tích xem định lượng thực phẩm (số gram, chén) của thực đơn trên đã hợp lý cho thể trạng người 108kg đang giảm mỡ chưa? Có cần tinh chỉnh gì không?\n4. Hãy cho tôi một câu động viên thật máu lửa."
            
            f.write(f"## Day {d} — {day_type}\n")
            f.write(f"**Prompt:**\n")
            f.write(f"{prompt}\n\n")
            f.write(f"**Bài tập:**\n")
            f.write(f"💪 **LỊCH TẬP ({duration}):**\n- Khởi động: Xoay các khớp cổ tay, chân, vai, hông thật kỹ (3 phút).\n{exercises}\n- Kết thúc: Giãn cơ tĩnh thả lỏng, hít thở sâu (3 phút).\n\n")
            f.write(f"🍽️ **THỰC ĐƠN HÔM NAY:**\n- {meal_plan}\n\n")
            f.write(f"**Tags:** #fitness #homeworkout #day{d} #low_impact\n\n")
            f.write("---\n\n")

if __name__ == '__main__':
    generate_fitness_roadmap()
