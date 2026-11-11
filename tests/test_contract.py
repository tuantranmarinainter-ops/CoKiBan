import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('cokiban',Path(__file__).parents[1]/'tools/cokiban.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ContractTests(unittest.TestCase):
    def test_srt_and_export_keep_cross_shot_cues(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            srt=root/'test.srt'
            srt.write_text('1\n00:00:00,000 --> 00:00:01,000\nXin chào\n\n2\n00:00:01,000 --> 00:00:03,000\nDòng hai\n',encoding='utf-8')
            cues=module.subtitles(srt)
            data=dict(source={'duration':2},subtitles=cues,shots=[dict(id='s001',dur=2,lines=[1,2],type=None,status='candidate')])
            module.export_studio(data,root)
            shots=json.loads((root/'shots.js').read_text().split(' = ',1)[1].rstrip(';\n'))
            self.assertNotIn('line',shots[0])
            self.assertNotIn('text',shots[0])
            self.assertEqual(json.loads((root/'reference.json').read_text())['subtitles'][1]['end'],3)
            self.assertEqual(json.loads((root/'integration-status.json').read_text())['fallback_shot_types'],['s001'])
            self.assertTrue(json.loads((root/'narration.json').read_text())['dry'])

    def test_invalid_srt_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bad.srt';p.write_text('1\n00:00:02,000 --> 00:00:01,000\nInvalid')
            with self.assertRaises(ValueError):module.subtitles(p)

if __name__=='__main__':unittest.main()
