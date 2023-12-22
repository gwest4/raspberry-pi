from picozero import Button

button = Button(15)

def on_press():
    print('Beep!')
    
button.when_pressed = on_press
print('Ready')