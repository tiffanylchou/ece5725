# Import necessary libraries
# Multiprocessing libraries
from threading import Thread
from multiprocessing import Process

# Hardware support libraries
import RPi.GPIO as GPIO
import keyboard

# PyGame libraries
from pygame.locals import *
import pygame as pg

# MIDI communication libraries
import music21
from music21 import *
from music21.chord import Chord
from music21.duration import Duration
from music21.instrument import Instrument
from music21.note import Note, Rest
from music21.stream import Stream
from music21.tempo import MetronomeMark
from music21.volume import Volume

# Standard libraries
import time
import os


# Function for playing recorded notes
def record_func(record, note_folder_path):
    # Initialize PyGame, PyGame mixer, and no. of sound channels for playing recording
    pg.init()
    pg.mixer.init()
    pg.mixer.set_num_channels(50)

    # Initialize time for the recording
    t = 0
    record_time = time.time()

    # Loop through the list of recorded notes with timestamp
    while t < len(record):

        # Play the recorded note if the current loop time syncs with the recorded timestamp
        if record[t][1] < (time.time()-record_time):
            key_r = f'{record[t][0]}.ogg'
            notepathr = note_folder_path + key_r
            pg.mixer.Sound(notepathr).play()
            print(notepathr)
            t = t + 1

            # Reset the function if the recording ends and play again
            if t == len(record):
                time.sleep(5 - record[len(record)-1][1])
                record_time = time.time()
                t = 0

# Function to create instruments using MIDI architecture
def make_instrument(id):
    i = Instrument()
    i.midiProgram = id
    return i


