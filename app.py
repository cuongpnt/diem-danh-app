import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import os

# Kết nối database SQLite
conn = sqlite3.connect('diem_danh.db')
c = conn.cursor()

# Tạo bảng nếu chưa tồn tại
c.execute('''CREATE TABLE IF NOT EXISTS lop_hoc 
             (lop TEXT PRIMARY KEY)''')
c.execute('''CREATE TABLE IF NOT EXISTS hoc_sinh 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, ho TEXT, ten TEXT, lop_chinh_thuc TEXT, ghi_chu TEXT, lop_diem_danh TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS diem_danh 
             (hoc_sinh_id INTEGER, ngay TEXT, buoi TEXT, trang_thai TEXT)''')
conn.commit()

# Danh sách lớp cố định
lop_chinh_thuc = ['6', '7', '8', '9', '10A', '11B1', '11B2', '12C1', '12C2', '12C3']
lop_noi_tru = ['Nội trú Nam 1', 'Nội trú Nam 2', 'Nội trú Nữ']
lop_ban_tru = ['Bán trú Nam', 'Bán trú Nữ']
tat_ca_lop = lop_chinh_thuc + lop_noi_tru + lop_ban_tru

# Thêm lớp vào DB nếu chưa có
for lop in tat_ca_lop:
    c.execute("INSERT OR IGNORE INTO lop_hoc (lop) VALUES (?)", (lop,))
conn.commit()

# Hàm xác định loại lớp
def get_loai_lop(lop):
    if lop in lop_chinh_thuc:
        return 'chinh_thuc'
    elif lop in lop_noi_tru:
        return 'noi_tru'
    elif lop in lop_ban_tru:
        return 'ban_tru'
    return None

# Hàm lấy 3 ngày: hôm nay và 2 ngày trước
def get_3_ngay_truoc():
    today = datetime.now()
    days = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(2, -1, -1)]
    return days

# Hàm tính số tuần theo ISO và danh sách tuần
def get_tuan_options():
    today = datetime.now()
    tuan_hien_tai = today.isocalendar()[1]
    options = []
    for offset in range(0, 11):  # 10 tuần trước + hiện tại
        tuan = tuan_hien_tai - offset
        label = f"Tuần {tuan}" + (" (hiện tại)" if offset == 0 else "")
        options.append((offset, label))
    return options

# CSS để canh giữa chữ trong selectbox và tăng kích thước
st.markdown("""
<style>
.stSelectbox > div > div > div {
    font-size: 16px !important;
    padding: 10px 20px !important;
    min-height: 60px !important;
    min-width: 100px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    white-space: nowrap !important;
    box-sizing: border-box !important;
}
.stSelectbox > div > div > div::after {
    content: none !important; /* Ẩn mũi tên dropdown */
}
.stTextInput > div > div > input {
    text-align: center !important;
    width: 100% !important;
    height: 40px !important;
    line-height: 40px !important;
    padding: 0 !important;
}
.stTextInput label, .stSelectbox label {
    display: none !important;
}
[data-testid="column"] {
    min-width: 0 !important;
}
[data-testid="column"] .stMarkdown {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
.stDataFrame {
    width: 100% !important;
}
.stDataEditor {
    width: 100% !important;
}
.stDataEditor th, .stDataEditor td {
    text-align: center !important;
    vertical-align: middle !important;
}
</style>
""", unsafe_allow_html=True)

# Sidebar menu
st.sidebar.title("Menu")
menu = st.sidebar.selectbox("Chọn tính năng", ["Import Dữ Liệu", "Sửa Danh Sách Lớp", "Điểm Danh", "Báo Cáo"], index=2)

