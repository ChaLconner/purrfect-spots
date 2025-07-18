"""
Test script for YOLOv5 model loading
Run this to test if the model loads correctly
"""

import os
import sys
import torch
from PIL import Image
import numpy as np

def test_yolo_loading():
    """Test different methods of loading YOLOv5"""
    print("🧪 Testing YOLOv5 model loading...")
    
    # Check device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🖥️ Using device: {device}")
    
    try:
        print("\n📦 Method 1: Download from ultralytics/yolov5...")
        # Clear cache first
        import shutil
        cache_dir = torch.hub.get_dir()
        yolo_cache = os.path.join(cache_dir, "ultralytics_yolov5_master")
        if os.path.exists(yolo_cache):
            shutil.rmtree(yolo_cache)
            print("🗑️ Cleared YOLOv5 cache")
        
        model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True, force_reload=True)
        model.to(device).eval()
        print("✅ Method 1: SUCCESS - Model loaded from ultralytics")
        
        # Test inference
        print("\n🔍 Testing inference...")
        # Create a dummy image
        test_img = Image.new('RGB', (640, 640), color='red')
        test_img_np = np.array(test_img)
        
        # Run inference
        results = model(test_img_np)
        print("✅ Inference test passed")
        print(f"📊 Results type: {type(results)}")
        
        # Test if we can get labels
        try:
            labels = results.pandas().xyxy[0]['name'].tolist()
            print(f"🏷️ Detection labels available: {len(labels)} detections")
        except Exception as e:
            print(f"⚠️ Could not get pandas results: {e}")
            try:
                # Alternative method
                labels = results.names
                print(f"🏷️ Model classes available: {len(labels)} classes")
                print(f"🐱 Cat class present: {'cat' in str(labels).lower()}")
            except Exception as e2:
                print(f"⚠️ Could not get model names: {e2}")
        
        return model
        
    except Exception as e:
        print(f"❌ Method 1 failed: {str(e)}")
        
    try:
        print("\n📁 Method 2: Load from local file...")
        if os.path.exists("yolov5s.pt"):
            model = torch.load("yolov5s.pt", map_location=device, weights_only=False)
            print("✅ Method 2: SUCCESS - Model loaded from local file")
            return model
        else:
            print("❌ Method 2: Local file not found")
    except Exception as e:
        print(f"❌ Method 2 failed: {str(e)}")
    
    print("\n❌ All methods failed")
    return None

if __name__ == "__main__":
    model = test_yolo_loading()
    
    if model:
        print("\n🎉 YOLO model is working!")
    else:
        print("\n💥 YOLO model failed to load")
        print("💡 Try running: pip install ultralytics")
        print("💡 Or check your internet connection")
