#!/usr/bin/env python3
"""Local video evidence preparation and 3JsStudio handoff. Python 3.10+."""
import argparse
import base64
import bisect
import html
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(result.stderr[-3000:])
    return result


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def timestamp(value):
    h, m, s = value.replace(',', '.').split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def subtitles(path):
    if path is None:
        return []
    result = []
    for block in re.split(r'\n\s*\n', path.read_text(encoding='utf-8-sig').strip()):
        lines = block.splitlines()
        match = next((i for i, line in enumerate(lines) if '-->' in line), None)
        if match is None:
            raise ValueError('Invalid SRT cue')
        a, b = lines[match].split('-->')
        start, end = timestamp(a.strip()), timestamp(b.strip())
        if end <= start or start < 0:
            raise ValueError('Invalid subtitle interval')
        result.append(dict(line=len(result)+1, who='narrator', text=' '.join(lines[match+1:]),
                           start=start, end=end, dur=end-start, source='reference-srt'))
    return result


def probe(video):
    data = json.loads(run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                          '-show_streams', '-show_frames', '-show_entries',
                          'stream=width,height,avg_frame_rate,r_frame_rate:frame=best_effort_timestamp_time,pkt_duration_time',
                          '-of', 'json', str(video)]).stdout)
    stream = data['streams'][0]
    frames = data['frames']
    raw = [float(f['best_effort_timestamp_time']) for f in frames]
    times = [t-raw[0] for t in raw]
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Non-increasing frame timestamps')
    rate = stream['avg_frame_rate'].split('/')
    fps = int(rate[0])/int(rate[1])
    tail = float(frames[-1].get('pkt_duration_time', 0)) or 1/fps
    return dict(filename=video.name, width=stream['width'], height=stream['height'],
                fps=fps, frame_count=len(times), duration=times[-1]+tail,
                frame_times=times, timestamp_origin=raw[0])