if menu == "Import Dữ Liệu":
    st.title("Import Dữ Liệu Học Sinh")
    lop = st.selectbox("Chọn lớp để import", tat_ca_lop)
    loai_lop = get_loai_lop(lop)
    
    c.execute("SELECT COUNT(*) FROM hoc_sinh WHERE lop_diem_danh = ?", (lop,))
    count = c.fetchone()[0]
    
    if count > 0:
        st.warning("Lớp này đã có dữ liệu. Import sẽ ghi đè.")
    
    uploaded_file = st.file_uploader("Chọn file Excel", type=["xlsx"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write("Dữ liệu xem trước (5 dòng đầu):")
        st.dataframe(df.head(5))
        
        if st.button("Import"):
            c.execute("DELETE FROM hoc_sinh WHERE lop_diem_danh = ?", (lop,))
            
            if loai_lop == 'chinh_thuc':
                for _, row in df.iterrows():
                    ho = row.get('Họ', '') or row.get('Ho', '')
                    ten = row.get('Tên', '') or row.get('Ten', '')
                    c.execute("INSERT INTO hoc_sinh (ho, ten, lop_chinh_thuc, lop_diem_danh) VALUES (?, ?, ?, ?)",
                              (ho, ten, lop, lop))
            else:
                for _, row in df.iterrows():
                    ho = row.get('Họ', '') or row.get('Ho', '')
                    ten = row.get('Tên', '') or row.get('Ten', '')
                    lop_chinh = row.get('Lớp', '') or row.get('Lop', '')
                    ghi_chu = row.get('Ghi chú', '') or row.get('Ghi chu', '')
                    c.execute("INSERT INTO hoc_sinh (ho, ten, lop_chinh_thuc, ghi_chu, lop_diem_danh) VALUES (?, ?, ?, ?, ?)",
                              (ho, ten, lop_chinh, ghi_chu, lop))
            conn.commit()
            st.success("Import thành công!")

elif menu == "Sửa Danh Sách Lớp":
    st.title("Sửa Danh Sách Lớp")
    lop = st.selectbox("Chọn lớp để sửa", tat_ca_lop)
    loai_lop = get_loai_lop(lop)
    
    # Lấy danh sách học sinh hiện tại
    c.execute("SELECT id, ho, ten, lop_chinh_thuc, ghi_chu FROM hoc_sinh WHERE lop_diem_danh = ?", (lop,))
    data = c.fetchall()
    
    if data:
        # Nếu có dữ liệu, sử dụng st.data_editor để chỉnh sửa
        df = pd.DataFrame(data, columns=['ID', 'Họ', 'Tên', 'Lớp', 'Ghi chú'])
        df = df.drop(columns=['ID'])  # Ẩn cột ID
        edited_df = st.data_editor(df, num_rows="dynamic", key=f"editor_{lop}")
        
        if st.button("Lưu Thay Đổi"):
            # Đảm bảo dữ liệu được cập nhật trước khi lưu
            c.execute("DELETE FROM hoc_sinh WHERE lop_diem_danh = ?", (lop,))
            for _, row in edited_df.iterrows():
                ho = row['Họ'] if pd.notna(row['Họ']) else ''
                ten = row['Tên'] if pd.notna(row['Tên']) else ''
                lop_chinh = row['Lớp'] if loai_lop != 'chinh_thuc' and pd.notna(row['Lớp']) else lop
                ghi_chu = row['Ghi chú'] if pd.notna(row['Ghi chú']) else ''
                c.execute("INSERT INTO hoc_sinh (ho, ten, lop_chinh_thuc, ghi_chu, lop_diem_danh) VALUES (?, ?, ?, ?, ?)",
                          (ho, ten, lop_chinh, ghi_chu, lop))
            conn.commit()
            st.success("Đã lưu thay đổi thành công!")  # Hiển thị thông báo
    else:
        # Nếu chưa có dữ liệu, tạo bảng mới với st.data_editor
        df = pd.DataFrame(columns=['Họ', 'Tên', 'Lớp', 'Ghi chú'])
        edited_df = st.data_editor(df, num_rows="dynamic", key=f"editor_{lop}")
        
        if st.button("Lưu Danh Sách"):
            for _, row in edited_df.iterrows():
                ho = row['Họ'] if pd.notna(row['Họ']) else ''
                ten = row['Tên'] if pd.notna(row['Tên']) else ''
                lop_chinh = row['Lớp'] if loai_lop != 'chinh_thuc' and pd.notna(row['Lớp']) else lop
                ghi_chu = row['Ghi chú'] if pd.notna(row['Ghi chú']) else ''
                c.execute("INSERT INTO hoc_sinh (ho, ten, lop_chinh_thuc, ghi_chu, lop_diem_danh) VALUES (?, ?, ?, ?, ?)",
                          (ho, ten, lop_chinh, ghi_chu, lop))
            conn.commit()
            st.success("Đã lưu danh sách mới thành công!")  # Hiển thị thông báo

elif menu == "Điểm Danh":
    st.title("Điểm Danh")
    lop = st.selectbox("Chọn lớp", tat_ca_lop)
    loai_lop = get_loai_lop(lop)
    
    # Lấy học sinh
    c.execute("SELECT id, ho, ten, lop_chinh_thuc, ghi_chu FROM hoc_sinh WHERE lop_diem_danh = ?", (lop,))
    hoc_sinh_list = c.fetchall()
    
    if not hoc_sinh_list:
        st.warning("Lớp chưa có dữ liệu. Hãy import trước.")
    else:
        # Chọn tuần
        tuan_options = get_tuan_options()
        selected_tuan = st.selectbox("Chọn tuần", [label for _, label in tuan_options], index=0)
        tuan_offset = [offset for offset, label in tuan_options if label == selected_tuan][0]
        ngay_list = get_3_ngay_truoc()  # Chỉ 3 ngày
        today = datetime.now().strftime('%Y-%m-%d')
        
        if loai_lop == 'chinh_thuc':
            buoi_list = ['Sáng', 'Chiều']
        elif loai_lop == 'noi_tru':
            buoi_list = ['Trưa', 'Chiều']
        elif loai_lop == 'ban_tru':
            buoi_list = ['Trưa']
        
        buoi = st.selectbox("Chọn buổi", buoi_list)
        
        # Khởi tạo session state
        if 'diem_danh_data' not in st.session_state:
            st.session_state['diem_danh_data'] = {}
        if 'ghi_chu_data' not in st.session_state:
            st.session_state['ghi_chu_data'] = {}
        
        # Tải trạng thái điểm danh từ DB
        for hs_id, _, _, _, ghi_chu in hoc_sinh_list:
            st.session_state['ghi_chu_data'][hs_id] = ghi_chu or ""
            for ngay in ngay_list:
                key = f"{hs_id}_{ngay}_{buoi}"
                c.execute("SELECT trang_thai FROM diem_danh WHERE hoc_sinh_id = ? AND ngay = ? AND buoi = ?",
                          (hs_id, ngay, buoi))
                trang_thai = c.fetchone()
                trang_thai = trang_thai[0] if trang_thai else None
                
                if ngay == today and trang_thai is None:
                    trang_thai = "Có"
                    c.execute("DELETE FROM diem_danh WHERE hoc_sinh_id = ? AND ngay = ? AND buoi = ?",
                              (hs_id, ngay, buoi))
                    c.execute("INSERT INTO diem_danh (hoc_sinh_id, ngay, buoi, trang_thai) VALUES (?, ?, ?, ?)",
                              (hs_id, ngay, buoi, trang_thai))
                    conn.commit()
                st.session_state['diem_danh_data'][key] = trang_thai if trang_thai else ""
        
        # Form điểm danh
        with st.form(key="diem_danh_form"):
            st.subheader("Bảng điểm danh")
            # Tạo header cho bảng
            cols = st.columns([1, 2, 2, 2] + [2] * len(ngay_list) + [3])  # Thêm cột ghi chú
            cols[0].write("STT")
            cols[1].write("Họ")
            cols[2].write("Tên")
            cols[3].write("Lớp")
            for i, ngay in enumerate(ngay_list, 4):
                cols[i].write(datetime.strptime(ngay, '%Y-%m-%d').strftime('%d/%m'))
            cols[len(ngay_list) + 4].write("Ghi chú")
            
            # Hiển thị dòng học sinh
            for idx, (hs_id, ho, ten, lop_chinh, _) in enumerate(hoc_sinh_list, 1):
                cols = st.columns([1, 2, 2, 2] + [2] * len(ngay_list) + [3])
                cols[0].write(idx)
                cols[1].write(ho)
                cols[2].write(ten)
                cols[3].write(lop_chinh)
                
                for i, ngay in enumerate(ngay_list, 4):
                    key = f"{hs_id}_{ngay}_{buoi}"
                    default = st.session_state['diem_danh_data'].get(key, "")
                    if loai_lop == 'chinh_thuc':
                        options = ["Có", "Vắng", "Đi trễ"]
                    else:
                        options = ["Có", "Vắng"]
                    st.session_state['diem_danh_data'][key] = cols[i].selectbox(
                        " ", options,
                        index=options.index(default) if default in options else 0,
                        key=key
                    )
                
                ghi_key = f"ghi_{hs_id}"
                st.session_state['ghi_chu_data'][hs_id] = cols[len(ngay_list) + 4].text_input(" ", value=st.session_state['ghi_chu_data'][hs_id], key=ghi_key)
            
            if st.form_submit_button("Save"):
                for hs_id, _, _, _, _ in hoc_sinh_list:
                    ghi_chu = st.session_state['ghi_chu_data'][hs_id]
                    c.execute("UPDATE hoc_sinh SET ghi_chu = ? WHERE id = ?", (ghi_chu, hs_id))
                
                for key, trang_thai in st.session_state['diem_danh_data'].items():
                    hs_id, ngay, buoi = key.split('_')
                    c.execute("DELETE FROM diem_danh WHERE hoc_sinh_id = ? AND ngay = ? AND buoi = ?",
                              (hs_id, ngay, buoi))
                    c.execute("INSERT INTO diem_danh (hoc_sinh_id, ngay, buoi, trang_thai) VALUES (?, ?, ?, ?)",
                              (hs_id, ngay, buoi, trang_thai))
                conn.commit()
                st.success("Đã lưu điểm danh và ghi chú!")
                st.session_state['diem_danh_data'] = {}
        
        # Phần báo cáo trong màn hình điểm danh
        st.subheader("Báo Cáo Điểm Danh")
        ngay_bao_cao = st.date_input("Chọn ngày báo cáo", value=datetime.now())
        ngay_bao_cao_str = ngay_bao_cao.strftime('%Y-%m-%d')
        buoi_bao_cao = st.selectbox("Chọn buổi báo cáo", buoi_list)
        
        if st.button("Tạo Báo Cáo"):
            tong_so = len(hoc_sinh_list)
            co_mat = 0
            vang = []
            di_tre = []
            
            for hs_id, ho, ten, lop_chinh, _ in hoc_sinh_list:
                c.execute("SELECT trang_thai FROM diem_danh WHERE hoc_sinh_id = ? AND ngay = ? AND buoi = ?",
                          (hs_id, ngay_bao_cao_str, buoi_bao_cao))
                tt = c.fetchone()
                if tt:
                    tt = tt[0]
                    if tt == "Có":
                        co_mat += 1
                    elif tt == "Vắng":
                        vang.append(f"{ten} ({lop_chinh})")
                    elif tt == "Đi trễ":
                        di_tre.append(f"{ten} ({lop_chinh})")
            
            bao_cao = f"Điểm danh lớp {lop} ngày {ngay_bao_cao.strftime('%d/%m/%Y')}\n"
            bao_cao += f"Buổi: {buoi_bao_cao}\n"
            bao_cao += f"Sĩ số: {co_mat}/{tong_so}\n"
            if di_tre:
                bao_cao += f"Đi trễ: {', '.join(di_tre)}\n"
            if vang:
                bao_cao += f"Vắng: {', '.join(vang)}\n"
            
            st.text_area("Nội dung báo cáo", bao_cao, height=200, key="report_text")
            # Thêm nút copy bằng HTML/JavaScript với textarea ID
            st.markdown(
                f"""
                <script>
                function copyToClipboard() {{
                    var text = document.getElementById('report_text').value;
                    if (navigator.clipboard && navigator.clipboard.writeText) {{
                        navigator.clipboard.writeText(text).then(() => {{
                            alert('Đã copy báo cáo vào clipboard!');
                        }}).catch(err => {{
                            alert('Lỗi khi copy: ' + err);
                        }});
                    }} else {{
                        alert('Trình duyệt không hỗ trợ copy clipboard.');
                    }}
                }}
                </script>
                <button onclick="copyToClipboard()">Copy Báo Cáo</button>
                """,
                unsafe_allow_html=True
            )

elif menu == "Báo Cáo":
    st.title("Báo Cáo Điểm Danh")
    lop = st.selectbox("Chọn lớp", tat_ca_lop)
    ngay = st.date_input("Chọn ngày", value=datetime.now())
    ngay_str = ngay.strftime('%Y-%m-%d')
    buoi = st.selectbox("Chọn buổi", ["Sáng", "Trưa", "Chiều"])
    
    if st.button("Tạo Báo Cáo"):
        c.execute("SELECT id, ho, ten, lop_chinh_thuc FROM hoc_sinh WHERE lop_diem_danh = ?", (lop,))
        hoc_sinh_list = c.fetchall()
        tong_so = len(hoc_sinh_list)
        
        co_mat = 0
        vang = []
        di_tre = []
        
        for hs_id, ho, ten, lop_chinh in hoc_sinh_list:
            c.execute("SELECT trang_thai FROM diem_danh WHERE hoc_sinh_id = ? AND ngay = ? AND buoi = ?",
                      (hs_id, ngay_str, buoi))
            tt = c.fetchone()
            if tt:
                tt = tt[0]
                if tt == "Có":
                    co_mat += 1
                elif tt == "Vắng":
                    vang.append(f"{ten} ({lop_chinh})")
                elif tt == "Đi trễ":
                    di_tre.append(f"{ten} ({lop_chinh})")
        
        bao_cao = f"Điểm danh lớp {lop} ngày {ngay.strftime('%d/%m/%Y')}\n"
        bao_cao += f"Buổi: {buoi}\n"
        bao_cao += f"Sĩ số: {co_mat}/{tong_so}\n"
        if di_tre:
            bao_cao += f"Đi trễ: {', '.join(di_tre)}\n"
        if vang:
            bao_cao += f"Vắng: {', '.join(vang)}\n"
        
        st.text_area("Nội dung báo cáo", bao_cao, height=200, key="report_text")
        # Thêm nút copy bằng HTML/JavaScript với textarea ID
        st.markdown(
            f"""
            <script>
            function copyToClipboard() {{
                var text = document.getElementById('report_text').value;
                if (navigator.clipboard && navigator.clipboard.writeText) {{
                    navigator.clipboard.writeText(text).then(() => {{
                        alert('Đã copy báo cáo vào clipboard!');
                    }}).catch(err => {{
                        alert('Lỗi khi copy: ' + err);
                    }});
                }} else {{
                    alert('Trình duyệt không hỗ trợ copy clipboard.');
                }}
            }}
            </script>
            <button onclick="copyToClipboard()">Copy Báo Cáo</button>
            """,
            unsafe_allow_html=True
        )