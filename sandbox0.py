from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='auto', target='en')

print((translator.source, translator.target) == ('auto', 'en'))


while True:
    # break
    sentence = input("Enter a sentence: ")
    if sentence == "q":
        break
    translation = translator.translate(sentence)
    print(type(translation))