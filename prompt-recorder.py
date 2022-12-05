# -*- coding: utf-8 -*-


import pyaudio
import wave
import keyboard
import time
import os
import nltk.data
import numpy as np
import pickle
import argparse

def get_valid_sentence(tokenized_text):
    invalid_chars = ['@','#','$','%','^','&','*','(',')',
                     '-','_','=','+','1','2','3','4','5',
                     '6','7','8','9','0','<','>','{','}',
                     '[',']',"\\","/", "\""]

    l = len(tokenized_text)
    
    while True:
        seed = np.random.randint(l)
        a = " ".join(tokenized_text[seed].split("\n"))
        if a != None and len(a) < 500 and not any([i in a for i in invalid_chars]):
            break
    return a

def format_filelist_for_hifigan(path):
    with open(path, encoding="mbcs") as f:
        text = f.readlines()
    path_split = path.split(".")
    if len(path_split) < 2:
        path = path + "_nospeaker"
    else:
        path = ".".join(path_split[:-1])+"_nospeaker."+path_split[-1]
    f = open(path, 'w+')
    for i, line in enumerate(text):
        f.write('|'.join(line.split('|')[:2])+'\n')
    f.close()

def gather_data(wav_dir, fn_prefix, filelist_path, corpus_path, speaker, overwrite_tokenized_corpus=False):
    
    chunk= 128
    sample_format = pyaudio.paInt16
    channels = 1
    fs = 22050
    seconds = 15
    
    if os.path.exists(corpus_path + ".tokenized") or overwrite_tokenized_corpus:
        with open(corpus_path + ".tokenized", 'rb') as config_dictionary_file:

            tokenized_text = pickle.load(config_dictionary_file) 
    else:
        with open(corpus_path, encoding="mbcs") as f:
            text = f.readlines()
        
        txt = []
        record = False
        for line in text:
            
            if 'START' in line and 'PROJECT GUTENBERG' in line:
                record = True
                continue
            elif 'END' in line and 'PROJECT GUTENBERG' in line:
                record = False
            
            if not record:
                continue
            
            txt.append(line)
        txt = ''.join(txt)
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
        tokenized_text = tokenizer.tokenize(txt)  
        with open(corpus_path+'.tokenized', 'wb') as config_dictionary_file:

          pickle.dump(tokenized_text, config_dictionary_file)
    
    ex_files = [i for i in os.listdir(wav_dir) if i.startswith(fn_prefix)]
    
    if ex_files:
        its = [int(i.split('-')[1].split('.')[0]) for i in ex_files]
        it = max(its) + 1
    else:
        it = 1
    
    q = False
        
    while True:
        time.sleep(0.01)
        if q:
            break
        
        sent = get_valid_sentence(tokenized_text)
        
        print(sent)
        print("s: begin/stop recording, n: new sentence, r: restart recording, q: quit")
        
        q = False
        start = False
        retry = False
        while True:
            if keyboard.is_pressed('q'):
                q = True
                start = False
                time.sleep(0.03)
                break
            elif keyboard.is_pressed('s'):
                start = True
                time.sleep(0.03)
                break
            elif keyboard.is_pressed('r'):
                start = True
                time.sleep(0.03)
                break
            elif keyboard.is_pressed('n'):
                retry = True
                time.sleep(0.03)
                break
            
        if q or retry:
            continue
        
        q = False
        if start:
            
            while True:
                time.sleep(0.05)
                if q:
                    break
                
                frames = []
                p = pyaudio.PyAudio()
                stream = p.open(format=sample_format,
                                channels=channels,
                                rate=fs,
                                frames_per_buffer=chunk,
                                input=True)
                q = False
                save = False
                restart = False
                for i in range(0, int(fs / chunk * seconds)):
                    data = stream.read(chunk)
                    frames.append(data)
                    if keyboard.is_pressed('q'):
                        q = True
                        save = False
                        time.sleep(0.03)
                        break
                    elif keyboard.is_pressed('s'):
                        save = True
                        time.sleep(0.03)
                        data = stream.read(chunk)
                        frames.append(data)
                        break
                    elif keyboard.is_pressed('r'):
                        restart = True
                        save = False
                        time.sleep(0.03)
                        break
                    elif keyboard.is_pressed('n'):
                        retry = True
                        time.sleep(0.03)
                        break
        
                time.sleep(0.05)
                stream.stop_stream()
                stream.close()
                p.terminate()
                
                if save:
                    save_fn = fn_prefix+'-'+str(it).zfill(4)+'.wav'
                    filename = os.path.join(wav_dir, save_fn)
                    wf = wave.open(filename, 'wb')
                    wf.setnchannels(channels)
                    wf.setsampwidth(p.get_sample_size(sample_format))
                    wf.setframerate(fs)
                    wf.writeframes(b''.join(frames))
                    wf.close()
                    
                    newline = save_fn+'|'+sent+'|'+speaker
                    f = open(filelist_path, "a+")
                    f.write("\n"+newline)
                    f.close()
                    
                    it += 1
                    time.sleep(0.05)
                    break
                    
                if q or retry:
                    time.sleep(0.05)
                    break
                
                    
        if q:
            print("press q to quit, or s to continue")
            while True:
                if keyboard.is_pressed('q'):
                    q = True
                    break
                elif keyboard.is_pressed('s'):
                    q = False
                    break
            if q:
                break
    
    with open(filelist_path, "r") as fl:
        text = fl.readlines()

    lines = []
    for line in text:
        if len(line.split('|')) < 3:
            continue
        wf = line.split('|')[0]
        l = len(line.split('|')[1])
        with wave.open(os.path.join(wav_dir, wf)) as f:
            frames = f.getnframes()  
        
        if frames/l < 1000:
            continue
        lines.append(line)

    with open(filelist_path, 'w+') as f:
        f.writelines(lines)    
    format_filelist_for_hifigan(filelist_path)    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--wav_dir', type=str,
        help='Directory to save .wav files', default='wavs')
    parser.add_argument('-f', '--file_list', type=str,
        help='Path to file_list of speech text', default='file_list.txt')
    parser.add_argument('-c', '--corpus', type=str,
        help='Path to text file containing Project Guttenberg texts', default='corpus.txt')
    parser.add_argument('-p', '--prefix', type=str,
        help='Prefix text for wav files e.g. speaker initials', default='speaker')
    parser.add_argument('-s', '--speaker', type=str,
        help='Speaker tag e.g. initials', default='abc')
    parser.add_argument('-o', '--overwrite_tokenizer', type=bool,
        help='Re-tokenize corpus text', default=False)
    args = parser.parse_args()
    gather_data(wav_dir=args.wav_dir,
            fn_prefix=args.prefix,
            filelist_path=args.file_list,
            corpus_path=args.corpus,
            speaker=args.speaker,
            overwrite_tokenized_corpus=args.overwrite_tokenizer)    
 
