def initialize_data(period):
    """Khởi tạo dữ liệu chỉ từ data_{period}.csv"""
    global data_df, original_df, filters
    filters = {}

    status_file = f"Data Test/data_{period.lower()}.csv"
    display_columns = [
        "SS", "Mã hàng", "MSKH", "Tên khách hàng", "Đối tượng gửi dữ liệu",
        "Yêu cầu đặc biệt khi gửi dữ liệu", "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'",
        "Nơi nhận dữ liệu", "Nội dung gửi mail", "Địa chỉ gửi mail", "DUNG LƯỢNG 1 LẦN GỬI", "Status"
    ]

    if not os.path.exists("Data Test"):
        os.makedirs("Data Test")
        print("Đã tạo thư mục Data Test")

    data_df = pd.DataFrame(columns=display_columns) # Khởi tạo DataFrame rỗng mặc định
    original_df = data_df.copy() # original_df cũng rỗng ban đầu

    # Chỉ cố gắng đọc từ status file
    if os.path.exists(status_file):
        encodings = ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1', 'utf-16']
        loaded_df = None
        for encoding in encodings:
            try:
                # Thử đọc file
                temp_loaded_df = pd.read_csv(status_file, encoding=encoding)
                print(f"Đã thử đọc {status_file} với encoding {encoding}")
                # Kiểm tra nếu đọc thành công và có ít nhất một cột
                if temp_loaded_df is not None and not temp_loaded_df.columns.empty:
                     loaded_df = temp_loaded_df
                     break # Đọc thành công với encoding này
                elif temp_loaded_df is not None and temp_loaded_df.empty:
                     loaded_df = temp_loaded_df # Đọc thành công nhưng file rỗng
                     print(f"File {status_file} rỗng nhưng đọc thành công với encoding {encoding}")
                     break
                else:
                    print(f"Đọc {status_file} với encoding {encoding} không trả về DataFrame hợp lệ")

            except Exception as e:
                print(f"Lỗi với encoding {encoding} khi đọc {status_file}: {e}")
                loaded_df = None # Reset loaded_df nếu có lỗi đọc với encoding này
                continue # Thử encoding tiếp theo

        if loaded_df is not None:
            if loaded_df.empty:
                 messagebox.showinfo("Thông báo", f"File {status_file} trống.")
                 data_df = pd.DataFrame(columns=display_columns) # Set về DataFrame rỗng với các cột đúng
            else:
                 # Đảm bảo tất cả các cột trong display_columns đều tồn tại trong loaded_df
                 # Thêm cột thiếu nếu cần và sắp xếp lại cột
                 for col in display_columns:
                     if col not in loaded_df.columns:
                         loaded_df[col] = "" # Thêm cột thiếu với giá trị rỗng

                 data_df = loaded_df.reindex(columns=display_columns, fill_value="")
                 original_df = data_df.copy()
                 print(f"Đã đọc dữ liệu từ {status_file} và cập nhật data_df")

        else: # Failed to read status file with any encoding
             messagebox.showerror("Lỗi", f"Không thể đọc file {status_file} với bất kỳ encoding nào.")
             data_df = pd.DataFrame(columns=display_columns) # Set về DataFrame rỗng với các cột đúng
             original_df = data_df.copy()


    else: # Status file does not exist
        messagebox.showinfo("Thông báo", f"Không tìm thấy file {status_file}. Tạo mới file rỗng.")
        data_df = pd.DataFrame(columns=display_columns) # Dataframe rỗng với cột
        original_df = data_df.copy()
        print(f"Không tìm thấy {status_file}, data_df được set rỗng.")
        # Tạo file rỗng ngay để lần sau có file
        try:
            data_df.to_csv(status_file, index=False, encoding='utf-8-sig')
            print(f"Đã tạo file {status_file} rỗng.")
        except Exception as e:
            print(f"Lỗi khi tạo file {status_file}: {e}")
            messagebox.showwarning("Cảnh báo", f"Không thể tạo file {status_file}.")


    # Cập nhật Treeview với data_df hiện tại (có thể là rỗng hoặc có dữ liệu)
    # Import update_table ngay trước khi dùng để tránh circular dependency nếu có
    # Việc gọi update_table sẽ được lên lịch trong gui.py sau khi initialize_data kết thúc.
    # Giữ lại lệnh gọi update_table ở đây chỉ để đảm bảo data_df được set và prints log,
    # nhưng việc hiển thị lên GUI sẽ do lệnh after trong gui.py đảm nhiệm.
    try:
        from .gui import update_table
        # print("Calling update_table from initialize_data...") # Debug print
        # update_table(data_df) # Bỏ gọi update_table trực tiếp ở đây để tránh xung đột timing với lệnh after trong gui.py
        pass # initialize_data chỉ cần đảm bảo data_df và original_df được set.
    except ImportError:
        print("Lỗi: Không thể import update_table từ .gui trong initialize_data")
    except Exception as e:
        print(f"Lỗi không mong muốn trong initialize_data sau khi đọc file: {e}")