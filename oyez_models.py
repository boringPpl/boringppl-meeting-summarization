import sys; import os
from models import (AudioData, AudioDataBunch, TranscriptData, TranscriptSection, SectionBunch)


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
        for _, section in self.transcript.transcript.items():
            s = SectionBunch()
            s.create(
                transcript_section=section, parent_audio_data=self.audio_data
            )
            self.bunch_sections.append(s)
            
        del audio_url
    
    
class OyezTranscriptData(TranscriptData):
    def __init__(self, cache_dir='transcripts', fp=None, url=None):
        self.url_fmt = 'https://apps.oyez.org/player/#/roberts10/oral_argument_audio/{}'
        self.fn_fmt = '{}_tranny.pickle'
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
            
        self.failures = None
        
    
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
            mun = TranscriptSpider(
                driver_fp=self.driver_fp, 
                url_to_crawl=self.url
            )

            mun.parse()
            self.parse(
                doc=bs4.BeautifulSoup(mun.data, 'html.parser')
            )
            del mun
                
            
    def write(self, fn):
        """
        Save transcript data to fn
        
        In:
            fn: str, a local filepath to write to
            
        Returns:
            None
        """
        self.fp = os.path.join(dirpath, fn)
        super().write(fn=fn, data={
            'failures': failures,
            'transcript': transcript,  # does this work to pick all these objects?
            'files': files
        })
        
        
class OyezTranscriptSection(TranscriptSection):
    
    def __init__(self):
        super().__init__()
        self.date_fmt = '%B %d, %Y'
        self.section = None
    
    
    def create(self, section):
        self.section = section
        self.section['conv_date'] = datetime.strftime(self.section['conv_date'], self.date_fmt)
