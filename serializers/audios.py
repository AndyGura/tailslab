import json
import os
import subprocess
import traceback
import wave
from typing import List, Dict, Tuple

from config import general_config
from library.utils import audio_ima_adpcm_codec, audio_ea_xa_codec, format_exception, path_join
from serializers import BaseFileSerializer


class EacsAudioSerializer(BaseFileSerializer):
    def serialize(self, data: dict, path: str, id=None, block=None, meta: dict = None, **kwargs) -> List[str]:
        super().serialize(data, path)
        wave_bytes = data['wave_data']
        if data['header']['compression'] == 2:
            wave_bytes = audio_ima_adpcm_codec.decode_block(wave_bytes, data['header']['channels'])
        else:
            # signed
            if data['header']['sound_resolution'] == 1:
                wav = list()
                for i in range(len(wave_bytes)):
                    wav.append(int.from_bytes(wave_bytes[i : i + 1], byteorder='little', signed=True) + 128)
                wave_bytes = bytes(wav)
            # unsigned
            else:
                wave_bytes = wave_bytes
        loop_start_time_ms = 1000 * data['header']['repeat_loop_beginning'] / data['header']['sampling_rate']
        loop_end_time_ms = (
            loop_start_time_ms + 1000 * (data['header']['repeat_loop_length'] - 1) / data['header']['sampling_rate']
        )
        self._save_wave_data(data['header'], wave_bytes, path)
        with open(f'{path}.meta.json', 'w') as file:
            file.write(
                json.dumps(
                    {
                        'loop': data['header']['repeat_loop_length'] > 0,
                        'loop_start_time_ms': loop_start_time_ms,
                        'loop_end_time_ms': loop_end_time_ms,
                        **(meta or {}),
                    },
                    indent=4,
                )
            )
        return [f'{path}.wav', f'{path}.meta.json']

    def _save_wave_data(self, eacs_header, wave_data, path):
        with wave.open(f'{path}.wav', 'w') as wf:
            wf.setnchannels(eacs_header['channels'])
            wf.setsampwidth(eacs_header['sound_resolution'])
            wf.setframerate(eacs_header['sampling_rate'])
            wf.writeframesraw(wave_data)


class FfmpegSupportedAudioSerializer(BaseFileSerializer):
    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        super().serialize(data, path)
        wav_path = f'{path}.wav'
        meta_path = f'{path}.meta.json'
        subprocess.run(
            [general_config().ffmpeg_executable, '-y', '-nostats', '-loglevel', '0', '-i', id, wav_path], check=True
        )
        with open(meta_path, 'w') as file:
            loop_start_time_ms = 1000 * data['repeat_loop_beginning'] / data['sampling_rate']
            loop_end_time_ms = loop_start_time_ms + 1000 * data['repeat_loop_length'] / data['sampling_rate']
            file.write(
                json.dumps(
                    {
                        'loop': data['repeat_loop_length'] > 0,
                        'loop_start_time_ms': loop_start_time_ms,
                        'loop_end_time_ms': loop_end_time_ms,
                    },
                    indent=4,
                )
            )
        return [wav_path, meta_path]


def decode_ea_sound_patch_layer(layer: Dict, wave_data: bytes) -> Tuple[bytes, int, int]:
    """Wave data of a layer of `EaSoundPatch` as (PCM bytes, sample width in bytes, channels). 8-bit PCM is unsigned,
    16-bit is signed little endian, as in WAV files"""
    channels = layer.get('channels', 1)
    num_samples = layer['num_samples']
    if layer.get('version', 0) == 0:
        codec = layer.get('codec')
        if codec is None:
            return wave_data[: num_samples * channels * 2], 2, channels
        if codec == 7:
            frames = (num_samples + 27) // 28
            return (
                audio_ea_xa_codec.decode_v1(wave_data[: frames * 0x0F * channels], channels, num_samples),
                2,
                channels,
            )
        raise NotImplementedError(f'Unsupported codec {codec}' + (' (EA MicroTalk)' if codec == 9 else ''))
    codec = layer.get('codec_2')
    if codec == 8:
        return wave_data[: num_samples * channels * 2], 2, channels
    if codec == 9:
        return bytes((x + 128) & 0xFF for x in wave_data[: num_samples * channels]), 1, channels
    if codec is None and channels == 1:
        return audio_ea_xa_codec.decode_v2(wave_data, num_samples), 2, channels
    raise NotImplementedError(f'Unsupported codec {codec} with {channels} channels, header version {layer["version"]}')


