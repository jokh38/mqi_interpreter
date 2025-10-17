"""
Configuration reader for MQI Interpreter
Loads and validates config.yaml settings
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Configuration manager for MQI Interpreter"""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to config.yaml. If None, looks in script directory.
        """
        if config_path is None:
            # Look for config.yaml in the parent directory of this script
            script_dir = Path(__file__).resolve().parent.parent
            config_path = script_dir / "config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            print(f"Warning: Config file not found at {self.config_path}")
            print("Using default configuration")
            return self._get_default_config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                if config is None:
                    print("Warning: Config file is empty, using defaults")
                    return self._get_default_config()
                return config
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            print("Using default configuration")
            return self._get_default_config()
        except Exception as e:
            print(f"Error loading config file: {e}")
            print("Using default configuration")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            'features': {
                'generate_moqui': True,
                'generate_topas': False,
                'export_excel': False,
                'process_mgn': False
            },
            'processing': {
                'dose_dividing_factor': 10,
                'calibration_mode': {
                    'enabled': False,
                    'use_correction_factors': True,
                    'multi_energy_layer': False
                }
            },
            'topas': {
                'use_schneider': False
            },
            'excel': {
                'export_ptn': True,
                'export_mgn': True,
                'include_raw_values': True
            },
            'logging': {
                'level': 'INFO',
                'show_progress': True
            }
        }

    # Feature flags
    @property
    def generate_moqui(self) -> bool:
        return self.config.get('features', {}).get('generate_moqui', True)

    @property
    def generate_topas(self) -> bool:
        return self.config.get('features', {}).get('generate_topas', False)

    @property
    def export_excel(self) -> bool:
        return self.config.get('features', {}).get('export_excel', False)

    @property
    def process_mgn(self) -> bool:
        return self.config.get('features', {}).get('process_mgn', False)

    # Processing parameters
    @property
    def dose_dividing_factor(self) -> int:
        return self.config.get('processing', {}).get('dose_dividing_factor', 10)

    @property
    def calibration_mode_enabled(self) -> bool:
        return self.config.get('processing', {}).get('calibration_mode', {}).get('enabled', False)

    @property
    def calibration_use_correction_factors(self) -> bool:
        return self.config.get('processing', {}).get('calibration_mode', {}).get('use_correction_factors', True)

    @property
    def calibration_multi_energy_layer(self) -> bool:
        return self.config.get('processing', {}).get('calibration_mode', {}).get('multi_energy_layer', False)

    # TOPAS parameters
    @property
    def topas_config(self) -> Dict[str, Any]:
        return self.config.get('topas', {})

    @property
    def topas_use_schneider(self) -> bool:
        return self.config.get('topas', {}).get('use_schneider', False)

    # Excel parameters
    @property
    def excel_export_ptn(self) -> bool:
        return self.config.get('excel', {}).get('export_ptn', True)

    @property
    def excel_export_mgn(self) -> bool:
        return self.config.get('excel', {}).get('export_mgn', True)

    @property
    def excel_include_raw_values(self) -> bool:
        return self.config.get('excel', {}).get('include_raw_values', True)

    # Logging parameters
    @property
    def log_level(self) -> str:
        return self.config.get('logging', {}).get('level', 'INFO')

    @property
    def show_progress(self) -> bool:
        return self.config.get('logging', {}).get('show_progress', True)

# Global config instance
_config_instance = None

def get_config(config_path: str = None) -> Config:
    """
    Get global config instance (singleton pattern)

    Args:
        config_path: Path to config.yaml. Only used on first call.

    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance

if __name__ == '__main__':
    # Test config loading
    config = get_config()
    print(f"Generate MOQUI: {config.generate_moqui}")
    print(f"Generate TOPAS: {config.generate_topas}")
    print(f"Export Excel: {config.export_excel}")
    print(f"Process MGN: {config.process_mgn}")
    print(f"Dose dividing factor: {config.dose_dividing_factor}")
