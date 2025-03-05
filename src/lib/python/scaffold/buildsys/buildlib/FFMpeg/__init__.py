
import os

import scaffold.variant

from .. import ThirdbaseLib
from ... import util as buildsys_util


class FFMpegLib(ThirdbaseLib):
    
    def _GetFFMpegDir(self, thirdparty_libs):

        ffmpeg_version = buildsys_util.get_required_thirdparty_version(
            thirdparty_libs, 'FFMpeg')

        if scaffold.variant.get_variant('platform_target') == 'wasm_32':
            ffmpeg_version += '_wasm'

        if os.name == 'nt':
            ffmpeg_version = '4.4.1'

        return os.path.join(self.thirdbase_dir, 'FFMpeg', ffmpeg_version)


    def init(self, benv):
        
        env = benv.env
        
        env['FFMPEGDIR'] = self._GetFFMpegDir(benv.required_thirdparty_libs)
        
        env['CPPPATH'].extend([os.path.join(env['FFMPEGDIR'], 'include')])
        env['LIBPATH'].extend([os.path.join(env['FFMPEGDIR'], 'lib')])
        # env['RPATH'].extend(env['LIBPATH'])
        env['LIBS'].extend(['avcodec',
                            'avdevice',
                            'avfilter',
                            'avformat',
                            'avutil',
                            'swresample',
                            'swscale'])

class WasmFFMpegLib(FFMpegLib):

    def init(self, benv):

        env = benv.env
        env['FFMPEGDIR'] = self._GetFFMpegDir(benv.required_thirdparty_libs)
        
        env['CPPPATH'].extend([os.path.join(env['FFMPEGDIR'], 'include')])
        env['LIBPATH'].extend([os.path.join(env['FFMPEGDIR'], 'lib')])
        
        if benv.build_type == 'binary_executable':
            for lib_entry in [
                'lib/libavcodec.a',
                'lib/libavdevice.a',
                'lib/libavformat.a',
                'lib/libavfilter.a',
                'lib/libavutil.a',
                'lib/libswresample.a',
                'lib/libswscale.a'
            ]:
                env['LINKFLAGS'].append(os.path.join(env['FFMPEGDIR'], lib_entry))
            

class DarwinFFMpegLib(FFMpegLib):

    def _GetFFMpegDir(self, thirdparty_libs):
        
        ffmpeg_version = buildsys_util.get_required_thirdparty_version(
            thirdparty_libs, 'FFMpeg')
        
        return os.path.join(self.thirdbase_dir, 'ffmpeg', ffmpeg_version)


class IOSFFMpegLib(FFMpegLib):

    def _GetFFMpegDir(self, thirdparty_libs):

        ffmpeg_version = buildsys_util.get_required_thirdparty_version(
            thirdparty_libs, 'FFMpeg')

        return os.path.join(self.thirdbase_dir, 'FFMpeg', 'ios')
    
    def init(self, benv):

        env = benv.env
        ffmpeg_dir = self._GetFFMpegDir(benv.required_thirdparty_libs)

        # for avlib in [
        #     'libavcodec',
        #     'libavdevice',
        #     'libavformat',
        #     'libavfilter',
        #     'libavutil',
        #     'libswresample',
        #     'libswscale'
        # ]:
        #     # env['FRAMEWORKS'].append(avlib)
        #     env['CPPPATH'].append(
        #         os.path.join(ffmpeg_dir, '{}.framework'.format(avlib), 'Headers')
        #     )

        # env['FRAMEWORKPATH'].append(ffmpeg_dir)
        env['CPPPATH'].append(
            os.path.join(ffmpeg_dir, 'FFmpeg-static-master', 'include')
        )



PLATFORM_MAP = \
[{'variants': {'platform_target': 'wasm_32'},
  'result': WasmFFMpegLib},
 {'variants':{'opsys':'Linux'},
  'result':FFMpegLib},
 {'variants': {'platform_target': 'ios'},
  'result':IOSFFMpegLib},
 {'variants':{'opsys':'Darwin'},
  'result':DarwinFFMpegLib},
 {'variants':{'opsys':'Windows'},
  'result':FFMpegLib}]
