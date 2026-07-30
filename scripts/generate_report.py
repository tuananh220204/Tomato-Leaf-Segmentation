"""
Final Data Preparation Statistics Report
"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_FILE = PROJECT_ROOT / "data_preparation_report.json"

def generate_detailed_report():
    """Generate detailed statistics report"""
    
    # Load existing report
    with open(REPORT_FILE, 'r') as f:
        report = json.load(f)
    
    print("\n" + "="*100)
    print(" "*30 + "TOMATO DISEASE SEGMENTATION PROJECT")
    print(" "*20 + "Phase 2: Data Preparation - Final Report")
    print("="*100)
    
    # Project Overview
    print("\n📊 PROJECT OVERVIEW")
    print("-"*100)
    print(f"Project Name: Hệ thống hỗ trợ chẩn đoán bệnh cây cà chua từ ảnh lá")
    print(f"Models: U-Net, SegNet, U-Net++")
    print(f"Task: Semantic Segmentation of Tomato Leaves")
    print(f"Data Source: Repository 2 (SIMPAC-2024-193)")
    print(f"Total Tomato Samples: {report['total_images']} images")
    
    # Data Statistics
    print("\n📈 DATA STATISTICS")
    print("-"*100)
    print(f"{'Metric':<40} {'Value':<20}")
    print("-"*60)
    print(f"{'Total Images':<40} {report['total_images']:<20}")
    print(f"{'Total Images with Masks':<40} {sum([v for v in report['split'].values()]):<20}")
    print(f"{'Train Set':<40} {report['split']['train']:<20} ({report['split']['train']/report['total_images']*100:.2f}%)")
    print(f"{'Validation Set':<40} {report['split']['val']:<20} ({report['split']['val']/report['total_images']*100:.2f}%)")
    print(f"{'Test Set':<40} {report['split']['test']:<20} ({report['split']['test']/report['total_images']*100:.2f}%)")
    
    # Disease Classes
    print("\n🌿 DISEASE CLASSES")
    print("-"*100)
    disease_mapping = {
        "bacterial_spot": "Bacterial Spot",
        "early_blight": "Early Blight",
        "healthy": "Healthy Leaf",
        "late_blight": "Late Blight",
        "target_spot": "Target Spot"
    }
    
    print(f"{'Disease Class':<30} {'Train':<12} {'Val':<12} {'Test':<12} {'Total':<12}")
    print("-"*78)
    
    total_train = total_val = total_test = 0
    for disease, full_name in disease_mapping.items():
        if disease in report['detailed_stats']:
            stats = report['detailed_stats'][disease]
            train = stats['train']
            val = stats['val']
            test = stats['test']
            total = train + val + test
            
            print(f"{full_name:<30} {train:<12} {val:<12} {test:<12} {total:<12}")
            total_train += train
            total_val += val
            total_test += test
    
    print("-"*78)
    print(f"{'TOTAL':<30} {total_train:<12} {total_val:<12} {total_test:<12} {total_train+total_val+total_test:<12}")
    
    # Data Distribution
    print("\n📋 DATA DISTRIBUTION BY CLASS")
    print("-"*100)
    for disease, full_name in disease_mapping.items():
        if disease in report['detailed_stats']:
            stats = report['detailed_stats'][disease]
            total = stats['train'] + stats['val'] + stats['test']
            percentage = (total / report['total_images']) * 100
            
            # Create visual bar
            bar_length = int(percentage / 2)
            bar = "█" * bar_length + "░" * (50 - bar_length)
            print(f"{full_name:<25} {bar} {percentage:>6.2f}% ({total:>5} samples)")
    
    # Data Location Info
    print("\n📁 DATA LOCATION STRUCTURE")
    print("-"*100)
    print(f"Raw Data Directory:       {PROJECT_ROOT / 'data' / 'raw'}")
    print(f"Processed Data Directory: {PROCESSED_DATA_DIR}")
    print(f"\nDirectory Structure:")
    print(f"""
    data/processed/
    ├── train/
    │   ├── images/    ({report['split']['train']} samples)
    │   └── masks/     (corresponding segmentation masks)
    ├── val/
    │   ├── images/    ({report['split']['val']} samples)
    │   └── masks/     (corresponding segmentation masks)
    └── test/
        ├── images/    ({report['split']['test']} samples)
        └── masks/     (corresponding segmentation masks)
    """)
    
    # Configuration Summary
    print("\n⚙️  CONFIGURATION SUMMARY")
    print("-"*100)
    print(f"{'Parameter':<40} {'Value':<20}")
    print("-"*60)
    print(f"{'Image Size (from config.py)':<40} {'512x512':<20}")
    print(f"{'Batch Size':<40} {'8':<20}")
    print(f"{'Learning Rate':<40} {'1e-3':<20}")
    print(f"{'Epochs':<40} {'50':<20}")
    print(f"{'Train/Val/Test Ratio':<40} {'70/15/15':<20}")
    print(f"{'Supported Models':<40} {'U-Net, SegNet, U-Net++':<20}")
    
    # Next Steps
    print("\n✅ NEXT STEPS - PHASE 3-5")
    print("-"*100)
    print("""
    Phase 3: Model Architecture Implementation
    - ✓ Implement U-Net, SegNet, U-Net++ models in src/models/
    - ✓ Create data loaders in src/data/
    - ✓ Implement loss functions (Dice, Focal Loss, BCE)
    
    Phase 4: Model Training & Evaluation
    - ✓ Setup training pipeline
    - ✓ Train models on prepared dataset
    - ✓ Evaluate on validation/test sets
    - ✓ Compare model performance
    
    Phase 5: Deployment
    - ✓ Build inference pipeline
    - ✓ Create web interface/API
    - ✓ Containerize with Docker
    - ✓ Deploy to production
    """)
    
    # Execution Details
    print("\n📝 EXECUTION DETAILS")
    print("-"*100)
    print(f"Prepared at: {report['timestamp']}")
    print(f"Python Script: scripts/split_data.py")
    print(f"Report Format: JSON (data_preparation_report.json)")
    
    print("\n" + "="*100)
    print(" "*35 + "DATA PREPARATION COMPLETE! ✓")
    print(" "*25 + "Ready to start Phase 3: Model Implementation")
    print("="*100 + "\n")


if __name__ == "__main__":
    generate_detailed_report()
