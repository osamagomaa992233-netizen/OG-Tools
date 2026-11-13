import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestDistribution(unittest.TestCase):
    def test_plugin_files_and_manifest(self):
        plugin = ROOT / 'plugin'
        m = json.loads((plugin / 'manifest.json').read_text())
        self.assertEqual(m['host']['app'], 'premierepro')
        self.assertEqual(m['version'], '0.8.0')
        for filename in ('index.html', 'main.js', 'style.css', 'native/keyframes.js', 'native/selection.js'):
            self.assertTrue((plugin / filename).is_file(), filename)

    def test_setup_and_builder_paths(self):
        setup = (ROOT / 'installer/windows/INSTALL_OG_TOOLS.ps1').read_text()
        build = (ROOT / '.github/workflows/build-windows-portable.yml').read_text()
        self.assertIn('INSTALL_OG_TOOLS.ps1', (ROOT / 'installer/windows/INSTALL_OG_TOOLS.cmd').read_text())
        self.assertIn('ENGINE_HIDDEN.cmd', setup)
        self.assertIn('OGToolsEngine.exe', setup)
        self.assertIn('/api/health', setup)
        self.assertIn('pyinstaller', build)
        self.assertIn('OG_Tools_v0.8_Windows_Portable.zip', build)


if __name__ == '__main__':
    unittest.main()
