# Meeting Summarization

## Environment
- >Python3.6
- pipenv

## Installation (Voice Identity)
```python
git clone https://github.com/free-soellingeraj/boringppl-meeting-summarization.git
cd boringppl-meeting-summarization
pipenv install
rclone config # follow instructions configure your google drive
rclone sync "your-rlcone-drive-name:voice-identity-models/dataset/oyez/full_audios/" "full_audios" --drive-shared-with-me
rclone sync "your-rlcone-drive-name:voice-identity-models/dataset/oyez/transcripts/" "transcripts" --drive-shared-with-me
```

## Voice identity modeling
The task is to develop a capability of voice identification.  The most successful voice identity model or model system will associate each "utterance" in the audio with the person who made the utterance ("speaker").  
Please see the file `voice-identity-modeling/Design` document.

### Oyez Dataset
The "Oyez dataset" is comprised of 1000s of recordings of US Supreme Court oral proceedings.  This dataset enables us to do a variety of experiments in automated conversational analysis in a somewhat controlled environment.  For more information, see: https://www.oyez.org/about  

See `voice-identity-modeling/oyez`  

#### Data Access
First you will need to download the `transcripts` and `full_audios` folders to the directory of your choosing.  I recommend using rclone (https://rclone.org/) to interact with google drive.  See the file called `rclone_access_examples`  

Note: the transcripts folder is currently >2GB compressed.  It will take some time to get them all.

See `example_data_access.ipynb`  
That example expects a directory structure as follows:
```
root
    |- example_data_access.ipynb
    |- full_audios/
    |- transcripts/
```
where seed data from the directories can be found in the google drive folder.

#### Sourcing the Oyez dataset
To source the dataset, we found that the transcripts were embedded in dynamically populated html documents.  A selenium script was constructed (see: path/to/script) to load the page and extract the transcripts.  These documents are minimally structured and indexed in files called "{}_tranny.pickle"  
The script will explore the urls from  
https://apps.oyez.org/player/#/roberts10/oral_argument_audio/12989  
to  
https://apps.oyez.org/player/#/roberts10/oral_argument_audio/25052  

##### Characteristics of transcript files 
1) filename: {OyezRecordingId}_tranny.{compression}  
2) file contents
  - failures: list of failed TranscriptSections (see below definition)
  - transcript: (chronologically) OrderedDict (key: md5(TranscriptSection.transcript+TranscriptSection.start_time+TranscriptSection.stop_time), values: TranscriptSection)
  - files: list of audio files for audio sourcing

3) TranscriptSection: a data object that occurs when a new speaker speaks in the conversation
  semantic key: md5(TranscriptSection.transcript+TranscriptSection.start_time+TranscriptSection.stop_time)
  - raw: html from which data was extracted
  - case_name: String, the title of the court case associated with the overall recording
  - conv_type: String, the type of oral proceeding 
  - conv_date: Date, on which the proceeding took place
  - speaker: String, the individual who is speaking "speaker"
  - start_time: String, a floating number that locates the beginning of the TranscriptSection.transcript in the audio
  - stop_time: String, a floating number that locates the end of the TranscriptSection.transcript in the audio

#### Gaps in Dataset
The Oyez dataset has limitations as compared to the kind of challenges that would exist in the real-world (e.g. zoom calls)
1) Highly structured conversation eliminating interruptions, cross-talk, most utterances (huh, uh huh, ya, and, ...)
2) Recordings were post processed with enhanced digital filtering by Oyez to improve sound quality
3) The field conv_date is not precise, instead it states the day.  Therefore, "real-time" conversation linking to external datasources is not possible in a realistic way.


### Using Selenium to scrape

#### Setup
Downloaded and installed selenium with pip
Downloaded the chromedriver from https://sites.google.com/a/chromium.org/chromedriver/home
Ran `xattr -d com.apple.quarantine /Users/free-soellingeraj/Downloads/chromedriver`
Then it's possible to pass that path into the MuncherySpider
