"""
CreditPilot Unified Color Configuration Module

This is the ONLY module for accessing color values throughout the entire system.
All color references must import from this module - NO hardcoded hex values allowed.

Usage:
    from config.colors import COLORS
    
    # Web UI - Use core colors only
    background = COLORS.core.black
    accent = COLORS.core.hot_pink
    border = COLORS.core.dark_purple
    
    # Status indicators
    success_color = COLORS.status.success
    error_color = COLORS.status.error
    
    # Excel reports - Use excel colors only
    header_bg = COLORS.excel.header_row.background
    
    # Buttons
    primary_btn_bg = COLORS.buttons.primary.background
    
Author: CreditPilot Development Team
Last Updated: 2025-11-17
Version: 2.0.0
"""

import json
import os
from pathlib import Path
from typing import Any, Dict


class ColorConfig:
    """
    Immutable color configuration container.
    Loads colors from config/colors.json and provides dot-notation access.
    """
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize color config from dictionary."""
        self._data = data
        
    def __getattr__(self, name: str) -> Any:
        """Access color properties using dot notation."""
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        
        value = self._data.get(name)
        if value is None:
            raise AttributeError(f"Color '{name}' not found in configuration")
        
        if isinstance(value, dict):
            return ColorConfig(value)
        return value
    
    def __getitem__(self, key: str) -> Any:
        """Access color properties using bracket notation."""
        return self.__getattr__(key)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._data.copy()
    
    def __repr__(self) -> str:
        return f"ColorConfig({self._data})"


class CreditPilotColors:
    """
    Main color configuration class for CreditPilot system.
    Provides easy access to all color definitions from config/colors.json.
    """
    
    def __init__(self):
        """Load color configuration from JSON file."""
        config_path = Path(__file__).parent / 'colors.json'
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Color configuration file not found: {config_path}\n"
                "Please ensure config/colors.json exists."
            )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        theme = data.get('creditpilot_theme', {})
        
        # Core colors (Web UI - Mandatory 3-color palette)
        self.core = ColorConfig(theme.get('core_colors', {}))
        
        # Status colors (Functional indicators)
        self.status = ColorConfig(theme.get('status_colors', {}))
        
        # Helper colors (Derived from core colors)
        self.helper = ColorConfig(theme.get('helper_colors', {}))
        
        # Excel colors (Excel reports only)
        self.excel = ColorConfig(theme.get('excel_colors', {}))
        
        # Button styles (Predefined button color combinations)
        self.buttons = ColorConfig(theme.get('button_styles', {}))
        
        # Gradient styles (Predefined gradient combinations)
        self.gradients = ColorConfig(theme.get('gradient_styles', {}))
        
        # Deprecated colors (For reference only - DO NOT USE)
        self.deprecated = ColorConfig(theme.get('deprecated_colors', {}))
        
        # Compliance rules
        self.compliance = theme.get('compliance_rules', {})
        
        # Theme metadata
        self.version = theme.get('version', '1.0.0')
        self.name = theme.get('name', 'CreditPilot Official Theme')
        self.description = theme.get('description', '')
    
    def get_web_ui_palette(self) -> Dict[str, str]:
        """
        Get the complete Web UI color palette (core + status + helper colors).
        Returns a flat dictionary for easy CSS variable generation.
        """
        palette = {
            # Core colors
            'black': self.core.black,
            'hot_pink': self.core.hot_pink,
            'dark_purple': self.core.dark_purple,
            'white': self.core.white,
            
            # Status colors
            'success': self.status.success,
            'success_bg': self.status.success_bg,
            'warning': self.status.warning,
            'warning_bg': self.status.warning_bg,
            'error': self.status.error,
            'error_bg': self.status.error_bg,
            'info': self.status.info,
            'info_bg': self.status.info_bg,
        }
        
        # Add helper colors
        try:
            palette.update({
                # Helper backgrounds
                'bg_primary': self.helper.backgrounds.primary,
                'bg_secondary': self.helper.backgrounds.secondary,
                'bg_tertiary': self.helper.backgrounds.tertiary,
                
                # Helper text
                'text_primary': self.helper.text.primary,
                'text_secondary': self.helper.text.secondary,
                'text_dim': self.helper.text.dim,
                'text_muted': self.helper.text.muted,
                
                # Helper hover states
                'hot_pink_hover': self.helper.hover_states.hot_pink_hover,
                'hot_pink_light': self.helper.hover_states.hot_pink_light,
                'dark_purple_hover': self.helper.hover_states.dark_purple_hover,
                'dark_purple_dark': self.helper.hover_states.dark_purple_dark,
            })
        except AttributeError:
            # Helper colors not defined in config (backward compatibility)
            pass
        
        return palette
    
    def get_excel_palette(self) -> Dict[str, Any]:
        """
        Get the complete Excel formatting palette.
        Returns nested dictionary matching config structure.
        """
        return self.excel.to_dict()
    
    def validate_color(self, color: str) -> bool:
        """
        Validate if a color hex code is allowed in the system.
        
        Args:
            color: Hex color code (e.g., '#FF007F')
            
        Returns:
            True if color is in approved palette, False otherwise
        """
        # Normalize color
        color = color.upper()
        
        # Get all allowed colors from web UI palette
        web_ui_palette = self.get_web_ui_palette()
        allowed_colors = [c.upper() for c in web_ui_palette.values() if isinstance(c, str) and c.startswith('#')]
        
        # Check Excel colors (flatten all excel colors)
        excel_colors = []
        
        def flatten_colors(d):
            for v in d.values():
                if isinstance(v, str) and v.startswith('#'):
                    excel_colors.append(v.upper())
                elif isinstance(v, dict):
                    flatten_colors(v)
        
        flatten_colors(self.excel.to_dict())
        
        # Combine all allowed colors
        all_allowed_colors = allowed_colors + excel_colors
        
        return color in all_allowed_colors
    
    def is_deprecated(self, color: str) -> bool:
        """
        Check if a color is deprecated.
        
        Args:
            color: Hex color code (e.g., '#D4AF37')
            
        Returns:
            True if color is deprecated, False otherwise
        """
        color = color.upper()
        deprecated_data = self.deprecated.to_dict()
        
        for category in deprecated_data.values():
            if isinstance(category, dict):
                for k, v in category.items():
                    if isinstance(v, str) and v.upper() == color:
                        return True
        
        return False
    
    def get_color_usage(self, color_name: str) -> str:
        """
        Get usage description for a specific color.
        
        Args:
            color_name: Name of the color (e.g., 'hot_pink', 'success')
            
        Returns:
            Usage description string
        """
        # Check core colors
        if hasattr(self.core, 'usage') and color_name in self.core.usage._data:
            return self.core.usage[color_name]
        
        # Check status colors
        if hasattr(self.status, 'usage') and color_name in self.status.usage._data:
            return self.status.usage[color_name]
        
        return f"No usage information available for '{color_name}'"


# Global color configuration instance
# Import this in all Python files that need colors
COLORS = CreditPilotColors()


# Convenience shortcuts for commonly used colors
# These are provided for backward compatibility and quick access

# Core colors (Web UI)
COLOR_BLACK = COLORS.core.black
COLOR_HOT_PINK = COLORS.core.hot_pink
COLOR_DARK_PURPLE = COLORS.core.dark_purple
COLOR_WHITE = COLORS.core.white

# Status colors
COLOR_SUCCESS = COLORS.status.success
COLOR_WARNING = COLORS.status.warning
COLOR_ERROR = COLORS.status.error
COLOR_INFO = COLORS.status.info

# Excel primary colors
EXCEL_MAIN_PINK = COLORS.excel.primary_colors.main_pink
EXCEL_DEEP_BROWN = COLORS.excel.primary_colors.deep_brown


# Helper function to generate CSS variables
def generate_css_variables(indent: int = 2) -> str:
    """
    Generate CSS custom properties (variables) from color configuration.
    
    Args:
        indent: Number of spaces for indentation
        
    Returns:
        CSS variable declarations as string
    """
    palette = COLORS.get_web_ui_palette()
    spaces = ' ' * indent
    
    lines = [':root {']
    
    # Core colors
    lines.append(f'{spaces}/* Core Colors - Mandatory 3-color palette */')
    lines.append(f'{spaces}--color-black: {palette["black"]};')
    lines.append(f'{spaces}--color-hot-pink: {palette["hot_pink"]};')
    lines.append(f'{spaces}--color-dark-purple: {palette["dark_purple"]};')
    lines.append(f'{spaces}--color-white: {palette["white"]};')
    lines.append('')
    
    # Status colors
    lines.append(f'{spaces}/* Status Colors - Functional indicators */')
    lines.append(f'{spaces}--color-success: {palette["success"]};')
    lines.append(f'{spaces}--color-warning: {palette["warning"]};')
    lines.append(f'{spaces}--color-error: {palette["error"]};')
    lines.append(f'{spaces}--color-info: {palette["info"]};')
    
    lines.append('}')
    
    return '\n'.join(lines)


# Example usage and testing
if __name__ == '__main__':
    print("CreditPilot Color Configuration")
    print("=" * 60)
    print(f"Theme: {COLORS.name}")
    print(f"Version: {COLORS.version}")
    print(f"Description: {COLORS.description}")
    print()
    
    print("Core Colors (Web UI):")
    print(f"  Black: {COLORS.core.black}")
    print(f"  Hot Pink: {COLORS.core.hot_pink}")
    print(f"  Dark Purple: {COLORS.core.dark_purple}")
    print(f"  White: {COLORS.core.white}")
    print()
    
    print("Status Colors:")
    print(f"  Success: {COLORS.status.success}")
    print(f"  Warning: {COLORS.status.warning}")
    print(f"  Error: {COLORS.status.error}")
    print(f"  Info: {COLORS.status.info}")
    print()
    
    print("Excel Primary Colors:")
    print(f"  Main Pink: {COLORS.excel.primary_colors.main_pink}")
    print(f"  Deep Brown: {COLORS.excel.primary_colors.deep_brown}")
    print()
    
    print("Button Styles:")
    print(f"  Primary: {COLORS.buttons.primary.background}")
    print(f"  Secondary: {COLORS.buttons.secondary.background}")
    print()
    
    print("Color Validation Examples:")
    print(f"  Is #FF007F allowed? {COLORS.validate_color('#FF007F')}")
    print(f"  Is #D4AF37 allowed? {COLORS.validate_color('#D4AF37')}")
    print(f"  Is #D4AF37 deprecated? {COLORS.is_deprecated('#D4AF37')}")
    print()
    
    print("CSS Variables:")
    print(generate_css_variables())
