import sys; import os
from datetime import datetime
import requests
from collections import OrderedDict

import bs4

from models import (AudioData, AudioDataBunch, TranscriptData, TranscriptSection, SectionBunch)
from scraping import SeleniumSpider

class OyezAudioData(AudioData):
    def __init__(self, cache_dir=''):
        super().__init__(cache_dir=cache_dir)
        self.raw_url = None
    
    def _clean_url(self, raw_url):
        return raw_url.replace('/', '?s?')


    def _unclean_url(self, clean_url):
        return clean_url.replace('?s?', '/')

    def download(self, url):
        self.raw_url = url
        clean_url = self._clean_url(raw_url=self.raw_url)
        fp = os.path.join(self.cache_dir, clean_url)
        
        if clean_url in os.listdir(self.cache_dir):
            self.load_wav(fp=os.path.join(self.cache_dir, clean_url))

        else:
            with requests.Session() as session:                                                     
                audio_bytes = session.get(url).content

            with open(fp, 'wb') as f:
                f.write(audio_bytes)
                                      
            del audio_bytes
            self.load_wav(fp=clean_url)


class OyezAudioDataBunch(AudioDataBunch):
    def __init__(self):
        super().__init__()
        
        
    def create(self, url=None, transcript_fp=None, transcript_dirpath='transcripts', 
                      audio_dirpath='full_audios'):
        self.transcript = OyezTranscriptData(
            cache_dir=transcript_dirpath, url=url, fp=transcript_fp
        )
        self.transcript.download()
        audio_url = self.transcript.get_audio_url(codec='mp3')
        self.audio_data = OyezAudioData(cache_dir=audio_dirpath)
        self.audio_data.download(url=audio_url)
        self.bunch_sections = []
        for section in self.transcript.transcript:
            s = SectionBunch()
            s.create(
                transcript_section=section, parent_audio_data=self.audio_data
            )
            self.bunch_sections.append(s)
            
        del audio_url
    
    
class OyezTranscriptData(TranscriptData):
    def __init__(self, cache_dir='transcripts', fp=None, url=None):
        self.url_fmt = 'https://apps.oyez.org/player/#/roberts10/oral_argument_audio/{}'
        self.fn_fmt = '{}_transcript.pickle'
        self.cache_dir = cache_dir
        super().__init__()
        if not fp and not url:
            raise Exception('TranscriptData requires either an url or fp.')
        if not fp:
            self.url = url
            self.oyez_id = self.id_from_url(url=url)
            self.fn = self.fn_fmt.format(self.oyez_id)
            self.fp = os.path.join(self.cache_dir, self.fn)
        elif not url:
            self.fp = fp
            self.fn = self.fp.split('/')[-1]
            self.oyez_id = self.id_from_fp(fp=fp)
            self.url = self.url_fmt.format(self.oyez_id)
                    
    
    def id_from_fp(self, fp):
        return int(fp.split('/')[-1].split('_')[0])

    
    def id_from_url(self, url):
        return int(url.split('/')[-1])
    
    
    def download(self):
        """
        Scrape the url to download the transcript.
        
        In:
            url: str, a url to the transcript
        Returns:
            None
            
        """
        try:
            data = self.get(transcript_fp=self.fp)
            self.failures = data['failures']
            self.transcript = data['transcript']
            self.files = data['files']
            del data
            
        except:
            mun = SeleniumSpider(
                driver_fp=self.driver_fp, 
                url_to_crawl=self.url
            )
            mun.parse(how='all', wait=3.5)
            self.parse(
                doc=bs4.BeautifulSoup(mun.data, 'html.parser')
            )
            del mun
            self.write()
            
    def write(self):
        """
        Save transcript data to fn
        
        In:
            fn: str, a local filepath to write to
            
        Returns:
            None
        """
        # TODO: deprecate this data structure to a simple list.
        ordered_transcript = OrderedDict({'{tx}{s}{st}'.format(
            tx=t.section['transcript'], s=t.section['start_time'], st=t.section['stop_time']
        ): t for t in self.transcript})
        super().write(data={
            'failures': self.failures,
            'transcript': ordered_transcript,  # does this work to pick all these objects?
            'files': self.files
        })
        
        
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
                        section.create(section={
                            'raw': paragraph, 
                            'case_name': case_name,
                            'conv_date': conv_date,
                            'speaker': speaker, 
                            'start_time': paragraph['start-time'],
                            'stop_time': paragraph['stop-time'],
                            'transcript': paragraph.get_text()
                        })
                        self.transcript.append(section)
                    
                    except Exception as e:
                        self.failures.append(paragraph)
        
        
class OyezTranscriptSection(TranscriptSection):
    
    def __init__(self):
        super().__init__()
        self.date_fmt = '%B %d, %Y'
        self.section = None
    
    
    def create(self, section):
        self.section = section
        self.section['conv_date'] = datetime.strptime(self.section['conv_date'], self.date_fmt)