class EaSoundBankSerializer(BaseFileSerializer):
    """Every layer of every sound to `<index>.wav` + `<index>.meta.json` (`<index>_layer_<n>` for the second and next
    layers of a sound), index in hex as in TNFS sound banks"""

    # tags, which describe wave data and are not needed next to a wav file
    WAVE_DATA_TAGS = ['data_offset', 'data_offset_channel_2', 'unk_0x8a', 'codec', 'codec_2', 'version']

    def __init__(self):
        super().__init__(is_dir=True)

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        super().serialize(data, path)
        patch_block = block.field_blocks_map['items'].child
        output = []
        skipped = []
        for index, item in zip(block.item_indices(data), data['items']):
            for layer_index, layer in enumerate(patch_block.layers(item)):
                name = hex(index) + (f'_layer_{layer_index}' if layer_index > 0 else '')
                try:
                    output.extend(self._serialize_layer(layer, block.wave_data(data, layer), path_join(path, name)))
                except Exception as ex:
                    traceback.print_exc()
                    skipped.append((name, format_exception(ex)))
        if skipped:
            with open(path_join(path, 'skipped.txt'), 'w') as f:
                for item in skipped:
                    f.write('%s\t\t%s\n' % item)
            output.append(path_join(path, 'skipped.txt'))
        return output

    def _serialize_layer(self, layer: Dict, wave_data: bytes, path: str) -> List[str]:
        pcm, sample_width, channels = decode_ea_sound_patch_layer(layer, wave_data)
        sampling_rate = layer.get('sampling_rate', 22050)
        num_samples = layer['num_samples']
        with wave.open(f'{path}.wav', 'w') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(sampling_rate)
            wf.writeframesraw(pcm)
        meta = {
            **ea_sound_patch_loop_meta(layer, num_samples, sampling_rate),
            **{k: v for k, v in layer.items() if k not in self.WAVE_DATA_TAGS},
        }
        with open(f'{path}.meta.json', 'w') as file:
            file.write(json.dumps(meta, indent=4))
        return [f'{path}.wav', f'{path}.meta.json']


def ea_sound_patch_loop_meta(layer: Dict, num_samples: int, sampling_rate: int) -> Dict:
    """`loop`, `loop_start_time_ms`, `loop_end_time_ms` of a layer of `EaSoundPatch`: a sound loops when it has one of
    `loop_start` / `loop_end` (inclusive sample indices), from 0 / up to the last sample when the other one is missing"""
    is_loop = 'loop_start' in layer or 'loop_end' in layer
    loop_start = layer.get('loop_start', 0) if is_loop else 0
    loop_end = layer.get('loop_end', num_samples - 1) if is_loop else num_samples - 1
    return {
        'loop': is_loop,
        'loop_start_time_ms': 1000 * loop_start / sampling_rate,
        'loop_end_time_ms': 1000 * loop_end / sampling_rate,
    }


def _save_wav(path: str, pcm: bytes, channels: int, sampling_rate: int):
    with wave.open(path, 'w') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sampling_rate)
        wf.writeframesraw(pcm)


def ea_audio_stream_pcm16(chunks: bytes, channels: int) -> bytes:
    """Wave data of the SCDl chunks of an EA audio stream with a version 0 header without codec: each chunk holds the
    amount of samples (4 bytes) and the samples, 16-bit little endian, channels interleaved"""
    res = bytearray()
    pos = 0
    while pos + 8 <= len(chunks):
        chunk_id, size = chunks[pos : pos + 4], int.from_bytes(chunks[pos + 4 : pos + 8], 'little')
        if size < 8:
            break
        if chunk_id == b'SCDl' and size >= 12:
            num_samples = int.from_bytes(chunks[pos + 8 : pos + 12], 'little')
            res += chunks[pos + 12 : min(pos + size, pos + 12 + num_samples * 2 * channels)]
        pos += size
    return bytes(res)


