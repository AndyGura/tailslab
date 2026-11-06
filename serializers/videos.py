import subprocess
from typing import List

from config import general_config
from serializers import BaseFileSerializer


class FfmpegSupportedVideoSerializer(BaseFileSerializer):
    def serialize(self, data: dict, path: str, id=None, block=None, **kwargs) -> List[str]:
        super().serialize(data, path)
        output_path = f'{path}.mp4'
        subprocess.run(
            [
                general_config().ffmpeg_executable,
                '-y',
                '-nostats',
                '-loglevel',
                '0',
                '-i',
                data,
                # transparent pixels black (they display wrong in Chrome), keeping the video's own frame rate (TNFS's
                # TGVs are 15 fps; a black `color` source under it made them 25 fps, repeating frames unevenly)
                '-vf',
                'format=rgba,premultiply=inplace=1,setsar=1',
                '-c:v',
                'libx264',
                # AAC: iOS plays MP3 audio in an MP4 as silence (the picture plays, no sound); Chrome and Firefox
                # play both
                '-c:a',
                'aac',
                '-vprofile',
                'main',
                '-pix_fmt',
                'yuv420p',
                output_path,
            ],
            check=True,
        )
        return [output_path]
