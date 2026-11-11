"""Structured visual annotations, evidence checks and schema migration."""
from pathlib import Path


def upgrade(data):
    """Add v2 fields without overwriting existing descriptions or observations."""
    if data.get('schema_version', 1) not in (1, 2):
        raise ValueError('Unsupported analysis schema version')
    data['schema_version'] = 2
    data.setdefault('objects', {})
    data.setdefault('review', {'inspected_frames': [], 'note': ''})
    for shot in data['shots']:
        shot.setdefault('object_instances', [])
        shot.setdefault('motion_events', [])
        shot.setdefault('camera_timeline', [])
        shot.setdefault('observations', [])
    return data


def validate(data, folder):
    """Return errors and review gaps; never turn uninspected frames into claims."""
    errors, gaps = [], []
    times = data['source']['frame_times']
    total = len(times)
    objects = data.get('objects', {})
    if not isinstance(objects, dict):
        return ['objects must be a dictionary keyed by ID'], []
    ids = set(objects)
    inspected = data.get('review', {}).get('inspected_frames', [])
    if not isinstance(inspected, list):
        return ['review.inspected_frames must be a list'], []
    seen = set()
    def frames(values, label, lo=0, hi=None):
        if not isinstance(values, list):
            errors.append(label + ': frame_ids must be a list'); return
        for f in values:
            if type(f) is not int or not 0 <= f < total or not lo <= f < (total if hi is None else hi):
                errors.append(f'{label}: invalid frame {f!r}'); continue
            if not (folder/'frames'/f'f{f:08d}.jpg').is_file():
                errors.append(f'{label}: frame {f} was not extracted')
            seen.add(f)
    frames(inspected, 'review.inspected_frames')
    for oid, obj in objects.items():
        if not isinstance(obj, dict):
            errors.append(f'object {oid}: expected object'); continue
        frames(obj.get('frame_ids', []), f'object {oid}')
        if not obj.get('description'):
            gaps.append(f'object {oid}: missing description')
    for s in data['shots']:
        sid = s['id']; lo=s['start_frame']; hi=s['end_frame_exclusive']
        if not 0 <= lo < hi <= total:
            errors.append(f'{sid}: invalid frame interval'); continue
        for item in s.get('object_instances', []):
            if item.get('object_id') not in ids:
                errors.append(f'{sid}: unknown object_id {item.get("object_id")!r}')
            frames(item.get('frame_ids', []), f'{sid} object', lo, hi)
            box = item.get('bbox')
            if box is not None and (not isinstance(box,list) or len(box)!=4 or any(type(v) not in (int,float) or not 0<=v<=1 for v in box) or box[2]<=0 or box[3]<=0 or box[0]+box[2]>1.000001 or box[1]+box[3]>1.000001):
                errors.append(f'{sid}: bbox must be normalized [x,y,width,height] within image')
        for field in ('camera_timeline', 'motion_events'):
            for event in s.get(field, []):
                start, end = event.get('start'), event.get('end')
                if type(start) not in (int,float) or type(end) not in (int,float) or not s['start'] <= start < end <= s['end']:
                    errors.append(f'{sid} {field}: invalid time interval')
                frames(event.get('frame_ids', []), f'{sid} {field}', lo, hi)
                if field == 'motion_events' and event.get('object_id') not in ids:
                    errors.append(f'{sid}: unknown motion object_id')
        for obs in s.get('observations', []):
            frames(obs.get('frame_ids', []), f'{sid} observation', lo, hi)
            if obs.get('kind') not in ('measured','observed','inferred','reconstruction'):
                errors.append(f'{sid}: invalid observation kind')
            if obs.get('confidence') not in ('low','medium','high'):
                errors.append(f'{sid}: invalid confidence')
            if not obs.get('frame_ids') or not obs.get('text'):
                gaps.append(f'{sid}: observation missing text or evidence')
            if obs.get('kind') == 'observed' and not set(obs.get('frame_ids', [])).issubset(set(inspected)):
                gaps.append(f'{sid}: observed evidence not listed as inspected')
        for field in ('object_instances','camera_timeline','observations'):
            if not s.get(field): gaps.append(f'{sid}: missing {field}')
        if s.get('status') != 'reviewed': gaps.append(f'{sid}: cut/shot not reviewed')
    return errors, gaps
