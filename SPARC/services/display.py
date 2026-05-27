"""
OLED Display Service for SPARC
Wraps Waveshare OLED, falls back to logging if unavailable.
"""
import logging
import os
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont
# imports
import sys
import os
from SPARC.config.config_io import load_config, save_config
from SPARC.config.settings import (
    OLED_DEFAULT_ROTATION, OLED_DEFAULT_SCAN_DIR,
    OLED_DEFAULT_OFFSET_X, OLED_DEFAULT_OFFSET_Y
)

# Use absolute paths for OLED module (new display)
# Attempt to use local lib if available, otherwise fallback to external path
# This part seems legacy/hardware specific.
PIC_DIR = '/home/pi/OLED_Module_Code/OLED_Module_Code/RaspberryPi/python/pic'
LIB_DIR = '/home/pi/OLED_Module_Code/OLED_Module_Code/RaspberryPi/python/lib'
if os.path.exists(LIB_DIR):
    sys.path.append(LIB_DIR)

try:
    from waveshare_OLED import OLED_1in51
    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False

class DisplayService:
    def __init__(self):
        self.logger = logging.getLogger('DisplayService')
        self.oled = None
        self.font_small = None
        self.font_medium = None
        self.font_large = None
        self.width = 128
        self.height = 64

        # Load persisted display config
        self._cfg = load_config()
        self._cfg_disp = self._cfg.get("display", {})
        # Set rotation to 0 - horizontal flip will be handled separately
        self.rotation = 0  # 0 degrees, horizontal flip handled in _blit()
        self.scan_dir = str(self._cfg_disp.get("scan_dir", OLED_DEFAULT_SCAN_DIR))
        self.offset_x = int(self._cfg_disp.get("offset_x", OLED_DEFAULT_OFFSET_X))
        self.offset_y = int(self._cfg_disp.get("offset_y", OLED_DEFAULT_OFFSET_Y))
        self.line_h_large = int(self._cfg_disp.get("line_height_large", 18))
        self.line_h_med = int(self._cfg_disp.get("line_height_med", 14))
        self.use_border = bool(self._cfg_disp.get("use_border", True))

        self._init_hardware()
        self._init_fonts()

    def _set_contrast(self, contrast_value):
        """Set display contrast (0-255, lower values = dimmer)"""
        if self.oled:
            self.oled.command(0x81)
            self.oled.command(contrast_value)

    def _init_hardware(self):
        if OLED_AVAILABLE:
            try:
                self.oled = OLED_1in51.OLED_1in51()
                self.oled.Init()
                
                # Set contrast to reduce brightness (lower value = dimmer)
                # Typical range: 0x50-0xCF, using 0x60 for dimmer display
                self._set_contrast(0x60)
                
                self.oled.clear()
                self.width, self.height = self.oled.width, self.oled.height
                self.logger.info('OLED 1.51 inch display initialized.')
            except Exception as e:
                self.logger.warning(f'OLED init failed: {e}. Falling back to log display.')
                self.oled = None
        else:
            self.logger.warning('waveshare_OLED not available. Using log display.')

    def _init_fonts(self):
        try:
            # Try OLED module font first
            font_path = os.path.join(PIC_DIR, 'Font.ttc')
            if os.path.exists(font_path):
                self.font_small = ImageFont.truetype(font_path, 12)
                self.font_medium = ImageFont.truetype(font_path, 14)
                self.font_large = ImageFont.truetype(font_path, 16)
                self.logger.info('Loaded custom fonts from OLED module Font.ttc')
            else:
                raise FileNotFoundError("Font.ttc not found")
        except Exception:
            try:
                self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
                self.font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
                self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
                self.logger.info('Loaded system DejaVu fonts')
            except Exception:
                self.font_small = ImageFont.load_default()
                self.font_medium = ImageFont.load_default()
                self.font_large = ImageFont.load_default()
                self.logger.info('Using default PIL font')

    def _apply_rotation_offset(self, img):
        # Rotate image (software) if needed to keep alignment consistent after reboot
        # Default to 0 degrees (display is physically flipped horizontally)
        rotation = self.rotation if self.rotation is not None else 0
        if rotation in (90, 180, 270):
            img = img.rotate(rotation, expand=True)
        return img

    def _fit_to_panel(self, img):
        """Ensure the image matches the panel size by center-cropping or padding.
        This prevents misalignment when rotation changes the aspect (e.g., 90/270).
        """
        if img.width == self.width and img.height == self.height:
            return img
        from PIL import Image
        # Convert to 1-bit if needed
        if img.mode != '1':
            img = img.convert('1')
        # If larger, center-crop to panel size
        if img.width >= self.width and img.height >= self.height:
            left = max(0, (img.width - self.width) // 2)
            top = max(0, (img.height - self.height) // 2)
            right = left + self.width
            bottom = top + self.height
            return img.crop((left, top, right, bottom))
        # If smaller in any dimension, center-pad onto a white canvas (1-bit mode)
        canvas = Image.new('1', (self.width, self.height), 255)  # White background
        x = max(0, (self.width - img.width) // 2)
        y = max(0, (self.height - img.height) // 2)
        canvas.paste(img, (x, y))
        return canvas

    def _blit(self, img):
        if not self.oled:
            return
        # Convert to 1-bit mode for OLED_1in51
        if img.mode != '1':
            img = img.convert('1')
        
        # Apply horizontal flip to correct for physically flipped display
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        
        # Apply rotation if needed (should be 0 for flipped display)
        rotation = self.rotation if self.rotation is not None else 0
        if rotation in (90, 180, 270):
            img = img.rotate(rotation)
        
        # Fit to panel
        out = self._fit_to_panel(img)
        
        # Safely apply x/y offsets without wrapping or raising on negatives
        canvas = Image.new('1', (self.width, self.height), 255)  # White background for 1-bit
        ox = int(self.offset_x)
        oy = int(self.offset_y)
        # Compute source crop and destination paste rectangles
        src_left = max(0, -ox)
        src_top = max(0, -oy)
        dst_left = max(0, ox)
        dst_top = max(0, oy)
        crop_w = min(self.width - dst_left, out.width - src_left)
        crop_h = min(self.height - dst_top, out.height - src_top)
        if crop_w > 0 and crop_h > 0:
            region = out.crop((src_left, src_top, src_left + crop_w, src_top + crop_h))
            canvas.paste(region, (dst_left, dst_top))
        self.oled.ShowImage(self.oled.getbuffer(canvas))

    def show_three_lines_bold(self, l1: str, l2: str, l3: str, hold_s: float = 0):
        if not self.oled:
            import logging, time
            logging.getLogger(__name__).info(f"[OLED] {l1} | {l2} | {l3}")
            if hold_s > 0: time.sleep(hold_s)
            return
        from PIL import Image, ImageDraw
        img = Image.new('1', (self.width, self.height), 255)  # White background for 1-bit
        draw = ImageDraw.Draw(img)
        font = self.font_large
        line_h = self.line_h_large

        lines = [l1, l2, l3]
        total_h = line_h * 3
        y0 = max(0, (self.height - total_h) // 2)

        for i, line in enumerate(lines):
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
            except AttributeError:
                w, _ = font.getsize(line)
            x = (self.width - w) // 2
            y = y0 + i * line_h
            for dx, dy in [(0,0),(1,0),(0,1),(1,1)]:
                draw.text((x+dx, y+dy), line, font=font, fill=0)  # Black text (0) on white background

        if self.use_border:
            draw.rectangle([(0,0),(self.width-1,self.height-1)], outline=0)

        self._blit(img)
        if hold_s > 0:
            import time; time.sleep(hold_s)

    def show_centered_lines_bold(self, lines, large=True, border=True, hold_s=0):
        """Render up to 3 lines centered. Horizontal centering uses font metrics;
        vertical spacing uses configured line heights for consistent alignment.
        """
        if not self.oled:
            import logging, time
            logging.getLogger(__name__).info(f"[OLED] {' | '.join(lines)}")
            if hold_s > 0: time.sleep(hold_s)
            return
        from PIL import Image, ImageDraw
        img = Image.new('1', (self.width, self.height), 255)  # White background for 1-bit
        draw = ImageDraw.Draw(img)

        # Clamp to 3 lines
        lines = list(lines)[:3]

        font = self.font_large if large else self.font_medium
        line_h = self.line_h_large if large else self.line_h_med
        # Measure widths for horizontal centering
        measured = []
        for text in lines:
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                w = bbox[2] - bbox[0]
            except AttributeError:
                w, _ = font.getsize(text)
            measured.append((text, w))

        total_h = line_h * len(measured)
        y0 = max(0, (self.height - total_h) // 2)

        for i, (text, w) in enumerate(measured):
            x = (self.width - w) // 2
            y = y0 + i * line_h
            for dx, dy in [(0,0), (1,0), (0,1), (1,1)]:
                draw.text((x+dx, y+dy), text, font=font, fill=0)  # Black text (0) on white background

        if border and self.use_border:
            draw.rectangle([(0,0),(self.width-1,self.height-1)], outline=0)

        self._blit(img)
        if hold_s > 0:
            import time; time.sleep(hold_s)

    def show_two_lines_bold(self, l1: str, l2: str, hold_s: float = 0):
        if not self.oled:
            import logging, time
            logging.getLogger(__name__).info(f"[OLED] {l1} | {l2}")
            if hold_s > 0: time.sleep(hold_s)
            return
        from PIL import Image, ImageDraw
        img = Image.new('1', (self.width, self.height), 255)  # White background for 1-bit
        draw = ImageDraw.Draw(img)
        font = self.font_large
        line_h = self.line_h_large
        total_h = line_h * 2
        y0 = max(0, (self.height - total_h) // 2)

        for i, line in enumerate([l1, l2]):
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
            except AttributeError:
                w, _ = font.getsize(line)
            x = (self.width - w) // 2
            y = y0 + i * line_h
            for dx, dy in [(0,0),(1,0),(0,1),(1,1)]:
                draw.text((x+dx, y+dy), line, font=font, fill=0)  # Black text (0) on white background

        if self.use_border:
            draw.rectangle([(0,0),(self.width-1,self.height-1)], outline=0)

        self._blit(img)

    def show_lines(self, lines, large=True, border=True, hold_s=0):
        """Show multiple lines of text with auto-fitting"""
        if not self.oled:
            import logging, time
            logging.getLogger(__name__).info(f"[OLED] {' | '.join(lines)}")
            if hold_s > 0: time.sleep(hold_s)
            return
        
        from PIL import Image, ImageDraw
        img = Image.new('1', (self.width, self.height), 255)  # White background for 1-bit
        draw = ImageDraw.Draw(img)
        
        # Choose font based on large parameter
        font = self.font_large if large else self.font_medium
        line_h = self.line_h_large if large else self.line_h_med
        
        # Limit to 3 lines max
        if len(lines) > 3:
            lines = lines[-3:]
        
        total_h = line_h * len(lines)
        y0 = max(0, (self.height - total_h) // 2)
        
        for i, line in enumerate(lines):
            # Measure text width
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
            except AttributeError:
                w, _ = font.getsize(line)
            
            # Truncate text if it exceeds display width (with margin)
            max_display_width = self.width - 8  # Leave 4px margin on each side
            if w > max_display_width:
                # Truncate line to fit
                truncated = line
                while True:
                    try:
                        bbox = draw.textbbox((0, 0), truncated + "...", font=font)
                        test_w = bbox[2] - bbox[0]
                    except AttributeError:
                        test_w, _ = font.getsize(truncated + "...")
                    if test_w <= max_display_width or len(truncated) <= 3:
                        break
                    truncated = truncated[:-1]
                line = truncated + "..." if len(truncated) < len(line) else line
                # Re-measure truncated text
                try:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    w = bbox[2] - bbox[0]
                except AttributeError:
                    w, _ = font.getsize(line)
            
            x = (self.width - w) // 2
            y = y0 + i * line_h
            # Ensure x is not negative (text starts at least at 0)
            x = max(0, x)
            for dx, dy in [(0,0),(1,0),(0,1),(1,1)]:
                draw.text((x+dx, y+dy), line, font=font, fill=0)  # Black text (0) on white background
        
        if border and self.use_border:
            draw.rectangle([(0,0),(self.width-1,self.height-1)], outline=0)
        
        self._blit(img)
        if hold_s > 0:
            import time; time.sleep(hold_s)

    def clear(self) -> None:
        if self.oled:
            self.oled.clear()
        else:
            self.logger.info('OLED: clear')

    def close(self) -> None:
        if self.oled:
            self.oled.module_exit()
        else:
            self.logger.info('OLED: close')

    # Add a quick calibration API
    def save_calibration(self, rotation=None, scan_dir=None, offset_x=None, offset_y=None, line_h_large=None, line_h_med=None, use_border=None):
        if rotation is not None: self.rotation = int(rotation)
        if scan_dir is not None: self.scan_dir = str(scan_dir)
        if offset_x is not None: self.offset_x = int(offset_x)
        if offset_y is not None: self.offset_y = int(offset_y)
        if line_h_large is not None: self.line_h_large = int(line_h_large)
        if line_h_med is not None: self.line_h_med = int(line_h_med)
        if use_border is not None: self.use_border = bool(use_border)
        # persist to config
        cfg = load_config()
        cfg["display"] = {
            "rotation": self.rotation,
            "scan_dir": self.scan_dir,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
            "line_height_large": self.line_h_large,
            "line_height_med": self.line_h_med,
            "use_border": self.use_border,
        }
        save_config(cfg)