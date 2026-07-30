import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Cấu hình giao diện đẹp, chuẩn báo cáo khoa học
sns.set_theme(style="whitegrid")
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.labelsize': 13,
    'axes.titlesize': 14,
    'figure.dpi': 150
})

# Gán trực tiếp số liệu (U-Net lấy chuẩn từ file tổng kết[cite: 1]; SegNet và U-Net++ bạn chỉ cần sửa số liệu tại đây)
models = ['U-Net', 'SegNet', 'U-Net++']

metrics_data = {
    'IoU Score': [0.4320, 0.3852, 0.3965],       # U-Net[cite: 1] | SegNet | U-Net++
    'Dice Coefficient': [0.5161, 0.4663, 0.4842]  # U-Net[cite: 1] | SegNet | U-Net++
}

x = np.arange(len(models))
width = 0.35  

fig, ax = plt.subplots(figsize=(8, 5))
colors = ['#1abc9c', '#3498db'] # Màu sắc hiện đại, tương phản tốt

multiplier = 0
for metric_name, values in metrics_data.items():
    offset = width * multiplier
    rects = ax.bar(x + offset, values, width, label=metric_name, color=colors[multiplier])
    ax.bar_label(rects, padding=3, fmt='%.4f', fontsize=9, fontweight='bold')
    multiplier += 1

# Tùy chỉnh trực quan biểu đồ
ax.set_title('So sánh hiệu năng IoU và Dice giữa các mô hình phân vùng', fontweight='bold', pad=15)
ax.set_xlabel('Kiến trúc mô hình', labelpad=8)
ax.set_ylabel('Giá trị điểm số (Score)', labelpad=8)
ax.set_xticks(x + width / 2)
ax.set_xticklabels(models, fontweight='bold')
ax.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.9)
ax.set_ylim(0, 0.7) # Thang đo tối ưu riêng cho dải điểm số IoU & Dice

plt.tight_layout()
output_path = 'metrics_iou_dice_bar.png'
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"[THÀNH CÔNG] Đã tạo biểu đồ cột nhóm tại: {output_path}")
plt.show()