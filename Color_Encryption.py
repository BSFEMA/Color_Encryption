#!/usr/bin/python3

"""
Application:  Color Encryption
Author:  BSFEMA
Started:  2023-06-03
Note:  I would appreciate it if you kept my attribution as the original author in any fork or remix that is made.
Purpose:  This is a Python + GTK (Glade) implementation of a program I wrote a few different times over the years.
          It encrypts text using AES, then converts the encrypted text to an image.
          It can then open and decrypt an image back to the original text.
          Note:  This was inspired by NCIS season 7 episode 9.
Command Line Parameters:  There is just 1:
                          It is the folder path that will be used to start looking at the *.mkv files from.
                          If this value isn't provided, then the starting path will be where this application file is located.
                          The intention is that you can call this application from a context menu from a file browser (e.g. Nemo) and it would automatically load up that folder.
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk as gtk
from gi.repository import GdkPixbuf as gdkPixbuf
from gi.repository import GLib as glib
from gi.repository import Gdk as gdk
import hashlib
from Crypto import Random  # pip install pycryptodome
from Crypto.Cipher import AES
from base64 import b64encode, b64decode
from PIL import Image as PIL_Image
from PIL import ImageDraw as PIL_ImageDraw
import math
import os
import sys

key = "hGGA9Y;yp-\\'h-\\c#8A+RQUsM5`Es!}K"  # Change this to your own value!
default_window_width = 900
default_window_height = 400
max_displayed_image_size = 500
default_folder_path = ""  # The path to save/load images from by default
colors = []
aes_class = ""
img_Unsaved = ""

""" ************************************************************************************************************ """
#  Encryption class
""" ************************************************************************************************************ """

class AESCipher(object):
    # https://medium.com/quick-code/aes-implementation-in-python-a82f582f51c2
    # https://gist.github.com/PaburoTC/74f96510479d5129100b994d1c06885a
    def __init__(self, key):
        self.block_size = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, plain_text):
        plain_text = self.__pad(plain_text)
        iv = Random.new().read(self.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        encrypted_text = cipher.encrypt(plain_text.encode())
        return b64encode(iv + encrypted_text).decode("utf-8")

    def decrypt(self, encrypted_text):
        encrypted_text = b64decode(encrypted_text)
        iv = encrypted_text[:self.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        plain_text = cipher.decrypt(encrypted_text[self.block_size:]).decode("utf-8")
        return self.__unpad(plain_text)

    def __pad(self, plain_text):
        number_of_bytes_to_pad = self.block_size - len(plain_text) % self.block_size
        ascii_string = chr(number_of_bytes_to_pad)
        padding_str = number_of_bytes_to_pad * ascii_string
        padded_plain_text = plain_text + padding_str
        return padded_plain_text

    @staticmethod
    def __unpad(plain_text):
        last_character = plain_text[len(plain_text) - 1:]
        return plain_text[:-ord(last_character)]

""" ************************************************************************************************************ """
#  GUI class
""" ************************************************************************************************************ """

class Main():
    def __init__(self):
        # Setup Glade Gtk
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(sys.path[0], "Color_Encryption.glade"))  # Looking where the python script is located
        self.builder.connect_signals(self)
        # Get UI components
        window = self.builder.get_object("main_Window")
        window.connect("delete-event", gtk.main_quit)
        window.set_title('Color Encryption')
        window.set_default_icon_from_file(os.path.join(sys.path[0], "Color_Encryption.svg"))  # Setting the "default" icon makes it usable in the about dialog. (This will take .ico, .png, and .svg images.)
        # Set the default size of the window
        window.resize(default_window_width, default_window_height)
        window.show()
        # Set the default spinner
        spin_PixelSize = self.builder.get_object("spin_PixelSize")
        spin_PixelSize.set_value(20)
        # Set the image to the logo for now
        img_Image = self.builder.get_object("img_Image")
        img_Image.set_from_file(os.path.join(sys.path[0], "Color_Encryption.svg"))

    """ ************************************************************************************************************ """
    #  These are the various widget's signal handler functions
    """ ************************************************************************************************************ """

    def textbuffer_Input_changed(self, widget):
        textbuffer_Output = self.builder.get_object("textbuffer_Output")
        textbuffer_Output.set_text("")
        textbuffer_Input = self.builder.get_object("textbuffer_Input")
        spin_PixelSize = self.builder.get_object("spin_PixelSize")
        text_In = textbuffer_Input.get_text(textbuffer_Input.get_start_iter(), textbuffer_Input.get_end_iter(), True)  # Grab the actual text (all of it) from the input buffer
        if len(text_In) > 0:
            encrypted = aes_class.encrypt(text_In)
            encryption_to_colors = convert_encryption_to_colors(encrypted)
            create_encrypted_image_multiplier(encryption_to_colors, spin_PixelSize.get_value_as_int())
        img_Image = self.builder.get_object("img_Image")
        global img_Unsaved
        data = img_Unsaved.tobytes()
        w, h = img_Unsaved.size
        data = glib.Bytes.new(data)
        pix = gdkPixbuf.Pixbuf.new_from_bytes(data, gdkPixbuf.Colorspace.RGB, False, 8, w, h, w * 3)
        # If the image is larger then max_displayed_image_size, scale the image, otherwise display it
        if w > max_displayed_image_size:
            pix_resized = pix.scale_simple(max_displayed_image_size, max_displayed_image_size, gdkPixbuf.InterpType.BILINEAR)
            img_Image.set_from_pixbuf(pix_resized)
        else:
            img_Image.set_from_pixbuf(pix)

    def button_Save_clicked(self, widget):
        global img_Unsaved
        spin_PixelSize = self.builder.get_object("spin_PixelSize")
        img_Unsaved.save(os.path.join(default_folder_path, "EncryptedImage_" + str(spin_PixelSize.get_value_as_int()) + ".png"))

    def button_Load_clicked(self, widget):
        textbuffer_Input = self.builder.get_object("textbuffer_Input")
        textbuffer_Input.set_text("")
        open_dialog = gtk.FileChooserDialog(title="Please choose an Color Encrypted PNG image", parent=None, action=gtk.FileChooserAction.OPEN)
        open_dialog.set_current_folder(os.path.expanduser(default_folder_path))
        open_dialog.add_buttons(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL, gtk.STOCK_OPEN, gtk.ResponseType.OK)
        open_dialog.set_local_only(False)
        open_dialog.set_modal(True)
        # *.png filter
        filter = gtk.FileFilter()
        filter.set_name("PNG files")
        filter.add_pattern("*.png")
        open_dialog.add_filter(filter)
        response = open_dialog.run()
        file = ""
        if response == gtk.ResponseType.OK:
            file = open_dialog.get_filename()
        elif response == gtk.ResponseType.CANCEL:
            file = ""
        open_dialog.destroy()
        if file != "":
            img_Image = self.builder.get_object("img_Image")
            pix = gdkPixbuf.Pixbuf.new_from_file(file)
            w = pix.get_width()
            # If the image is larger then max_displayed_image_size, scale the image, otherwise display it
            if w > max_displayed_image_size:
                pix_resized = pix.scale_simple(max_displayed_image_size, max_displayed_image_size, gdkPixbuf.InterpType.BILINEAR)
                img_Image.set_from_pixbuf(pix_resized)
            else:
                img_Image.set_from_pixbuf(pix)
            # Decrypt image and output text
            image_encryption = decrypt_image_multiplier(file)
            colors_to_encryption = convert_colors_to_encryption(image_encryption)
            decrypted = aes_class.decrypt((colors_to_encryption))
            textbuffer_Output = self.builder.get_object("textbuffer_Output")
            textbuffer_Output.set_text(decrypted)

""" ************************************************************************************************************ """
#  Functions
""" ************************************************************************************************************ """

def choose_colors():  # DO NOT USE #000000
    global colors
    colors.append("#202020")
    colors.append("#606060")
    colors.append("#A0A0A0")
    colors.append("#E0E0E0")
    colors.append("#000040")
    colors.append("#000080")
    colors.append("#0000C0")
    colors.append("#0000FF")
    colors.append("#004000")
    colors.append("#004040")
    colors.append("#004080")
    colors.append("#0040C0")
    colors.append("#0040FF")
    colors.append("#008000")
    colors.append("#008040")
    colors.append("#008080")
    colors.append("#0080C0")
    colors.append("#0080FF")
    colors.append("#00C000")
    colors.append("#00C040")
    colors.append("#00C080")
    colors.append("#00C0C0")
    colors.append("#00C0FF")
    colors.append("#00FF00")
    colors.append("#00FF40")
    colors.append("#00FF80")
    colors.append("#00FFC0")
    colors.append("#00FFFF")
    colors.append("#400000")
    colors.append("#400040")
    colors.append("#400080")
    colors.append("#4000C0")
    colors.append("#4000FF")
    colors.append("#404000")
    colors.append("#404040")
    colors.append("#404080")
    colors.append("#4040C0")
    colors.append("#4040FF")
    colors.append("#408000")
    colors.append("#408040")
    colors.append("#408080")
    colors.append("#4080C0")
    colors.append("#4080FF")
    colors.append("#40C000")
    colors.append("#40C040")
    colors.append("#40C080")
    colors.append("#40C0C0")
    colors.append("#40C0FF")
    colors.append("#40FF00")
    colors.append("#40FF40")
    colors.append("#40FF80")
    colors.append("#40FFC0")
    colors.append("#40FFFF")
    colors.append("#800000")
    colors.append("#800040")
    colors.append("#800080")
    colors.append("#8000C0")
    colors.append("#8000FF")
    colors.append("#804000")
    colors.append("#804040")
    colors.append("#804080")
    colors.append("#8040C0")
    colors.append("#8040FF")
    colors.append("#808000")
    colors.append("#808040")
    colors.append("#808080")
    colors.append("#8080C0")
    colors.append("#8080FF")
    colors.append("#80C000")
    colors.append("#80C040")
    colors.append("#80C080")
    colors.append("#80C0C0")
    colors.append("#80C0FF")
    colors.append("#80FF00")
    colors.append("#80FF40")
    colors.append("#80FF80")
    colors.append("#80FFC0")
    colors.append("#80FFFF")
    colors.append("#C00000")
    colors.append("#C00040")
    colors.append("#C00080")
    colors.append("#C000C0")
    colors.append("#C000FF")
    colors.append("#C04000")
    colors.append("#C04040")
    colors.append("#C04080")
    colors.append("#C040C0")
    colors.append("#C040FF")
    colors.append("#C08000")
    colors.append("#C08040")
    colors.append("#C08080")
    colors.append("#C080C0")
    colors.append("#C080FF")
    colors.append("#C0C000")
    colors.append("#C0C040")
    colors.append("#C0C080")
    colors.append("#C0C0C0")
    colors.append("#C0C0FF")
    colors.append("#C0FF00")
    colors.append("#C0FF40")
    colors.append("#C0FF80")
    colors.append("#C0FFC0")
    colors.append("#C0FFFF")
    colors.append("#FF0000")
    colors.append("#FF0040")
    colors.append("#FF0080")
    colors.append("#FF00C0")
    colors.append("#FF00FF")
    colors.append("#FF4000")
    colors.append("#FF4040")
    colors.append("#FF4080")
    colors.append("#FF40C0")
    colors.append("#FF40FF")
    colors.append("#FF8000")
    colors.append("#FF8040")
    colors.append("#FF8080")
    colors.append("#FF80C0")
    colors.append("#FF80FF")
    colors.append("#FFC000")
    colors.append("#FFC040")
    colors.append("#FFC080")
    colors.append("#FFC0C0")
    colors.append("#FFC0FF")
    colors.append("#FFFF00")
    colors.append("#FFFF40")
    colors.append("#FFFF80")
    colors.append("#FFFFC0")
    colors.append("#FFFFFF")

def choose_colors_alt():  # DO NOT USE #000000
    global colors
    colors.append("#020202")
    colors.append("#040404")
    colors.append("#060606")
    colors.append("#080808")
    colors.append("#0A0A0A")
    colors.append("#0C0C0C")
    colors.append("#0E0E0E")
    colors.append("#101010")
    colors.append("#121212")
    colors.append("#141414")
    colors.append("#161616")
    colors.append("#181818")
    colors.append("#1A1A1A")
    colors.append("#1C1C1C")
    colors.append("#1E1E1E")
    colors.append("#202020")
    colors.append("#222222")
    colors.append("#242424")
    colors.append("#262626")
    colors.append("#282828")
    colors.append("#2A2A2A")
    colors.append("#2C2C2C")
    colors.append("#2E2E2E")
    colors.append("#303030")
    colors.append("#323232")
    colors.append("#343434")
    colors.append("#363636")
    colors.append("#383838")
    colors.append("#3A3A3A")
    colors.append("#3C3C3C")
    colors.append("#3E3E3E")
    colors.append("#404040")
    colors.append("#424242")
    colors.append("#444444")
    colors.append("#464646")
    colors.append("#484848")
    colors.append("#4A4A4A")
    colors.append("#4C4C4C")
    colors.append("#4E4E4E")
    colors.append("#505050")
    colors.append("#525252")
    colors.append("#545454")
    colors.append("#565656")
    colors.append("#585858")
    colors.append("#5A5A5A")
    colors.append("#5C5C5C")
    colors.append("#5E5E5E")
    colors.append("#606060")
    colors.append("#626262")
    colors.append("#646464")
    colors.append("#666666")
    colors.append("#686868")
    colors.append("#6A6A6A")
    colors.append("#6C6C6C")
    colors.append("#6E6E6E")
    colors.append("#707070")
    colors.append("#727272")
    colors.append("#747474")
    colors.append("#767676")
    colors.append("#787878")
    colors.append("#7A7A7A")
    colors.append("#7C7C7C")
    colors.append("#7E7E7E")
    colors.append("#808080")
    colors.append("#828282")
    colors.append("#848484")
    colors.append("#868686")
    colors.append("#888888")
    colors.append("#8A8A8A")
    colors.append("#8C8C8C")
    colors.append("#8E8E8E")
    colors.append("#909090")
    colors.append("#929292")
    colors.append("#949494")
    colors.append("#969696")
    colors.append("#989898")
    colors.append("#9A9A9A")
    colors.append("#9C9C9C")
    colors.append("#9E9E9E")
    colors.append("#A0A0A0")
    colors.append("#A2A2A2")
    colors.append("#A4A4A4")
    colors.append("#A6A6A6")
    colors.append("#A8A8A8")
    colors.append("#AAAAAA")
    colors.append("#ACACAC")
    colors.append("#AEAEAE")
    colors.append("#B0B0B0")
    colors.append("#B2B2B2")
    colors.append("#B4B4B4")
    colors.append("#B6B6B6")
    colors.append("#B8B8B8")
    colors.append("#BABABA")
    colors.append("#BCBCBC")
    colors.append("#BEBEBE")
    colors.append("#C0C0C0")
    colors.append("#C2C2C2")
    colors.append("#C4C4C4")
    colors.append("#C6C6C6")
    colors.append("#C8C8C8")
    colors.append("#CACACA")
    colors.append("#CCCCCC")
    colors.append("#CECECE")
    colors.append("#D0D0D0")
    colors.append("#D2D2D2")
    colors.append("#D4D4D4")
    colors.append("#D6D6D6")
    colors.append("#D8D8D8")
    colors.append("#DADADA")
    colors.append("#DCDCDC")
    colors.append("#DEDEDE")
    colors.append("#E0E0E0")
    colors.append("#E2E2E2")
    colors.append("#E4E4E4")
    colors.append("#E6E6E6")
    colors.append("#E8E8E8")
    colors.append("#EAEAEA")
    colors.append("#ECECEC")
    colors.append("#EEEEEE")
    colors.append("#F0F0F0")
    colors.append("#F2F2F2")
    colors.append("#F4F4F4")
    colors.append("#F6F6F6")
    colors.append("#F8F8F8")
    colors.append("#FAFAFA")
    colors.append("#FCFCFC")
    colors.append("#FEFEFE")
    colors.append("#FFFFFF")

def convert_encryption_to_colors(encrypted_text):
    output = ""
    for char in encrypted_text:
        output = output + colors[ord(char)]
    return output

def convert_colors_to_encryption(color_values):
    output = ""
    temp = color_values.split("#")
    for x in range(1, len(temp)):
        temp_color = "#" + temp[x]
        output = output + chr(colors.index(temp_color.upper()))
    return output

def decrypt_image(location):  # Currently not using the 'location' for anything (i.e. hardcoded image)
    img = PIL_Image.open(location)    # rgba = img.convert("RGBA")  # If you want transparancy
    rgba = img.convert("RGB")
    datas = rgba.getdata()
    output = ""
    for item in datas:
        r = hex(item[0]).split('x')[-1].zfill(2)
        g = hex(item[1]).split('x')[-1].zfill(2)
        b = hex(item[2]).split('x')[-1].zfill(2)
        if r == '00' and g == '00' and b == '00':  # Ignore the black colors at the end that were for padding...
            pass
        else:
            output = output + "#" + str(r) + str(g) + str(b)
    return output

def create_encrypted_image_multiplier(color_values, square_size):
    length = len(color_values)/7
    square = math.ceil(math.sqrt(int(length)))
    image = PIL_Image.new(mode="RGB", size=(square * square_size, square * square_size), color=(255, 255, 255))
    temp = color_values.split("#")
    # rows x columns
    for x in range(int(image.width/square_size)):
        for y in range(int(image.height/square_size)):
            position = int((x*int(image.width/square_size)) + y) + 1
            if position > int(length):
                r=0
                g=0
                b=0
            else:
                r = int(temp[position][:2], 16)
                g = int(temp[position][2:-2], 16)
                b = int(temp[position][-2:], 16)
            x0 = y * square_size
            y0 = x * square_size
            x1 = x0 + square_size
            y1 = y0 + square_size
            img1 = PIL_ImageDraw.Draw(image)
            img1.rectangle((x0, y0, x1, y1), fill="#" + hex(r).split('x')[-1].zfill(2) + hex(g).split('x')[-1].zfill(2) + hex(b).split('x')[-1].zfill(2), outline=None)
    global img_Unsaved
    img_Unsaved = image

def decrypt_image_multiplier(location):  # Currently not using the 'location' for anything (i.e. hardcoded image)
    square_size = location.split(".")
    square_size = square_size[0]
    square_size = square_size.split("_")
    square_size = int(square_size[1])
    img = PIL_Image.open(location)
    # rgba = img.convert("RGBA")  # If you want transparancy
    rgba = img.convert("RGB")
    datas = rgba.getdata()
    output = ""
    height = int(img.height / square_size)
    pixels = list(datas)
    position = 0
    for row in range(height):
        for col in range(height):
            temp = pixels[position]
            r = hex(temp[0]).split('x')[-1].zfill(2)
            g = hex(temp[1]).split('x')[-1].zfill(2)
            b = hex(temp[2]).split('x')[-1].zfill(2)
            if r == '00' and g == '00' and b == '00':  # Ignore the black colors at the end that were for padding...
                pass
            else:
                output = output + "#" + str(r) + str(g) + str(b)
            position = position + square_size
        position = (row + 1) * square_size * height * square_size
    return output

"""
########################################################################################################################
"""

if __name__ == "__main__":
    # Check for command line arguments, and set the default_folder_path appropriately
    if len(sys.argv) > 1:  # If there is a command line argument, check if it is a folder
        if os.path.isdir(sys.argv[1]):  # Valid folder:  so set the default_folder_path to it
            default_folder_path = sys.argv[1]
        elif os.path.isdir(os.path.dirname(os.path.abspath(sys.argv[1]))):  # If valid file path was sent:  use folder path from it.
            default_folder_path = os.path.dirname(os.path.abspath(sys.argv[1]))
        elif "file://" in sys.argv[1]:  # In case using 'Bulk Rename' option in Nemo, get file path from first parameter and auto-select the files.
            update_parameter_files_at_start(sys.argv[1:])  # Convert URL encoded files to paths
            if os.path.isdir(os.path.dirname(os.path.abspath(parameter_files[0]))):  # If the first file is a valid path:  use folder path from it.
                default_folder_path = os.path.dirname(os.path.abspath(parameter_files[0]))
            else:  # Invalid first file path:  so set the default_folder_path to where the python file is
                default_folder_path = sys.path[0]
        else:  # Invalid file/folder paths:  so set the default_folder_path to where the python file is
            default_folder_path = sys.path[0]
    else:  # No command line argument:  so set the default_folder_path to where the python file is
        default_folder_path = sys.path[0]
    choose_colors()
    aes_class = AESCipher(key)  # Where the parameter is the "key"
    main = Main()
    gtk.main()