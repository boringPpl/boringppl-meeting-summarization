import sys; import os
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--transcript_fp', 
        type=str, 
        help='local filepath to a transcript file.'
    )
    parser.add_argument(
        '--audio_dirpath', 
        type=str, 
        help='local filepath to a directory with audio files.'
    )
    args = parser.parse_args()
    
    audio_url, transcript, waveform, sample_rate = \
        get_databunch(
            transcript_fp=args.transcript_fp, 
            audio_dirpath=args.audio_dirpath
    )
    
