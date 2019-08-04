from os.path import join, dirname
from ibm_watson import TextToSpeechV1
from ibm_watson.websocket import SynthesizeCallback
import pyaudio
import pytesseract as ocr
import asyncio
from PIL import Image
import pyscreenshot as ImageGrab
import threading
def getCredentials():
    import json
    with open('./credentials/text2speech.json') as json_file:
        data = json.load(json_file)
        return(data["apikey"], data["url"])
    return None

pya = pyaudio.PyAudio()

class MySynthesizeCallback(SynthesizeCallback):
    def __init__(self):
        SynthesizeCallback.__init__(self)
        self.stream = pya.open(format=pya.get_format_from_width(width=2), channels=1, rate=23050, output=True)
        
    def on_connected(self):
        print('Connection was successful')

    def on_error(self, error):
        print('Error received: {}'.format(error))

    def on_content_type(self, content_type):
        print('Content type: {}'.format(content_type))

    def on_timing_information(self, timing_information):
        print(timing_information)

    def on_audio_stream(self, audio_stream):
        
        self.stream.write(audio_stream)
        
        # self.fd.write(audio_stream)

    def on_close(self):
        self.stream.stop_stream()
        self.stream.close()
        print('Done synthesizing. Closing the connection')

def getImage():
    # original = ImageGrab.grab()
    original = Image.open("./outro.png")
    width, height = original.size
    cropped_example = original.crop((1.5*height/4, height/1.25, 3.1/4*width, height))
    thresh = 254
    fn = lambda x : 255 if x > thresh else 0
    cropped_example = cropped_example.convert('L').point(fn, mode='1')
    cropped_example.save("new.png")
    return cropped_example

def getPhrase():
    phrase = ocr.image_to_string(getImage(), lang='por')
    new_p = ""
    for p in phrase.split(" "):
        if("\n" in p):
            for lp in p.split("\n"):
                if(not lp or lp == "[" or lp =="]"):
                    continue
                new_p += " " + lp
            continue
        new_p += " " + p
    return new_p

def isRepetitive(phrase, lastPhrase):
    words = phrase.split(" ")
    lastWords = lastPhrase.split(" ")
    count = 0
    
    for atual, last in zip(words, lastWords):
        if(atual == last):            
            count += 1
    return (count >= len(words)*0.7 and count != 0) or len(words) < 3

def asyncCallback(service,phrase):
    my_callback = MySynthesizeCallback()
    service.synthesize_using_websocket(phrase,
                                    my_callback,
                                    accept='audio/wav',
                                    voice='pt-BR_IsabelaVoice'
                                    )

async def main():
    apikey, url = getCredentials()
    await asyncio.sleep(2)
    lastPhrase = ""
    service = TextToSpeechV1(url=url,
                             iam_apikey=apikey)
    threads = []
    while True:
        await asyncio.sleep(0.1)
        phrase = getPhrase()
        if(not phrase or len(phrase) < 3 or isRepetitive(phrase, lastPhrase)):
            continue
        lastPhrase = phrase
        # print(phrase)
        thread = threading.Thread(target=asyncCallback, args=(service,phrase,))
        thread.start()
        threads.append(thread)
        if(len(threads) > 2):
            for t in threads:
                t.join()
            threads=[]

if __name__ == "__main__":
    asyncio.run(main())
    