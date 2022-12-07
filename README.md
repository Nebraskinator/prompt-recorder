Clone your voice into a text-to-speech synthesizer!
===

Step 1:
  - Clone this repository, and the following:
    - https://github.com/Nebraskinator/hifi-gan
    - https://github.com/Nebraskinator/tacotron2
    - https://github.com/Nebraskinator/radtts
    
Step 2:
  - Use the environment.yml to create a new environment
  
Step 3:
  - Create a transcribed speech dataset (4+ hours recommended).
    - Record from prompt:
      - Create a corpus of text. 
      - You can download plain-text books from Project Guttenberg (www.guttenberg.org). Paste them into the corpus.txt file.
      - Run prompt-recorder.py and follow onscreen instructions
      ```
      python prompt-recorder.py
      ```
    - OR use the following repository to generate a transcribed dataset from audio recordings:
      - https://github.com/miguelvalente/whisperer
      
Step 4:
  - Generate mel spectrographs from wav files
    - Copy the file_list_nospeaker.txt to the tacotron2/filelists folder (tacotron2 reposity linked above)
    - Move the wav files to the tacotron2/filelists/wav folder
    - Download the [published tacotron2 statedict](https://drive.google.com/file/d/1c5ZTuT7J08wLUoVZ2KkUs_VdZuJ86ZqA/view?usp=sharing) into the tacotron2/models folder
    - Run generate_mels.py in the tacotron2 repository to create mel spectrographs
    ```
    python generate_mels.py -o output -c models/tacotron2_statedict.pt
    ```
    
Step 5:
  - Fine-tune HiFi-GAN
    - Download the [pretrained HiFi-GAN generator and discriminator models](https://drive.google.com/drive/folders/1YuOoV3lO2-Hhn1F2HJ2aQ4S0LC1JdKLd) into hifi-gan/models
    - Move the wav files into hifi-gan/LJSpeech-1.1/wavs
    - Move the mel files (.npy) from the tacotron2/output folder into hifi-gan/LJSpeech-1.1/wavs
    - Copy the file_list_nospeaker.txt to the hifi-gan/LJSpeech-1.1 folder
    - Run train.py in the hifi-gan repository for 50k-100k iterations to fine-tune the model
    ```
    python train.py --fine_tuning True --config config_v1.json --checkpoint_path models
    ```

Step 6:
  - Train the text-to-speech decoder
    - Move the wav files into radtts/filelists/wavs
    - Copy the file_list.txt into radtts/filelists
    - Run train.py in the radtts repository for ~500k iterations to train the decoder
    ```
    python train.py -c configs/config_ljs_decoder.json
    ```
    
Step 7:
  - Train the attribute predictor
    - Move the decoder model file into the radtts/models folder (by default, it is in root/debug)
    - Run train.py in the radtts repository with either deterministic (dap, ~5k iterations) or autogressive (agap, ~25k iterations) prediction
    ```
    python train.py -c configs/config_ljs_dap.json -p train_config.warmstart_checkpoint_path=models/model_{iteration #}
    ```
    OR
    ```
    python train.py -c configs/config_ljs_agap.json -p train_config.warmstart_checkpoint_path=models/model_{iteration #}
    ```
    
Step 8:
  - Generate speech from text input
    - Move the attribute predictor model file into the radtts/models folder (by default, it is in root/debug)
    - Move the attribute predictor config file into the radtts/models folder (by default, it is in root/debug)
    - Create a text.txt file in radtts/filelists and enter lines of text to be synthesized
    - Move the fine-tuned HiFi-GAN generator file from hifi-gan/models to radtts/models
    - Copy the config file config_v1.json from hifi-gan to radtts/models
    - Run inference.py in the radtts directory to generate wav files
    ```
    python inference.py -c models/config.json -r models/model_{dap iterations} -v models/g_{hifi-gan iterations} -k models/config_v1.json -t filelists/text.txt -s {speaker ID} --speaker_attributes {speaker ID} --speaker_text {speaker ID} -o results/
    ```
    OR
    ```
    python inference.py -c models/config.json -r models/model_{dap iterations} -v models/g_{hifi-gan iterations} -k models/config_v1.json -t filelists/text.txt -s {speaker ID} --speaker_attributes {speaker ID} --speaker_text {speaker ID} -o results/
    ```
Step 9:
  - Evaluate the results!
  - Example for deterministic attribute predictor (dap): [dap](dap0.wav)
  - Example for autoregressive attribute predictor (agap): [agap](agap0.wav)
  
