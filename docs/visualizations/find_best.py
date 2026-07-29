import json
from pathlib import Path

def find_best_metrics(json_filename):
    file_path = Path(json_filename)
    if not file_path.exists():
        print(f"[Bỏ qua] Không tìm thấy file: {json_filename}")
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    epochs = data.get('epoch', None)
    
    print(f"📁 Tệp: {json_filename}")
    
    # Tự động quét tất cả các key lưu mảng dữ liệu số trong file JSON
    for key, values in data.items():
        if key == 'epoch':
            continue
            
        if isinstance(values, list) and len(values) > 0 and isinstance(values[0], (int, float)):
            current_epochs = epochs[:len(values)] if epochs and len(epochs) >= len(values) else list(range(1, len(values) + 1))
            
            # Nếu tên key chứa chữ 'loss' thì tìm giá trị nhỏ nhất (Min), ngược lại tìm giá trị lớn nhất (Max)
            is_loss = 'loss' in key.lower()
            
            if is_loss:
                best_val = min(values)
                best_idx = values.index(best_val)
                best_epoch = current_epochs[best_idx]
                print(f"   📉 Best {key} (Min): {best_val:.4f} (tại Epoch {best_epoch})")
            else:
                best_val = max(values)
                best_idx = values.index(best_val)
                best_epoch = current_epochs[best_idx]
                print(f"   📈 Best {key} (Max): {best_val:.4f} (tại Epoch {best_epoch})")
                
    print("-" * 40)

if __name__ == '__main__':
    # Quét toàn bộ các file history trong thư mục
    history_files = [
        'unet_training_history.json',
        'segnet_training_history.json',
        'unetpp_training_history.json'
    ]
    
    for file_name in history_files:
        find_best_metrics(file_name)