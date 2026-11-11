import importlib.util
import json
import tempfile
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]/'tools'))

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


class AnnotationTests(unittest.TestCase):
    def fixture(self, root):
        (root/'frames').mkdir()
        for i in range(3): (root/'frames'/f'f{i:08d}.jpg').write_bytes(b'fake jpeg')
        data = {'schema_version':1, 'source':{'frame_times':[0,.1,.2], 'duration':.3}, 'subtitles':[],
            'shots':[{'id':'s001','start_frame':0,'end_frame_exclusive':3,'start':0,'end':.3,'dur':.3,
              'references':[0,1,2], 'lines':[], 'status':'reviewed','type':None}]}
        module.upgrade(data)
        data['objects']['house']={'name':'House','description':'red roof','frame_ids':[0]}
        data['review']['inspected_frames']=[0,2]
        data['shots'][0].update(object_instances=[{'object_id':'house','bbox':[.1,.1,.5,.5],'frame_ids':[0]}],
            motion_events=[{'object_id':'house','start':0,'end':.3,'description':'moves','frame_ids':[0,2]}],
            camera_timeline=[{'start':0,'end':.3,'movement':'unknown','frame_ids':[0,2]}],
            observations=[{'kind':'observed','text':'red roof','confidence':'high','frame_ids':[0]}])
        return data

    def test_validate_render_and_export_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); data=self.fixture(root)
            self.assertEqual(module.validate(data,root),([],[]))
            module.render(data,root,1)
            text=(root/'storyboard-part-01.html').read_text()
            self.assertIn('camera_timeline',text)
            self.assertIn('red roof',text)
            module.export_studio(data,root)
            self.assertEqual(json.loads((root/'reference.json').read_text())['shots'][0]['camera_timeline'][0]['movement'],'unknown')

    def test_bad_reference_time_bbox_and_unseen_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); data=self.fixture(root); shot=data['shots'][0]
            shot['object_instances'][0].update(object_id='missing',bbox=[.9,.1,.5,.5])
            shot['camera_timeline'][0]['end']=.4
            shot['observations'][0]['frame_ids']=[1]
            errors,gaps=module.validate(data,root)
            self.assertTrue(any('unknown object_id' in x for x in errors))
            self.assertTrue(any('bbox' in x for x in errors))
            self.assertTrue(any('invalid time' in x for x in errors))
            self.assertTrue(any('not listed as inspected' in x for x in gaps))

if __name__=='__main__': unittest.main()