# Main function
if __name__ == '__main__':

    # Setup PiTFT touchscreen
    os.putenv('SDL_VIDEODRIVER', 'fbcon')
    os.putenv('SDL_FBDEV', '/dev/fb1')
    os.putenv('SDL_MOUSEDRV', 'TSLIB')
    os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
    pg.mouse.set_visible(False)

    # Initialize PyGame, PyGame mixer, and no. of sound channels for realtime playing
    pg.mixer.init()
    pg.init()
    pg.mixer.set_num_channels(100)

    # Setup PiTFT screen for display
    size = width, height = 320, 240
    screen = pg.display.set_mode(size)

    # Setup font and color for the display screen
    font = pg.font.Font(None, 35)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    # Initialize disctionaries of buttons for the various functions of the keyboard
    buttons = {(80, 210): 'Metronome', (240, 210): 'Quit', (80, 170): 'Octave Up', (240, 170): 'Octave Down', (80, 130): 'Drum', (240, 130): 'Piano'}
    # buttons = {(80, 210): 'Metronome', (240, 210): 'Quit', (80, 170): 'Octave Up', (240, 170): 'Octave Down', (80, 130): 'Layering', (240, 130): 'Record', (80, 90): 'Drum', (240, 90): 'Piano'}

    # Display text for buttons on the PiTFT screen
    for text_pos, my_text in buttons.items():
        text_surface = font.render(my_text, True, WHITE)
        rect = text_surface.get_rect(center=text_pos)
        screen.blit(text_surface, rect)

    # Refresh and paint the screen for displaying the buttons
    pg.display.flip()

    # Define path for the Piano and Drum sounds
    pianopath = 'PianoKeys/'
    drumpath = 'DrumKeys/'

    # Setup the GPIO pins for each key on the keyboard
    channellist = [17, 27, 22, 5, 6, 13, 19, 23, 12, 16, 20, 21]                    # DEFINE CHANNEL LIST IN ORDER
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(channellist, GPIO.IN,  pull_up_down=GPIO.PUD_UP)

    # Define a listt of individual white and black keyboard keys
    whitekey = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    blackkey = ['C#', 'D#', 'F#', 'G#', 'A#']

    # Initialize the state of each key in the keyboard in a dictionary (first 7 white keys and then 5 black keys)
    keyspressed = {0: '0', 1: '0', 2: '0', 3: '0', 4: '0', 5: '0', 6: '0', 7: '0', 8: '0', 9: '0', 10: '0', 11: '0'}
    # strings_channellist = [17, 23, 27, 12, 22, 5, 16, 6, 20, 13, 21, 19]
    # strings = {0: 'C', 1: 'C#', 2: 'D', 3: 'D#', 4: 'E', 5: 'F', 6: 'F#', 7: 'G', 8: 'G#', 9: 'A', 10: 'A#', 11: 'B', 12: 'C', 13: 'C#', 14: 'D', 15: 'D#', 16: 'E', 17: 'F', 18: 'F#'}

    # Load strong and weak beat for the Metronome
    strong_beat = pg.mixer.Sound('Strong_beat.wav')
    weak_beat = pg.mixer.Sound('Weak_beat.wav')

    # Initialize variables for recording and playing the recorded music
    layering = 0
    layering_temp = {}
    layer = 0

    octave = 4                                                                      # Initialize octave for the keyboard

    # Initialize time signature, tempo, timing, and state of the metronome
    time_signature = 4
    tempo = 100
    time_m = time.time()
    metronome_on = 0
    count_m = 1

    is_quit = 1                                                                     # Initialize the state for the quit button

    is_piano = 1                                                                    # Initialize the state for the type of sound (piano or drum)
    # is_not_piano = 0
    
    start_time = time.time()                                                        # Define start time for the keyboard

    # Main loop for playing the keyboard with a maximum time of 5 mins.
    while is_quit and (time.time() - start_time) < 300 :

        # Refresh and paint the screen for displaying the buttons
        pg.display.flip()
        screen.fill(BLACK)

        # Display text for buttons on the PiTFT screen alongwith the appropriate color based on the current function of the keyboard
        for text_pos, my_text in buttons.items():
            text_surface = font.render(my_text, True, WHITE)
            rect = text_surface.get_rect(center=text_pos)
            rect2_corner = tuple(map(lambda i, j: i - j, text_pos, (78,15)))
            rect2 = ((rect2_corner),(156,30))
            rect_color = [0,0,0]
            if (my_text == 'Layering'):                                             # If the layering button is pressed change the color of the button from red to green
                rect_color = [0,255,0] if layering else [200,0,0]
            elif (my_text == 'Piano'):                                              # If the piano button is pressed change the color of the button from red to green
                rect_color = [0,255,0] if is_piano else [200,0,0]
            elif (my_text == 'Drum'):                                               # If the drum button is pressed change the color of the button from red to green
                rect_color = [200,0,0] if is_piano else [0,255,0]
            elif (my_text == 'Metronome'):                                          # If the metronome button is pressed change the color of the button from red to green
                rect_color = [0,255,0] if metronome_on else [200,0,0]
            else:
                rect_color = [200,0,0]

            # Draw the buttons with the colors on the screen
            pg.draw.rect(screen,rect_color,rect2)
            screen.blit(text_surface, rect)
        
        # Loop for checking if any of the buttons is pressed
        for event in pg.event.get():
            if event.type is MOUSEBUTTONDOWN:
                pos = pg.mouse.get_pos()
            elif event.type is MOUSEBUTTONUP:
                pos = pg.mouse.get_pos()
                x, y = pos

                if ((y > 190) & (y < 230)) & ((x > 0) & (x < 160)):                 # Check if the metronome is pressed
                    metronome_on = abs(metronome_on - 1)

                if ((y > 190) & (y < 230)) & ((x > 160) & (x < 320)):               # Check if the quit button is pressed
                    is_quit = 0
                    
                if ((y > 150) & (y < 190)) & ((x > 0) & (x < 160)):                 # Check if the octave + button is pressed
                    octave = octave + 1
                    time.sleep(0.1)
                    if octave > 7:
                        octave = 7
                    
                if ((y > 150) & (y < 190)) & ((x > 160) & (x < 320)):               # Check if the octave - button is pressed
                    octave = octave - 1
                    time.sleep(0.1)
                    if octave < 1:
                        octave = 1
                
                # if ((y > 110) & (y < 150)) & ((x > 0) & (x < 160)):               # Check if the recording button is pressed
                #    layering_time = time.time()
                #    layering = 1
                #    layering_temp = {}
                #    layer = 0

                if ((y > 110) & (y < 150)) & ((x > 0) & (x < 160)):                 # Check if the piano button is pressed
                    is_piano = 0
                    # is_not_piano = 1

                if ((y > 110) & (y < 150)) & ((x > 160) & (x < 320)):               # Check if the drum button is pressed
                    is_piano = 1
                    # is_not_piano = 0
        
        # Main function for the Metronome
        if metronome_on:
            if time.time()-time_m >= 1/(tempo/60):                                  # Play the strong beat of the metronome for the first beat
                if count_m == 1:
                    strong_beat.play()
                    time_m = time.time()
                    count_m = count_m + 1
                else:                                                               # Play the weak beat of the metronome for the remainder beats
                    weak_beat.play()
                    time_m = time.time()
                    count_m = count_m + 1
                if count_m == time_signature:                                       # Reset the metronome after the bar is complete
                    count_m = 0
    
        # Main loop for the piano functionality
        if (is_piano == 1):

            # Loop for playing the White keys of the keyboard
            for i in range(7):
                Wkey = f'{whitekey[i]}'

                # Check if the GPIO pin corresponding to the white key is pressed or not
                if (GPIO.input(channellist[i])) and keyspressed[i] == '0':

                    # Load the piano sound corresponding to the White key presssed
                    keyW = f'{whitekey[i]}{octave}.ogg'
                    notePath = pianopath + keyW

                    pg.mixer.Sound(notePath).play()                                 # Play the piano sound corresponding to the White key pressed

                    keyspressed[i] = '1'                                            # Change the state of the White key pressed so that it doesn't play repeatedly while pressed
                    # starttimeW = time.time()

                    # Record the White key pressed and the time at which it was pressed in a dictionary for recording and playing
                    if layering == 1:
                        key_temp = f'{whitekey[i]}{octave}'
                        time_temp = time.time() - layering_time
                        arr_temp = [key_temp, time_temp]
                        layering_temp[layer] = arr_temp
                        layer += 1
                    # print(notePath)

                # Check if the GPIO pin corresponding to the white key pressed is released or not
                if (not GPIO.input(channellist[i])) and keyspressed[i] == '1':

                    # Load the piano sound corresponding to the White key released
                    keyW = f'{whitekey[i]}{octave}.ogg'
                    notePath = pianopath + keyW

                    pg.mixer.Sound(notePath).stop()                                 # Stop playing the piano sound corresponding to the White key that was released

                    keyspressed[i] = '0'                                            # Change the state of the White key released so that it can be played again
                    # endtimeW = time.time()
                    # print(endtimeW-starttimeW)

            # Loop for playing the Black keys of the keyboard
            for j in range(5):
                Bkey = f'{blackkey[j]}'

                # Check if the GPIO pin corresponding to the black key is pressed or not
                if (GPIO.input(channellist[j+7])) and keyspressed[j+7] == '0':

                    # Load the piano sound corresponding to the Black key presssed
                    keyB = f'{blackkey[j]}{octave}.ogg'
                    notePath = pianopath + keyB

                    pg.mixer.Sound(notePath).play()                                 # Play the piano sound corresponding to the Black key pressed

                    keyspressed[j+7] = '1'                                          # Change the state of the Black key pressed so that it doesn't play repeatedly while pressed
                    # starttimeB = time.time()

                    # Record the Black key pressed and the time at which it was pressed in a dictionary for recording and playing
                    if layering == 1:
                        key_temp = f'{blackkey[j]}{octave}'
                        time_temp = time.time() - layering_time
                        arr_temp = [key_temp, time_temp]
                        layering_temp[layer] = arr_temp
                        layer += 1
                    # print(notePath)

                # Check if the GPIO pin corresponding to the black key pressed is released or not
                if (not GPIO.input(channellist[j+7])) and keyspressed[j+7] == '1':

                    # Load the piano sound corresponding to the Black key released
                    keyB = f'{blackkey[j]}{octave}.ogg'
                    notePath = pianopath + keyB

                    pg.mixer.Sound(notePath).stop()                                 # Stop playing the piano sound corresponding to the Black key that was released

                    keyspressed[j+7] = '0'                                          # Change the state of the Black key released so that it can be played again
                    # endtimeB = time.time()
                    # print(endtimeB-starttimeB)

        # Condition to play the recorded music as a parallel process
        # if (is_piano == 1) and (is_not_piano == 0):                               # Check if the piano is playing or not

            # if (layering == 1) and ((time.time() - layering_time) > 5):           # Check if the recording time has exceeded or not

            #     layering_notes = layering_temp                                    # Pass the dictionary of recorded notes with time stamps

            #     layering = 0                                                      # Change the state so that the recording does not play again

            # Define and start the parallel multiprocess for playing the recording
            #     p1 = Process(target=record_func, args=(layering_notes, path,))
            #     p1.start()

        # Main loop for the drum functionality
        else:

            # Loop for playing the White keys of the keyboard
            for i in range(7):
                Wkey = f'{whitekey[i]}'

                # Check if the GPIO pin corresponding to the white key is pressed or not
                if (GPIO.input(channellist[i])) and keyspressed[i] == '0':

                    # Load the drum sound corresponding to the White key presssed
                    keyW = f'{whitekey[i]}{4}.ogg'
                    notePath = drumpath + keyW

                    pg.mixer.Sound(notePath).play()                                 # Play the drum sound corresponding to the White key pressed

                    keyspressed[i] = '1'                                            # Change the state of the White key pressed so that it doesn't play repeatedly while pressed
                    # starttimeW = time.time()

                    # Record the White key pressed and the time at which it was pressed in a dictionary for recording and playing
                    # if layering == 1:
                    #     key_temp = f'{whitekey[i]}{4}'
                    #     time_temp = time.time() - layering_time
                    #     arr_temp = [key_temp, time_temp]
                    #     layering_temp[layer] = arr_temp
                    #     layer += 1
                    # print(notePath)

                # Check if the GPIO pin corresponding to the white key pressed is released or not
                if (not GPIO.input(channellist[i])) and keyspressed[i] == '1':

                    # Load the drum sound corresponding to the White key released
                    keyW = f'{whitekey[i]}{4}.ogg'
                    notePath = drumpath + keyW

                    pg.mixer.Sound(notePath).stop()                                 # Stop playing the drum sound corresponding to the White key that was released

                    keyspressed[i] = '0'                                            # Change the state of the White key released so that it can be played again
                    # endtimeW = time.time()
                    # print(endtimeW-starttimeW)

            # Loop for playing the Black keys of the keyboard
            for j in range(5):
                Bkey = f'{blackkey[j]}'

                # Check if the GPIO pin corresponding to the black key is pressed or not
                if (GPIO.input(channellist[j+7])) and keyspressed[j+7] == '0':

                    # Load the drum sound corresponding to the Black key presssed
                    keyB = f'{blackkey[j]}{4}.ogg'
                    notePath = drumpath + keyB

                    pg.mixer.Sound(notePath).play()                                 # Play the drum sound corresponding to the Black key pressed

                    keyspressed[j+7] = '1'                                          # Change the state of the Black key pressed so that it doesn't play repeatedly while pressed
                    # starttimeB = time.time()

                    # Record the Black key pressed and the time at which it was pressed in a dictionary for recording and playing
                    # if layering == 1:
                    #     key_temp = f'{blackkey[j]}{octave}'
                    #     time_temp = time.time() - layering_time
                    #     arr_temp = [key_temp, time_temp]
                    #     layering_temp[layer] = arr_temp
                    #     layer += 1
                    # print(notePath)

                # Check if the GPIO pin corresponding to the black key pressed is released or not
                if (not GPIO.input(channellist[j+7])) and keyspressed[j+7] == '1':

                    # Load the drum sound corresponding to the Black key released
                    keyB = f'{blackkey[j]}{4}.ogg'
                    notePath = drumpath + keyB

                    pg.mixer.Sound(notePath).stop()                                 # Stop playing the drum sound corresponding to the Black key that was released

                    keyspressed[j+7] = '0'                                          # Change the state of the Black key released so that it can be played again
                    # endtimeB = time.time()
                    # print(endtimeB-starttimeB)

    # Refresh and paint the screen for displaying the text
    pg.display.flip()
    screen.fill(BLACK)

    # Display the text for exiting the program
    string = 'QUIT'
    text_surface = font.render(string, True, WHITE)
    rect = text_surface.get_rect(center=(160,120))

    # Refresh and close the screen after exiting the program
    screen.blit(text_surface, rect)
    pg.display.flip()

    print("Exited")                                                                 # Print to the console after the program terminates

    GPIO.cleanup()                                                                  # Cleanup all the GPIO pins after closing the program
