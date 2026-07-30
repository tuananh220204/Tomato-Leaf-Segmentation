"""
Data Splitting Script - Split raw data into train/val/test sets with masks
"""
import os
import shutil
from pathlib import Path
from collections import defaultdict
import random
import json
from datetime import datetime

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Split ratios
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Disease classes for Tomato
TOMATO_CLASSES = {
    "Tomato___Bacterial_spot": "bacterial_spot",
    "Tomato___Early_blight": "early_blight",
    "Tomato___healthy": "healthy",
    "Tomato___Late_blight": "late_blight",
    "Tomato___Target_Spot": "target_spot",
}

def create_directories():
    """Create processed data directories"""
    for split in ["train", "val", "test"]:
        (PROCESSED_DATA_DIR / split / "images").mkdir(parents=True, exist_ok=True)
        (PROCESSED_DATA_DIR / split / "masks").mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Created processed data directories")


def split_and_organize_data():
    """Split data into train/val/test sets and organize with matching masks"""
    print("\n" + "="*80)
    print("Splitting data into train/val/test sets with masks")
    print("="*80)
    
    split_stats = defaultdict(lambda: {"train": 0, "val": 0, "test": 0})
    
    for disease_idx, disease_name in enumerate(TOMATO_CLASSES.values(), 1):
        images_dir = RAW_DATA_DIR / disease_name / "images"
        masks_dir = RAW_DATA_DIR / disease_name / "masks"
        
        # Get all image files
        image_files = sorted(list(images_dir.glob("*.*")))
        
        if not image_files:
            print(f"! No images found for {disease_name}")
            continue
        
        # Shuffle for random split
        random.shuffle(image_files)
        
        total_images = len(image_files)
        train_count = int(total_images * TRAIN_RATIO)
        val_count = int(total_images * VAL_RATIO)
        
        # Split indices
        train_images = image_files[:train_count]
        val_images = image_files[train_count:train_count + val_count]
        test_images = image_files[train_count + val_count:]
        
        # Copy to processed directories with consistent naming
        for split_name, image_list in [("train", train_images), ("val", val_images), ("test", test_images)]:
            split_img_dir = PROCESSED_DATA_DIR / split_name / "images"
            split_mask_dir = PROCESSED_DATA_DIR / split_name / "masks"
            
            mask_count = 0
            for image_idx, img_file in enumerate(image_list, 1):
                # Create consistent filename: disease_id_split_index
                new_name = f"tomato_{disease_idx:02d}_{split_name}_{image_idx:04d}"
                img_ext = img_file.suffix
                
                # Copy image
                new_img_path = split_img_dir / f"{new_name}{img_ext}"
                try:
                    shutil.copy2(img_file, new_img_path)
                except Exception as e:
                    print(f"  ! Error copying image {img_file.name}: {str(e)}")
                
                # Copy corresponding mask if exists
                # Mask naming convention: image_name_without_ext + "_final_masked" + ext
                img_stem = img_file.stem
                potential_mask_names = [
                    f"{img_stem}_final_masked{img_ext}",
                    f"{img_stem}_final_masked.jpg",
                    f"{img_stem}_final_masked.png",
                    img_file.name  # Try original name as fallback
                ]
                
                for mask_name in potential_mask_names:
                    mask_path = masks_dir / mask_name
                    if mask_path.exists():
                        new_mask_path = split_mask_dir / f"{new_name}{img_ext}"
                        try:
                            shutil.copy2(mask_path, new_mask_path)
                            mask_count += 1
                        except Exception as e:
                            print(f"  ! Error copying mask {mask_name}: {str(e)}")
                        break
            
            split_stats[disease_name][split_name] = len(image_list)
        
        print(f"✓ {disease_name}: Train={len(train_images)}, Val={len(val_images)}, Test={len(test_images)}")
    
    return split_stats


def generate_statistics_report(split_stats):
    """Generate comprehensive statistics report"""
    print("\n" + "="*80)
    print("Data Statistics Report")
    print("="*80)
    
    total_stats = {"train": 0, "val": 0, "test": 0}
    
    print(f"\n{'Disease Class':<25} {'Train':<10} {'Val':<10} {'Test':<10} {'Total':<10}")
    print("-" * 65)
    
    for disease_name in TOMATO_CLASSES.values():
        if disease_name in split_stats:
            stats = split_stats[disease_name]
            train = stats["train"]
            val = stats["val"]
            test = stats["test"]
            total = train + val + test
            
            print(f"{disease_name:<25} {train:<10} {val:<10} {test:<10} {total:<10}")
            
            total_stats["train"] += train
            total_stats["val"] += val
            total_stats["test"] += test
    
    print("-" * 65)
    total_all = sum(total_stats.values())
    print(f"{'TOTAL':<25} {total_stats['train']:<10} {total_stats['val']:<10} {total_stats['test']:<10} {total_all:<10}")
    
    # Percentage breakdown
    print(f"\nPercentage Split:")
    print(f"  Train: {total_stats['train']/total_all*100:.2f}% ({total_stats['train']} images)")
    print(f"  Val:   {total_stats['val']/total_all*100:.2f}% ({total_stats['val']} images)")
    print(f"  Test:  {total_stats['test']/total_all*100:.2f}% ({total_stats['test']} images)")
    
    # Save report to JSON
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_images": total_all,
        "split": total_stats,
        "disease_classes": dict(TOMATO_CLASSES),
        "ratios": {
            "train": TRAIN_RATIO,
            "val": VAL_RATIO,
            "test": TEST_RATIO
        },
        "detailed_stats": dict(split_stats)
    }
    
    report_path = PROJECT_ROOT / "data_preparation_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Report saved to: {report_path}")
    
    return total_stats


def verify_split_data():
    """Verify that images and masks are properly paired"""
    print("\n" + "="*80)
    print("Verifying data integrity")
    print("="*80)
    
    for split in ["train", "val", "test"]:
        split_img_dir = PROCESSED_DATA_DIR / split / "images"
        split_mask_dir = PROCESSED_DATA_DIR / split / "masks"
        
        images = set(f.stem for f in split_img_dir.glob("*.*"))
        masks = set(f.stem for f in split_mask_dir.glob("*.*"))
        
        print(f"✓ {split.upper()}: {len(images)} images, {len(masks)} masks")
        
        # Check for orphaned files
        orphan_images = images - masks
        orphan_masks = masks - images
        
        if orphan_images:
            print(f"  ! Warning: {len(orphan_images)} images without masks")
        if orphan_masks:
            print(f"  ! Warning: {len(orphan_masks)} masks without images")


def main():
    """Main execution flow"""
    print("\n" + "="*80)
    print("TOMATO DISEASE SEGMENTATION - DATA SPLITTING PIPELINE")
    print("="*80)
    
    try:
        # Step 1: Create directory structure
        create_directories()
        
        # Step 2: Split and organize data
        split_stats = split_and_organize_data()
        
        # Step 3: Generate statistics report
        final_stats = generate_statistics_report(split_stats)
        
        # Step 4: Verify split data
        verify_split_data()
        
        print("\n" + "="*80)
        print("✓ DATA SPLITTING COMPLETED SUCCESSFULLY!")
        print("="*80)
        print(f"\nProcessed data locations:")
        print(f"  {PROCESSED_DATA_DIR}")
        print(f"\nReady for training!")
        
    except Exception as e:
        print(f"\n✗ ERROR during data splitting: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)
    main()