class EaAudioStreamsSerializer(BaseFileSerializer):
    """EA audio streams (`EaAudioStreams`) to WAV, decoded by FFmpeg. One stream: `<name>.wav` + `<name>.meta.json`.
    More streams (`.MUS` interactive music): a folder with `<index>.wav` + `<index>.meta.json` per stream (index of the
    node in the map file next to it, else of the stream in the file) and `playthrough.wav` + `playthrough.meta.json`:
    the nodes as the map plays them from its start node with the music state value `PLAYTHROUGH_STATE_VALUE`, up to
    the first node played again (the loop start) or an end node; all streams in file order when there is no map. The
    map is the `.LIN` file (NFS3: the linear song, one branch per node) when there is one, else the `.MAP` file"""

    PLAYTHROUGH_STATE_VALUE = 50

    def __init__(self):
        # is_dir depends on the data: method below, as in DelegateBlockSerializer
        pass

    def is_dir(self, block, data) -> bool:
        return len(data['streams']) > 1

    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        if path.endswith('/') or path.endswith('\\'):
            path += id.replace('\\', '/').rsplit('/', 1)[-1]
        stream_block = block.field_blocks_map['streams'].child
        streams = data['streams']
        if len(streams) == 1:
            os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
            pcm, channels, sampling_rate, meta = self._decode_stream(stream_block, streams[0])
            _save_wav(f'{path}.wav', pcm, channels, sampling_rate)
            with open(f'{path}.meta.json', 'w') as file:
                file.write(json.dumps(meta, indent=4))
            return [f'{path}.wav', f'{path}.meta.json']
        os.makedirs(path, exist_ok=True)
        map_name, music_map = self._find_music_map(id)
        stream_offsets = []
        offset = 0
        for stream in streams:
            stream_offsets.append(offset)
            offset += stream_block.estimate_packed_size(stream)
        if music_map:
            stream_index_by_offset = {x: i for i, x in enumerate(stream_offsets)}
            node_streams = [stream_index_by_offset.get(x) for x in music_map['stream_offsets']]
        else:
            node_streams = list(range(len(streams)))
        output = []
        skipped = []
        decoded = {}
        for node, stream_index in enumerate(node_streams):
            name = str(node)
            if stream_index is None:
                skipped.append((name, f'No audio stream at offset {music_map["stream_offsets"][node]}'))
                continue
            try:
                pcm, channels, sampling_rate, meta = self._decode_stream(stream_block, streams[stream_index])
            except Exception as ex:
                traceback.print_exc()
                skipped.append((name, format_exception(ex)))
                continue
            decoded[node] = (pcm, channels, sampling_rate, meta)
            _save_wav(path_join(path, f'{name}.wav'), pcm, channels, sampling_rate)
            with open(path_join(path, f'{name}.meta.json'), 'w') as file:
                file.write(json.dumps(meta, indent=4))
            output += [path_join(path, f'{name}.wav'), path_join(path, f'{name}.meta.json')]
        output = self._save_playthrough(path, decoded, map_name, music_map) + output
        if skipped:
            with open(path_join(path, 'skipped.txt'), 'w') as f:
                for item in skipped:
                    f.write('%s\t\t%s\n' % item)
            output.append(path_join(path, 'skipped.txt'))
        return output

    @staticmethod
    def _find_music_map(id: str) -> Tuple[str, Dict]:
        """File name and data of the `.LIN`, else `.MAP` file next to a `.MUS` file (any case), (None, None) for an
        archive item or without one"""
        from library import require_file
        from library.loader import id_to_path

        if not id or '__' in id:
            return None, None
        file_path = id_to_path(id)
        directory, file_name = os.path.split(file_path)
        stem = file_name.rsplit('.', 1)[0].lower()
        try:
            names = os.listdir(directory or '.')
        except OSError:
            return None, None
        for extension in ['lin', 'map']:
            map_name = next((x for x in names if x.lower() == f'{stem}.{extension}'), None)
            if not map_name:
                continue
            try:
                _, map_block, map_data = require_file(path_join(directory, map_name), lazy=False)
            except Exception:
                traceback.print_exc()
                continue
            if map_block.__class__.__name__ == 'EaMusicMap':
                return map_name, map_data
        return None, None

    def _playthrough_nodes(self, music_map, nodes) -> Tuple[List[int], int]:
        """Nodes the map plays and the index in this list of the node it loops to (None without a loop)"""
        if not music_map:
            return sorted(nodes), None
        path = []
        node = music_map['start_node']
        while node not in path and node < len(music_map['nodes']):
            path.append(node)
            map_node = music_map['nodes'][node]
            node = next(
                (
                    b['next_node']
                    for b in map_node['branches'][: map_node['num_branches']]
                    if b['min_value'] <= self.PLAYTHROUGH_STATE_VALUE <= b['max_value']
                ),
                None,
            )
            if node is None:
                return path, None
        return path, path.index(node) if node in path else None

    def _save_playthrough(self, path: str, decoded: Dict, map_name: str, music_map) -> List[str]:
        nodes, loop_index = self._playthrough_nodes(music_map, decoded.keys())
        nodes = [x for x in nodes if x in decoded]
        if not nodes:
            return []
        _, channels, sampling_rate, _ = decoded[nodes[0]]
        frame_size = 2 * channels
        pcm = bytearray()
        loop_start_frame = 0
        for i, node in enumerate(nodes):
            node_pcm, node_channels, node_sampling_rate, _ = decoded[node]
            if (node_channels, node_sampling_rate) != (channels, sampling_rate):
                raise ValueError(f'Node {node} has another format than node {nodes[0]}')
            if i == loop_index:
                loop_start_frame = len(pcm) // frame_size
            pcm += node_pcm
        num_frames = len(pcm) // frame_size
        _save_wav(path_join(path, 'playthrough.wav'), bytes(pcm), channels, sampling_rate)
        meta = {
            'loop': loop_index is not None,
            'loop_start_time_ms': 1000 * loop_start_frame / sampling_rate if loop_index is not None else 0,
            'loop_end_time_ms': 1000 * (num_frames - 1) / sampling_rate,
            'nodes': nodes,
            **({'map': map_name, 'state_value': self.PLAYTHROUGH_STATE_VALUE} if music_map else {}),
        }
        with open(path_join(path, 'playthrough.meta.json'), 'w') as file:
            file.write(json.dumps(meta, indent=4))
        return [path_join(path, 'playthrough.wav'), path_join(path, 'playthrough.meta.json')]

    @staticmethod
    def _decode_stream(stream_block, stream: Dict) -> Tuple[bytes, int, int, Dict]:
        """(16-bit PCM, channels, sampling rate, loop meta) of a stream of `EaAudioStreams`"""
        from resources.eac.audios import EaSoundPatch

        layer = EaSoundPatch.layers(stream['header'])[0]
        if layer.get('codec_2' if layer.get('version', 0) else 'codec') == (4 if layer.get('version', 0) else 9):
            raise NotImplementedError('Unsupported codec EA MicroTalk')
        channels = layer.get('channels', 1)
        sampling_rate = layer.get('sampling_rate', 22050)
        if not layer.get('version', 0) and 'codec' not in layer:
            # 16-bit PCM (NFS3 show1, show3, show4, show5, show7 menu music), which FFmpeg's EA demuxer refuses
            pcm = ea_audio_stream_pcm16(stream['data'], channels)
            num_samples = layer.get('num_samples', len(pcm) // (2 * channels))
            pcm = pcm[: num_samples * 2 * channels]
            return pcm, channels, sampling_rate, ea_sound_patch_loop_meta(layer, num_samples, sampling_rate)
        result = subprocess.run(
            [
                general_config().ffmpeg_executable,
                '-nostats',
                '-loglevel',
                'error',
                '-f',
                'ea',
                '-i',
                'pipe:0',
                '-f',
                's16le',
                '-acodec',
                'pcm_s16le',
                '-ac',
                str(channels),
                '-ar',
                str(sampling_rate),
                'pipe:1',
            ],
            input=stream_block.pack(stream),
            capture_output=True,
        )
        if result.returncode != 0 or not result.stdout:
            raise Exception(f'FFmpeg could not decode the stream: {result.stderr.decode(errors="replace")[-500:]}')
        pcm = result.stdout[: len(result.stdout) - len(result.stdout) % (2 * channels)]
        num_samples = layer.get('num_samples', len(pcm) // (2 * channels))
        return pcm, channels, sampling_rate, ea_sound_patch_loop_meta(layer, num_samples, sampling_rate)