def prepare(args, dest):
    video = args.video.resolve()
    meta = probe(video)
    times = meta['frame_times']
    detection = run(['ffmpeg', '-hide_banner', '-i', str(video), '-vf',
                     f"select='gt(scene,{args.threshold})',showinfo", '-an', '-f', 'null', '-'])
    cut_times = [float(t) for t in re.findall(r'pts_time:([\d.]+)', detection.stderr)]
    # FFmpeg input timestamps normally start at zero; match decoded reference timestamps.
    bounds = [0]
    for t in cut_times:
        index = min(range(max(0, bisect.bisect_left(times,t)-1), min(len(times),bisect.bisect_left(times,t)+1)),
                    key=lambda i: abs(times[i]-t)) if t <= times[-1] else len(times)-1
        if index > bounds[-1] and times[index]-times[bounds[-1]] >= args.min_shot:
            bounds.append(index)
    if len(bounds)>1 and meta['duration']-times[bounds[-1]] < args.min_shot:
        bounds.pop()
    bounds.append(len(times))
    lines = subtitles(args.srt)
    shots = []
    indices = set()
    for number, (a,b) in enumerate(zip(bounds,bounds[1:]),1):
        end = times[b] if b<len(times) else meta['duration']
        refs = sorted(set([a,(a+b-1)//2,b-1]))
        indices.update(refs)
        shots.append(dict(id=f's{number:03}', start_frame=a, end_frame_exclusive=b,
                          start=times[a],end=end,dur=end-times[a], references=refs,
                          lines=[c['line'] for c in lines if c['start']<end and c['end']>times[a]],
                          status='candidate', type=None, at=None, who=None,
                          description='', camera='', action='', lighting='', continuity='',
                          evidence=[], reconstruction={}, sfx=[]))
    if args.all_frames:
        indices = set(range(len(times)))
    fd = dest/'frames'
    fd.mkdir()
    ordered = sorted(indices)
    terms = [f'eq(n\\,{i})' for i in ordered]
    # Balance the expression tree to avoid FFmpeg parser recursion limits.
    while len(terms) > 1:
        terms = ['(' + '+'.join(terms[i:i+2]) + ')' for i in range(0, len(terms), 2)]
    select = '1' if args.all_frames else terms[0]
    filter_file = dest/'filter.txt'
    filter_file.write_text(f'select={select},scale={args.width}:-2', encoding='utf-8')
    run(['ffmpeg','-v','error','-i',str(video),'-filter_script:v',str(filter_file),
         '-fps_mode','passthrough','-start_number','0','-q:v','5',str(fd/'%08d.jpg')])
    filter_file.unlink()
    extracted = sorted(fd.glob('*.jpg'))
    if len(extracted)!=len(ordered):
        raise ValueError('Extracted image count differs from selected frame count')
    for path,index in zip(extracted,ordered):
        path.rename(fd/f'f{index:08d}.jpg')
    data = dict(schema_version=1, source=meta, subtitles=lines, shots=shots,
                actors={}, places={}, warnings=['Cut boundaries are candidates. Visual descriptions require AI/human review.'])
    if any(c['end']>meta['duration'] for c in lines):
        data['warnings'].append('Some subtitle cues extend beyond the video. Preserve and review source timing.')
    write_json(dest/'analysis.json',data)
    render(data,dest,args.max_mb)


def render(data, folder, max_mb):
    limit = int(max_mb*1_000_000)
    header = '<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CoKiBan storyboard</title><style>body{background:#142031;color:#edf3fa;font:16px/1.6 system-ui;max-width:1100px;margin:auto;padding:20px}article{border:1px solid #526477;padding:16px;margin:16px 0;border-radius:12px}.frames{display:flex;gap:12px;overflow:auto}figure{margin:0}img{width:180px}pre{white-space:pre-wrap}small{color:#b5c9de}</style><h1>CoKiBan · Storyboard</h1><p>Điểm cắt tự động là ứng viên. Nội dung còn trống cần AI hoặc người dựng bổ sung.</p>'
    cards=[]
    for shot in data['shots']:
        card=f'<article id="{shot["id"]}"><h2>{shot["id"]} · {shot["start"]:.3f}–{shot["end"]:.3f}s</h2><p>F{shot["start_frame"]}–F{shot["end_frame_exclusive"]-1} · {html.escape(shot["status"])}</p><div class="frames">'
        for f in shot['references']:
            blob=base64.b64encode((folder/'frames'/f'f{f:08d}.jpg').read_bytes()).decode()
            card+=f'<figure><img src="data:image/jpeg;base64,{blob}"><figcaption>F{f} · {data["source"]["frame_times"][f]:.3f}s</figcaption></figure>'
        card+='</div>'
        for field in ['description','camera','action','lighting','continuity']:
            card+=f'<p><b>{field}</b> {html.escape(shot.get(field) or "Chưa phân tích")}</p>'
        card+='<p>'+html.escape(' '.join(c['text'] for c in data['subtitles'] if c['line'] in shot['lines']))+'</p></article>'
        cards.append(card)
    pages=[]
    page=header
    for card in cards:
        if len((header+card+'</html>').encode())>limit:
            raise ValueError('One shot exceeds HTML size limit; reduce --width or increase --max-mb')
        if len((page+card+'</html>').encode())>limit:
            pages.append(page+'</html>');page=header
        page+=card
    pages.append(page+'</html>')
    # Only replace files owned by this exporter after successful size checks.
    for old in folder.glob('storyboard-part-*.html'):
        old.unlink()
    for i,page in enumerate(pages,1):
        (folder/f'storyboard-part-{i:02}.html').write_text(page,encoding='utf-8')


def export_studio(data, dest):
    shots=[]
    unresolved=[]
    allowed={'establish','crowd','walkBy','follow','closeup','reaction','overShoulder','insert','chase','reveal','dialogue'}
    for s in data['shots']:
        kind=s.get('type')
        if kind not in allowed:
            kind='establish';unresolved.append(s['id'])
        item=dict(id=s['id'],dur=s['dur'],type=kind)
        for key in ['at','who','sfx']:
            if s.get(key):item[key]=s[key]
        if len(s['lines'])==1:item['line']=s['lines'][0]
        shots.append(item)
    episode=dict(seed=7,rule='',twist='',actors=data.get('actors',{}),places=data.get('places',{}))
    (dest/'episode.js').write_text('export const EPISODE = '+json.dumps(episode,ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
    (dest/'shots.js').write_text('export const SHOTS = '+json.dumps(shots,ensure_ascii=False,indent=2)+';\n',encoding='utf-8')
    narration=dict(dry=True,total=data['source']['duration'],timing_source='reference-srt',lines=data['subtitles'])
    write_json(dest/'narration.json',narration)
    (dest/'narration.txt').write_text('\n'.join(c['text'] for c in data['subtitles']),encoding='utf-8')
    write_json(dest/'reference.json',data)
    write_json(dest/'integration-status.json',dict(status='draft',fallback_shot_types=unresolved,
               reviewed_shots=sum(s.get('status')=='reviewed' for s in data['shots']),
               narration_audio_available=False, target='3JsStudio',target_revision='a9c33b3834cd1c0e95b7ebddc9a05e845a885237'))
    (dest/'HANDOFF.md').write_text('''# CoKiBan → 3JsStudio

Read the target CLAUDE.md and HANDOFF.md first. Review reference.json and storyboard images.
The JS exports match the documented EPISODE/SHOTS shape. This is a draft data handoff.
Complete actors, places, rule, twist, shot type, camera, animation and continuity from evidence.
Fallback types and missing narration audio are in integration-status.json.
Subtitles may cross shots; reference.json preserves the complete many-to-many mapping.
The line field is emitted only for a single intersecting cue. Do not use shot.text for subtitles.
Reference timing comes from video/SRT. dry=true means no synthesized audio is supplied.
If using the target TTS workflow, regenerate narration timing and retime shots explicitly.
At inspected revision the target stage.js, timeline.js, shots.js engine and HyperFrames
composition still need implementation. Do not claim this bundle already renders a movie.
Use existing R6 + winter modules. Drive animation from hf-seek time, seeded randomness,
window.THREE and loading readiness. Support renderAt(t), __ready and capture mode for snap.js.
Keep source evidence separate from reconstruction estimates. Review camera values visually.
''',encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('analyze');a.add_argument('video',type=Path);a.add_argument('--srt',type=Path)
    a.add_argument('--out',required=True,type=Path);a.add_argument('--threshold',type=float,default=.27)
    a.add_argument('--min-shot',type=float,default=.15);a.add_argument('--width',type=int,default=240)
    a.add_argument('--all-frames',action='store_true');a.add_argument('--max-mb',type=float,default=25)
    r=sub.add_parser('render');r.add_argument('analysis',type=Path);r.add_argument('--max-mb',type=float,default=25)
    e=sub.add_parser('export-3js');e.add_argument('analysis',type=Path);e.add_argument('--out',required=True,type=Path)
    args=p.parse_args()
    try:
        if hasattr(args,'max_mb') and (not math.isfinite(args.max_mb) or args.max_mb<=0):
            raise ValueError('--max-mb must be positive')
        if args.command=='render':
            render(json.loads(args.analysis.read_text(encoding='utf-8')),args.analysis.parent,args.max_mb);return
        if args.out.exists():
            raise ValueError('Output already exists; choose a new directory to preserve prior work')
        args.out.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=args.out.parent,prefix='.cokiban-') as tmp:
            stage=Path(tmp)/'result';stage.mkdir()
            if args.command=='analyze':
                if not 0<args.threshold<1 or args.min_shot<0 or args.width<32:
                    raise ValueError('Invalid threshold, min-shot or image width')
                for tool in ['ffmpeg','ffprobe']:
                    if not shutil.which(tool):raise ValueError(f'Missing {tool}')
                prepare(args,stage)
            else:
                export_studio(json.loads(args.analysis.read_text(encoding='utf-8')),stage)
            stage.rename(args.out)
        print(args.out)
    except (ValueError,KeyError,OSError,subprocess.CalledProcessError) as exc:
        p.exit(1,f'Error: {exc}\n')


if __name__=='__main__':
    main()
