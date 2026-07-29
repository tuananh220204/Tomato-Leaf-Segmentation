import sqlite3

# Kết nối đến cơ sở dữ liệu SQLite
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# ID bản ghi bạn muốn sửa
target_id = 48

# 1. Chạy lệnh SELECT để kiểm tra thông tin bản ghi trước khi sửa
cursor.execute("SELECT id, filename, record_keccak FROM records WHERE id = ?", (target_id,))
print(">>> Dữ liệu TRƯỚC khi sửa:", cursor.fetchone())

# 2. Chạy lệnh UPDATE để sửa mã băm cho riêng bản ghi có ID này
cursor.execute("UPDATE records SET record_keccak = '0xdeadbeef' WHERE id = ?", (target_id,))
cursor.execute("UPDATE records SET record_sha256 = 'deadbeef' WHERE id = ?", (target_id,))

conn.commit()

# 3. Kiểm tra lại sau khi đã UPDATE
cursor.execute("SELECT id, filename, record_keccak, record_sha256 FROM records WHERE id = ?", (target_id,))
print(">>> Dữ liệu SAU khi sửa:", cursor.fetchone())

conn.close()