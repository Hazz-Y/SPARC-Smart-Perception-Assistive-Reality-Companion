#!/usr/bin/env python3
"""
Quick OLED alignment fixer
Provides common alignment presets
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_io import load_config, save_config

def apply_preset(preset_name):
    """Apply a preset alignment configuration"""
    config = load_config()
    
    presets = {
        "default": {
            "rotation": 0,
            "offset_x": 0,
            "offset_y": 0,
            "line_height_large": 18,
            "line_height_med": 14,
            "use_border": True
        },
        "shifted_right": {
            "rotation": 0,
            "offset_x": -3,
            "offset_y": 0,
            "line_height_large": 18,
            "line_height_med": 14,
            "use_border": True
        },
        "shifted_left": {
            "rotation": 0,
            "offset_x": 3,
            "offset_y": 0,
            "line_height_large": 18,
            "line_height_med": 14,
            "use_border": True
        },
        "shifted_down": {
            "rotation": 0,
            "offset_x": 0,
            "offset_y": -3,
            "line_height_large": 18,
            "line_height_med": 14,
            "use_border": True
        },
        "shifted_up": {
            "rotation": 0,
            "offset_x": 0,
            "offset_y": 3,
            "line_height_large": 18,
            "line_height_med": 14,
            "use_border": True
        },
        "rotated_90": {
            "rotation": 90,
            "offset_x": 0,
            "offset_y": 0,
            "line_height_large": 18,
            "line_height_med": 14,
            "use_border": True
        },
        "rotated_180": {
            "rotation": 180,
            "offset_x": 0,
            "offset_y": 0,
            "line_height_large": 18,
            "line_height_med": 14,
            "use_border": True
        },
        "smaller_text": {
            "rotation": 0,
            "offset_x": 0,
            "offset_y": 0,
            "line_height_large": 16,
            "line_height_med": 12,
            "use_border": True
        },
        "larger_text": {
            "rotation": 0,
            "offset_x": 0,
            "offset_y": 0,
            "line_height_large": 20,
            "line_height_med": 16,
            "use_border": True
        }
    }
    
    if preset_name not in presets:
        print(f"Unknown preset: {preset_name}")
        print(f"Available presets: {', '.join(presets.keys())}")
        return False
    
    # Apply preset
    config["display"].update(presets[preset_name])
    save_config(config)
    
    print(f"Applied preset '{preset_name}':")
    print(f"  rotation: {config['display']['rotation']}")
    print(f"  offset_x: {config['display']['offset_x']}")
    print(f"  offset_y: {config['display']['offset_y']}")
    print(f"  line_height_large: {config['display']['line_height_large']}")
    print(f"  use_border: {config['display']['use_border']}")
    
    return True

def show_current():
    """Show current configuration"""
    config = load_config()
    print("Current display configuration:")
    print(f"  rotation: {config['display']['rotation']}")
    print(f"  offset_x: {config['display']['offset_x']}")
    print(f"  offset_y: {config['display']['offset_y']}")
    print(f"  line_height_large: {config['display']['line_height_large']}")
    print(f"  line_height_med: {config['display']['line_height_med']}")
    print(f"  use_border: {config['display']['use_border']}")

def main():
    if len(sys.argv) < 2:
        print("OLED Alignment Fixer")
        print("Usage: python fix_display_alignment.py <preset_name>")
        print("\nAvailable presets:")
        print("  default        - Reset to default settings")
        print("  shifted_right  - Move text left (if text appears too far right)")
        print("  shifted_left   - Move text right (if text appears too far left)")
        print("  shifted_down   - Move text up (if text appears too low)")
        print("  shifted_up     - Move text down (if text appears too high)")
        print("  rotated_90     - Rotate display 90 degrees")
        print("  rotated_180    - Rotate display 180 degrees")
        print("  smaller_text   - Use smaller line heights")
        print("  larger_text    - Use larger line heights")
        print("\nCurrent configuration:")
        show_current()
        return
    
    preset_name = sys.argv[1]
    if apply_preset(preset_name):
        print("\nConfiguration saved! Restart SPARC to see changes.")
    else:
        print("Failed to apply preset.")

if __name__ == "__main__":
    main()

