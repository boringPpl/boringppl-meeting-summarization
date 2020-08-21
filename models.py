import sys; import os
import requests
import pickle
import subprocess
import hashlib
from collections import OrderedDict

import torch
import torchaudio
from bs4 import BeautifulSoup
        

class AudioData:
    def __init__(self, cache_dir=''):
        """
        In:
            cache_dir: str, path to local files

        """
        self.cache_dir = cache_dir # str
        self.waveform = None # torch.Tensor
        self.sample_rate = None # int
        
    
    def slice_waveform(self, start_sec, close_sec):
        """"""            
        s = round(start_sec*self.sample_rate)
        c = round(close_sec*self.sample_rate)
        slc = AudioData(cache_dir='temp')
        slc.waveform = self.waveform[:, s:c]
        slc.sample_rate = self.sample_rate
        return slc
    
    
    def write_wav(self, fp):
        """
        Writes torchaudio file to wav format.

        In:
            fp: str, path to write

        Returns:
            None
        """
        scipy.io.wavfile.write(
            filename=fp,
            rate=self.sample_rate,
            data=self.waveform.numpy().transpose()
        )
        
    def load_wav(self, fp):
        """
        Loads wav data from file.
        
        In:
            fp: str, path to wav file
            
        Returns:
            None
        """
        self.waveform, self.sample_rate = torchaudio.load(fp)


class TranscriptData:
    def __init__(self):
        """"""
        self.transcript = []
        self.files = []
        self.driver_fp = '/Users/free-soellingeraj/Downloads/chromedriver'
        
    def get_audio_url(self, codec='mp3'):
        """"""
        if not self.transcript:
            raise Exception('No transcript available.')
            
        if not self.files:
            raise Exception('No files available in transcript.')
            
        for url in self.files:
            if codec in url:
                return url
            
        raise Exception(
            'No file found with codec: {}.'.format(codec)
        )
    
    
    def get(self, transcript_fp):
        """"""
        with open(transcript_fp, 'rb') as f:
            return pickle.load(f)
        
        
    
    def write(self, fn, data):
        """
        Save transcript data to fn
        
        In:
            fn: str, a local filepath to write to
            
        Returns:
            None
        """
        with open(self.fp, 'wb') as fout:
            pickle.dump(data, fout)
        
    
    def parse(self, doc):
        """
        Parses raw html doc containing oyez transcript.
        
        In:
            doc: BeautifulSoup, html document
        
        Returns:
            None, writes to self.transcript, self.failures, self.files
            
        """
        sys.setrecursionlimit(50000)
        self.files = [
            thing['src'] 
            for thing 
            in doc.find_all('audio')[0].find_all('source')
        ]
        for article in doc.find_all('article'):
            case_name = article.find('h1').get_text()
            t = article.find('h2').get_text().split(' - ')
            conv_type = t[0]
            conv_date = t[1]
            for section in article.find_all('section'):
                speaker = section.find('h4').get_text()
                for paragraph in section.find_all('p'):
                    try:
                        section = OyezTranscriptSection()
                        section.create(
                            raw=paragraph, 
                            case_name=case_name,
                            conv_name=conv_name,
                            conv_date=conv_date,
                            speaker=speaker, 
                            start_time=paragraph['start-time'],
                            stop_time=paragraph['stop-time'],
                            transcript=paragraph.get_text()
                        )
                        self.transcript.append(section)
                    
                    except:
                        self.failures.append(paragraph)
                        
                        
class AudioDataBunch:
    def __init__(self):
        """"""
        self.transcript = None
        self.audio_data = None
        self.bunch_sections = []
    
    
class TranscriptSection:
    def __init__(self):
        """
        transcript_section.keys(): 
            ['raw', 'case_name', 'conv_type', 'conv_date', 
             'speaker', 'start_time', 'stop_time', 'transcript']
             
        """
        self.raw = None
        self.parent_transcript = None
        self.conv_type = None
        self.conv_date = None
        self.speaker = None
        self.start_time = None
        self.stop_time = None
        self.text = None
        
        
    def write_text(fp):
        """
        Writes transcript text to txt file.

        In: 
            fp: str, path to write

        Returns:
            None
        """
        with open(fp, 'w') as f:
            f.write(self.text)
        

class ForceAlignedSection:
    
    def __init__(self):
        """"""
        path_to_gentle = '/Users/free-soellingeraj/code/gentle/align.py'
    
    def force_align(tempdir, outdir, section_id, transcript_text, 
            audio_section, sample_rate):
        """
        Force aligns transcript_text with audio waveform (audio_section).

        Requires: lowerquality/gentle following installation procedures.

        In:
            tempdir: str, path that runtime has access to for temp storage.
            outdir: str, path that the force-aligned output will be written
            section_id: str, 
                {case_name}_{conv_type}_{speaker}_{start_time}_{stop_time}
            transcript_text: str, transcription to align
            audio_section: torch.Tensor,
                audio waveform that contains transcription_text
            sample_rate: 

        Note: process writes 2 temp files.  1 wav and 1 txt.

        TODO: add log lines
        """
        wav_fp = os.path.join(tempdir, 'temp_'+section_id+'.wav')
        txt_fp = os.path.join(tempdir, 'temp_'+section_id+'.txt')
        out_fp = os.path.join(outdir, section_id+'.json')
        if os.path.exists(out_fp): return

        write_wav(
            fp=wav_fp, 
            sample_rate=sample_rate, 
            audio_section=audio_section
        )
        write_transcript_section(
            fp=txt_fp,
            transcript_text=transcript_text
        )
        cmd = ['python3', 
               self.path_to_gentle,
               wav_fp, txt_fp, '-o', out_fp]
        var = subprocess.call(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        os.remove(wav_fp)
        os.remove(txt_fp)
        return var
    

class SectionBunch:
    def __init__(self):
        self.transcript_section = None
        self.audio_data = None
    
    def create(self, transcript_section, parent_audio_data):
        self.transcript_section = transcript_section
        self.audio_data = parent_audio_data.slice_waveform(
            start_sec=float(self.transcript_section['start_time']),
            close_sec=float(self.transcript_section['stop_time'])
        )