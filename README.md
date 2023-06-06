# Color Encryption

## Purpose:
This is a Python + GTK (Glade) implementation of a program I wrote a few different times over the years.  It encrypts text using AES, then converts the encrypted text to an PNG image.  It can then open and decrypt an image back to the original text.  Note:  This was inspired by NCIS s07e09.

## Functionality:
* Encrypt:
  * Select the pixel size (1-1000)
  * Enter text into the top text box
  * Click the Save Image button
    * The image will be saved as "EncryptedImage_[pixel_size].png"
* Decrypt:
  * Click the Load Image button
  * Select a PNG image file
  * The decrypted text will be displayed in the bottom text box
* Notes:
  * The "key" for encrypting/decrypting is called "key".  I recommend you change it, but the sender and receiver need to have the same ones.
  * There are 128 different colors and the order they are in are essentially a second "key".  Feel free to change them too, but the sender and receiver need to have the same ones.
  * The displayed image will start getting scaled ones it reaches the "max_displayed_image_size".
  * You can change the filename, but it needs to have the "_[pixel_size]" part at the end.

## Author:
BSFEMA

## Started:
2023-06-03

## Screenshot:
![screenshot](https://github.com/BSFEMA/color_encryption/raw/master/screenshot.png)

## Prerequisites:
Unlike most of my other recent programs, this one requires several python libraries that might not be installed.  You may need the following:
pip install pycryptodome

## Command Line Parameters:
There is just 1.  It is the folder path that will be used to start looking at the *.mkv files from.  If this value isn't provided, then the starting path will be where this application file is located.  The intention is that you can call this application from a context menu from a file browser (e.g. Nemo) and it would automatically load up that folder.