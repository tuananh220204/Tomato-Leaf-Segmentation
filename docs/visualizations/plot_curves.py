import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Cấu hình giao diện biểu đồ chuẩn bài báo khoa học (Publication-ready)
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'legend.fontsize': 10,
    'figure.dpi': 250
})

def plot_combined_training_curves():
    # Lấy đường dẫn thư mục hiện tại (docs/visualizations)
    current_dir = Path(__file__).parent
    
    # Khai báo mapping tên mô hình với đúng tên file JSON
    model_files = {
        'U-Net': current_dir / 'unet_training_history.json',
        'SegNet': current_dir / 'segnet_training_history.json',
        'U-Net++': current_dir / 'unetpp_training_history.json'
    }
    
    # Mở rộng thành 3 cột subplot: [Loss, IoU, Dice]
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    
    # Bảng màu định danh cho từng mô hình
    colors = {
        'U-Net': '#2ecc71',    # Xanh lá
        'SegNet': '#3498db',   # Xanh dương
        'U-Net++': '#e74c3c'   # Đỏ cam
    }
    
    has_data = False

    for model_name, file_path in model_files.items():
        if not file_path.exists():
            print(f"[CẢNH BÁO] Không tìm thấy file: {file_path.name}")
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            has_data = True
            
            # Tự động tìm số epochs
            epochs = data.get('epoch', range(1, len(data.get('val_loss', data.get('loss', [0]))) + 1))
            
            # 1. Các key cho Loss
            loss_key = 'val_loss' if 'val_loss' in data else ('loss' if 'loss' in data else None)
            
            # 2. Các key cho IoU
            iou_key = next((k for k in ['val_iou', 'iou'] if k in data), None)
            
            # 3. Các key cho Dice (hoặc F1-score tương đương)
            dice_key = next((k for k in ['val_dice', 'dice', 'val_f1', 'f1'] if k in data), None)
            
            # Vẽ đường Loss (Subplot 0)
            if loss_key and loss_key in data:
                axes[0].plot(
                    epochs, data[loss_key], 
                    linestyle='-', linewidth=2, 
                    label=model_name, 
                    color=colors.get(model_name, '#333333')
                )
                
            # Vẽ đường IoU (Subplot 1)
            if iou_key and iou_key in data:
                axes[1].plot(
                    epochs, data[iou_key], 
                    linestyle='-', linewidth=2, 
                    label=model_name, 
                    color=colors.get(model_name, '#333333')
                )
            
            # Vẽ đường Dice (Subplot 2)
            if dice_key and dice_key in data:
                axes[2].plot(
                    epochs, data[dice_key], 
                    linestyle='-', linewidth=2, 
                    label=model_name, 
                    color=colors.get(model_name, '#333333')
                )
            else:
                print(f"[THÔNG BÁO] Model {model_name} không tìm thấy key Dice trong file JSON.")
                
        except Exception as e:
            print(f"[LỖI] Khi đọc file {file_path.name}: {e}")

    if not has_data:
        print("[LỖI KHÔNG THỂ VẼ] Không đọc được dữ liệu từ bất kỳ file JSON nào.")
        return

    # Cấu hình Subplot 0: Loss Curve
    axes[0].set_title('So sánh Loss qua các Epochs', fontweight='bold')
    axes[0].set_xlabel('Epochs')
    axes[0].set_ylabel('Loss Value')
    axes[0].legend(frameon=True, facecolor='white', framealpha=0.9)
    axes[0].grid(True, linestyle='--', alpha=0.5)

    # Cấu hình Subplot 1: IoU Curve
    axes[1].set_title('So sánh IoU qua các Epochs', fontweight='bold')
    axes[1].set_xlabel('Epochs')
    axes[1].set_ylabel('IoU Score')
    axes[1].legend(frameon=True, facecolor='white', framealpha=0.9)
    axes[1].grid(True, linestyle='--', alpha=0.5)

    # Cấu hình Subplot 2: Dice Curve
    axes[2].set_title('So sánh Dice qua các Epochs', fontweight='bold')
    axes[2].set_xlabel('Epochs')
    axes[2].set_ylabel('Dice Score')
    axes[2].legend(frameon=True, facecolor='white', framealpha=0.9)
    axes[2].grid(True, linestyle='--', alpha=0.5)

    # Xuất ảnh gộp 3 biểu đồ
    plt.tight_layout()
    output_path = current_dir / 'training_comparison_curves.png'
    plt.savefig(output_path, dpi=250, bbox_inches='tight')
    print(f"[THÀNH CÔNG] Đã lưu biểu đồ gộp (Loss, IoU, Dice) tại: {output_path}")
    plt.show()

if __name__ == '__main__':
    plot_combined_training_curves()